# Skill Writing Best Practices (Auto-loaded Rule)

When writing or modifying skills (SKILL.md files), apply these evidence-based principles:

1. **Checklist visibility**: Skills with 3+ steps MUST instruct Claude to create a TaskCreate checklist before starting. Steps not on a checklist get skipped.
2. **Separate mechanical from creative**: Don't mix rule-based steps (file operations, builds) with judgment-heavy steps (content creation, analysis) in the same phase without a checkpoint between them.
3. **Concrete examples over abstract rules**: Include at least one before/after example for any non-obvious instruction.
