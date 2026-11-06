# skill-best-practices

Evidence-based practices for writing better Claude Code skills.

## Components

| Type | Name | Purpose |
|------|------|---------|
| Skill | `/skill-best-practices` | Audit a skill or learn best practices |
| Hook (`SessionStart`) | `scripts/session_start.py` | Injects the Practice 7 and Practice 8 runtime rules at every session start, resume, clear and compaction |
| Hook (`PreToolUse`, `Bash`) | `scripts/search_truncation_reminder.py` | Adds a one-line reminder next to the result when a search is piped to `head`/`tail` or capped with `-m` |
| Hook (`PreToolUse`, `Write\|Edit`) | `scripts/skill_writing_reminder.py` | Adds `rules/skill-writing.md` as context the first time a `SKILL.md` is written or edited in a session |

`rules/skill-writing.md` is data read by the last hook. Plugins have no `rules/` component and a plugin-root `CLAUDE.md` is not loaded ([plugins reference](https://code.claude.com/docs/en/plugins-reference.md), "Standard layout"), so before 0.2.0 that rule never reached the model. None of the hooks returns a `permissionDecision`; they add context and never block a tool call.

## When This Plugin Activates

- **Hooks** (every session): the Practice 7 and 8 rules at session start, the truncated-search reminder on `Bash`, and the skill-writing rule when a `SKILL.md` is edited
- **Skill** (on demand or auto): invoked when creating, reviewing, or debugging skills

## Tests

```bash
python3 -m unittest discover -s plugins/skill-best-practices/tests
```

The tests feed synthetic hook payloads on stdin and check the scripts' stdout.

## Research Sources

| # | Practice | Primary Source |
|---|----------|---------------|
| 1 | Checklist visibility | Gawande (2009); Hales & Pronovost (2006) |
| 2 | Separate mechanical/creative | Sweller (1988); Monsell (2003) |
| 3 | Implementation intentions | Gollwitzer (1999) |
| 4 | Concrete examples | LeFevre & Dixon (1986); Chi et al. (1989) |
| 5 | Self-check before completion | Reason (1990) |
| 6 | Salient labeling | Tversky & Kahneman (1981); Mayer (2009) |
| 7 | Search locates, reading decides | Simon (1956); Pirolli & Card (1999); Klayman & Ha (1987) |
| 8 | Ask only when the answer changes the next step | Horvitz (1999); Mark, Gudith, & Klocke (2008); Altmann & Trafton (2002); Ancker et al. (2017) |
