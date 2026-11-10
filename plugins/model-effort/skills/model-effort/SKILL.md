---
name: model-effort
description: |
  Choose the Claude model and effort level for a piece of work. Use whenever a model or effort
  level is being chosen or questioned: the session's /model and /effort, the model and effort of
  a subagent (Agent tool parameters or subagent frontmatter), each agent() in a Workflow script,
  skill frontmatter, or the model and output_config.effort of a Claude API script. Also answers
  "why isn't the effort level the one I set", "which model is this subagent on", "which is
  cheaper", "how high should Fable 5.2 go". Triggers: which model, what effort, opus or sonnet,
  is haiku enough, xhigh, max, ultrathink, fast mode, too expensive, burning tokens, rate limit,
  pin the model.
---

# Model and effort

The facts in this file were checked on **2026-11-10** against Claude Code **2.1.322**, the Claude Code and Claude API documentation, and Anthropic's blog post of 2026-11-09 (sources at the end). Model names, defaults and prices change. Re-check the sources before you copy a number into another file, when your version differs, or when this date is more than a month old.

Every recommendation carries its basis:

| Tag | Basis |
|-----|-------|
| [docs] | Claude Code or Claude API documentation |
| [blog] | Anthropic's post "Which Claude model should you build with?"; its numbers are Anthropic's own benchmarks |
| [measured] | A measurement in this repository, with its sample size |
| [judgment] | A trade-off with no direct evidence. The user's own preference wins |

Where two sources disagree, this file lists both. It does not merge them.

## Check what is actually set

Before recommending anything, read what applies now:

- `/effort status` shows the level the session sends. [docs]
- `/tasks` shows the model and effort of each running subagent. [docs]
- In `~/.claude/settings.json`: `model`, `effortLevel`, `modelSettings`, and `env` entries `CLAUDE_CODE_EFFORT_LEVEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`. Project and managed settings can set them too.

## Principles

1. **When a result falls short, change one thing at a time, in this order.** [blog]
   1. Let the model check its own work: a test, a build, a script that calls the endpoint.
   2. Raise effort one level, up to `high`. If the work already runs at `high`, skip this step: test the next model up first (principle 2).
   3. Move to the next model up, starting at a lower effort level than you used on the smaller one.

   A higher effort level will not give a model knowledge or skill it lacks; that needs a bigger model. [blog]

   Tighten the prompt before raising effort. [measured, n=1] In this repository's verification of #4, a devil's-advocate reviewer on Sonnet returned zero findings in 36 seconds. The next round kept Sonnet and rewrote the brief as a numbered list of required checks, and the reviewer did the checks. It is one uncontrolled comparison, so treat it as a step to try, not as proof that the model does not matter.
2. **Past `high`, compare the next model up at a lower level.** [blog] Past `high`, one more effort level can cost as much as a bigger model. Two examples from Anthropic's runs:
   - On FrontierCode 2.0, Fable 5.2 at `high` scored about level with Opus 5.5 at `max` (45.3% vs 45.5%) for roughly half the cost per task.
   - On SWE-bench Pro, compared with Opus 5.5 at `high`, Opus 5.5 at `medium` scored about 2.5 points lower for about 70% of the cost, at `low` about 8 points lower for about a third, and at `xhigh` about 1.4 points higher for 2.5 times the cost.
3. **Compare cost per finished task, not price per token.** [blog] A higher price per token does not always mean a higher cost per task. Price the hardest tasks in your set as well as the typical ones: on one 20-problem benchmark, two problems carried 43% of the spend. A result that has to be redone costs more than the price difference saved.
4. **When outcomes can be checked automatically, run everything low and re-run only the failures high.** [blog] On a SWE-bench Pro subset, Opus 5.5 at `low` with failures re-run at `high` passed about 97% of tasks for about $0.17 each, against 95.3% for $0.29 with every task at `high`.
5. **Switch models at a natural break.** [blog] The prompt cache belongs to the model that wrote it, so the first turn on a new model pays the cache-write price on the whole conversation. Run `/compact` first, or start a fresh session with a short written plan. A move from Fable 5.2 to any other generally available model drops Fable's earlier thinking.

## Defaults differ between Claude Code and the API

