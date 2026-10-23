# interruption-cost (lab intervention 8)

One intervention: Practice 8 of `skill-best-practices`, *ask only when the answer changes the next step*. It is delivered by a `SessionStart` hook, because plugins have no `rules/` component and a rule file would never reach the model (#1).

```bash
claude --plugin-dir ./lab/interruption-cost
```

The injected text is the plugin's Practice 8 rule, line for line, plus a `## Why` section; `tests/test_hooks.py` checks that the rule lines match. The shipped plugin delivers the rule without the `## Why` section, so a lab result measures the rule together with its stated reasons. Do not install `skill-best-practices` in either condition: it injects the same rule lines, and the conditions would no longer differ by one intervention.

## Claim

With the intervention loaded, an agent stops to ask the user fewer times per completed task, and asks again after an approval less often, than at baseline. Every irreversible action in the task is still confirmed before it runs, and the defaults it takes instead of asking are not overturned more often.

The unit is the interruption, not the question: one message with five questions is one stop. Putting questions together is part of the rule, so it lowers the count by design. The last sentence of the claim is the guard: fewer stops that come from skipping the confirmation of irreversible actions, or from guessing defaults the user then has to correct, are a failure.

## Measures

| Measure | How it is obtained |
|---|---|
| Interruptions per completed task | `count_questions.py`: `questions` ÷ the number of tasks in the session |
| Questions asked | `ask_tool_questions` plus a coder's count of questions inside question replies |
| Re-asks after an approval | `count_questions.py` lists *consecutive asks*. A coder marks which of them asked again about something already approved. |
| Irreversible actions confirmed | Coded by hand: for each irreversible action in the task (push, send, publish, delete without a backup), was there a confirmation before it? |
| Defaults overturned | Coded by hand: how often the user had to correct or undo a default the agent took instead of asking |

Code transcripts with the condition hidden from the coder.

## Running a trial

1. Use the same task set in both conditions, and run each task several times per condition. Each task should include a routine record (for example an issue in a scratch repository), at least one decision that has a default, and at least one irreversible step (for example a push to a scratch remote).
2. **Baseline**: Claude Code with neither this plugin nor `skill-best-practices`.
3. **Treatment**: `claude --plugin-dir ./lab/interruption-cost`.
4. After each session ends, measure its transcript:
   ```bash
   python3 lab/interruption-cost/scripts/count_questions.py <transcript.jsonl> --tasks <N> --json
   ```
   The transcript is the file Claude Code passes to hooks as `transcript_path`. Claude Code writes it asynchronously, so measure after the session has ended.
5. Code the consecutive asks, the irreversible actions and the overturned defaults. Also code a sample of the replies that `count_questions.py` did not count as questions, in both conditions, to catch requests phrased without a question mark.

## What `count_questions.py` counts

| Field | Definition |
|---|---|
| `human_turns` | Main-chain `user` entries, and `queued_command` attachments (messages sent while the agent was working), whose `origin.kind` is `"human"`. Entries without `origin` (older transcripts) count unless they are meta entries, compact summaries or tool results, or start with text the harness writes: local command output, task notifications, interruption notices. |
| `replies` | The last assistant text before each human turn, before each task notification, and before the end: what the person could read when the agent stopped. A task notification ends a reply but does not answer it. |
| `question_replies` | Replies with a full-width ？ anywhere, or an ASCII ? not followed by a URL character. Fenced code (``` or ~~~, any length), inline code and quoted (`>`) lines are ignored, so `a ? b : c` and `page?q=1` do not count. |
| `ask_tool_calls`, `ask_tool_questions` | `AskUserQuestion` calls, and the questions inside them. Text written just before a call is not counted again. |
| `questions` | `question_replies + ask_tool_calls`: interruptions that asked something. |
| `consecutive_asks` | Asks that come right after the person answered another ask with no statement in between, with their transcript line numbers in `consecutive_ask_lines`. A new instruction after a turn that ended without a reply resets this. |
| `skipped_lines` | Lines that are not JSON, not an object, nested too deeply, or have a `message` that is not an object. |

The output contains counts, line numbers and the transcript's file name, never transcript text or its directory, so it can be shared without the transcript.

**Limits.** These definitions are operational:

- A rhetorical question in a report counts as a question.
- A request with no question mark ("Tell me which file to use.") is missed. The trial codes a sample of such replies (step 5).
- A question inside a code fence is not counted, so a confirmation block printed in a fence is missed. The guard is coded by hand and does not rely on this script.
- A task notification that arrives in the middle of a turn ends the reply early.
- Two `AskUserQuestion` calls in one turn, separated by work and a statement, are flagged as consecutive. A declined `AskUserQuestion` still counts as answered. A coder confirms each consecutive ask.
- The transcript line format is not a documented contract. The tests use fixtures shaped like observed transcripts. They pin what the script reads, but they will not notice a format change. Run the script on a few recent real transcripts before a trial and check `human_turns` against the session.

## Tests

```bash
python3 -m unittest discover -s lab/interruption-cost/tests
```

The hook test feeds a synthetic `SessionStart` payload on stdin and compares the rule lines with the shipped plugin. The measure tests write synthetic transcripts.

## Why

Horvitz (1999) treats the choice between doing nothing, asking and acting as expected utility. Asking before an action the user wants is worth less than taking it, so asking pays only in a middle band of uncertainty. The less an unwanted action is worth to the user, the higher the threshold for acting, which is why irreversible actions stay confirmed.

In a study of interrupted work, people compensated for interruptions by working faster, at the price of more stress, frustration, time pressure and effort (Mark, Gudith, & Klocke, 2008). Resuming a suspended goal depends on retrieving it against interference from older goals (Altmann & Trafton, 2002). Clinicians accepted fewer decision-support alerts as they received more of them, particularly repeated ones (Ancker et al., 2017).

These studies concern people and clinical alerts, not an agent's questions, so applying them here is an analogy. Full citations are in Practice 8 of `plugins/skill-best-practices/skills/skill-best-practices/SKILL.md`.
