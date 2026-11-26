"""Сборка миссии 1 v2 «Через границу» -> build/01_cherez_granitsu_v2.aoe2scenario

Источники: missions/01-cherez-granitsu.v2-design.md (§13), missions/01-cherez-granitsu.dialogue.v2.md,
missions/01-cherez-granitsu.spec.md (механика конверсии), build/NOTES.md (v1).
Файл v1 не трогается. Запуск:  .venv\\Scripts\\python.exe -I -X utf8 scripts\\build_01_v2.py
Скрипт состоит из частей, выполняемых в общем пространстве имён:
  v2_part1*.py        карта: высоты, местность, города, декор
  v2_part2_triggers.py триггеры, реплики, цели
  v2_part3_verify.py  запись, повторное чтение, сверка, NOTES_v2.md
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ns = {"__name__": "build_v2", "HERE": HERE}
PARTS = ("v2_part1_world.py", "v2_part1b_cities.py", "v2_part1c_finish.py", "v2_part2_triggers.py", "v2_part3_verify.py")
import os
if os.environ.get("V2_ONLY_WORLD"):
    PARTS = PARTS[:3] + ("v2_dbg.py",)
for part in PARTS:
    code = compile((HERE / part).read_text(encoding="utf-8"), str(HERE / part), "exec")
    exec(code, ns)