| Model (API ID) | Claude Code default | API default | Input / output per MTok | Cache read per MTok | Fast mode |
|---|---|---|---|---|---|
| Fable 5.2 (`claude-fable-5-2`) | `medium` | **`high`** | $8 / $40 | $0.20 | Yes, $16 / $80 |
| Opus 5.5 (`claude-opus-5-5`) | `medium` | `medium` | $4 / $20 | $0.20 | Yes, $8 / $40 |
| Sonnet 5.5 (`claude-sonnet-5-5`) | `medium` | **`high`** | $2 / $10 | $0.10 | No |
| Haiku 5.5 (`claude-haiku-5-5`) | `medium` | `medium` | $0.10 / $0.50 up to 100K-token prompts; $0.50 / $2.50 over | $0.01; $0.05 over 100K | No |

Notes [docs, blog]:

- All four models offer `low`, `medium`, `high`, `xhigh` and `max`, a 1M-token context window and 128K output tokens.
- Each model's levels are calibrated separately: the same name is not the same amount of reasoning on another model. Do not carry a level over when you switch models.
- The Batch API is half price.
- Fable 5.2 and Opus 5.5 have the same cache-read price. On a long, cache-heavy run, the gap between them comes down to uncached input and output, where Fable 5.2 costs twice as much.
- Haiku 5.5 is the only model whose price depends on prompt length. When every call needs a long prompt, compare it with Sonnet 5.5 on cost per finished task.
- Fast mode is up to 2.5 times faster at the same quality. On a Claude subscription it is paid from usage credits.

Aliases on the Anthropic API [docs]:

| Alias | Resolves to |
|-------|-------------|
| `opus`, `best` | Opus 5.5 |
| `sonnet` | Sonnet 5.5 |
| `haiku` | Haiku 5.5 |
| `fable` | Fable 5.2 (Fable 5 in Claude apps gateway sessions) |

On Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry and Claude Platform on AWS, `sonnet` and `haiku` resolve to older versions. Check the model-config page for your provider.

`opusplan` plans with Opus in plan mode and then carries out the plan with Sonnet, which puts code edits on Sonnet. [blog] That is the reverse of keeping edits and judgment on the main model. Measure it on your own tasks before you make it your default.

## How Claude Code picks the session's effort level

Claude Code takes the first of these that applies: [docs]

1. The `CLAUDE_CODE_EFFORT_LEVEL` environment variable. It also overrides skill and subagent levels.
2. A level picked in the session, with `/effort` or the `/model` picker.
3. `--effort` at launch.
4. Settings: the level saved for the model in `modelSettings`, or an `effortLevel` key.
5. The model's default, from the table above.

Places where this goes wrong without a warning [docs]:

- **A top-level `effortLevel` in the user settings file does not count for Opus 5.5 or models released after it.** It is the form `/effort` wrote before levels were saved per model, and it still applies to Opus 5, Fable 5.1 and earlier models. Those newer models read `modelSettings` and otherwise start at their own default. A top-level `effortLevel` in project, local or managed settings, or one passed with `--settings`, applies to every model.
- **Saving a level is a keystroke choice.** `Enter` in the `/effort` slider or the `/model` picker, or a level typed after `/effort`, saves it as that model's default. `s` applies it to this session only. `/effort auto` clears the saved level for the active model.
- **`max` cannot be saved.** Neither `modelSettings` nor `effortLevel` accepts it. Unless it comes from the environment variable, it lasts for the current session only.
- **Thinking cannot be turned off** on Opus 5.5, Sonnet 5.5, Haiku 5.5 or the Fable models in Claude Code. `alwaysThinkingEnabled: false` and `MAX_THINKING_TOKENS=0` have no effect there; effort is the control.
- **`ultrathink` raises one turn.** The word anywhere in a prompt asks for deeper reasoning on that turn without changing the session level. Typed in the terminal, it can raise the turn to `xhigh` (v2.1.311 or later; the word shows in rainbow colors when it does). "Think hard" and similar phrases are ordinary text.
- **`ultracode` is a setting, not a level.** It has Claude plan a Workflow for each substantive task, at whatever effort level the session runs.

## Situations (a closed list: only these six; do not extend it by similarity)

### 1. The main session

