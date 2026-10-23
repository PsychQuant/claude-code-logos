#!/usr/bin/env python3
"""Count the times an agent stopped to ask the user something, in a Claude Code transcript.

This is the measure behind the interruption-cost claim. It reads a session
transcript (JSONL, one object per line; Claude Code passes its path to hooks as
`transcript_path`) and counts, on the main chain:

  replies             what the person read before answering: the last assistant
                      text before each human turn, before each task
                      notification, and before the end
  question_replies    replies that ask something: a full-width ？ anywhere, or
                      an ASCII ? not followed by a URL character; fenced code
                      (``` or ~~~, any length), inline code and quoted (>) lines
                      are ignored
  ask_tool_calls      AskUserQuestion tool calls
  ask_tool_questions  questions inside those calls (a call with three questions
                      counts three)
  questions           question_replies + ask_tool_calls: the number of times the
                      agent stopped and asked. One message with five questions
                      is one stop.
  consecutive_asks    asks that come right after the person answered another
                      ask, with no statement in between: candidates for "asked
                      again after an approval", for a coder to confirm (their
                      transcript lines are listed)

A human turn is a `user` entry, or a `queued_command` attachment (a message sent
while the agent was working), whose `origin.kind` is "human". Entries without
`origin` (older transcripts) count as human unless they are meta entries,
compact summaries or tool results, or start with text the harness writes (local
command output, task notifications, interruption notices). A task notification
ends a reply but does not answer it. Sidechain (subagent) entries are ignored.
The transcript format is not a documented contract, so lines that cannot be
read (not JSON, not an object, nested too deeply, a `message` that is not an
object) are skipped and counted.

The output holds counts, line numbers and the transcript's file name, never
transcript text or its directory.

Usage:
  count_questions.py TRANSCRIPT [--tasks N] [--json]
"""
import argparse
import json
import os
import re
import sys

