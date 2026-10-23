# interruption-cost (lab intervention 8)

One intervention: Practice 8 of `skill-best-practices`, *ask only when the answer changes the next step*. It is delivered by a `SessionStart` hook, because plugins have no `rules/` component and a rule file would never reach the model (#1).

```bash
claude --plugin-dir ./lab/interruption-cost
```

The injected text contains every rule line of the plugin's Practice 8 word for word; `tests/test_hooks.py` checks this. Its heading and opening sentence differ, and it adds a `## Why` section, which the shipped plugin does not deliver. A lab result therefore measures the rule together with its stated reasons.

## Claim

With the intervention loaded, an agent stops to ask the user fewer times per completed task, and asks again after an approval less often, than at baseline. Every irreversible action in the task is still confirmed before it runs, and the defaults it takes instead of asking are not overturned more often.

The unit is the stop, not the question: one message with five questions is one stop. Putting questions together is part of the rule, so it lowers the count by design. The last sentence of the claim is the guard: fewer stops that come from skipping the confirmation of irreversible actions, or from guessing defaults the user then has to correct, are a failure.

## Measures

| Measure | How it is obtained |
|---|---|
| **Stops per completed task** (primary) | A coder marks every reply where the agent waited on a decision from the user, with or without a question mark, and divides by the number of completed tasks. `count_questions.py` gives the candidate list and a lower bound (`questions`). |
| Questions asked | `ask_tool_questions` plus a coder's count of the questions inside each coded stop |
| Re-asks after an approval | A coder starts from `reask_after_typed_answer_lines` (asked again right after the person typed an answer), then the rest of `consecutive_ask_lines`, and marks which asked again about something already approved |
| Irreversible actions confirmed | Coded by hand: for each irreversible action in the task (push, send, publish, delete without a backup), was there a confirmation before it? |
| Defaults overturned | Coded by hand: how often the user had to correct or undo a default the agent took instead of asking |

The script's `questions` cannot be the primary measure. The rule asks for short reports that say "what is left for the user to decide", which can end a turn with a statement instead of a question, so a script that counts question marks would favour the treatment.

Most consecutive asks are a different next question in the same workflow, not a re-ask. On 80 of the author's recent transcripts the script found 581 asks, 148 consecutive asks and 123 asks right after a typed answer.

## Running a trial

1. Use the same task set in both conditions, and run each task several times per condition. Each task should include a routine record (for example an issue in a scratch repository), at least one decision that has a default, and at least one irreversible step (for example a push to a scratch remote). Use disposable repositories and remotes, and leave Claude Code's permission prompts on.
2. Run both conditions with a fresh configuration directory, for example `CLAUDE_CONFIG_DIR=<an empty directory>`, and in a task repository with no CLAUDE.md that states a similar rule. A user CLAUDE.md, a project CLAUDE.md or an installed plugin can carry the same rule into the baseline. If a clean configuration is not possible, record which CLAUDE.md files and plugins each run loaded and keep them the same in both conditions.
3. **Baseline**: Claude Code with neither this plugin nor `skill-best-practices`.
4. **Treatment**: `claude --plugin-dir ./lab/interruption-cost`.
5. After each session ends, prepare the transcript for blind coding by removing hook output. The treatment's rule text is recorded in `hook_*` attachments, and again in the raw request copies (`api-request*` entries):
   ```bash
   python3 -c 'import json,sys
   for line in open(sys.argv[1]):
       try:
           e = json.loads(line)
       except ValueError:
           e = None
       a = e.get("attachment") if isinstance(e, dict) else None
       if isinstance(e, dict) and str(e.get("type", "")).startswith("api-request"):
           continue
       if isinstance(a, dict) and e.get("type") == "attachment" and str(a.get("type", "")).startswith("hook"):
           continue
       sys.stdout.write(line)' <transcript.jsonl> > for-coding.jsonl
   python3 lab/interruption-cost/scripts/count_questions.py for-coding.jsonl --tasks <completed tasks> --json
   ```
   The transcript is the file Claude Code passes to hooks as `transcript_path`, under the configuration directory. Claude Code writes it asynchronously, so measure after the session has ended. Run the script on the stripped file so its line numbers match what the coder reads. Blinding is partial: the treatment's behaviour, such as stating a default in one line, can still reveal the condition.
6. Code the stops, the re-asks, the irreversible actions and the overturned defaults.

## What `count_questions.py` counts

| Field | Definition |
|---|---|
| `human_turns` | Main-chain `user` entries, and `queued_command` attachments (messages sent while the agent was working), whose `origin.kind` is `"human"`. Entries without `origin` (older transcripts) count unless they are meta entries, compact summaries, tool results or blank, or start with text the harness writes: local command output, task notifications, interruption notices. |
| `replies` | What the person could read when the agent stopped: the assistant text before each human turn, before each task notification, and before the end. Text blocks written in a row form one reply; a tool call, a tool result or another user entry starts a new one. A task notification ends a reply but does not answer it. |
| `question_replies` | Replies with a full-width ？ anywhere, or an ASCII ? not followed by a letter, digit or URL character (`= & % # / +`). Fenced code (``` or ~~~, any length or indent), inline code and quoted (`>`) lines are ignored, so `a ? b : c` and `page?q=1` do not count. |
| `ask_tool_calls`, `ask_tool_questions` | `AskUserQuestion` calls, and the questions inside them. Text written just before a call is not counted again. |
| `questions` | `question_replies + ask_tool_calls`: stops that asked with a question mark or the ask tool. |
| `consecutive_asks` | Asks that come right after the person answered another ask, with their transcript lines in `consecutive_ask_lines`. A statement reply, or a turn that ended without a reply before a new instruction, breaks the chain. |
| `reasks_after_typed_answer` | The consecutive asks whose previous ask the person answered by typing, not through `AskUserQuestion`, with their lines in `reask_after_typed_answer_lines`. |
| `skipped_lines` | Lines that are not JSON, not an object, nested too deeply, or have a `message` that is not an object. |

The output contains counts, line numbers and the transcript's file name, never transcript text or its directory, so it can be shared without the transcript.

**Limits.** These definitions are operational:

- A rhetorical question in a report counts as a question; a request with no question mark ("Tell me which file to use.") does not. The coder marks stops by reading, not by this count.
- A question inside a code fence is not counted, so a confirmation block printed in a fence is missed. The guard is coded by hand and does not rely on this script.
- A task notification, or a message the person sends while the agent is still working, ends the reply at that point, so narration written before it can be counted as a reply.
- Two `AskUserQuestion` blocks in one assistant message are counted as consecutive. A declined `AskUserQuestion` still counts as answered. A new instruction sent before the agent writes anything keeps the chain. A coder confirms each consecutive ask.
- The treatment adds a few hundred words of context that the baseline does not have. A length-matched neutral text in the baseline would separate the rule's content from its length; it is not part of this protocol.
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
