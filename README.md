# libryazhahand

**EN:** Tesla overlay library for Nintendo Switch homebrew. Source-compatible fork of [ppkantorski/libultrahand](https://github.com/ppkantorski/libultrahand) with the runtime config namespace changed from `ultrahand` to `ryazhahand` (overlays read themes/sounds/settings from `/config/ryazhahand/` instead of `/config/ultrahand/`). Used by Ryazhahand-Overlay and RCU. License: GPL-2.0.

---

## Что это

Tesla/overlay-библиотека для homebrew-оверлеев Nintendo Switch (libnx). Канонический submodule для всех проектов Ryazha-экосистемы:

- [Ryazhahand-Overlay](https://github.com/Dimasick-git/Ryazhahand-Overlay) — главный Tesla-меню.
- [RCU (ryazha-clk)](https://github.com/Dimasick-git/RCU) — overlay для управления частотами.
- Любые сторонние оверлеи которые хотят `/config/ryazhahand/` вместо `/config/ultrahand/`.

Source-совместима с upstream libultrahand — большинство Ultrahand-overlay'ев пересобираются под libryazhahand без правок исходников, только пересборка с новым submodule.

## Состав

| Каталог | Что внутри |
|---------|------------|
| `libryazha/` | C++ utility headers + i18n + config helpers. Фор `ult::` namespace (бинарная совместимость с upstream). |
| `libtesla/` | UI primitives (List, ListItem, NamedStepTrackBar и т.д.). Форк WerWolv/libtesla с дополнениями. |

Подключение в проектах:

```cpp
#include <tesla.hpp>     // UI: tsl::elm::*, tsl::Gui, tsl::changeTo, etc.
#include <tsl_utils.hpp> // ult:: namespace helpers
```

## Главные отличия от upstream

- `RYZHAND_*` symbol prefix (вместо `ULTRAHAND_*`).
- `BASE_CONFIG_PATH = "/config/ryazhahand/"`.
- PNG-обои через libpng (`loadPngToRGBA4444`) вместо raw `.rgba`.
- Расширенный аудио-pipeline (prime silent buffer в `Audio::initialize()` против первой-press lag'а).
- Поддержка `loadRGBA8888toRGBA4444` для notification-иконок (32×32).

## Использование как submodule

```sh
# В проекте, который зависит от Tesla:
git submodule add https://github.com/Dimasick-git/libryazhahand.git lib/libryazhahand
git submodule update --init --recursive

# Makefile:
LIBDIRS += $(CURDIR)/lib/libryazhahand
```

## Sync с upstream

`.upstream-sync` — коммит upstream libultrahand с которым мы синхронизированы. Обновление вручную:

```sh
# В корне libryazhahand:
git remote add upstream https://github.com/ppkantorski/libultrahand.git  # один раз
git fetch upstream
git merge upstream/main  # резолвим конфликты в global_vars.cpp -- наш ryazhahand namespace
echo "<new-upstream-sha>" > .upstream-sync
```

## Лицензия

GPL-2.0. См. `LICENSE`. Upstream lic-история сохранена в `SUB_LICENSE`.

Авторы: ppkantorski (upstream Ultrahand/libultra), WerWolv (libtesla основа), Dimasick-git (Ryazha-форк).
