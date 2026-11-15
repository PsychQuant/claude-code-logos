# Claude Code Logos

**Plugins that manage how Claude Code runs.**

Logos (λόγος) — reason, principle, rational order.

Each plugin here changes how Claude Code itself works: how skills are written and followed, which model and effort level a piece of work gets, where answers about a library come from, which deletions and edits under archive folders are refused. Every plugin says what its claims rest on — published research, vendor documentation, reading the primary source live, or, where there is nothing more than that, the author's own experience, said as such.

## Install

```bash
claude plugin marketplace add PsychQuant/claude-code-logos
claude plugin install skill-best-practices@claude-code-logos
claude plugin install model-effort@claude-code-logos
claude plugin install livedocs@claude-code-logos
claude plugin install archive-first@claude-code-logos
```

If you already installed `livedocs@livedocs-marketplace`, remove that marketplace first (`claude plugin marketplace remove livedocs-marketplace`, which also uninstalls its plugin), so that two copies of the plugin are not enabled together.

The same holds for `archive-first@psychquant-claude-plugins`: it is the same plugin, so disable or uninstall that one before installing `archive-first` from here, or each hook runs twice.

Or, in a session on Claude Code 2.1.275 or later: `/plugin install skill-best-practices --marketplace PsychQuant/claude-code-logos`

## Principles

1. **State the evidence** — every plugin says what its claims rest on, and marks what it has not checked
2. **Nudge, don't force** — guide behavior through design, not restriction
3. **Measurable impact** — each plugin should have a testable claim

## Plugins

| Plugin | What it does | Rests on | Lives in |
|--------|--------------|----------|----------|
| `skill-best-practices` | Eight evidence-based practices for writing Claude Code skills, as an on-demand skill, plus hooks that deliver the rules while Claude works: session-start rules (read search results before concluding; ask the user only when the answer changes the next step, while still confirming irreversible actions) and a reminder when search output is truncated | Published research (see [Research Foundations](#research-foundations)) | this repository |
| `model-effort` | An on-demand skill for choosing the Claude model and effort level: the session's `/model` and `/effort`, subagents, Workflow `agent()` calls, skill frontmatter, and Claude API scripts. Claude Code defaults and API defaults are kept apart, and settings that fail silently are named (a top-level `effortLevel` that newer models ignore, subagents that don't inherit the session's level) | Claude Code and Claude API documentation and Anthropic's own benchmarks, each recommendation is tagged with its source and the skill states the date its facts were checked; a stale date is a reason to re-check | this repository |
| `livedocs` | An MCP server and a look-up skill that answer questions about a library, SDK or CLI from its primary source instead of from training data or a pre-built index. macOS only; the plugin's wrapper downloads an executable, the MCP server, from the GitHub Releases of `PsychQuant/livedocs` to `~/bin` and runs it | The library's own primary source, read at the time of the question (llms.txt, package registry, repository, OpenAPI/GraphQL, CLI introspection) | [`PsychQuant/livedocs`](https://github.com/PsychQuant/livedocs), included here as a git submodule at `plugins/livedocs`; this repository records the commit that is installed |
| `archive-first` | Three PreToolUse hooks and three commands. The Bash hook refuses a command when one of its parts (split at `;`, `&&`, `||`) contains the word `rm`, `rmdir` or `unlink` and the text `archive/` or `archived/`. The Write and Edit hooks refuse a file path that contains `/archive/` or `/archived/`. The commands copy a folder into `archived/` with a timestamp before it is reorganised, and turn the hooks off and on. What the hooks do not stop: removing the directory itself when it is written without a trailing slash; `cd` into it and then a deletion; any other Bash way of changing the files (`mv`, `find -delete`, a redirect, `cp`, `sed -i`, `git clean`, a path held in a variable); a directory spelled another way (`Archive/`, `archives/`); NotebookEdit. A harmless command whose text has both a deleting word and such a path is refused, and so is one on a path that only ends the same way (`myarchive/`). The hooks need `jq` and a POSIX shell; without `jq` they allow everything. Turning the hooks off creates one file, `~/.cache/archive-first/disabled`, which turns them off in every project and session until it is deleted, and the agent can create that file itself | The author's own experience of a coding agent deleting files, and the copy-first habit that followed. The write-up the plugin links to was not reachable on 2026-11-15, so it is not cited here. No published research, and no measurement of how often the hooks stop a deletion | [`PsychQuant/archive-first`](https://github.com/PsychQuant/archive-first), included here as a git submodule at `plugins/archive-first`; this repository records the commit that is installed. That repository's own README still describes version 1 (other command names, a lock hook, macOS only); this row follows the 2.2.0 hooks and commands |

**`skill-best-practices` changes when the agent asks you.** For work you asked for, in a repository you can write to, it no longer asks first before four routine GitHub records: creating an issue or comment, editing your own issue body or comment, setting a label or milestone or assigning you, and the IDD baseline tag. If the content is private or mentions someone, it still asks. A stricter policy of your own wins, and Claude Code's permission prompts still apply.

## Research Foundations

This section applies to `skill-best-practices`.

| Principle | Source | Application |
|-----------|--------|-------------|
| Checklist effect | Gawande (2009); Hales & Pronovost (2006) | Task lists prevent step-skipping |
| Implementation intentions | Gollwitzer (1999) | Plan-then-execute improves completion rates |
| Cognitive load theory | Sweller (1988) | Break complex tasks into manageable chunks |
| Nudge theory | Thaler & Sunstein (2008) | Small design changes improve decisions |
| Deliberate practice | Ericsson et al. (1993) | Feedback loops improve performance |
| Error detection | Reason (1990) | Verification cycles catch mistakes |
| Satisficing; information foraging; positive test strategy | Simon (1956); Pirolli & Card (1999); Klayman & Ha (1987) | Search output locates passages; reading them decides |
| Mixed-initiative interaction; interruption cost; memory for goals; alert fatigue | Horvitz (1999); Mark, Gudith, & Klocke (2008); Altmann & Trafton (2002); Ancker et al. (2017) | Ask only when the answer changes the next step; confirm irreversible actions once |

## License

MIT
