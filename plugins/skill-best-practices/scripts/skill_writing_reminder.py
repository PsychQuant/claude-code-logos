#!/usr/bin/env python3
"""PreToolUse hook on Write|Edit: deliver rules/skill-writing.md for SKILL.md.

Plugins have no rules/ component, so the rule file is never auto-loaded.
This hook is what delivers it: when the target path is a SKILL.md, the file's
text is added as context, once per session (tracked with a marker file under
the system temp directory). Never decides the call.
"""
import json
import pathlib
import re
import sys
import tempfile

RULE_FILE = pathlib.Path(__file__).resolve().parents[1] / "rules" / "skill-writing.md"


def is_skill_file(path):
    return isinstance(path, str) and re.split(r"[\\/]", path)[-1] == "SKILL.md"


def first_time_this_session(session_id):
    if not session_id:
        return True
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(session_id))
    marker = pathlib.Path(tempfile.gettempdir()) / "skill-best-practices" / f"{safe}.skill-writing"
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=False)
        return True
    except FileExistsError:
        return False
    except OSError:
        return True


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(payload, dict):
        return 0
    path = (payload.get("tool_input") or {}).get("file_path")
    if not is_skill_file(path) or not first_time_this_session(payload.get("session_id")):
        return 0
    try:
        rule = RULE_FILE.read_text(encoding="utf-8")
    except OSError:
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": rule,
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
