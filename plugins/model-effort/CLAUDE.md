# model-effort — CLAUDE.md

A skill-only plugin: `skills/model-effort/SKILL.md` helps choose the Claude model and effort level for six situations (main session, Agent tool subagents, Workflow `agent()`, skill and subagent frontmatter, Claude API scripts, tools with their own model settings). Tracking issue: #11.

## Maintenance

- The facts are dated. The skill states the day and the Claude Code version they were checked against. When a new model ships, or when defaults, aliases or prices change, re-check every source listed at the end of the skill, update the facts and the date together, and bump the version.
- Keep the evidence tags (`[docs]`, `[blog]`, `[measured]`, `[judgment]`) on every recommendation. Where two sources disagree, list both; do not merge them.
- Keep machine-specific values out: no user's settings values, account names, local paths, or private plugin internals. This repository is public.
- The situations are a closed list. Add a situation only with its own entry, not by widening an existing one.
