# libryazhahand

Lightweight Tesla/Ultra-overlay library used by the [Ryazha-CLK](https://github.com/Dimanchikgshehsbshene/RCU)
ecosystem. Source-compatible fork of [ppkantorski/libultrahand](https://github.com/ppkantorski/libultrahand)
with one practical change: the runtime config namespace is `ryazhahand` instead of
`ultrahand`, so overlays built against this library look in
`/config/ryazhahand/` for themes, sounds, and overlay settings.

## Relationship to upstream

`scripts/sync_from_upstream.py` runs daily via GitHub Actions and mirrors new
commits from `ppkantorski/libultrahand`. Each upstream commit is replayed on top
of this tree with a narrow set of branding rewrites (see `CONTENT_REWRITES` in
the script). Public namespaces, headers, and class/function signatures match
upstream exactly so swapping libraries is a one-line change in your `Makefile`.

The current upstream checkpoint is recorded in `.upstream-sync`. Manual sync:

```sh
python3 scripts/sync_from_upstream.py            # apply
python3 scripts/sync_from_upstream.py --dry-run  # preview
```

## Usage in a project

Add it as a git submodule under your overlay:

```sh
git submodule add https://github.com/Dimanchikgshehsbshene/libryazhahand.git \
    lib/libryazhahand
```

Then in your overlay's `Makefile`:

```make
include ${TOPDIR}/lib/libryazhahand/ultrahand.mk
```

That's it — the include path, source list, and link flags are pulled in
automatically.

## Config directory

| Asset      | Lives in                                                  |
|------------|-----------------------------------------------------------|
| Themes     | `sdmc:/config/ryazhahand/themes/`                         |
| Sounds     | `sdmc:/config/ryazhahand/sounds/`                         |
| Overlays   | `sdmc:/switch/.overlays/`                                 |
| Library config | `sdmc:/config/ryazhahand/config.ini`                  |

## License

GPL-2.0 — see `LICENSE`. Upstream license is preserved in `SUB_LICENSE`.
