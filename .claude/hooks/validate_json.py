"""PostToolUse: после правки .json проверяет, что файл остался валидным JSON."""
import json
import sys

sys.stderr.reconfigure(encoding="utf-8")

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

path = str((data.get("tool_input") or {}).get("file_path", ""))
if path.lower().endswith(".json"):
    try:
        with open(path, encoding="utf-8") as f:
            json.load(f)
    except FileNotFoundError:
        sys.exit(0)
    except Exception as e:
        print(f"Невалидный JSON в {path}: {e}", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