- **How to set it**: `/model`, `/effort`, or `--model` and `--effort` at launch. Claude cannot change the session's model itself; it can only suggest a change.
- **Where to start** [blog]: start most work on Opus 5.5 at `medium`, the default model in Claude Code, at half Fable 5.2's per-token price. From there:
  - **Move down to Sonnet 5.5** for well-scoped everyday work, such as a bug fix or a feature built against a spec. A clear spec alone is not enough: a migration or a performance optimization can have a clear spec and still need Opus 5.5, or Fable 5.2 for a major one.
  - **Move up to Fable 5.2** for the hardest technical projects: major refactors and migrations, architecture planning, leading many subagents, deep research, and scientific or quantitative analysis. Also move up when Opus 5.5 at `high` still falls short, and for long unattended runs.
- **Fable 5.2's starting level, two sources**: the blog's table says "`medium`, then `high`" in Claude Code. The API effort guide says "Start with `high`".
- **What each level fits** [docs]:
  - `low`: quick exchanges where you review each result, such as brainstorming, a first sketch, or a rename.
  - `medium`: day-to-day engineering with a clear scope.
  - `high`: work where verification matters or edge cases are likely, such as fixing a bug in an existing codebase.
  - `xhigh`: deeper reasoning at higher token spend.
  - `max`: hard problems Claude works through without you, such as finding security vulnerabilities. It may show diminishing returns and overthink, so test it before adopting it broadly.
- **Effort costs latency** [blog]: for replies a person waits on, start Sonnet 5.5 at `low` or `medium`.
- **Keep the main context lean** [blog]: the bigger the main model, the more a lean main context matters. Keep the expensive model's context for the decisions, and let cheaper subagents do the verbose reading.
- **The user's settings** [judgment]: follow the levels the user saved and do not change their settings unasked. If their default model differs from the blog's general advice, that is their choice; mention it once when cost comes up, not on every turn.

### 2. Subagents started with the Agent tool

- **Model** [docs]: the Agent tool's `model` parameter takes an alias only (`sonnet`, `opus`, `haiku`, `fable`). Claude Code resolves the subagent's model in this order:
  1. The `model` parameter on this call.
  2. The subagent definition's `model`.
  3. `CLAUDE_CODE_SUBAGENT_MODEL`.
  4. The main session's model.
- **Effort** [docs]: the `effort` parameter (v2.1.292 or later) overrides the definition's `effort`. `CLAUDE_CODE_EFFORT_LEVEL` overrides both.
- **Always pass `model`** [judgment]: without it the subagent runs on the session's model, which is the most expensive choice when the session runs Fable.
- **Pass `effort` when depth matters** [docs, judgment]: on a different model from the session, the session's level does not apply. The docs do not say which level it gets instead, so do not assume one; name it.
- **What to delegate** [blog]: keep small models on work where a mistake is cheap to spot, such as finding files, running tests and reading logs. Keep code edits and judgment calls on the main model. When a small model misreads a search result, the main model opens the wrong file and spends tokens on it.
- **Starting points** (four kinds of work, a closed list):

| Subagent's work | Model | Effort |
|---|---|---|
| Find and report: search files, read logs, extract a passage, summarize in a fixed format | `haiku` or `sonnet` [blog, docs] | Two sources: the blog says the model's default; the API effort guide names `low` for "simpler tasks ... such as subagents". [judgment] Use `low` when the output has a fixed format and the main model reads it |
| Repeated, well-defined agent tasks: investigation, checklist review, drafting | `sonnet` [blog] | `medium` [blog] |
| Review that needs judgment: devil's advocate, cross-file reasoning, finding contradictions in a spec | `sonnet` at `high`, or `opus` at `medium` [judgment]; tighten the prompt first (principle 1) | as left |
| Final verdicts, proofs, architecture trade-offs | Keep on the main model; if delegated, `opus` or `fable` [blog: judgment calls stay on the main model] | `high` [judgment] |

