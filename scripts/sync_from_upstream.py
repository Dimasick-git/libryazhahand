#!/usr/bin/env python3
"""
libryazhahand <- libultrahand sync (v2: 3-way merge кастомных файлов).

Тянет коммиты ppkantorski/libultrahand с момента последнего синка
(.upstream-sync) и встраивает их в наше дерево:

  * обычные файлы      -- копирование с branding-переписыванием;
  * кастомные файлы    -- НАСТОЯЩЕЕ 3-way слияние (git merge-file):
                          base   = upstream@last-sync (переписанный),
                          ours   = наш файл с кастомами,
                          theirs = upstream@HEAD (переписанный).
                          Наши правки сохраняются, upstream-новинки вливаются.
                          Конфликт => файл остаётся нашим, скрипт выходит с
                          кодом 2, workflow открывает issue -- ничего не
                          ломается молча.

Branding-переписывание узкое и детерминированное: переименовываются только
наши идентификаторы/строки (RYZHAND_*, LIBRYZHAND_*, пути /config/ryazhahand/),
остальной API остаётся идентичным upstream, чтобы оверлеи подключали
библиотеку сменой include-пути.

Путь-маппинг: upstream `libultra/` -> наш `libryazha/`.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

UPSTREAM_URL    = "https://github.com/ppkantorski/libultrahand.git"
UPSTREAM_BRANCH = "main"

# ── Branding-переписывание ────────────────────────────────────────────────────
# Применяется к каждому текстовому файлу, приходящему из upstream (и к base, и
# к theirs при 3-way merge -- одинаково, чтобы diff был только содержательный).
# Порядок важен: длинные/специфичные паттерны раньше коротких.
CONTENT_REWRITES: list[tuple[str, str]] = [
    # Идентификаторы и lang-ключи (то, что ломало сборку при голом копировании:
    # tesla.cpp ссылался на ult::ULTRAHAND_CONFIG_INI_PATH, которого у нас нет).
    (r"\bLIBULTRAHAND_", "LIBRYZHAND_"),
    (r"\bCAPITAL_ULTRAHAND_", "CAPITAL_RYZHAND_"),
    (r"\bULTRAHAND_", "RYZHAND_"),
    # CamelCase-идентификаторы (наш форк переименовал useLibultrahandTitles/
    # Versions в tsl_utils.*; без этого правила каждый upstream-синк падает
    # в конфликт на строках объявления -- см. issue #12).
    (r"\buseLibultrahand", "useLibryazhahand"),
    # Runtime-пути.
    (r"/config/ultrahand/", "/config/ryazhahand/"),
    # Отображаемые имена.
    (r'"Ultrahand"', '"RyazhaHand"'),
    (r'"ultrahand"', '"ryazhahand"'),
    (r"\bUltrahand Overlay\b", "RyazhaHand Overlay"),
]

# Путь-маппинг: upstream `libultra/` -> наш `libryazha/`.
PATH_REWRITES: list[tuple[str, str]] = [
    ("libultra/", "libryazha/"),
]

# Никогда не трогаем (наша инфраструктура / переименованные файлы).
EXCLUDED_PATHS = {
    "README.md",
    ".github/FUNDING.yml",
    ".github/workflows/sync_from_upstream.yml",
    ".github/workflows/verify_build.yml",
    "scripts/sync_from_upstream.py",
    # Upstream-овский mk живёт у нас под именем ryazhahand.mk.
    "ultrahand.mk",
    "example/Makefile",
    "example/source/main.cpp",
    # Наш libryazha/README.md переведён вручную.
    "libultra/README.md",
}

# Файлы с нашими кастомами: вместо скипа -- 3-way merge.
#   tesla.hpp     -- do/while TSL_R_TRY (GCC15), кастомное аудио, RYZHAND_* пути;
#   tsl_utils.*   -- per-event sound toggles, форк-строки UI, PNG-обои и т.д.
MERGE_PATHS = {
    "libtesla/include/tesla.hpp",
    "libultra/include/tsl_utils.hpp",
    "libultra/source/tsl_utils.cpp",
}

# Пост-merge инварианты: если upstream перепишет эти куски и слияние их
# потеряет -- лучше упасть громко, чем уехать в сломанную сборку.
TESLA_HPP_GUARDS = [
    "do {",                       # do/while-форма TSL_R_TRY (GCC15-совместимая)
]


def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def remap(path: str) -> str:
    for src, dst in PATH_REWRITES:
        if path.startswith(src):
            return dst + path[len(src):]
    return path


def is_text(blob: bytes) -> bool:
    return b"\x00" not in blob[:4096]


def rewrite_text(content: str) -> str:
    for pat, repl in CONTENT_REWRITES:
        content = re.sub(pat, repl, content)
    return content


def upstream_file(upstream: Path, sha: str, path: str) -> str | None:
    """Содержимое файла из upstream-клона на коммите sha (с переписыванием)."""
    p = run(["git", "show", f"{sha}:{path}"], cwd=str(upstream), check=False)
    if p.returncode != 0:
        return None
    return rewrite_text(p.stdout)


def merge_three_way(ours_path: Path, base_text: str, theirs_text: str,
                    tmpdir: Path, label: str) -> tuple[bool, str]:
    """git merge-file: (clean?, merged-or-conflict text)."""
    o = tmpdir / "ours.txt";   o.write_text(ours_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    b = tmpdir / "base.txt";   b.write_text(base_text, encoding="utf-8")
    t = tmpdir / "theirs.txt"; t.write_text(theirs_text, encoding="utf-8")
    p = run(["git", "merge-file", "-p",
             "-L", "ours(libryazhahand)", "-L", f"base({label})", "-L", "theirs(upstream)",
             str(o), str(b), str(t)], check=False)
    return p.returncode == 0, p.stdout


def last_synced_sha(our_repo: Path) -> str | None:
    marker = our_repo / ".upstream-sync"
    if marker.exists():
        sha = marker.read_text().strip()
        return sha or None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--our-repo", default=os.getcwd())
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    our_repo = Path(args.our_repo).resolve()
    if not (our_repo / ".git").exists():
        print(f"[!] {our_repo} is not a git repo")
        return 1

    with tempfile.TemporaryDirectory(prefix="libultra_") as tmp:
        upstream = Path(tmp) / "upstream"
        mergetmp = Path(tmp) / "merge"
        mergetmp.mkdir()
        print(f"[*] Cloning upstream {UPSTREAM_URL} ...")
        # Полный клон: для 3-way merge нужен blob на last-sync коммите,
        # который может быть сколь угодно старым.
        run(["git", "clone", "--branch", UPSTREAM_BRANCH, UPSTREAM_URL, str(upstream)])

        head_sha = run(["git", "rev-parse", "HEAD"], cwd=str(upstream)).stdout.strip()
        last_sha = last_synced_sha(our_repo)
        if last_sha == head_sha:
            print(f"[*] Already up to date with {head_sha[:7]}")
            return 0
        if last_sha:
            ok = run(["git", "cat-file", "-e", f"{last_sha}^{{commit}}"],
                     cwd=str(upstream), check=False).returncode == 0
            if not ok:
                print(f"[!] last-sync sha {last_sha[:7]} отсутствует в upstream "
                      f"(force-push?) -- нужен ручной ресинк")
                return 1

        if last_sha:
            diff = run(["git", "diff", "--name-status", f"{last_sha}..{head_sha}"],
                       cwd=str(upstream)).stdout
        else:
            names = run(["git", "ls-tree", "-r", "--name-only", head_sha],
                        cwd=str(upstream)).stdout
            diff = "\n".join(f"M\t{p}" for p in names.splitlines() if p)

        changed = 0
        conflicts: list[str] = []
        for line in diff.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            status, upath = parts[0], parts[-1]
            if upath in EXCLUDED_PATHS:
                continue
            path = remap(upath)
            dst = our_repo / path

            if status.startswith("D"):
                if upath in MERGE_PATHS:
                    print(f"  ! upstream удалил кастомный {upath} -- оставляю наш, требуется ручное решение")
                    conflicts.append(path)
                    continue
                if dst.exists():
                    print(f"  - delete {path}")
                    if not args.dry_run:
                        dst.unlink()
                    changed += 1
                continue

            if upath in MERGE_PATHS:
                theirs = upstream_file(upstream, head_sha, upath)
                base = upstream_file(upstream, last_sha, upath) if last_sha else None
                if theirs is None:
                    continue
                if base is None or not dst.exists():
                    # первый синк файла: просто кладём upstream-версию
                    print(f"  ~ M {upath} -> {path} (первичная копия)")
                    if not args.dry_run:
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        dst.write_text(theirs, encoding="utf-8")
                    changed += 1
                    continue
                clean, merged = merge_three_way(dst, base, theirs, mergetmp, last_sha[:7])
                if not clean:
                    print(f"  ✗ CONFLICT {path} -- оставляю наш файл; нужен человек")
                    conflicts.append(path)
                    continue
                if upath == "libtesla/include/tesla.hpp":
                    missing = [g for g in TESLA_HPP_GUARDS if g not in merged]
                    if missing:
                        print(f"  ✗ GUARD-FAIL {path}: после merge пропали {missing}")
                        conflicts.append(path)
                        continue
                print(f"  ⇄ merge {upath} -> {path}")
                if not args.dry_run:
                    dst.write_text(merged, encoding="utf-8")
                changed += 1
                continue

            # обычный файл: копирование с переписыванием
            probe = run(["git", "show", f"{head_sha}:{upath}"], cwd=str(upstream), check=False)
            if probe.returncode != 0:
                continue
            print(f"  ~ {status[:1]} {upath} -> {path}")
            if args.dry_run:
                changed += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            raw = subprocess.run(["git", "show", f"{head_sha}:{upath}"], cwd=str(upstream),
                                 capture_output=True).stdout
            if is_text(raw):
                dst.write_text(rewrite_text(raw.decode("utf-8", errors="replace")), encoding="utf-8")
            else:
                dst.write_bytes(raw)
            changed += 1

        if conflicts:
            print(f"[!] {len(conflicts)} файл(ов) с конфликтами: {', '.join(conflicts)}")
            print("[!] Коммит не создан, маркер не сдвинут -- разрулите вручную и перезапустите.")
            return 2

        if changed == 0:
            print("[*] No applicable changes")
            return 0

        if args.dry_run:
            print(f"[*] {changed} file(s) would be updated (dry-run)")
            return 0

        (our_repo / ".upstream-sync").write_text(head_sha + "\n")
        run(["git", "add", "-A"], cwd=str(our_repo))
        staged = run(["git", "diff", "--cached", "--name-only"], cwd=str(our_repo)).stdout
        if not staged.strip():
            print("[*] All upstream changes collapsed to no-ops after rewrite")
            return 0

        short = head_sha[:7]
        run(["git", "commit", "-m", f"sync: pull libultrahand upstream {short} (3-way merge кастомов)"],
            cwd=str(our_repo))
        print(f"[*] Committed sync to {short}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
