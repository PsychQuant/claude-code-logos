#!/usr/bin/env python3
"""SessionStart hook: inject the interruption-cost intervention (Practice 8).

The rule lines are the ones skill-best-practices ships, word for word, so the
lab measures the rule users get; tests/test_hooks.py checks that they match.
The lab text adds a `## Why` section, which the shipped rule does not carry.

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

- This rule governs only questions you would add on your own. An explicit instruction from the user, their CLAUDE.md or a skill to ask, confirm or wait still applies, and so does any stricter confirmation policy they set.
- Ask the user only when the answer would change what you do next and there is no reasonable default. For a reversible decision, a convention, a skill default or an earlier answer in this conversation is a default: use it and say so in one line.
- When you do need answers, ask them together in one message, not over several turns.
- Irreversible or private actions still need confirmation: anything that cannot be undone, or whose content would leave this machine or reach someone else. When unsure, treat the action as irreversible. Ask once, listing every such action you are about to take.
- One approval covers only the items listed in the message it answers. If an item changes (new commits, another remote, edited content) or a new one appears, ask again. Do not ask again about an item the user approved and that has not changed. An earlier answer is never approval for an irreversible action it did not list.
- Routine records are the one exception to the confirmation rule, only these four, never extended by similarity: (1) creating an issue or a comment in a repository the user can write to; (2) editing the user's own issue body or comment; (3) setting a label, milestone or assignee; (4) the IDD baseline tag (idd-N-baseline) on the default branch. Do these and then report them, unless the content is private (third-party verbatim text, other people's names or personal data, unpublished work, local paths) or mentions someone with @. Anything else on a remote (closing or deleting an issue, pushing code, a release) goes back to confirmation.
- Keep reports short: what was done, where, and what is left for the user to decide. Leave out options the user has nothing to decide about.

## Why

Horvitz (1999) treats the choice between doing nothing, asking and acting as expected utility. Asking before an action the user wants is worth less than simply taking it, so asking pays only when the agent is genuinely unsure. The less an unwanted action is worth to the user, the higher the threshold for acting, which is why irreversible actions stay confirmed. In a study of interrupted work, people compensated for interruptions by working faster, at the price of more stress, frustration, time pressure and effort (Mark, Gudith, & Klocke, 2008). Resuming a suspended goal depends on retrieving it against interference from older goals (Altmann & Trafton, 2002). Clinicians accepted fewer decision-support alerts as they received more of them, particularly repeated ones (Ancker et al., 2017). These studies concern people and clinical alerts, not an agent's questions: applying them here is an analogy."""


def main():
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": RULE,
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
