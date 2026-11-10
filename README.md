# Claude Code Logos

**Science-backed plugins that make Claude Code work better.**

Logos (λόγος) — reason, principle, rational order.

Every plugin in this marketplace is grounded in published research from cognitive science, behavioral economics, or software engineering. We don't guess what makes AI agents better — we apply what's already been proven in human performance research.

## Install

```bash
claude plugin marketplace add PsychQuant/claude-code-logos
claude plugin install skill-best-practices@claude-code-logos
claude plugin install model-effort@claude-code-logos
```

Or, in a session on Claude Code 2.1.275 or later: `/plugin install skill-best-practices --marketplace PsychQuant/claude-code-logos`

## Principles

1. **Evidence first** — every mechanism cites published research
2. **Nudge, don't force** — guide behavior through design, not restriction
3. **Measurable impact** — each plugin should have a testable claim

## Plugins

| Plugin | What it does |
|--------|--------------|
| `skill-best-practices` | Eight evidence-based practices for writing Claude Code skills, as an on-demand skill, plus hooks that deliver the rules while Claude works: session-start rules (read search results before concluding; ask the user only when the answer changes the next step, while still confirming irreversible actions) and a reminder when search output is truncated |

| `model-effort` | An on-demand skill for choosing the Claude model and effort level: the session's `/model` and `/effort`, subagents, Workflow `agent()` calls, skill frontmatter, and Claude API scripts. Claude Code defaults and API defaults are kept apart, and settings that fail silently are named (a top-level `effortLevel` that newer models ignore, subagents that don't inherit the session's level) |

**`model-effort` rests on vendor evidence, not published research.** Its sources are the Claude Code and Claude API documentation and Anthropic's own benchmarks, each recommendation is tagged with its source, and the skill states the date its facts were checked. Model names, defaults and prices change between releases, so treat a stale date as a reason to re-check.

**`skill-best-practices` changes when the agent asks you.** For work you asked for, in a repository you can write to, it no longer asks first before four routine GitHub records: creating an issue or comment, editing your own issue body or comment, setting a label or milestone or assigning you, and the IDD baseline tag. If the content is private or mentions someone, it still asks. A stricter policy of your own wins, and Claude Code's permission prompts still apply.

## Research Foundations

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
