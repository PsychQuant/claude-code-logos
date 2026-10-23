#!/usr/bin/env python3
"""Count user-facing questions in a Claude Code session transcript.

This is the measure behind the interruption-cost claim. It reads a session
transcript (JSONL, one object per line; Claude Code passes its path to hooks as
`transcript_path`) and counts, on the main chain:

  replies            what the person read before answering: the last assistant
                     text before each human turn, and before the end
  question_replies   replies that ask something: a full-width ？ anywhere, or an
                     ASCII ? followed by whitespace, closing punctuation or the end
                     of a line; fenced code, inline code and quoted (>) lines are
                     ignored
  ask_tool_calls     AskUserQuestion tool calls
  questions          question_replies + ask_tool_calls
  consecutive_asks   questions that come right after the person answered another
                     question: candidates for "asked again after an approval",
                     for a coder to confirm (their transcript lines are listed)

A human turn is a `user` entry whose `origin.kind` is "human". Entries without
`origin` (older transcripts) count as human unless they are meta entries,
compact summaries or tool results, or start with text the harness writes
(local command output, task notifications, interruption notices). Sidechain
(subagent) entries are ignored. The transcript format is not a documented
contract, so lines that cannot be parsed are skipped and counted.

The output holds counts and line numbers only, never transcript text.

Usage:
  count_questions.py TRANSCRIPT [--tasks N] [--json]
"""
import argparse
import json
import re
import sys

NOT_TYPED_PREFIXES = ("<local-command-", "<task-notification>", "[Request interrupted", "<system-reminder>")
FENCED_CODE = re.compile(r"```.*?(?:```|\Z)", re.S)
INLINE_CODE = re.compile(r"`[^`\n]*`")
ASCII_QUESTION = re.compile(r"\?(?=[)\]}\"'*_”’」』）]*(?:\s|$))")


def blocks(entry):
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def block_text(block):
    text = block.get("text", "")
    return text if isinstance(text, str) else ""


def is_human_turn(entry):
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    content = blocks(entry)
    if any(b.get("type") == "tool_result" for b in content):
        return False
    text = "".join(block_text(b) for b in content if b.get("type") == "text").strip()
    if not text:
        return False
    origin = entry.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind") == "human"
    return not text.startswith(NOT_TYPED_PREFIXES)


def is_question(text):
    text = INLINE_CODE.sub("", FENCED_CODE.sub("", text))
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))
    return "？" in body or bool(ASCII_QUESTION.search(body))


def measure(lines):
    counts = {
        "human_turns": 0,
        "replies": 0,
        "question_replies": 0,
        "ask_tool_calls": 0,
        "questions": 0,
        "consecutive_asks": 0,
        "consecutive_ask_lines": [],
        "skipped_lines": 0,
    }
    state = {"pending": None, "last_was_ask": False}

    def record_ask(line_no):
        if state["last_was_ask"]:
            counts["consecutive_asks"] += 1
            counts["consecutive_ask_lines"].append(line_no)
        state["last_was_ask"] = True

    def close_reply():
        if state["pending"] is None:
            return
        line_no, text = state["pending"]
        state["pending"] = None
        counts["replies"] += 1
        if is_question(text):
            counts["question_replies"] += 1
            record_ask(line_no)
        else:
            state["last_was_ask"] = False

    for line_no, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except ValueError:
            counts["skipped_lines"] += 1
            continue
        if not isinstance(entry, dict):
            counts["skipped_lines"] += 1
            continue
        if entry.get("isSidechain"):
            continue
        if entry.get("type") == "assistant":
            for block in blocks(entry):
                if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                    counts["ask_tool_calls"] += 1
                    state["pending"] = None  # text before the call introduced this question
                    record_ask(line_no)
                elif block.get("type") == "text" and block_text(block).strip():
                    state["pending"] = (line_no, block_text(block))
        elif is_human_turn(entry):
            counts["human_turns"] += 1
            close_reply()
    close_reply()
    counts["questions"] = counts["question_replies"] + counts["ask_tool_calls"]
    return counts


def summary(path, result):
    lines = result["consecutive_ask_lines"]
    per_task = result["questions_per_task"]
    return "\n".join([
        f"transcript:          {path}",
        f"human turns:         {result['human_turns']}",
        f"replies:             {result['replies']}",
        f"  with a question:   {result['question_replies']}",
        f"AskUserQuestion:     {result['ask_tool_calls']}",
        f"questions:           {result['questions']}",
        f"consecutive asks:    {result['consecutive_asks']} (lines: {', '.join(map(str, lines)) or '-'})",
        f"tasks:               {result['tasks'] if result['tasks'] is not None else '- (pass --tasks N)'}",
        f"questions per task:  {f'{per_task:.2f}' if per_task is not None else '-'}",
        f"skipped lines:       {result['skipped_lines']}",
    ])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Count user-facing questions in a Claude Code transcript.")
    parser.add_argument("transcript", help="session transcript (.jsonl)")
    parser.add_argument("--tasks", type=int, help="number of completed tasks in the session")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args(argv)
    if args.tasks is not None and args.tasks < 1:
        print("count_questions: --tasks must be a positive integer", file=sys.stderr)
        return 2
    try:
        with open(args.transcript, encoding="utf-8", errors="replace") as f:
            result = measure(f)
    except OSError as e:
        print(f"count_questions: cannot read {args.transcript}: {e.strerror}", file=sys.stderr)
        return 2
    result["tasks"] = args.tasks
    result["questions_per_task"] = result["questions"] / args.tasks if args.tasks else None
    print(json.dumps(result, indent=2) if args.json else summary(args.transcript, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
