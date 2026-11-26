"""PreToolUse: защита файлов игры AoE2 DE.

Блокирует:
- Write/Edit внутри каталога установки игры;
- Write/Edit, перезаписывающие уже существующий файл в папке пользовательских сценариев;
- команды Bash, удаляющие/перемещающие/перезаписывающие что-либо в каталоге игры
  или удаляющие файлы в папке пользовательских сценариев.
"""
import json
import os
import re
import sys

sys.stderr.reconfigure(encoding="utf-8")

GAME_DIR = r"c:\program files (x86)\steam\steamapps\common\aoe2de"
SCENARIO_MARK = r"resources\_common\scenario"
DESTRUCTIVE = re.compile(
    r"(\brm\b|\bdel\b|\berase\b|remove-item|\bmv\b|\bmove\b|move-item|\brmdir\b|\brd\b|"
    r"set-content|out-file|add-content|clear-content|rename-item|\bren\b|\bcopy\b.*?/y|"
    r"copy-item.*?-force|\bcp\b.*?-f|\bsed\b.*?-i|\btruncate\b|>\s*\S)",
    re.IGNORECASE,
)


def norm(p: str) -> str:
    return os.path.normpath(p).replace("/", "\\").lower()


def block(msg: str):
    print(msg, file=sys.stderr)
    sys.exit(2)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
ti = data.get("tool_input") or {}

if tool in ("Write", "Edit", "NotebookEdit"):
    path = norm(str(ti.get("file_path", "")))
    if path.startswith(GAME_DIR):
        block("Заблокировано: файлы игры AoE2 DE менять нельзя.")
    if SCENARIO_MARK in path and os.path.exists(ti.get("file_path", "")):
        block(
            "Заблокировано: нельзя перезаписывать существующий файл в папке сценариев игры. "
            "Используй новое имя (суффикс версии) или /install-scenario."
        )

elif tool == "Bash":
    cmd = str(ti.get("command", ""))
    low = cmd.lower().replace("/", "\\")
    touches_game = GAME_DIR in low or GAME_DIR.replace("\\", "\\\\") in low
    touches_scen = SCENARIO_MARK in low
    # Безобидные перенаправления (2>&1, >/dev/null, >nul) не считаются записью
    scrubbed = re.sub(r"\d?>&\d|>\s*(/dev/null|nul)\b", "", cmd, flags=re.IGNORECASE)
    if (touches_game or touches_scen) and DESTRUCTIVE.search(scrubbed):
        block(
            "Заблокировано: команда может удалить или перезаписать файлы игры или "
            "пользовательские сценарии. Копируй только новые файлы через /install-scenario."
        )

sys.exit(0)
