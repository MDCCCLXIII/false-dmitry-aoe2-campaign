"""PreToolUse: запрещает прямую запись в бинарные файлы сценариев AoE2."""
import json
import sys

sys.stderr.reconfigure(encoding="utf-8")

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {}).get("file_path", "")).lower()
if path.endswith((".aoe2scenario", ".aoe2campaign")):
    print(
        "Заблокировано: файлы сценариев и кампаний бинарные. "
        "Меняй их только скриптами в scripts/ (scenario-builder).",
        file=sys.stderr,
    )
    sys.exit(2)
sys.exit(0)
