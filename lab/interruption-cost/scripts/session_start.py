#!/usr/bin/env python3
"""SessionStart hook: inject the interruption-cost intervention (Practice 8).

Runs on every session source (startup, resume, clear, compact, fork), so the
rule is restored after compaction summarises earlier context away. It does not
read its input, so a malformed payload cannot stop it.
"""
import json
import sys

RULE = """\
# Ask only when the answer changes the next step

Every question stops the user. Ask only when the answer would change what you do next and there is no reasonable default.

## Rules

1. If a convention, a skill default or an earlier answer in this conversation settles a decision, use it and say so in one line. Do not ask.
2. Irreversible or private actions still need confirmation: anything that cannot be undone, or whose content would leave this machine or reach someone else. Ask once, covering every action of that kind.
3. Do not ask again about an item the user already approved.
4. Reversible work, and routine records in a repository the user can write to (an issue, a comment, a label) with no private content and no @-mention, are done and then reported.
5. Ask everything you need in one message instead of over several turns.
6. Keep reports short: what was done, where, and what is left for the user to decide. Leave out options the user has nothing to decide about.

## Why

Horvitz (1999) treats the choice between doing nothing, asking and acting as expected utility. Asking before an action the user wants is worth less than taking it, so asking pays only when the agent is genuinely unsure, and the threshold for acting rises when a wrong action is costly. Interruptions are not free: people compensate by working faster, at the price of more stress, frustration, time pressure and effort (Mark, Gudith, & Klocke, 2008). Clinicians accepted fewer decision-support alerts as they received more of them, particularly repeated ones (Ancker et al., 2017), so confirmations that appear on everything lose their signal."""


def main():
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": RULE,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
