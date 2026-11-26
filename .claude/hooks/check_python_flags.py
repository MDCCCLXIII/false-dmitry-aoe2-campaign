"""PreToolUse (Bash): требует `-X utf8` при запуске Python из .venv.

Без него вывод AoE2ScenarioParser падает на кодировке cp1252 (эмодзи в логе).
Не трогает `-m pip`, `--version` и вызовы без скриптов.
"""
import json
import re
import sys

sys.stderr.reconfigure(encoding="utf-8")

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if data.get("tool_name") != "Bash":
    sys.exit(0)

cmd = str((data.get("tool_input") or {}).get("command", ""))
uses_venv_python = re.search(r"\.venv[\\/]+Scripts[\\/]+python(\.exe)?", cmd, re.IGNORECASE)
runs_code = re.search(r"\.py\b|\s-c\s|<<", cmd)
is_pip = re.search(r"-m\s+(pip|venv|ensurepip)\b", cmd) or "--version" in cmd

if uses_venv_python and runs_code and not is_pip and not re.search(r"-X\s*utf8", cmd, re.IGNORECASE):
    print(
        "Добавь флаг -X utf8: `.venv\\Scripts\\python.exe -I -X utf8 ...` "
        "(без него парсер сценариев падает на кодировке).",
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
