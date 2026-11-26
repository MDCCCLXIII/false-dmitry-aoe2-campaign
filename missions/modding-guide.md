# Руководство: мод данных для AoE2 DE (проект «Лжедмитрий I»)

Дата исследования: 26.11.2026. Ничего не скачивалось и не устанавливалось, файлы игры не изменялись (только чтение).

## 0. Что установлено на этом компьютере (проверено чтением файлов)

| Что | Значение | Как проверено |
|---|---|---|
| Steam-билд | `buildid 26249352` (appid 813780) | `steamapps\appmanifest_813780.acf` |
| Файл данных | `AoE2DE\resources\_common\dat\empires2_x2_p1.dat`, 11 963 833 байт, изменён 29.10.2026 | список файлов |
| Версия формата DAT | **`VER 8.9`** | распаковал первые байты (zlib) Python-скриптом, только чтение |
| Профиль игры | `%USERPROFILE%\Games\Age of Empires 2 DE\<STEAM_ID>\` | список папок |
| Папки модов | `...\mods\local\` (пусто), `...\mods\subscribed\`, `...\mods\mod-status.json` | список папок |
| AGE в комплекте с игрой | `AoE2DE\Tools_Builds\AdvancedGenieEditor3.exe` (файл от 07.06.2026, ReadMe рядом: последняя версия в истории 2026.2.12) | `Tools_Builds\docs\AGE_ReadMe.txt` |
| texconv в комплекте с игрой | `AoE2DE\Tools_Builds\texconv.exe`, `texassemble.exe` | список файлов |
| Python-окружение проекта | `.venv` с `AoE2ScenarioParser 0.9.9` | список site-packages |

Важно: поддержку `VER 8.9` в библиотеку genieutils (основа AGE) добавили 08.07.2026 (коммит «Added support for more versions of AoE 2 DE»). Встроенный в игру AGE собран раньше (июнь 2026, версия ≤ 2026.2.12), поэтому **он, скорее всего, не откроет текущий DAT** `[ПРОВЕРИТЬ: запустить встроенный AGE и посмотреть, выдаст ли «Unsupported version VER 8.9»]`. Нужен AGE 2026.10.22 с GitHub.

## 1. Структура мода DE

Мод — это папка в `mods\local\`, повторяющая структуру `resources` игры. Игра берёт файл из мода вместо оригинального с тем же относительным путём.

```
%USERPROFILE%\Games\Age of Empires 2 DE\<STEAM_ID>\mods\local\Lzhedmitry Data\
├── info.json
├── thumbnail.jpg                       (необязательно, превью в менеджере модов)
├── resources\
│   ├── _common\
│   │   ├── dat\
│   │   │   ├── empires2_x2_p1.dat      (КОПИЯ оригинала, правленная в AGE)
│   │   │   └── civilizations.json      (копия оригинала; сообщество советует класть всегда)
│   │   ├── drs\...                     (звуки/графика, если нужны; сейчас не нужны)
│   │   └── wpfg\resources\
│   │       ├── civ_emblems\slavs.png   (герб в меню выбора цивилизации)
│   │       ├── civ_techtree\menu_techtree_slavs.png
│   │       └── uniticons\NNN_50730.png (иконка юнита для дерева технологий)
│   ├── ru\strings\key-value\key-value-modded-strings-utf8.txt   (русские строки)
│   ├── en\strings\key-value\key-value-modded-strings-utf8.txt   (английский запасной вариант)
│   └── ru\strings\history\slavs-utf8.txt  (текст «Истории» цивилизации, при желании)
└── widgetui\textures\ingame\
    ├── units\NNN_50730.DDS             (иконка юнита в игре, кнопка обучения)
    └── emblems\slavs.png               (герб в интерфейсе матча)