- **Name the level.** When you follow this table, pass the level by name (`low`, `medium`, `high`), not a relative step.
- **Two traps** [docs]:
  - **Explore follows the session's model, with one exception.** The built-in Explore subagent runs on the main conversation's model. When the main conversation runs Fable, on a Claude subscription, a Console account or an LLM gateway, Explore runs on the model the `opus` alias resolves to. To keep exploration cheap, define your own subagent named `Explore` with `model: haiku` [blog]. `CLAUDE_CODE_SUBAGENT_MODEL` alone does not change Explore; set it together with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`.
  - **A family alias can resolve to the session's model.** When the alias names the main conversation's family, the subagent runs on the main conversation's exact model, including a `[1m]` suffix, not on the version the alias points to.

### 3. `agent()` in a Workflow script

- **Options** [workflow-authoring skill]: `agent(prompt, {model, effort, ...})`, where `effort` is `'low' | 'medium' | 'high' | 'xhigh' | 'max'`. Omitted, both come from the session.
- **Cost** [docs]: Claude Code picks each workflow agent's model in the same order as for subagents, and a model the script names counts as the per-invocation model. When nothing assigns one, the agent runs on the session's model. The docs' advice: check `/model` before a large run, and use a smaller model for stages that don't need the strongest one. [judgment] A wide fan-out with no pins pays the session model's price once per agent.
- **Delegating bulk work** [blog]: on a defect-search benchmark over about 22 million tokens of source code, an Opus 5.5 lead with up to 25 Sonnet 5.5 workers at a time cost about a third less than Opus 5.5 alone at its default effort, and scored about the same. For one chain of dependent steps, or for work that fits in one context window, skip the fan-out: planning and merging cost more than they save.
- **Starting points** [judgment]:
  - Wide fan-out (four or more agents): pin every `agent()` to `model: 'sonnet'` or `'haiku'`.
  - Mechanical stages (set-up, moving data, extracting to a schema): add `effort: 'low'`.
  - The final verify or judge stage: `'high'`.
  - One or two agents in sequence: inheriting the session is affordable.

### 4. Skill and subagent frontmatter

- **Skill** [docs]: `model` and `effort` apply for the rest of the current turn and are not saved; the session's settings return with the next prompt. With `context: fork`, they set the forked subagent's model and effort instead.
- **Subagent definition** [docs]: `model` takes an alias, a full model ID, or `inherit`. `effort` applies while the subagent runs, unless the invocation overrides it. Example from the blog:

```markdown
---
name: log-reader
description: Reads test output and logs, and reports each failing case. Use after a test run.
tools: Read, Grep, Glob, Bash
model: haiku
---

