"""Tests for the skill-best-practices hook scripts.

Each test feeds a synthetic hook payload on stdin, the way Claude Code does,
and checks what the script prints. Run with:

    python3 -m unittest discover -s plugins/skill-best-practices/tests
"""
import json
import pathlib
import subprocess
import unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "scripts"


def run(script, payload, env=None):
    proc = subprocess.run(
        ["python3", str(SCRIPTS / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def bash_payload(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


class SearchTruncationReminder(unittest.TestCase):
    SCRIPT = "search_truncation_reminder.py"

    def reminder(self, command):
        code, out, err = run(self.SCRIPT, bash_payload(command))
        self.assertEqual(code, 0, err)
        if not out.strip():
            return None
        data = json.loads(out)
        hso = data["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        # A reminder never decides the call: no permissionDecision of any kind.
        self.assertNotIn("permissionDecision", hso)
        return hso["additionalContext"]

    def test_grep_piped_to_head_gets_reminder(self):
        self.assertIn("evidence", self.reminder("grep -nE 'alpha|beta' notes.txt | head -12"))

    def test_rg_piped_to_head_without_count(self):
        self.assertIsNotNone(self.reminder("rg -n alpha src | head"))

    def test_grep_piped_to_tail(self):
        self.assertIsNotNone(self.reminder("grep -n alpha notes.txt | tail -n 5"))

    def test_grep_max_count_flag(self):
        self.assertIsNotNone(self.reminder("grep -m 3 alpha notes.txt"))
        self.assertIsNotNone(self.reminder("grep --max-count=3 alpha notes.txt"))

    def test_git_grep_piped_to_head(self):
        self.assertIsNotNone(self.reminder("git grep -n alpha origin/main | head -8"))

    def test_search_inside_longer_pipeline(self):
        self.assertIsNotNone(self.reminder("cat notes.txt | grep -v '^#' | grep -n alpha | cut -c1-80 | head -12"))

    def test_redirection_does_not_end_the_pipeline(self):
        self.assertIsNotNone(self.reminder("grep -rn alpha src 2>/dev/null | head -5"))
        self.assertIsNotNone(self.reminder("grep -rn alpha src 2>&1 | head -5"))

    def test_separate_commands_are_not_a_pipeline(self):
        self.assertIsNone(self.reminder("grep -n alpha notes.txt; head -3 other.txt"))
        self.assertIsNone(self.reminder("grep -q alpha notes.txt && tail -n 2 log.txt"))

    def test_untruncated_grep_is_silent(self):
        self.assertIsNone(self.reminder("grep -n alpha notes.txt"))

    def test_counting_is_silent(self):
        self.assertIsNone(self.reminder("grep -c alpha notes.txt"))
        self.assertIsNone(self.reminder("grep alpha notes.txt | wc -l"))

    def test_head_without_search_is_silent(self):
        self.assertIsNone(self.reminder("ls -la | head -5"))
        self.assertIsNone(self.reminder("git log --oneline | head -5"))
        self.assertIsNone(self.reminder("cat notes.txt | head -50"))

    def test_word_containing_grep_is_not_a_search(self):
        self.assertIsNone(self.reminder("echo regrep | head -1"))

    def test_non_bash_tool_is_silent(self):
        code, out, _ = run(self.SCRIPT, {"hook_event_name": "PreToolUse", "tool_name": "Read",
                                         "tool_input": {"file_path": "/tmp/x"}})
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "")

    def test_malformed_input_never_blocks(self):
        proc = subprocess.run(["python3", str(SCRIPTS / self.SCRIPT)], input="not json",
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")


class SessionStartRule(unittest.TestCase):
    def test_injects_runtime_rule(self):
        code, out, err = run("session_start.py", {"hook_event_name": "SessionStart", "source": "startup"})
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        hso = data["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "SessionStart")
        text = hso["additionalContext"]
        self.assertIn("Search locates, reading decides", text)
        self.assertIn("truncated", text)

    def context(self, source="startup"):
        code, out, err = run("session_start.py", {"hook_event_name": "SessionStart", "source": source})
        self.assertEqual(code, 0, err)
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]

    def test_injects_practice_8_rule(self):
        text = self.context()
        self.assertIn("Ask only when the answer changes the next step", text)
        self.assertIn("Practice 8", text)

    def test_practice_8_keeps_irreversible_actions_confirmed(self):
        text = self.context()
        self.assertIn("Irreversible or private actions still need confirmation", text)
        self.assertIn("do not ask again", text)

    def test_practice_8_asks_in_one_message(self):
        self.assertIn("in one message, not over several turns", self.context())

    def test_both_rules_restored_after_compaction(self):
        text = self.context("compact")
        self.assertIn("Search locates, reading decides", text)
        self.assertIn("Ask only when the answer changes the next step", text)


class SkillWritingReminder(unittest.TestCase):
    SCRIPT = "skill_writing_reminder.py"

    def context(self, tool, path):
        code, out, err = run(self.SCRIPT, {"hook_event_name": "PreToolUse", "tool_name": tool,
                                           "tool_input": {"file_path": path}})
        self.assertEqual(code, 0, err)
        if not out.strip():
            return None
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertNotIn("permissionDecision", hso)
        return hso["additionalContext"]

    def test_editing_a_skill_file_gets_the_rule(self):
        text = self.context("Edit", "/repo/plugins/x/skills/y/SKILL.md")
        self.assertIsNotNone(text)
        self.assertIn("Practice 7", text)

    def test_writing_a_skill_file_gets_the_rule(self):
        self.assertIsNotNone(self.context("Write", "/repo/skills/y/SKILL.md"))

    def test_windows_separators(self):
        self.assertIsNotNone(self.context("Edit", "C:\\repo\\skills\\y\\SKILL.md"))

    def test_other_files_are_silent(self):
        self.assertIsNone(self.context("Edit", "/repo/README.md"))
        self.assertIsNone(self.context("Edit", "/repo/skills/y/NOTSKILL.md"))

    def test_injected_once_per_session(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "TMPDIR": tmp}
            payload = {"hook_event_name": "PreToolUse", "tool_name": "Edit", "session_id": "s-1",
                       "tool_input": {"file_path": "/repo/skills/y/SKILL.md"}}
            _, first, _ = run(self.SCRIPT, payload, env)
            _, second, _ = run(self.SCRIPT, payload, env)
            _, other, _ = run(self.SCRIPT, {**payload, "session_id": "s-2"}, env)
        self.assertTrue(first.strip())
        self.assertEqual(second.strip(), "")
        self.assertTrue(other.strip())


class HooksManifest(unittest.TestCase):
    def test_hooks_json_wires_all_three_scripts(self):
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
        commands = json.dumps(hooks)
        for name in ("session_start.py", "search_truncation_reminder.py", "skill_writing_reminder.py"):
            self.assertIn(name, commands)
        matchers = {m["matcher"] for m in hooks["PreToolUse"]}
        self.assertIn("Bash", matchers)
        self.assertTrue(any("Write" in m and "Edit" in m for m in matchers))


if __name__ == "__main__":
    unittest.main()
