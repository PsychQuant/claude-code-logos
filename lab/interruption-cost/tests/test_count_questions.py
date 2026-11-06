"""Tests for count_questions.py, the measure behind the interruption-cost claim.

Each test writes a synthetic transcript (one JSON object per line, in the shape
Claude Code writes) and checks the counts. Run with:

    python3 -m unittest discover -s lab/interruption-cost/tests
"""
import json
import pathlib
import re
import subprocess
import tempfile
import textwrap
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "count_questions.py"
README = SCRIPT.parents[1] / "README.md"


def human(content):
    return {"type": "user", "origin": {"kind": "human"}, "message": {"role": "user", "content": content}}


def assistant(*blocks, **extra):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}, **extra}


def text(t):
    return {"type": "text", "text": t}


def ask_tool():
    return {"type": "tool_use", "id": "toolu_ask", "name": "AskUserQuestion", "input": {"questions": []}}


def bash_tool():
    return {"type": "tool_use", "id": "toolu_bash", "name": "Bash", "input": {}}


def tool_result():
    return {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_ask", "content": "ok"}]},
        "toolUseResult": {},
    }


def queued(prompt, kind="human"):
    # A message sent while the agent was working: Claude Code records it as an
    # attachment, not a user entry (shape taken from real transcripts).
    attachment = {"type": "queued_command", "prompt": prompt, "origin": {"kind": kind}}
    if kind == "human":
        attachment["humanTurn"] = True
    return {"type": "attachment", "attachment": attachment}


