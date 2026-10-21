# Skill Writing Best Practices

Delivered by the plugin's `PreToolUse` hook on `Write|Edit` when the target is a `SKILL.md` (once per session). Plugins have no `rules/` component, so this file is never loaded on its own; `scripts/skill_writing_reminder.py` reads it and adds it as context.

When writing or modifying skills (SKILL.md files), apply these evidence-based principles:

1. **Checklist visibility**: Skills with 3+ steps MUST provide a **fixed task table** for Claude to create with TaskCreate. Skill 給清單，不是讓 Claude 自己決定建什麼。表格中標注每步的類型（機械/創意/驗證）和跳過條件。注意：TaskCreate 是 Claude Code 內部工具，不能從 `!`command`` shell injection 呼叫，但可以用 shell injection 掃描素材讓 Claude 判斷哪些 task 要建。

   **Concrete template — Step 0 Bootstrap**（已在 idd-* / plugin-tools / mcp-tools 60+ skill 驗證）：

   ````markdown
   ## Step 0: Bootstrap Stage Task List（強制）

   **動任何事之前**先用 `TaskCreate` 建 stage-level todo list：

   ```
   TaskCreate(name="phase_1_name", description="做什麼，包含子步驟")
   TaskCreate(name="phase_2_name", description="做什麼")
   TaskCreate(name="phase_n_name", description="做什麼")
   ```

   完成每一步立即 `TaskUpdate → completed`。**靜默完成 = 違規**。

   **為什麼強制**：[此 skill 特定的 silent failure 風險，例如「有 X 個 phase，漏了 Y 會導致 Z」]
   ````

   放在 YAML frontmatter 後、第一個執行步驟前。未提供 "為什麼" 段落的 skill 會被降級——使用者不知道為什麼要遵守就會跳過。
2. **Separate mechanical from creative**: Don't mix rule-based steps (file operations, builds) with judgment-heavy steps (content creation, analysis) in the same phase. Label creative steps with ⚠️ and explicit importance markers.
3. **Concrete examples over abstract rules**: Include at least one before/after example for any non-obvious instruction. Use tables instead of prose for task lists — tables are less likely to be rewritten by Claude.
4. **Search locates, reading decides** (Practice 7): any step that checks something against a source must name the reading action — which file and which section to `Read` — not only a search. Truncated search output (`| head`, `| tail`, `grep -m N`) is never evidence that a source lacks something. When the claim is that a source *decided* or *confirmed* something, the step reads that source's conclusions section in full. Before concluding absence, try other wordings and read the surrounding section.
