"""Tests for count_questions.py, the measure behind the interruption-cost claim.

Each test writes a synthetic transcript (one JSON object per line, in the shape
Claude Code writes) and checks the counts. Run with:

    python3 -m unittest discover -s lab/interruption-cost/tests
"""
import json
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "count_questions.py"


def human(content):
    return {"type": "user", "origin": {"kind": "human"}, "message": {"role": "user", "content": content}}


def assistant(*blocks, **extra):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}, **extra}


def text(t):
    return {"type": "text", "text": t}


def ask_tool():
    return {"type": "tool_use", "id": "toolu_ask", "name": "AskUserQuestion", "input": {"questions": []}}


def tool_result():
    return {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_ask", "content": "ok"}]},
        "toolUseResult": {},
    }


class Measure(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, entries, raw_lines=()):
        path = pathlib.Path(self.tmp.name) / "transcript.jsonl"
        lines = [json.dumps(e) for e in entries] + list(raw_lines)
        path.write_text("\n".join(lines) + "\n")
        return path

    def cli(self, *args):
        proc = subprocess.run(["python3", str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=10)
        return proc.returncode, proc.stdout, proc.stderr

    def measure(self, entries, *args, raw_lines=()):
        code, out, err = self.cli(self.write(entries, raw_lines), "--json", *args)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    # A reply the person reads before answering is a "waiting reply".

    def test_question_reply_is_counted(self):
        m = self.measure([human("fix it"), assistant(text("Done. Push now?")), human("yes")])
        self.assertEqual((m["replies"], m["question_replies"], m["questions"]), (1, 1, 1))

    def test_statement_reply_is_not_a_question(self):
        m = self.measure([human("fix it"), assistant(text("Done.")), human("thanks")])
        self.assertEqual((m["replies"], m["question_replies"]), (1, 0))

    def test_final_reply_without_an_answer_counts(self):
        m = self.measure([human("fix it"), assistant(text("Push now?"))])
        self.assertEqual((m["replies"], m["question_replies"]), (1, 1))

    def test_human_turn_with_list_content(self):
        m = self.measure([human([text("fix it")]), assistant(text("Push?")), human([text("yes")])])
        self.assertEqual((m["human_turns"], m["question_replies"]), (2, 1))

    # AskUserQuestion is answered inside the turn, through a tool result.

    def test_ask_user_question_call_is_counted(self):
        m = self.measure([human("go"), assistant(text("Checking."), ask_tool()), tool_result(), assistant(text("Done."))])
        self.assertEqual((m["ask_tool_calls"], m["question_replies"], m["questions"]), (1, 0, 1))

    def test_text_before_the_ask_tool_is_not_a_second_question(self):
        m = self.measure([human("go"), assistant(text("Which one?"), ask_tool()), tool_result()])
        self.assertEqual((m["ask_tool_calls"], m["question_replies"], m["questions"]), (1, 0, 1))

    def test_tool_result_is_not_a_human_turn(self):
        m = self.measure([human("go"), assistant(text("Run the tests?")), tool_result(), assistant(text("All pass.")), human("ok")])
        self.assertEqual((m["human_turns"], m["replies"], m["question_replies"]), (2, 1, 0))

    # Consecutive asks: answered, then asked again. Candidates for re-asks.

    def test_consecutive_asks_are_flagged_with_their_line(self):
        m = self.measure([human("ship it"), assistant(text("Push A?")), human("yes"), assistant(text("Push B too?")), human("yes")])
        self.assertEqual(m["consecutive_asks"], 1)
        self.assertEqual(m["consecutive_ask_lines"], [4])

    def test_ask_after_a_statement_is_not_consecutive(self):
        m = self.measure([
            human("go"), assistant(text("Push?")), human("yes"),
            assistant(text("Pushed.")), human("next"), assistant(text("Release?")), human("no"),
        ])
        self.assertEqual((m["questions"], m["consecutive_asks"]), (2, 0))

    def test_ask_tool_then_question_reply_is_consecutive(self):
        m = self.measure([human("go"), assistant(ask_tool()), tool_result(), assistant(text("Also push?")), human("yes")])
        self.assertEqual(m["consecutive_asks"], 1)

    # Entries that are not a person replying.

    def test_sidechain_entries_are_ignored(self):
        m = self.measure([
            human("go"),
            assistant(text("Subagent: which file?"), isSidechain=True),
            {**human("README"), "isSidechain": True},
            assistant(text("Done.")),
            human("thanks"),
        ])
        self.assertEqual((m["human_turns"], m["replies"], m["question_replies"]), (2, 1, 0))

    def test_meta_compact_and_notifications_are_not_human_turns(self):
        m = self.measure([
            human("go"),
            assistant(text("Waiting for the agent?")),
            {"type": "user", "isMeta": True, "message": {"role": "user", "content": "skill text"}},
            {"type": "user", "origin": {"kind": "task-notification"}, "message": {"role": "user", "content": "<task-notification>done</task-notification>"}},
            {"type": "user", "isCompactSummary": True, "message": {"role": "user", "content": "This session is being continued"}},
            assistant(text("Done.")),
            human("thanks"),
        ])
        self.assertEqual((m["human_turns"], m["replies"], m["question_replies"]), (2, 1, 0))

    def test_entries_without_origin_fall_back_to_prefixes(self):
        m = self.measure([
            {"type": "user", "message": {"role": "user", "content": "start"}},
            assistant(text("OK?")),
            {"type": "user", "message": {"role": "user", "content": "<local-command-stdout>x</local-command-stdout>"}},
            {"type": "user", "message": {"role": "user", "content": [text("[Request interrupted by user]")]}},
            assistant(text("Done.")),
            {"type": "user", "message": {"role": "user", "content": "thanks"}},
        ])
        self.assertEqual((m["human_turns"], m["replies"], m["question_replies"]), (2, 1, 0))

    # What counts as a question.

    def test_code_urls_and_quotes_are_not_questions(self):
        reply = "\n".join([
            "Changed the check:",
            "```python",
            "x = a if ok else b  # why?",
            "```",
            "It uses `cond ? a : b` now. See https://example.com/page?q=1 for details.",
            "> Did you mean the other file?",
            "Done.",
        ])
        m = self.measure([human("go"), assistant(text(reply)), human("ok")])
        self.assertEqual(m["question_replies"], 0)

    def test_full_width_question_mark_mid_line_counts(self):
        m = self.measure([human("推"), assistant(text("要推嗎？推了就收不回。")), human("推")])
        self.assertEqual(m["question_replies"], 1)

    # Robustness and the CLI.

    def test_malformed_lines_are_skipped_and_reported(self):
        m = self.measure([human("go"), assistant(text("Push?")), human("yes")], raw_lines=["{not json", "[1, 2]"])
        self.assertEqual((m["skipped_lines"], m["question_replies"]), (2, 1))

    def test_questions_per_task(self):
        m = self.measure([
            human("a"), assistant(text("One?")), human("b"), assistant(text("Two?")), human("c"), assistant(text("Three?")),
        ], "--tasks", 2)
        self.assertEqual((m["questions"], m["tasks"], m["questions_per_task"]), (3, 2, 1.5))

    def test_human_readable_summary(self):
        code, out, err = self.cli(self.write([human("go"), assistant(text("Push?")), human("yes")]), "--tasks", 1)
        self.assertEqual(code, 0, err)
        self.assertIn("questions per task", out)

    def test_missing_file_exits_2(self):
        code, out, err = self.cli(pathlib.Path(self.tmp.name) / "missing.jsonl")
        self.assertEqual(code, 2)
        self.assertIn("missing.jsonl", err)

    def test_tasks_must_be_positive(self):
        code, out, err = self.cli(self.write([human("go")]), "--tasks", 0)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
