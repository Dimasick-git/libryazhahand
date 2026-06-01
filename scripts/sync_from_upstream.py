#!/usr/bin/env python3
"""
libryazhahand <- libultrahand sync.

Pulls every commit since the last sync from ppkantorski/libultrahand and
re-applies it on top of our tree, rewriting branding inline so the result
stays a libryazhahand rather than a libultrahand checkout.

Branding rewrites are intentionally narrow: namespace identifiers and other
internal API names are kept identical to upstream so application code can
swap libraries by changing the include path / Makefile snippet only.

Path mapping: upstream uses `libultra/`, we keep our renamed `libryazha/`.
Files copied from upstream `libultra/foo` land in our tree at `libryazha/foo`.
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

# Branding rewrites applied to every text file we copy in from upstream.
# Order matters: longer/more specific patterns first.
CONTENT_REWRITES: list[tuple[str, str]] = [
    # Display name (exact case).
    (r'"Ultrahand"', '"RyazhaHand"'),
    # Config / runtime directory name used by the library.
    (r'"ultrahand"', '"ryazhahand"'),
    # README/doc-only mentions: leave package URLs like
    # github.com/ppkantorski/Ultrahand-Overlay untouched by anchoring on
    # word boundaries.
    (r"\bUltrahand-Overlay\b", "Ultrahand-Overlay"),  # keep upstream URL ref
    (r"\bUltrahand Overlay\b", "RyazhaHand Overlay"),
]

# Path mapping: upstream uses `libultra/`, we keep our renamed `libryazha/`.
# Public API (#include <ultra.hpp>, namespace ult::) stays identical so that
# overlays don't need any source-level change.
PATH_REWRITES: list[tuple[str, str]] = [
    ("libultra/", "libryazha/"),
]


def remap(path: str) -> str:
    for src, dst in PATH_REWRITES:
        if path.startswith(src):
            return dst + path[len(src):]
    return path


# Paths to never copy in (we don't want our README/workflow blown away).
EXCLUDED_PATHS = {
    "README.md",
    ".github/FUNDING.yml",
    ".github/workflows/sync_from_upstream.yml",
    ".github/workflows/verify_build.yml",
    "scripts/sync_from_upstream.py",
    # Upstream's mk file lives under our renamed name (ryazhahand.mk).
    # Never bring back the old filename: downstream Makefiles include
    # ryazhahand.mk and would break otherwise.
    "ultrahand.mk",
    "example/Makefile",
    "example/source/main.cpp",
    # Our libryazha/README.md is hand-translated.
    "libultra/README.md",
    # tesla.hpp upstream uses a GNU statement-expression macro
    # (`#define TSL_R_TRY(...) ({ ... })`) that GCC 15 in the devkitpro
    # CI container refuses to parse. We keep our do/while(0) rewrite.
    # If upstream eventually moves off the GNU extension, drop this entry.
    "libtesla/include/tesla.hpp",
    # tsl_utils.hpp / tsl_utils.cpp содержат наши кастомные добавки:
    # per-event sound toggles (useNavigationSound, useEnterSound, useExitSound,
    # useWallSound), u64 holdDurationMs (PR #309 backport), PNG-wallpaper loader,
    # RYZHAND_* идентификаторы, SOUND_SUPPORT_DISABLED, INPUT/HOLD_TIME strings,
    # TXT_READER / SOUND_EFFECTS / SOUND_NAVIGATION / ... строки UI,
    # LIBRYZHAND_TITLES / LIBRYZHAND_VERSIONS, RYZHAND_HAS_STARTED и т.д.
    # Слепое копирование из апстрима всё это затирает -- держим файлы вручную.
    "libultra/include/tsl_utils.hpp",
    "libultra/source/tsl_utils.cpp",
}


def run(cmd: list[str], cwd: str | None = None) -> str:
    out = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return out.stdout


def is_text_file(path: Path) -> bool:
    """Cheap heuristic: read 1 KiB and treat as text if no NUL bytes."""
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
        return b"\x00" not in chunk
    except OSError:
        return False


def rewrite_text(content: str) -> str:
    for pat, repl in CONTENT_REWRITES:
        content = re.sub(pat, repl, content)
    return content


def last_synced_sha(our_repo: Path) -> str | None:
    marker = our_repo / ".upstream-sync"
    if marker.exists():
        sha = marker.read_text().strip()
        return sha or None
    return None


def write_marker(our_repo: Path, sha: str) -> None:
    (our_repo / ".upstream-sync").write_text(sha + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--our-repo", default=os.getcwd(),
                    help="Path to libryazhahand working tree (default: cwd)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print what would change without writing")
    args = ap.parse_args()

    our_repo = Path(args.our_repo).resolve()
    if not (our_repo / ".git").exists():
        print(f"[!] {our_repo} is not a git repo")
        return 1

    with tempfile.TemporaryDirectory(prefix="libultra_") as tmp:
        upstream = Path(tmp) / "upstream"
        print(f"[*] Cloning upstream {UPSTREAM_URL} ...")
        run(["git", "clone", "--depth=50", "--branch", UPSTREAM_BRANCH,
             UPSTREAM_URL, str(upstream)])

        head_sha = run(["git", "rev-parse", "HEAD"], cwd=str(upstream)).strip()
        last_sha = last_synced_sha(our_repo)
        if last_sha == head_sha:
            print(f"[*] Already up to date with {head_sha[:7]}")
            return 0

        # Files changed in [last_sha, head_sha] (or all files on first sync).
        if last_sha:
            diff = run(["git", "diff", "--name-status", f"{last_sha}..{head_sha}"],
                       cwd=str(upstream))
        else:
            diff = run(["git", "ls-tree", "-r", "--name-only", head_sha],
                       cwd=str(upstream))
            diff = "\n".join(f"M\t{p}" for p in diff.splitlines() if p)

        changed = 0
        for line in diff.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            status = parts[0]
            upath  = parts[-1]            # path in upstream tree
            if upath in EXCLUDED_PATHS:
                continue
            path = remap(upath)           # path in our tree
            dst = our_repo / path

            if status.startswith("D"):
                if dst.exists():
                    print(f"  - delete {path}")
                    if not args.dry_run:
                        dst.unlink()
                        changed += 1
                continue

            src = upstream / upath
            if not src.exists():
                continue

            print(f"  ~ {status[:1]} {upath} -> {path}")
            if args.dry_run:
                changed += 1
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            if is_text_file(src):
                text = src.read_text(encoding="utf-8", errors="replace")
                text = rewrite_text(text)
                dst.write_text(text, encoding="utf-8")
            else:
                dst.write_bytes(src.read_bytes())
            changed += 1

        if changed == 0:
            print("[*] No applicable changes")
            return 0

        if args.dry_run:
            print(f"[*] {changed} file(s) would be updated (dry-run)")
            return 0

        write_marker(our_repo, head_sha)
        run(["git", "add", "-A"], cwd=str(our_repo))
        # Bail early if nothing actually changed in the index after rewrites.
        staged = run(["git", "diff", "--cached", "--name-only"], cwd=str(our_repo))
        if not staged.strip():
            print("[*] All upstream changes collapsed to no-ops after rewrite")
            return 0

        short = head_sha[:7]
        msg = f"sync: pull libultrahand upstream {short}"
        run(["git", "commit", "-m", msg], cwd=str(our_repo))
        print(f"[*] Committed sync to {short}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
