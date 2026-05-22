# libryazha

Утилитарный «скелет» библиотеки [libryazhahand](../README.md): набор
C++-заголовков для разработки Tesla-overlay'ев под Nintendo Switch
(libnx). Является source-совместимым форком `libultra` из upstream
`ppkantorski/libultrahand`, но рассчитан на runtime-namespace
`ryazhahand` (см. родительский README).

Подключение через единый заголовок:

```cpp
#include <ryz.hpp>
```

(namespace `ult::` сохранён ради бинарной совместимости с upstream
libultrahand -- упрощает cherry-pick патчей через sync_from_upstream.py)

---

## Состав

### `ryz.hpp`
Корневой include, подтягивающий все остальные заголовки libryazha
одним подключением. Поддерживает директивы `RYZ_TARGETED_SPEED` и
`RYZ_TARGETED_SIZE` для покомпонентной оптимизации.

### `global_vars.hpp`
Глобальные константы, общие пути, атомарные переменные состояния.

- Канонические пути: `SETTINGS_PATH`, `OVERLAY_PATH`, `PACKAGE_PATH`,
  `DOWNLOADS_PATH`, `SOUNDS_PATH`, `NOTIFICATIONS_PATH`.
- Атомарные счётчики: `downloadPercentage`, `unzipPercentage`,
  `copyPercentage`, `displayPercentage`.
- UI-символы: `CHECKMARK_SYMBOL`, `CROSSMARK_SYMBOL`, `DOWNLOAD_SYMBOL`,
  `STAR_SYMBOL`, `THROBBER_SYMBOLS`.

### `debug_funcs.hpp`
Потокобезопасный лог с timestamp в файл.

```cpp
ult::logMessage("событие в оверлее");
```

### `string_funcs.hpp`
Строковые утилиты: split, trim, replace, padding, числовые конверсии,
UTF-8-aware длина.

### `path_funcs.hpp`
File I/O для оверлея: безопасное чтение/запись, копирование папок,
рекурсивное удаление, поиск файлов, проверка существования.

### `ini_funcs.hpp`
INI-парсер совместимый с конфигом upstream Ultrahand. Чтение, запись,
обновление секций. Атомарная запись через temp-файл.

### `json_funcs.hpp`
Тонкая обёртка над cJSON. Чтение/запись JSON-документов с понятными
ошибками.

### `hex_funcs.hpp`
Hex-патчинг бинарей: поиск pattern → patch, маски, чтение/запись
произвольных смещений.

### `download_funcs.hpp`
HTTP/HTTPS-загрузки через libcurl с прогрессом и retries.

### `list_funcs.hpp`
Утилиты работы со списками: фильтрация, сортировка, поиск.

### `mod_funcs.hpp`
Конвертеры модов и пакетов оверлеев.

### `audio.hpp`
Воспроизведение WAV/звуков из `sdmc:/config/ryazhahand/sounds/`.

### `haptics.hpp`
Управление вибрацией Joy-Con через `hidsys` / `hidvibrationdevice`.

### `tsl_utils.hpp`
Утилиты между libryazha и libtesla: маппинг кнопок, чтение INPUT-INI,
hold-time, конфигурация UI.

### `exception_wrap.hpp`
Обёртка вокруг исключений: подменяет `__cxa_throw`, `_Unwind_Resume`,
`__gxx_personality_v0` на no-op для уменьшения размера бинаря и
ускорения link'а.

Активируется флагом `USE_EXCEPTION_WRAP=1` в Makefile + соответствующие
`-Wl,--wrap=...` в LDFLAGS + `-fno-exceptions` в CXXFLAGS.

---

## Использование

Просто `include ${TOPDIR}/lib/libryazhahand/ryazhahand.mk` в Makefile
оверлея — `INCLUDES` и `SOURCES` подтянутся автоматически.

## Лицензия

GPL-2.0. См. `LICENSE` в корне репозитория. Авторство upstream
сохранено в `SUB_LICENSE` (ppkantorski). Автор форка: **Dimasick-git**.
