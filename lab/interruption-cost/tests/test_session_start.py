"""Tests for the interruption-cost lab plugin's hook.

The test feeds a synthetic SessionStart payload on stdin, the way Claude Code
does, and checks what the script prints. Run with:

    python3 -m unittest discover -s lab/interruption-cost/tests
"""
import importlib.util
import json
import pathlib
import subprocess
import unittest

PLUGIN = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "scripts"


def load(path):
    spec = importlib.util.spec_from_file_location(f"mod_{abs(hash(str(path)))}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(script, stdin):
    proc = subprocess.run(
        ["python3", str(SCRIPTS / script)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return proc.returncode, proc.stdout, proc.stderr


class SessionStartIntervention(unittest.TestCase):
    def output(self, source="startup"):
        code, out, err = run("session_start.py", json.dumps({"hook_event_name": "SessionStart", "source": source}))
        self.assertEqual(code, 0, err)
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "SessionStart")
        return hso

    def test_injects_the_practice_8_rule(self):
        self.assertIn("Ask only when the answer changes the next step", self.output()["additionalContext"])

    def test_injected_text_has_a_why_section(self):
        self.assertIn("## Why", self.output()["additionalContext"])

    def test_keeps_irreversible_actions_confirmed(self):
        text = self.output()["additionalContext"]
        self.assertIn("Irreversible or private actions still need confirmation", text)
        self.assertIn("Do not ask again", text)

    def test_never_decides_a_tool_call(self):
        self.assertNotIn("permissionDecision", self.output())

    def test_restored_after_compaction(self):
        self.assertIn("Ask only when the answer changes the next step", self.output("compact")["additionalContext"])

    def test_malformed_input_never_blocks(self):
        code, out, err = run("session_start.py", "not json")
        self.assertEqual(code, 0, err)
        self.assertIn("additionalContext", out)

    def test_rule_lines_match_the_shipped_plugin(self):
        # The lab must test the rule users get. Every rule line of the plugin's
        # Practice 8 appears in the lab text, word for word.
        shipped = load(PLUGIN.parents[1] / "plugins" / "skill-best-practices" / "scripts" / "session_start.py").PRACTICE_8
        lab = self.output()["additionalContext"]
        lines = [l for l in shipped.splitlines() if l.startswith("- ")]
        self.assertGreater(len(lines), 3)
        for line in lines:
            self.assertIn(line, lab)

    def test_why_section_states_measured_outcomes_only(self):
        text = self.output()["additionalContext"]
        self.assertNotIn("lose their signal", text)
        self.assertIn("analogy", text)


class Manifest(unittest.TestCase):
    def test_hooks_json_wires_only_the_session_start_script(self):
        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]
        self.assertEqual(set(hooks), {"SessionStart"})
        self.assertIn("session_start.py", json.dumps(hooks["SessionStart"]))

    def test_no_rules_directory(self):
        # Plugins have no rules/ component (#1): a rules/ file here would never load.
        self.assertFalse((PLUGIN / "rules").exists())


if __name__ == "__main__":
    unittest.main()
