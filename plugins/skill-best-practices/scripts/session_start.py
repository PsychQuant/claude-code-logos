#!/usr/bin/env python3
"""SessionStart hook: inject the runtime rules from Practices 7 and 8.

Runs on every session source (startup, resume, clear, compact, fork), so the
rules are restored after compaction summarises earlier context away.
"""
import json
import sys

PRACTICE_7 = """\
Search locates, reading decides (skill-best-practices, Practice 7).
- Use search (grep, rg, Grep) to find where a passage is. Use Read on that section to decide what it says.
- Never treat truncated search output (| head, | tail, grep -m N) as evidence that a source lacks something; the deciding line may sit past the cut.
- When checking a claim that a source decided or confirmed something, read the source's conclusions section in full, not a summary or the first matching line.
- Before saying a source does not contain something, try other wordings and read the surrounding section."""

PRACTICE_8 = """\
Ask only when the answer changes the next step (skill-best-practices, Practice 8).
- Ask the user only when the answer would change what you do next and there is no reasonable default. A convention, a skill default or an earlier answer in this conversation is a default: use it and say so in one line.
- When you do need answers, ask everything in one message, not over several turns.
- Irreversible or private actions still need confirmation: anything that cannot be undone, or whose content would leave this machine or reach someone else. Ask once, covering every action of that kind, and do not ask again about an item the user already approved.
- Reversible work, and routine records in a repository the user can write to (an issue, a comment, a label) with no private content and no @-mention, are done and then reported.
- Keep reports short: what was done, where, and what is left for the user to decide. Leave out options the user has nothing to decide about."""

RULES = (PRACTICE_7, PRACTICE_8)


def main():
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "\n\n".join(RULES),
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
