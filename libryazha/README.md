# libryazha

Утилитарный модуль внутри [libryazhahand](../README.md): C++ headers для Tesla-overlay'ев (libnx). Source-совместим с `libultra` из upstream `ppkantorski/libultrahand`, но переcмаппит runtime-namespace на `ryazhahand` (см. родительский README).

## Подключение

```cpp
#include <tsl_utils.hpp>   // ult:: helpers (PNG, audio, config paths, i18n)
```

`ult::` namespace оставлен ради бинарной совместимости с upstream-overlay'ями. Имена `RYZHAND_*` (бывшие `ULTRAHAND_*`) внутри.

## Содержимое

- `source/global_vars.cpp` — пути конфигов (`/config/ryazhahand/`), wallpaper.png, sound packs.
- `source/tsl_utils.cpp` — PNG-обои (libpng → RGBA4444 packed), 32×32 notification icons.
- `source/audio.cpp` — audout стриминг + prime silent buffer (против первой-press lag).
- `include/tsl_utils.hpp` — публичные функции.

## Лицензия

GPL-2.0. Унаследовано от libultrahand. См. родительский `LICENSE`.
