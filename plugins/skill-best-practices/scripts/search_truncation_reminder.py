#!/usr/bin/env python3
"""PreToolUse hook on Bash: remind that a truncated search is not evidence.

Fires when a search command (grep, rg, ag, ack, git grep) is piped into
head/tail, or caps its own output with -m / --max-count. Adds one line of
context next to the tool result and never decides the call: no
permissionDecision is returned, so the command runs exactly as it would
without the hook. See Practice 7 in skills/skill-best-practices/SKILL.md.
"""
import json
import re
import shlex
import sys

SEARCHERS = {"grep", "egrep", "fgrep", "rg", "ag", "ack"}
TRUNCATORS = {"head", "tail"}
# Words that may precede the real command inside a pipeline stage.
PREFIXES = {"sudo", "time", "nice", "command", "exec", "(", "{", "$"}
PIPES = {"|", "|&"}
# Tokens that end a pipeline. Redirections (>, 2>&1, <) are not here: they
# stay inside their stage and do not stop output from reaching the next pipe.
SEPARATORS = {";", ";;", "&&", "||", "&", "(", ")"}

REMINDER = (
    "This search output is truncated (piped to head/tail or capped with -m). "
    "A truncated search can locate passages, but it is not evidence that the source "
    "lacks something: the line that settles the question may sit past the cut. "
    "Before concluding, read the relevant section with Read; if nothing matched, "
    "try other wordings first."
)


def tokenize(command):
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        # Unbalanced quotes: fall back to a rough split rather than give up.
        return command.replace("|", " | ").split()


def pipelines(tokens):
    """Yield each pipeline as a list of stages; each stage is a token list."""
    stages, current = [], []
    for tok in tokens:
        if tok in PIPES:
            stages.append(current)
            current = []
        elif tok in SEPARATORS:
            stages.append(current)
            if any(stages):
                yield [s for s in stages if s]
            stages, current = [], []
        else:
            current.append(tok)
    stages.append(current)
    if any(stages):
        yield [s for s in stages if s]


def command_words(stage):
    return [w for w in stage if w not in PREFIXES and not re.match(r"^\w+=", w)]


def is_search(words):
    if not words:
        return False
    if words[0] in SEARCHERS:
        return True
    return len(words) > 1 and words[0] == "git" and words[1] == "grep"


def caps_own_output(words):
    return any(w == "-m" or re.match(r"^-m\d+$", w) or w.startswith("--max-count")
               for w in words[1:])


def truncated_search(command):
    for stages in pipelines(tokenize(command)):
        words = [command_words(s) for s in stages]
        for i, w in enumerate(words):
            if not is_search(w):
                continue
            if caps_own_output(w):
                return True
            if any(later and later[0] in TRUNCATORS for later in words[i + 1:]):
                return True
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if isinstance(command, str) and truncated_search(command):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": REMINDER,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
