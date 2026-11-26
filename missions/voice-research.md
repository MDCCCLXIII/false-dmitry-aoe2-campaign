# Озвучка и оформление реплик в DE: исследование

Дата: 2026-11-24. Метки: **[ПРАКТИКА]** проверено на этом компьютере, **[ДОКА]** только по документации/форумам, **[НЕ ПРОВЕРЕНО В ИГРЕ]** в самой игре ничего не запускалось. Файлы игры и мод не менялись.

## 1. Звук в Display Instructions

Поля эффекта в AoE2ScenarioParser 0.9.9 **[ПРАКТИКА]** (сигнатуры из установленной в `.venv` библиотеки):

```python
t.new_effect.display_instructions(object_list_unit_id=..., source_player=1, string_id=None,
    display_time=8, instruction_panel_position=..., play_sound=..., message="...",
    sound_name="имя_без_расширения", use_tag_color_for_icon=False)
t.new_effect.play_sound(source_player=1, location_x=.., location_y=.., location_object_reference=..,
    global_sound=1, sound_name="имя")
t.new_effect.send_chat(source_player=1, string_id=None, message="...", sound_name="имя")
```

- `sound_id` в DE нет. Звук задаётся **строкой** `sound_name` (в редакторе поле "Sound (Event) Name"). Параметр `play_sound` в display_instructions: флаг "проиграть уведомление", не имя файла **[ДОКА: ugc.aoe2.rocks]**.
- Отдельный эффект **Play Sound существует** (`EffectId.PLAY_SOUND`, **[ПРАКТИКА]** в парсере). Поля: source_player, location, global_sound, sound_name.
- Встроенные звуки называются `Play_<Имя>` (Play_Victory, Play_Wolves) **[ДОКА: AoKH]**.
- Формат: DE использует Wwise, файлы **.wem**. mp3/ogg/wav напрямую **не поддерживаются** **[ДОКА]**. Сжатые (Vorbis) .wem для модов не подходят, нужен **несжатый PCM** (в Wwise Project Settings выбрать PCM) **[ДОКА: AoKH, подтверждено двумя пользователями]**.
- Папка: внутри **мода**, не в папке игры: `mods\local\<Мод>\resources\_common\drs\sounds\*.wem`; сценарий рядом: `mods\local\<Мод>\resources\_common\drs\scenario\` (иногда пишут `resources\_common\scenario\`) **[ДОКА: AoKH "Guide to DE Custom Sound Files"]**. В `resources\_common` пользователя сейчас только ai, campaign, scenario, xs; папки drs нет, это пользовательская папка сохранений, звуки туда класть не нужно **[ПРАКТИКА: листинг]**.
- В поле имени пишется имя файла **без** `.wem` (`test.wem` -> `test`); префикс `Play_` не нужен **[ДОКА]**. Один пост про `.mp3` в папке `sound` мода: неподтверждённый единичный случай.
- Известные ограничения **[ДОКА, 2020-2024, свежего подтверждения нет]**:
  - Display Instructions: звук не привязан к камере, но играет только если в сообщении есть текст (хотя бы пробел), и пока звук идёт, другие Display Instructions не показываются.
  - Play Sound с позицией затухает при отдалении камеры, без позиции привязан к центру экрана в момент срабатывания; `global_sound=1` должен это обходить.
  - Есть посты, что Play Sound ломался после патчей.
  - Сценарий с кастомным звуком должен распространяться как мод (сценарий + sounds), иначе звука не будет.

### Генерация русской речи **[ПРАКТИКА]**
- Установлены голоса: Microsoft Irina Desktop (ru-RU, женский), Zira и David (en-US). Мужского русского голоса нет.
- Тест создан: `build\audio_test\test_ru.wav` (205 720 байт, PCM 22050 Гц, 16 бит, моно, около 4,7 с) через `System.Speech.Synthesis.SpeechSynthesizer` + `SetOutputToWaveFile`.
- В системе **нет** ffmpeg, Wwise, vgmstream, sox. Значит wav -> wem здесь сделать нечем без установки Wwise (бесплатный Audiokinetic Launcher; я его не скачивал, это нужно разрешение пользователя). Пайплайн: wav (Irina) -> Wwise (PCM) -> wem -> `sounds\`.
- Ограничение по смыслу: Irina одна для всех персонажей, мужские реплики будут женским голосом. Различать можно высотой (в System.Speech `Rate`, `PromptBuilder` с `<prosody pitch>` SSML) **[ПРАКТИКА не проверена]**.
- Работа ещё не проверена: примет ли игра именно такой wem и как DE ведёт себя в Display Instructions. Риск: **[НЕ ПРОВЕРЕНО В ИГРЕ]**.

## 2. Как отличить говорящего

- **Цветовые префиксы** в начале сообщения Display Instructions, Display Timer и Send Chat: `<BLUE> <RED> <GREEN> <YELLOW> <AQUA> <PURPLE> <GREY> <ORANGE>`. Префикс должен стоять первым и сам не показывается **[ДОКА: ugc.aoe2.rocks]**. Проект уже использует `prefix + text` в `build_01.py` **[ПРАКТИКА: код]**; отображение в игре не проверено.
- Теги `<b>`, `<i>` и т.п.: **подтверждений нет**, считать не работающими, пока не проверено.
- **Иконка/портрет**: `object_list_unit_id` показывает иконку юнита в панели; `source_player` задаёт цвет рамки иконки; `use_tag_color_for_icon` (bool) в парсере есть, смысл не документирован **[ДОКА: ugc.aoe2.rocks, парсер]**. Портретов произвольных картинок нет, только иконки юнитов.
- **Позиция**: `instruction_panel_position`, в парсере нет перечисления; по ugc-гиде на одну позицию показывается одна инструкция (последняя перебивает). Значения позиций **[ПРОВЕРИТЬ: пробовать 0..N в игре]**.
- **Длительность**: `display_time` в секундах реального времени.
- **Подпись**: имя говорящего писать в тексте: `"<RED>Лжедмитрий: ..."`. Send Chat с префиксом "Имя:" — рабочий запасной вариант, но ugc-гид не советует его для инструкций, одинаковые сообщения не дублируются.
- Цветные имена игроков: через `change_player_name` (есть в EffectId), цвет задаёт цвет игрока **[ДОКА/парсер, в игре не проверено]**.

Совет: говорящий = иконка юнита (`object_list_unit_id`: царевич — рыцарь/герой, Мнишек — иной юнит) + цветовой префикс + имя в начале строки. Чтобы реплики не обрезали друг друга, ставить разные позиции или разносить по времени.

## 3. Крылатый гусар

Проверено в установленном парсере **[ПРАКТИКА]**:
- `UnitInfo.WINGED_HUSSAR.ID == 1707` (иконка 371, dead unit 1708); обычный `UnitInfo.HUSSAR` = 441.
- Технологии: `TechInfo.HUSSAR` = 428, `TechInfo.WINGED_HUSSAR` = 786 (общая), `WINGED_HUSSAR_LITHUANIANS` = 788, `WINGED_HUSSAR_POLES` = 789.
- В игре это апгрейд Hussar -> Winged Hussar (исследование заменяет все гусары), требует civ Poles/Lithuanians (Dawn of the Dukes) **[ДОКА: Age of Empires wiki]**. Юнит 1707 существует независимо от civ; можно выдать другой стороне триггером.
- Путь для нашего мода (как уже делается для Hussar в `build_01.py`): `enable_disable_object(object_list_unit_id=1707, source_player=P1, enabled=1)` плюс `add_train_location(object_list_unit_id=1707, source_player=P1, object_list_unit_id_2=STABLE, button_location=...)`, при необходимости `change_object_name`. Или спавн напрямую `UnitInfo.WINGED_HUSSAR.ID` через `place_unit`. **[ПРОВЕРИТЬ: ограничения кнопки, цены; в игре не запускалось]**. Явного документа "включить Winged Hussar для не-поляков" нет, это вывод из общей механики эффектов.
- Для гусара-наёмника миссии 1 лучше остаться на обычном Hussar (441) с переименованием: Крылатый гусар историчен для Речи Посполитой, но в игре его "крылья" это модель 1707.

## 4. Выводы

- **Озвучить можно** технически: Irina (ru-RU) -> wav -> .wem (PCM, Wwise) -> `<Мод>\resources\_common\drs\sounds\` -> имя в `sound_name` у Display Instructions/Send Chat/Play Sound.
- **Не получится**: прямые mp3/wav/ogg; разные русские голоса (только Irina); блокировка других инструкций, пока играет звук; тег `<b>`.
- Блокер: нужен Wwise (не установлен) и проверка в игре.

## Источники
- AoE2ScenarioParser (локально, `.venv`, 0.9.9); GitHub: https://github.com/KSneijders/AoE2ScenarioParser (datasets/effects.py, datasets/units.py)
- UGC Guide, эффекты: https://ugc.aoe2.rocks/scenarios/triggers/effects/effects/
- AoKH, гид по звукам DE: https://aok.heavengames.com/cgi-bin/forums/display.cgi?action=st&fn=4&tn=44702
- AoKH, Custom Sounds for scenarios/campaigns in DE: https://aok.heavengames.com/cgi-bin/forums/display.cgi?action=ct&f=4,44648,,30
- Форум AoE: https://forums.ageofempires.com/t/custom-sound-files-in-the-scenario-editor-problems/80428 , https://forums.ageofempires.com/t/how-can-i-add-custom-sounds-to-the-dialogues-in-the-scenery-editor/182469
- Wiki: https://ageofempires.fandom.com/wiki/Winged_Hussar_(Age_of_Empires_II)