```

Подтверждения:
- Путь `resources\_common\dat\` для DAT и `info.json` в корне мода: гайд на форуме Age of Empires (раздел 7, ссылки [F1], [F3]).
- Зеркальная структура и поля `info.json`: UGC Guide [G1].
- Официальный мод «[TheVikingSagas] Main Menu» на этом компьютере (подписка) переопределяет и `resources\_common\wpfg\...`, и `widgetui\textures\...`: значит, моды могут подменять обе ветки.
- Шаблон строк: в игре уже лежит `resources\ru\strings\key-value\key-value-modded-strings-utf8.txt` с комментарием разработчиков: в этот файл кладут только изменяемые/новые строки, исходные не удалять; английский файл служит запасным, если строки нет в родном языке.
- Иконки юнитов в игре: `widgetui\textures\ingame\units\114_50730.DDS` (боярин; 256×256, несжатый 32-бит), новые файлы 128×128. Номер файла = поле «Icon ID» юнита в DAT. В дереве технологий: `resources\_common\wpfg\resources\uniticons\114_50730.png` (путь прописан в `civilizations.json`).

### info.json

Генератор не нужен: это одна строка JSON. Пример официального мода на этом компьютере:
```json
{"Author":"AoE Official","CacheStatus":0,"Description":"The Viking Sagas main menu background mod","Title":"[TheVikingSagas] Main Menu"}
```
Для нас: `{"Author":"FalseDmitryMod","CacheStatus":0,"Description":"Русские вместо славян, стрелец","Title":"Lzhedmitry Data"}`. Сохранять в UTF-8. `Title` — имя в меню модов.

### Как игра подхватывает мод и как его включить
1. Положить папку в `mods\local\`.
2. В игре: «Моды» → «Мои моды» → кнопка **Import Local Mods** (импортировать локальные моды). Без неё бывает ошибка «Problem Loading Data Mod» [F2], [S1]. После каждой правки DAT: перезапуск игры или повторный импорт [F3].
3. Мод с DAT — это **мод данных (Data Mod)**. Он не включается галочкой, а выбирается из выпадающего списка «Data Mod» внизу экрана: в Редакторе сценариев перед «Создать сценарий», в одиночной игре/лобби, в экране кампании (справа от выбора сложности) [F2], [F5]. В обычной игре без выбора действует стандартный набор данных [F1].
4. Строковые/интерфейсные части (строки, иконки) — обычные моды: включаются галочкой и приоритетом. После обновления Return of Rome UI-мод вместе с DAT в одной папке работает, но иконки цивилизаций, по опыту автора гайда, требовали отдельного мода [F1]; UGC Guide предупреждает, что смешивание мода данных с UI/контентом «снова сломано» [G1]. Практичный вариант: **два мода** — «Lzhedmitry Data» (DAT + civilizations.json) и «Lzhedmitry UI» (строки, иконки, гербы), второй включить галочкой с высоким приоритетом. `[ПРОВЕРИТЬ на текущем билде, работает ли всё в одной папке]`

### Сетевая игра
- Моды данных **не скачиваются автоматически** (в отличие от пользовательских сценариев): каждый игрок должен сам подписаться на тот же мод той же версии; иначе лобби пишет, что версия устарела [S1].
- Для мультиплеера мод публикуют через менеджер модов (mods.aoe2.com), после чего его можно выбрать при создании лобби [S1]. Все клиенты должны иметь идентичный DAT, иначе рассинхрон.

### Сценарии
- Сценарий (`.aoe2scenario`) не содержит DAT. Он хранит ID юнитов/технологий. Если сценарий ставит юнит «Стрелец» с новым ID, без мода данных этот ID не существует → ошибка «Could not create world. Possibly the required dataset is unavailable» или пропажа юнитов [F4].
- Порядок работы: в Редакторе выбрать Data Mod → «Создать сценарий» (**новый**, а не открыть старый) → новые юниты появятся в списке, если у них в AGE снят флаг «Hide in Editor» [F3].
- Игрок перед запуском сценария/кампании должен выбрать тот же Data Mod в выпадающем списке. Автоматической зависимости «сценарий → мод данных» нет; есть только запрос сообщества на такую функцию [F6]. В описании сценария и кампании нужно писать: «Требуется мод данных Lzhedmitry Data».
- Наш генератор (`AoE2ScenarioParser`) ставит юниты по числовому ID, поэтому новые ID из DAT можно вписать в `data/units.json`. Подтвердить `[ПРОВЕРИТЬ: AoE2ScenarioParser допускает ID вне своего перечня UnitInfo, передав число]`.

## 2. Инструменты: что и откуда скачать

| # | Инструмент | Официальная страница | Что скачать | Размер | Как проверено |
|---|---|---|---|---|---|
| 1 | **Advanced Genie Editor (AGE)**, Tapsa, версия **2026.10.22** (последняя, 22.10.2026; поддерживает `VER 8.9`) | https://github.com/Tapsa/AGE/releases | `AdvancedGenieEditor20261022x64.zip` (прямая ссылка: https://github.com/Tapsa/AGE/releases/download/2026.10.22/AdvancedGenieEditor20261022x64.zip) | 3 809 943 байт (≈3,6 МБ) | Открыл страницу релизов и страницу ассетов; имя/размер — через GitHub API; поддержку 8.9 — по исходнику `genieutils/include/genie/Types.h` (`{"VER 8.9", GV_C32}`) |
| 2 | **texconv** (Microsoft DirectXTex) — конвертация PNG→DDS | https://github.com/microsoft/DirectXTex/releases | **Не скачивать**: уже есть `AoE2DE\Tools_Builds\texconv.exe`. Если нужен новее: `texconv.exe` из релиза `may2026` | 966 480 байт | Открыл страницу релизов; имя/размер — через GitHub API; локальный файл — списком папки |
| 3 | **GIMP** 3.2.8 — рисование иконки 128×128 / 256×256, экспорт PNG (умеет и DDS) | https://www.gimp.org/downloads/ | `gimp-3.2.8-setup.exe` (с download.gimp.org) | ≈ несколько сотен МБ `[ПРОВЕРИТЬ размер на странице]` | Загрузил HTML страницы curl'ом: «current stable release of GIMP is 3.2.8», ссылка `download.gimp.org/gimp/v3.2/windows/gimp-3.2.8-setup.exe` |
| 4 | Редактор строк | — | **Не нужен**: файл `key-value-modded-strings-utf8.txt` — обычный UTF-8 текст, хватит Блокнота Windows или VS Code. Опционально Notepad++ 8.9.9.1 с https://notepad-plus-plus.org/downloads/ | — | Страница Notepad++ ответила HTTP 200 (curl), версия видна в ссылках; WebFetch к домену заблокирован политикой |
| 5 | Генератор info.json | — | **Не нужен** (одна строка JSON, см. выше; менеджер модов игры сам дополняет при публикации) | — | По образцу официального мода на диске |
| 6 | (опционально, для автоматизации) **genieutils-py** 0.1.2 — Python-правка DAT скриптом вместо ручного AGE | https://github.com/SiegeEngineers/genieutils-py , PyPI `genieutils-py` | `pip install genieutils-py==0.1.2` в `.venv` (wheel `genieutils_py-0.1.2-py3-none-any.whl`, 30 КБ) | 30 313 байт | PyPI JSON API; коммит 28.04.2026 «Support FileVersion 8.9»; рекомендован UGC Guide [G2] |

Предостережения:
- AGE скачивать **только с GitHub Tapsa/AGE**. Старые сборки на AoK Heaven (aok.heavengames.com, fileid=11002) и «All-in-One» на сторонних сайтах (ageofnotes.com и т. п.) устаревшие: пользователи пишут, что версия с Heaven не открывает DE-файл [F7]. Неофициальные зеркала могут содержать вредоносный код.
- AGE распространяется как zip без установщика: «распаковать куда угодно и запустить» (ReadMe). Если какой-то сайт предлагает «AGE Setup.exe» или загрузчик — это не официальный файл.
- GIMP: только gimp.org / download.gimp.org; на сторонних «download»-порталах бывают обёртки с рекламными установщиками. При установке ничего лишнего не предлагается; если предлагается — файл не тот.
- Notepad++: только notepad-plus-plus.org (существуют поддельные похожие домены).
- Антивирус: AGE — неподписанный exe, Windows SmartScreen может предупредить «неизвестный издатель». Это ожидаемо для файла с GitHub Tapsa; перед запуском проверить zip в Защитнике Windows (ПКМ → «Проверить»). Не отключать антивирус.
- Paint.NET (getpaint.net) проверить не удалось: сайт с этого компьютера не открылся (WebFetch: DNS-ошибка, curl: 301 без продолжения). Не нужен, GIMP достаточно.

### Порядок установки
1. Сделать резервные копии (раздел 5).
2. AGE 2026.10.22 x64 → распаковать в `C:\Tools\AGE\` (не в `steamapps`).
3. GIMP (если будем рисовать иконку сами).
4. texconv — уже есть в `Tools_Builds`.
5. Опционально genieutils-py в `.venv`.

## 3. Как открыть и сохранить DAT в AGE
1. Скопировать `AoE2DE\resources\_common\dat\empires2_x2_p1.dat` и `civilizations.json` в `mods\local\Lzhedmitry Data\resources\_common\dat\`. Оригинал не трогать.
2. Запустить AGE → окно «Open» → версия игры **Age of Empires II: Definitive Edition**, путь к DAT — **копия в папке мода**. Языковые файлы DLL не указывать (в DE строки в txt) `[ПРОВЕРИТЬ: поля пути к key-value в AGE]`. Путь к папке игры можно указать для просмотра графики.
3. Правки → File → Save (сохранение в тот же файл копии). AGE с 2024.4.18 предупреждает при сохранении в `steamapps` — это сигнал, что открыт оригинал; отменить. Включить авто-бэкап AGE в настройках («Make your own backups or use the auto-backup feature!» — ReadMe).
4. В игре: Import Local Mods → выбрать Data Mod → Редактор → новый сценарий → проверить.

## 4. Добавление юнита «Стрелец» и технологии (на уровне идей)

### Юнит
1. Вкладка **Units**, цивилизация любая (юниты дублируются по всем цивилизациям; копировать/вставлять для всех). Найти **Hand Cannoneer** (ручной пушкарь, ID 5 `[ПРОВЕРИТЬ в AGE]`).
2. **Copy → Paste в конец списка** («Add»/«Paste insert» в конец). **Не использовать «Insert copies» в середину**: это сдвигает ID и ломает дерево технологий и сценарии [S1]. Новый ID = следующий свободный (например 2000+; запомнить и записать в `data/units.json`).
3. Поля:
   - **Language File Name / Creation / Help / Short Tooltip ID / Extended Tooltip ID** → новые номера строк (свободный диапазон, например 1 001 000+ `[ПРОВЕРИТЬ, что номера не заняты]`), тексты — в `key-value-modded-strings-utf8.txt`:
     ```
     1001000 "Стрелец"
     1001001 "Создать <b>стрельца<b> (<cost>)\nРусская пехота с пищалью и бердышом. ..."
     ```
   - **Icon ID / Button Icon ID** → свой номер (например 940) → файлы `widgetui\textures\ingame\units\940_50730.DDS` и `resources\_common\wpfg\resources\uniticons\940_50730.png`.
   - **Hide in Editor = 0**, чтобы появился в Редакторе [F3].
   - Характеристики (HP, атака, броня, точность, стоимость, время обучения), **Train Location** = Castle (замок, ID 82) или Barracks (казарма, ID 12), номер кнопки. С 2025.2.13 у юнита может быть несколько мест обучения.
   - **Enabled = 0** у всех цивилизаций, кроме нужной (или оставить выключенным и открывать технологией).
4. Графику и звуки оставить от ручного пушкаря (новые спрайты — отдельная большая работа).

### Технология открытия
1. Вкладка **Effects**: создать новый эффект (в конец), команда «Enable/Disable Unit» → ID стрельца, режим «включить».
2. Вкладка **Techs**: новая технология (в конец): имя/описание через строки, Civilization = нужная, Research Location = Castle, стоимость/время, Effect = созданный эффект. Для «доступен сразу» — технология без стоимости с флагом автоматического изучения или эффект в «Tech tree» цивилизации. Для элитного варианта — второй юнит + эффект «Upgrade Unit».
3. Для сценариев проще: юнит выключен, а триггер «Изменить доступность объекта / Enable Object» в сценарии включает его. Это не требует технологии вовсе.

## 5. «Переделать славян в русских»
Уровень 1 (только строки, без DAT; работает и в обычной игре как UI-мод):
- `10293` «Славяне» → «Русские»; `20352` «Славяне» (вторая копия названия); `90293` «Нажмите, чтобы играть за славян.»; `120172` описание для дерева технологий (бонусы, уникальный юнит, технологии); история — `resources\ru\strings\history\slavs-utf8.txt`.
- Уникальный юнит: `5447` «Боярин», `26447`/`26449` подсказки; технологии: `7448`/`17448`/`28448` «Детинец», `7269`/`17269`/`28269` «Дружина». (Номера найдены в русском файле строк этого билда.)
- Имена ИИ-правителей: `computer_name_string_table_offset` 5980 в `civilizations.json` (строки `5981…`: «Игорь Старый» и др.).
- То же продублировать в `en\...` (запасной язык).

Уровень 2 (DAT + civilizations.json, только как мод данных):
- Бонусы цивилизации — эффекты/техи цивилизации Slavs во вкладках Techs/Effects (бонусы гражданского типа — техи с Civilization = Slavs, подключённые к «Civ bonus/Tech tree» эффекту). Менять значения в командах; ненужные бонусы не удалять, а ставить Effect = −1 (удаление сдвигает индексы) [F1].
- Сменить уникальный юнит на стрельца: в `civilizations.json` у записи `"internal_name": "Slavs"` поля `unique_unit_id` 876, `elite_unique_unit_id` 878, `unique_unit_line`, `unique_unit_upgrade_id` 504, `unique_unit_string_ids`, `unique_unit_image_paths`, `unique_tech_id_1/2` (513, 455) — именно они управляют деревом технологий, подсказками и ИИ («It is now possible to modify previously hardcoded civilization settings in civilizations.json» — официальные заметки поддержки [O1]).
- `internal_name`, `data_name` (`SLAVIC-CIV`), `tech_tree_name` **не менять**: на них опираются ИИ-скрипты, сценарии и сравнение с оригиналом; известны сбои при изменении `data_name` [F8].
- Герб: заменить `wpfg\resources\civ_emblems\slavs.png` и `widgetui\textures\ingame\emblems\slavs.png` (имя файла то же). Музыка и реплики остаются славянскими (ничего не делать).

## 6. Риски
- **Обновления игры ломают мод.** Каждое обновление меняет `empires2_x2_p1.dat`; старый DAT в моде продолжит работать как «другая версия» лишь до тех пор, пока формат не меняется, а с новым форматом — ошибка загрузки. Нужен журнал всех правок (какой ID, какое поле) и перенос в свежий DAT; крупные моды делают это скриптом на genieutils-py и держат в git [F9]. Наш проект: хранить изменения в `data/*.json` и писать скрипт применения.
- **AGE должен знать версию DAT.** После очередного патча может понадобиться новый AGE (в истории версий видны частые обновления под DE).
- **Ачивки.** С модом данных достижения не засчитываются (консенсус сообщества, официального заявления не нашёл) [S2].
- **Мультиплеер и синхронизация**: у всех одинаковый мод той же версии, сам он не скачивается [S1].
- **Сохранения** игр на моде данных могут не загружаться после изменения мода [F6].
- **Резервные копии (сначала!)**: перед любой работой скопировать в проект `backup\26249352\` файлы `empires2_x2_p1.dat`, `civilizations.json`, `key-value-modded-strings-utf8.txt` (ru/en) и записать buildid. Оригинал в `steamapps` никогда не перезаписывать (старый совет «заменить DAT в папке игры» [F10] — не применять: ломает мультиплеер и проверку файлов Steam).
- Ошибки флажков в AGE могут дать DAT, на котором игра падает [F9]; тестировать после каждой правки.

## 7. Чего нельзя / не стоит
- Нельзя сделать так, чтобы сценарий или кампания **сами** подгружали мод данных: игрок выбирает Data Mod вручную.
- Нельзя заставить мод данных скачиваться автоматически у соперников в сети.
- Добавить **новую, 5x-ю цивилизацию** рискованно: при числе цивилизаций, отличном от `civilizations.json`, мод не грузится, есть баги с описанием [F8]. Поэтому — переименовать существующих славян, а не добавлять «русских» отдельно.
- Не вставлять объекты в середину списков AGE (сдвиг ID).
- Не менять файлы в `steamapps\common\AoE2DE`.
- Не получить ачивки и рейтинговую игру с модом данных.
- Новые анимации/модели юнита — вне рамок этого мода (графика SMX — отдельная работа); стрелец использует спрайты ручного пушкаря.

## 8. Источники и как проверены
- [A1] https://github.com/Tapsa/AGE/releases — открыл (WebFetch), релиз 2026.10.22 «Latest»; ассеты — https://github.com/Tapsa/AGE/releases/expanded_assets/2026.10.22 (открыл) и GitHub API.
- [A2] https://github.com/Tapsa/genieutils — исходник `include/genie/Types.h` (curl raw), коммит 08.07.2026 (GitHub API).
- [A3] Локально: `AoE2DE\Tools_Builds\docs\AGE_ReadMe.txt` — прочитал.
- [T1] https://github.com/microsoft/DirectXTex/releases — открыл (WebFetch) + GitHub API.
- [T2] https://www.gimp.org/downloads/ — загрузил HTML (curl).
- [T3] https://notepad-plus-plus.org/downloads/ — HTTP 200 (curl), WebFetch заблокирован.
- [T4] https://pypi.org/project/genieutils-py/ — PyPI JSON API; https://github.com/SiegeEngineers/genieutils-py — API коммитов.
- [G1] https://ugc.aoe2.rocks/mods/ (бывш. divy1211.github.io/AoE2DE_UGC_Guide) — открыл.
- [G2] https://ugc.aoe2.rocks/tools/mods/ — открыл.
- [F1] https://forums.ageofempires.com/t/creating-custom-op-civs-with-advanced-genie-editor/178596 — открыл.
- [F2] https://steamcommunity.com/app/813780/discussions/4/4695657761337262292 — открыл (обозначено [S1]).
- [F3] https://forums.ageofempires.com/t/new-units-not-appearing-in-scenario-editor/80326 — открыл.
- [F4] https://forums.ageofempires.com/t/modding-via-genie-editor-gives-error-could-not-create-world-possibly-the-required-dataset-is-unavailable/84690 — только в выдаче поиска, не открывал.
- [F5] https://forums.ageofempires.com/t/is-the-data-mod-option-for-the-chronicle-dlc-officially-disabled/269867 — открыл.
- [F6] https://forums.ageofempires.com/t/request-loading-dataset-mods/72889 — только в выдаче поиска.
- [F7] https://forums.ageofempires.com/t/how-do-you-mod-this-games-dat-files-solved/60929 — только в выдаче поиска.
- [F8] https://forums.ageofempires.com/t/civilization-description-doesnt-work-the-same-way-for-modded-civilizations-as-for-regular-ones/231014 и …/many-data-mods-are-failed-to-load-data-set/264410 — только в выдаче поиска.
- [F9] https://forums.ageofempires.com/t/easy-way-to-update-data-mod-when-game-updates/290354 — открыл.
- [F10] https://forums.ageofempires.com/t/is-it-possible-to-make-data-mods-affect-campaigns/65555 — открыл (2019, устарело).
- [S2] https://steamcommunity.com/app/813780/discussions/4/4040356398515159957 — только в выдаче поиска (про ачивки).
- [O1] https://support.ageofempires.com/hc/en-us/articles/15607286588948-Return-of-Rome-Mod-Updates — официальная статья; WebFetch получил HTTP 403, цитата взята из выдачи поиска. `[ПРОВЕРИТЬ: открыть в Chrome вручную]`
- Официальной пошаговой документации Microsoft/World's Edge по модам данных найти не удалось; основные сведения — сообщество.