def notification():
    return {"type": "user", "origin": {"kind": "task-notification"},
            "message": {"role": "user", "content": "<task-notification>done</task-notification>"}}


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

    def test_meta_and_compact_entries_are_not_human_turns(self):
        # Task notifications are not ignored: they end a reply (see
        # test_notification_ends_a_reply_without_answering_it).
        m = self.measure([
            human("go"),
            assistant(text("Waiting for the agent?")),
            {"type": "user", "isMeta": True, "message": {"role": "user", "content": "skill text"}},
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

    # Verify round 1 (#4): defects found by the reviewers, one reproduction each.

    def test_image_only_human_reply_answers_the_question(self):
        image = {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AA=="}}
        m = self.measure([human("help"), assistant(text("Can you send a screenshot?")), human([image]),
                          assistant(text("Found it."))])
        self.assertEqual((m["human_turns"], m["question_replies"]), (2, 1))

    def test_queued_message_is_a_human_turn(self):
        m = self.measure([human("ship it"), assistant(text("Push A?")), queued("yes"),
                          assistant(text("Push B too?")), human("yes")])
        self.assertEqual((m["human_turns"], m["question_replies"], m["consecutive_asks"]), (3, 2, 1))

    def test_notification_ends_a_reply_without_answering_it(self):
        for boundary in (notification(), queued("<task-notification>done</task-notification>", kind="task-notification")):
            m = self.measure([human("go"), assistant(text("Push A and B?")), boundary,
                              assistant(text("Job finished. Waiting on your push decision.")), human("yes")])
            self.assertEqual((m["human_turns"], m["replies"], m["question_replies"]), (2, 2, 1))

    def test_new_instruction_after_an_answered_ask_tool_is_not_consecutive(self):
        work = {"type": "tool_use", "id": "toolu_bash", "name": "Bash", "input": {"command": "ls"}}
        m = self.measure([human("go"), assistant(ask_tool()), tool_result(), assistant(work), tool_result(),
                          human("next task"), assistant(text("Which file?")), human("a.txt")])
        self.assertEqual((m["questions"], m["consecutive_asks"]), (2, 0))

    def test_duplicate_human_entry_keeps_the_consecutive_ask(self):
        m = self.measure([human("ship it"), assistant(text("Push A?")), human("yes"), queued("yes"),
                          assistant(text("Push B too?")), human("yes")])
        self.assertEqual(m["consecutive_asks"], 1)

    def test_ask_tool_questions_are_counted_separately(self):
        call = {"type": "tool_use", "id": "toolu_ask", "name": "AskUserQuestion",
                "input": {"questions": [{"question": "a"}, {"question": "b"}, {"question": "c"}]}}
        m = self.measure([human("go"), assistant(call), tool_result(), assistant(text("Done."))])
        self.assertEqual((m["ask_tool_calls"], m["ask_tool_questions"]), (1, 3))

    def test_message_that_is_not_an_object_is_skipped(self):
        m = self.measure([human("go"), {"type": "assistant", "message": "oops"}, assistant(text("Push?")), human("yes")])
        self.assertEqual((m["skipped_lines"], m["question_replies"]), (1, 1))

    def test_deeply_nested_line_is_skipped(self):
        m = self.measure([human("go"), assistant(text("Push?")), human("yes")], raw_lines=["[" * 100000])
        self.assertEqual((m["skipped_lines"], m["question_replies"]), (1, 1))

    def test_question_mark_variants_count(self):
        for reply in ("What?!", "Push now?(yes/no)", "Which one?:", "Push now?。", "要推嗎?還是不要"):
            m = self.measure([human("go"), assistant(text(reply)), human("ok")])
            self.assertEqual(m["question_replies"], 1, reply)

    def test_tilde_and_long_fences_are_code(self):
        for reply in ("~~~\nwhy?\n~~~\nDone.", "````markdown\n```\nwhy?\n```\n````\nDone."):
            m = self.measure([human("go"), assistant(text(reply)), human("ok")])
            self.assertEqual(m["question_replies"], 0, reply)

    # Verify round 2 (#4).

    def test_question_followed_by_a_second_text_block_still_counts(self):
        m = self.measure([human("ship it"), assistant(text("Push now?"), text("I will wait for your approval.")), human("yes")])
        self.assertEqual(m["question_replies"], 1)
        m = self.measure([human("ship it"), assistant(text("Push now?")), assistant(text("I will wait.")), human("yes")])
        self.assertEqual(m["question_replies"], 1)

    def test_answer_after_a_notification_keeps_the_ask_answered(self):
        m = self.measure([human("ship it"), assistant(text("Push A?")), notification(), human("yes"),
                          assistant(text("Push B too?")), human("yes")])
        self.assertEqual(m["consecutive_asks"], 1)

    def test_queued_notification_without_origin_is_a_boundary(self):
        legacy = {"type": "attachment", "attachment": {"type": "queued_command", "commandMode": "task-notification",
                                                      "prompt": "<task-notification>done</task-notification>"}}
        m = self.measure([human("go"), assistant(text("Push A and B?")), legacy,
                          assistant(text("Job finished. Waiting on your push decision.")), human("yes")])
        self.assertEqual((m["human_turns"], m["replies"], m["question_replies"]), (2, 2, 1))

    def test_queued_human_turn_without_origin(self):
        legacy = {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "yes", "humanTurn": True}}
        m = self.measure([human("go"), assistant(text("Push?")), legacy])
        self.assertEqual((m["human_turns"], m["question_replies"]), (2, 1))

    def test_blank_entry_without_origin_is_not_a_human_turn(self):
        m = self.measure([human("go"), assistant(text("Push?")),
                          {"type": "user", "message": {"role": "user", "content": [text("   ")]}}])
        self.assertEqual(m["human_turns"], 1)

    def test_indented_fence_is_code(self):
        reply = "Steps:\n1. Run\n    ```bash\n    x = a ? b : c\n    ```\nDone."
        m = self.measure([human("go"), assistant(text(reply)), human("ok")])
        self.assertEqual(m["question_replies"], 0)

    def test_italic_and_trailing_dots_questions_count(self):
        for reply in ("_Ready to push?_", "Ready?...", "~~Push?~~ Done", "*Ready?*"):
            m = self.measure([human("go"), assistant(text(reply)), human("ok")])
            self.assertEqual(m["question_replies"], 1, reply)

    def test_reasks_after_a_typed_answer_are_separated_from_ask_tool_chains(self):
        m = self.measure([human("go"), assistant(ask_tool()), tool_result(), assistant(text("Also push?")), human("yes"),
                          assistant(text("And tag it?")), human("yes")])
        self.assertEqual((m["consecutive_asks"], m["reasks_after_typed_answer"]), (2, 1))
        self.assertEqual(m["reask_after_typed_answer_lines"], [6])

    # Text before a tool call. These pin a decision on #4 (verify round 3): the
    # script favours recall, so changing them moves the coder's candidate list.

    def test_text_before_a_tool_call_is_the_reply_when_no_later_text_replaces_it(self):
        m = self.measure([human("go"), assistant(text("Should I check the log?")), assistant(bash_tool()), tool_result(),
                          human("next")])
        self.assertEqual((m["replies"], m["question_replies"]), (1, 1))

    def test_later_text_replaces_text_before_a_tool_call(self):
        m = self.measure([human("go"), assistant(text("Should I check the log?")), assistant(bash_tool()), tool_result(),
                          assistant(text("Checked.")), human("next")])
        self.assertEqual((m["replies"], m["question_replies"]), (1, 0))

    def test_a_statement_before_a_tool_call_keeps_the_chain_for_a_text_question(self):
        m = self.measure([human("go"), assistant(text("Which file?")), human("a.py"),
                          assistant(text("Reading it.")), assistant(bash_tool()), tool_result(),
                          assistant(text("Which section?")), human("intro")])
        self.assertEqual((m["consecutive_asks"], m["reasks_after_typed_answer"]), (1, 1))

    def test_a_statement_before_a_tool_call_breaks_the_chain_for_the_ask_tool(self):
        m = self.measure([human("go"), assistant(text("Which file?")), human("a.py"),
                          assistant(text("Reading it.")), assistant(bash_tool()), tool_result(),
                          assistant(ask_tool()), tool_result(), human("next")])
        self.assertEqual((m["consecutive_asks"], m["reasks_after_typed_answer"]), (0, 0))

    def test_a_question_before_a_background_tool_is_a_stop_at_the_notification(self):
        m = self.measure([human("go"), assistant(text("Running it. Want the log too?")), assistant(bash_tool()), tool_result(),
                          notification(), human("yes")])
        self.assertEqual((m["replies"], m["question_replies"]), (1, 1))

    def test_summary_names_the_file_without_its_directory(self):
        path = self.write([human("go"), assistant(text("Push?")), human("yes")])
        code, out, err = self.cli(path)
        self.assertEqual(code, 0, err)
        self.assertIn(path.name, out)
        self.assertNotIn(str(path.parent), out)


class ReadmeCommand(unittest.TestCase):
    def test_deidentification_command_runs_as_written(self):
        fence = re.search(r"^ *```bash\n((?:(?!```).)*?> for-coding\.jsonl\n)", README.read_text(), re.S | re.M)
        self.assertIsNotNone(fence, "no bash fence in the README ends in `> for-coding.jsonl`")
        command = textwrap.dedent(fence.group(1))
        lines = [
            json.dumps(human("go")),
            json.dumps({"type": "attachment", "attachment": {"type": "hook_additional_context"}}),
            json.dumps({"type": "api-request-blob"}),
            "not json",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            (directory / "transcript.jsonl").write_text("\n".join(lines) + "\n")
            proc = subprocess.run(["bash", "-c", command], cwd=directory, capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            kept = (directory / "for-coding.jsonl").read_text().splitlines()
        self.assertEqual(kept, [lines[0], lines[3]])


if __name__ == "__main__":
    unittest.main()