Read the logs you're given. For each failure, report the file, the test name and the first error line. Don't edit any files.
```

- **When writing a skill** [judgment]:
  - Set `effort` only when the skill's work clearly needs a different depth, such as `low` for bulk mechanical work.
  - Avoid `model` in a skill that runs in the main conversation: it swaps the session's model for the rest of the turn, a model the user did not choose. To move work to a cheaper model, use `context: fork` with `model`, or have the skill name the model it passes when it starts a subagent.

### 5. Claude API scripts

- **Write the code with the `claude-api` skill.** Do not write SDK calls from memory. Effort goes in `output_config: {effort: ...}`; use `thinking: {type: "adaptive"}`.
- **Request shapes that fail on the current models**: test each before moving a request to another model.
  - `budget_tokens` is rejected with a 400 on Fable 5.2, Opus 5.5 and Sonnet 5.5. [claude-api skill]
  - From Haiku 4.5 to Haiku 5.5: replace `budget_tokens` with an effort level; drop non-default `temperature`, `top_p` and `top_k`, which return a 400; end `messages` with a user turn. [blog]
  - Opus 5.5 and Fable 5.2 always think, and a request that turns thinking off returns an error. Sonnet 5.5's `between_tools` limits thinking to the gaps between tool calls. Haiku 5.5 can turn thinking off at `high` or below. On every model, read content blocks by `type`, because a response can begin with a thinking block. [blog, docs]
  - A `tool_choice` of `any` or `tool` returns a 400 on Sonnet 5.5, Opus 5.5 and Fable 5.2. Send `auto`, mark the tool `strict: true`, and say in the prompt when to use it. [blog]
  - Fable 5.2 rejects a request with a 400 when anything before one of its thinking blocks has changed, including the system prompt, the tools or an earlier message, unless you opt in to dropping the affected thinking. Keep history append-only. [blog]
- **Starting model and level** [blog, docs]:
  - Classification, routing, tagging and high-volume extraction: Haiku 5.5 at `medium`.
  - Well-scoped coding and repeated agent tasks: Sonnet 5.5 at `medium`, `high` for harder ones. Sonnet 5.5's API default is `high`, so an omitted `effort` runs at `high`.
  - Not sure yet: Opus 5.5 at `medium`.
  - The hardest technical work: Fable 5.2. The API guide says start at `high`; use `xhigh` only for the hardest long-running work where you have measured a gain, and keep `max` for measuring the ceiling. Effort barely changes reply length; use the prompt to change length and tone.
  - At `high` and above, set a large `max_tokens`. It caps thinking and reply together.
- **Spend** [claude-api skill]: every run that calls the model costs money. Before a batch, estimate items × (input + output tokens) × price, use the Batch API when results can wait, and get the user's approval for the estimate.
- **Measure on your own work** [blog]:
  1. Pull a sample of real tasks and write an outcome check for each.
  2. Run each candidate model at two or three effort levels, each in its own session so the runs do not share a cache.
  3. Record the cost of each finished task from the `usage` field.
  4. Plot score against spend. Keep a multi-model setup only if it beats every single-model point.
  5. Run the winner in shadow on a slice of real traffic before you cut over.

  For a quick check in Claude Code, run one task on two models with `/model` and compare what `/usage` reports.
- **Several models in one system** [blog]: build every request for the strictest model: append-only history, `tool_choice: auto` with strict tools, content blocks read by `type`, and prompts precise enough for the most literal model. Then a step can move up or down a tier without a code change. When the routing rule is simple, such as one model per step type, let code pick the model.

### 6. Tools with their own model settings

Plugins, CLIs and services that call models themselves (an ensemble reviewer, a Codex or other vendor CLI, a local model server) have their own model and effort settings. Read that tool's configuration and documentation. Do not apply this file's Claude effort names to another vendor's models.

## Before answering

Before recommending a model or starting work on one, check:

1. Did you read what is set now (`/effort status`, `/tasks`, the settings keys above)?
2. Which of the six situations is it? If none fits, say so and look it up; do not extend the list by similarity.
3. Is each default you cite the Claude Code one or the API one? Where sources disagree, give both.
4. Does every subagent and `agent()` you start name its model, and, where depth matters, its effort level by name?
5. If you suggest switching models, did you count the cost of the switch (principle 5)?
6. Which parts of your answer are [judgment]? Say so in the answer.

## Sources (read 2026-11-10)

- Claude Code documentation, under `https://code.claude.com/docs/en/`:
  - `model-config.md`: Adjust effort level, Model aliases, Extended thinking
  - `sub-agents.md`: Built-in subagents, Choose a model, Choose an effort level
  - `skills.md`: frontmatter `model` and `effort`
  - `workflows.md`: Cost
  - `costs.md`: Choose the right model
  - `fast-mode.md`
- Claude API documentation:
  - `https://platform.claude.com/docs/en/build-with-claude/effort.md`: per-model recommendations
  - `https://platform.claude.com/docs/en/about-claude/pricing.md`
- Addy Osmani, "Which Claude model should you build with? Fable, Opus, Sonnet, or Haiku", Anthropic, 2026-11-09, `https://claude.dev/blog/which-claude-model-should-you-build-with/`
- Bundled Claude Code skills: `workflow-authoring` (the `agent()` options) and `claude-api` (cost rules, model IDs, `budget_tokens`)

## Why

Choosing a model and an effort level is a decision under uncertainty about cost and quality, made many times a day. The facts it rests on are scattered across several documentation pages, differ between Claude Code and the API, and change with each release. Several of the failures are silent: a saved level that does not apply, a subagent that does not inherit the session's level, a fan-out that inherits the most expensive model.

Before this skill was written, a model answered three scenarios without it. Its answers had four gaps that this file covers:

- For a proof on Fable 5.2 it kept `xhigh` and offered `max` to go deeper. Neither source starts above `high`.
- For an API grading script it was not sure of the current model IDs or the effort parameter's name.
- For a shallow devil's-advocate reviewer, its first change was a bigger model at higher effort. Tightening the prompt came second, although that alone had worked (principle 1).
- It did not know that `agent()` takes an effort level, so it set none.

The evidence here is vendor documentation and Anthropic's own benchmarks, not peer-reviewed research, and it goes stale as models change. That is why every line carries its source and the file carries the date it was checked. If a later edit wants to fold these rules into one general sentence, look at the list above first: each item is a case a general sentence answered wrongly.