NOT_TYPED_PREFIXES = ("<local-command-", "<task-notification>", "[Request interrupted", "<system-reminder>")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`[^`\n]*`")
ASCII_QUESTION = re.compile(r"\?(?![A-Za-z0-9=&%#/+])")


def blocks(entry):
    content = entry["message"].get("content") if isinstance(entry.get("message"), dict) else None
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def block_text(block):
    text = block.get("text", "")
    return text if isinstance(text, str) else ""


def classify(entry):
    """'human' for a person's message, 'boundary' for a task notification, else None."""
    if entry.get("type") == "attachment":
        attachment = entry.get("attachment")
        if not isinstance(attachment, dict) or attachment.get("type") != "queued_command":
            return None
        origin = attachment.get("origin")
        kind = origin.get("kind") if isinstance(origin, dict) else None
        if kind == "human" or (kind is None and attachment.get("humanTurn")):
            return "human"
        prompt = attachment.get("prompt")
        if (kind == "task-notification" or attachment.get("commandMode") == "task-notification"
                or (isinstance(prompt, str) and prompt.startswith("<task-notification>"))):
            return "boundary"
        return None
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return None
    content = blocks(entry)
    if any(b.get("type") == "tool_result" for b in content):
        return None
    origin = entry.get("origin")
    if isinstance(origin, dict):
        if origin.get("kind") == "human":
            return "human"
        return "boundary" if origin.get("kind") == "task-notification" else None
    text = "".join(block_text(b) for b in content if b.get("type") == "text").strip()
    if not text:
        return "human" if any(b.get("type") != "text" for b in content) else None
    if text.startswith("<task-notification>"):
        return "boundary"
    return None if text.startswith(NOT_TYPED_PREFIXES) else "human"


def strip_fenced_code(text):
    kept, fence = [], None
    for line in text.splitlines():
        m = FENCE.match(line)
        if fence is None:
            if m:
                fence = m.group(1)
            else:
                kept.append(line)
        elif m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and line.strip() == m.group(1):
            fence = None
    return "\n".join(kept)


def is_question(text):
    text = INLINE_CODE.sub("", strip_fenced_code(text))
    body = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(">"))
    return "？" in body or bool(ASCII_QUESTION.search(body))


def ask_tool_question_count(block):
    questions = (block.get("input") or {}).get("questions") if isinstance(block.get("input"), dict) else None
    return len(questions) if isinstance(questions, list) and questions else 1


def measure(lines):
    counts = {
        "human_turns": 0,
        "replies": 0,
        "question_replies": 0,
        "ask_tool_calls": 0,
        "ask_tool_questions": 0,
        "questions": 0,
        "consecutive_asks": 0,
        "consecutive_ask_lines": [],
        "reasks_after_typed_answer": 0,
        "reask_after_typed_answer_lines": [],
        "skipped_lines": 0,
    }
    # last: None, "ask_open" (asked, not answered yet), "answered_tool" (an
    # AskUserQuestion the person answered), "answered_typed" (a question the
    # person answered by typing) or "statement".
    # activity: whether the assistant did anything since the last human turn.
    # text_open: whether the next text block continues the pending reply.
    state = {"pending": None, "last": None, "activity": False, "text_open": False}

    def record_ask(line_no):
        if state["last"] in ("answered_tool", "answered_typed"):
            counts["consecutive_asks"] += 1
            counts["consecutive_ask_lines"].append(line_no)
            if state["last"] == "answered_typed":
                counts["reasks_after_typed_answer"] += 1
                counts["reask_after_typed_answer_lines"].append(line_no)
        state["last"] = "ask_open"

    def close_reply():
        if state["pending"] is None:
            return False
        line_no, text = state["pending"]
        state["pending"] = None
        state["text_open"] = False
        counts["replies"] += 1
        if is_question(text):
            counts["question_replies"] += 1
            record_ask(line_no)
        else:
            state["last"] = "statement"
        return True

    for line_no, raw in enumerate(lines, 1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except (ValueError, RecursionError):
            counts["skipped_lines"] += 1
            continue
        if not isinstance(entry, dict) or ("message" in entry and not isinstance(entry["message"], (dict, type(None)))):
            counts["skipped_lines"] += 1
            continue
        if entry.get("isSidechain"):
            continue
        if entry.get("type") == "assistant":
            state["activity"] = True
            for block in blocks(entry):
                if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                    counts["ask_tool_calls"] += 1
                    counts["ask_tool_questions"] += ask_tool_question_count(block)
                    if state["pending"] is not None and not is_question(state["pending"][1]):
                        state["last"] = "statement"  # a statement since the last answer breaks the chain
                    state["pending"] = None  # text before the call introduced this question
                    state["text_open"] = False
                    record_ask(line_no)
                    state["last"] = "answered_tool"  # the tool returns once the person has answered
                elif block.get("type") == "tool_use":
                    state["text_open"] = False  # text before a tool call is narration, not the reply
                elif block.get("type") == "text" and block_text(block).strip():
                    if state["text_open"] and state["pending"] is not None:
                        state["pending"] = (line_no, state["pending"][1] + "\n" + block_text(block))
                    else:
                        state["pending"] = (line_no, block_text(block))
                    state["text_open"] = True
            continue
        if entry.get("type") == "user":
            state["text_open"] = False  # a tool result, a local command or a meta entry breaks the reply
        kind = classify(entry)
        if kind == "boundary":
            close_reply()  # the agent stopped here, but nobody answered
        elif kind == "human":
            counts["human_turns"] += 1
            if state["activity"]:
                close_reply()
                if state["last"] == "ask_open":
                    state["last"] = "answered_typed"  # also when a notification already closed the reply
                elif state["last"] != "statement":
                    state["last"] = None  # the turn ended without a reply: this is a new instruction
            # no assistant activity since the last human turn: a repeated or follow-up message, state unchanged
            state["activity"] = False
    close_reply()
    counts["questions"] = counts["question_replies"] + counts["ask_tool_calls"]
    return counts


def summary(path, result):
    lines = result["consecutive_ask_lines"]
    per_task = result["questions_per_task"]
    return "\n".join([
        f"transcript:          {os.path.basename(path)}",
        f"human turns:         {result['human_turns']}",
        f"replies:             {result['replies']}",
        f"  with a question:   {result['question_replies']}",
        f"AskUserQuestion:     {result['ask_tool_calls']} ({result['ask_tool_questions']} questions)",
        f"questions (asks):    {result['questions']}",
        f"consecutive asks:    {result['consecutive_asks']} (lines: {', '.join(map(str, lines)) or '-'})",
        f"  after a typed answer: {result['reasks_after_typed_answer']} (lines: {', '.join(map(str, result['reask_after_typed_answer_lines'])) or '-'})",
        f"tasks:               {result['tasks'] if result['tasks'] is not None else '- (pass --tasks N)'}",
        f"questions per task:  {f'{per_task:.2f}' if per_task is not None else '-'}",
        f"skipped lines:       {result['skipped_lines']}",
    ])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Count the times an agent stopped to ask the user, in a Claude Code transcript.")
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
