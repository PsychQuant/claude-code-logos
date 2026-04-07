# Skill Writing Best Practices (Auto-loaded Rule)

When writing or modifying skills (SKILL.md files), apply these evidence-based principles:

1. **Checklist visibility**: Skills with 3+ steps MUST provide a **fixed task table** for Claude to create with TaskCreate. Skill 給清單，不是讓 Claude 自己決定建什麼。表格中標注每步的類型（機械/創意/驗證）和跳過條件。注意：TaskCreate 是 Claude Code 內部工具，不能從 `!`command`` shell injection 呼叫，但可以用 shell injection 掃描素材讓 Claude 判斷哪些 task 要建。
2. **Separate mechanical from creative**: Don't mix rule-based steps (file operations, builds) with judgment-heavy steps (content creation, analysis) in the same phase. Label creative steps with ⚠️ and explicit importance markers.
3. **Concrete examples over abstract rules**: Include at least one before/after example for any non-obvious instruction. Use tables instead of prose for task lists — tables are less likely to be rewritten by Claude.
