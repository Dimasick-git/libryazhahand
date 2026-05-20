# libryazhahand

Лёгкая Tesla/overlay-библиотека, лежащая в основе экосистемы
[Ryazhahand-Overlay](https://github.com/Dimanchikgshehsbshene/Ryazhahand-Overlay)
и [RCU (ryazha-clk)](https://github.com/Dimanchikgshehsbshene/RCU).
Это source-совместимый форк
[ppkantorski/libultrahand](https://github.com/ppkantorski/libultrahand) с одним
практическим изменением: runtime-namespace конфигурации называется
`ryazhahand`, а не `ultrahand`. Оверлеи, собранные с этой библиотекой,
читают темы, звуки и настройки из `/config/ryazhahand/`.

- Автор форка: **Dimasick-git**
- Лицензия: **GPL-2.0** (см. `LICENSE`, оригинальная лицензия upstream
  сохранена в `SUB_LICENSE`)
- Версия API: совместима с upstream libultrahand на коммите, указанном в
  `.upstream-sync`

## Что внутри

| Каталог | Описание |
|------------|------------------------------------------------------------|
| `libryazha/` | Логика библиотеки: I/O, JSON, INI, hex, путь, аудио, haptics. |
| `libtesla/` | Tesla overlay-фреймворк: GUI, элементы, ввод, рендер. |
| `common/` | Общий код: download, exception wrap, cJSON, get_funcs. |
| `example/` | Минимальный референсный overlay (собирается через CI). |
| `scripts/` | `sync_from_upstream.py` — авто-синхронизация с upstream. |

## Подключение в проект

Добавьте библиотеку как git submodule в оверлей:

```sh
git submodule add https://github.com/Dimanchikgshehsbshene/libryazhahand.git \
    lib/libryazhahand
```

Затем в `Makefile` оверлея:

```make
include ${TOPDIR}/lib/libryazhahand/ryazhahand.mk
```

Этого достаточно — пути include, список source-файлов и -I флаги
подтянутся автоматически. Линковка libs (`-lcurl -lz -lmbedtls
-lmbedx509 -lmbedcrypto -lnx`) и `-D__SWITCH__` остаются на стороне
оверлея, как у upstream.

## Каталоги конфигурации

| Что | Лежит в |
|-----------------|-----------------------------------------------------------|
| Темы | `sdmc:/config/ryazhahand/themes/` |
| Звуки | `sdmc:/config/ryazhahand/sounds/` |
| Оверлеи | `sdmc:/switch/.overlays/` |
| Конфиг библиотеки | `sdmc:/config/ryazhahand/config.ini` |

## Синхронизация с upstream

`scripts/sync_from_upstream.py` запускается раз в сутки через GitHub
Actions (`.github/workflows/sync_from_upstream.yml`) и переносит новые
коммиты из `ppkantorski/libultrahand` в это дерево. Каждый коммит
проходит через узкий набор branding-переписывалок (см. `CONTENT_REWRITES`
в скрипте). Публичные namespace, заголовки, сигнатуры классов и функций
совпадают с upstream, чтобы смена библиотеки в оверлее сводилась к
изменению `include` в `Makefile`.

Текущая отметка upstream хранится в `.upstream-sync`. Ручной запуск:

```sh
python3 scripts/sync_from_upstream.py            # применить
python3 scripts/sync_from_upstream.py --dry-run  # предпросмотр
```

## Сборка example

```sh
cd example
make -j$(nproc)
```

CI (`.github/workflows/verify_build.yml`) делает то же самое в контейнере
`devkitpro/devkita64` и помечает PR красным, если сборка падает.

## Где используется

- [Ryazhahand-Overlay](https://github.com/Dimanchikgshehsbshene/Ryazhahand-Overlay) — основной overlay-меню для CFW Switch.
- [RCU / ryazha-clk](https://github.com/Dimanchikgshehsbshene/RCU) — overlay управления частотами и режимами CFW.
- RyazhaTune, Ryazha-Status-Monitor, Living_Ladders — модули из общей
  экосистемы, использующие тот же libryazhahand.

## Лицензия

GPL-2.0 (см. `LICENSE`). Все upstream-права сохранены, авторство
оригинала `ppkantorski` указано в `SUB_LICENSE`.
