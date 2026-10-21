#!/usr/bin/env python3
"""SessionStart hook: inject the runtime rule from Practice 7.

Runs on every session source (startup, resume, clear, compact, fork), so the
rule is restored after compaction summarises earlier context away.
"""
import json
import sys

RULE = """\
Search locates, reading decides (skill-best-practices, Practice 7).
- Use search (grep, rg, Grep) to find where a passage is. Use Read on that section to decide what it says.
- Never treat truncated search output (| head, | tail, grep -m N) as evidence that a source lacks something; the deciding line may sit past the cut.
- When checking a claim that a source decided or confirmed something, read the source's conclusions section in full, not a summary or the first matching line.
- Before saying a source does not contain something, try other wordings and read the surrounding section."""


def main():
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": RULE,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
