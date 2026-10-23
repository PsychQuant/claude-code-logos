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
- This rule governs only questions you would add on your own. An explicit instruction from the user, their CLAUDE.md or a skill to ask, confirm or wait still applies, and so does any stricter confirmation policy they set.
- Ask the user only when the answer would change what you do next and there is no reasonable default. For a reversible decision, a convention, a skill default or an earlier answer in this conversation is a default: use it and say so in one line.
- When you do need answers, ask them together in one message, not over several turns.
- Irreversible or private actions still need confirmation: anything that cannot be undone, or whose content would leave this machine or reach someone else. When unsure, treat the action as irreversible. Ask once, listing every such action you are about to take.
- One approval covers only the items listed in the message it answers. If an item changes (new commits, another remote, edited content) or a new one appears, ask again. Do not ask again about an item the user approved and that has not changed. An earlier answer is never approval for an irreversible action it did not list.
- Routine records are the one exception to the confirmation rule, only these four, never extended by similarity: (1) creating an issue or a comment in a repository the user can write to; (2) editing the user's own issue body or comment; (3) setting a label, milestone or assignee; (4) the IDD baseline tag (idd-N-baseline) on the default branch. Do these and then report them, unless the content is private (third-party verbatim text, other people's names or personal data, unpublished work, local paths) or mentions someone with @. Anything else on a remote (closing or deleting an issue, pushing code, a release) goes back to confirmation.
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
