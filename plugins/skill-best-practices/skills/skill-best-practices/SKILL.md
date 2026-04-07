---
name: skill-best-practices
description: |
  Evidence-based practices for writing better Claude Code skills.
  Use when creating new skills, reviewing existing skills, or when a skill
  isn't performing as expected. Also triggers when user says "improve skill",
  "skill not working", "why did it skip steps", "audit skill".
argument-hint: "[skill-path or topic]"
---

# Skill Best Practices

Each practice below is grounded in published research. When auditing or writing a skill, check each practice and apply where relevant.

---

## Practice 1: Checklist Visibility

> Steps not on a checklist get skipped.

**Research**: Gawande (2009) *The Checklist Manifesto* — surgical checklists reduced mortality by 47%. Hales & Pronovost (2006) showed ICU catheter infection rates dropped from 11% to 0% with a 5-item checklist. The mechanism: **making steps visible prevents omission errors**, especially for routine tasks where attention drifts.

**Application to skills**: Claude Code's `TaskCreate` tool makes steps visible in the UI. When a skill has 3+ steps, steps without a corresponding task are significantly more likely to be skipped — especially creative/judgment-heavy steps sandwiched between mechanical ones.

**How to apply**:

Skill 裡直接提供**固定的 task 清單表格**，Claude 只需要照抄建立，不需要自己決定要建什麼。

**技術限制**（來自 Claude Code 源碼驗證）：
- `TaskCreate` 是 Claude Code 的內部工具（`buildTool` 註冊），**不是 shell 命令**
- Skill 的 `!`command`` shell injection **無法呼叫 TaskCreate**，只能跑 shell 命令
- 因此 task 清單只能透過**自然語言指示** Claude 建立，不能自動執行
- 但 shell injection 可以**掃描素材**（`ls`、`find`），讓 Claude 看到具體檔案再決定哪些 task 要建、哪些要跳過

**最佳做法**：shell injection 掃描 + 固定 task 表格

```markdown
## 素材掃描（自動執行）
```!
echo "SRT:"; find lectures/ -name "*.srt" 2>/dev/null || echo "  (無)"
echo "MD:"; find lectures/ -name "*.md" 2>/dev/null || echo "  (無)"
```

## 建立 Checklist
根據掃描結果，用 TaskCreate 工具建立以下 task（一次全部建完）。
沒有素材的步驟直接標 completed（附註「無素材」）。

| # | subject（直接複製） | 類型 | 跳過條件 |
|---|-------------------|------|---------|
| 1 | SRT 基礎校正 | 機械 | 沒有 .srt |
| 2 | ⚠️ 讀逐字稿，充實講義內容 | **創意** | **不可跳過** |
| 3 | 講義結構自檢 | 驗證 | 不可跳過 |
| 4 | HTML build | 機械 | 沒有 .srt |
```

**Before (bad)** — 讓 Claude 自己決定建什麼：
```markdown
## Steps
1. Read the SRT file
2. Correct misheard words
3. Read transcript and enrich lecture content ← SKIPPED
4. Build HTML
5. Update index
```

**After (good)** — skill 直接給出表格，Claude 照建：
```markdown
| # | subject（直接複製到 TaskCreate） | 類型 |
|---|--------------------------------|------|
| 1 | SRT 基礎校正（Speaker + 誤聽詞庫） | 機械 |
| 2 | **⚠️ 讀逐字稿全文，充實講義內容** | **創意** |
| 3 | 講義結構自檢 | 驗證 |
| 4 | HTML build + 影片連結 | 機械 |
```

**三個關鍵原則**：
1. **Skill 給清單，不是 Claude 自己建** — 減少 Claude 的判斷空間，降低遺漏
2. **用表格格式** — subject 欄直接複製，比自然語言段落更不容易被改寫
3. **標注類型（機械/創意/驗證）** — 讓 Claude 知道哪些步驟需要放慢

---

## Practice 2: Separate Mechanical from Creative

> Don't mix assembly-line work with judgment work in the same phase.

**Research**: Sweller (1988) *Cognitive Load Theory* — working memory has limited capacity. Switching between rule-following (mechanical) and open-ended judgment (creative) tasks imposes **extraneous cognitive load**. Monsell (2003) showed task-switching costs increase with task complexity.

**Application to skills**: When a skill mixes `sed` replacements, `make` commands, and "read the full transcript to find missing content" in one linear flow, the mechanical steps create momentum that carries past the creative step. The agent wants to keep "making progress" (completing tasks) rather than slowing down for judgment.

**How to apply**:

Group steps by type, with creative steps explicitly called out:

```markdown
## Phase 1: Mechanical Setup
- [ ] SRT speaker labels
- [ ] Misheard word replacements
- [ ] File organization

## Phase 2: Content Creation (requires judgment)
- [ ] Read full transcript
- [ ] Identify teaching points not in notes
- [ ] Restructure and enrich lecture content
- [ ] Self-check: does the lecture pass the structure template?

## Phase 3: Mechanical Build
- [ ] HTML conversion + CSS
- [ ] Index update
- [ ] Video links
```

---

## Practice 3: Implementation Intentions

> "I will do X when Y happens" doubles the completion rate.

**Research**: Gollwitzer (1999) *Implementation Intentions* — meta-analysis showed that specifying **when, where, and how** to perform an action doubles completion rates (d = 0.65). The mechanism: pre-deciding removes the need for in-the-moment deliberation.

**Application to skills**: Vague instructions like "enrich the content" leave room for the agent to decide "this looks good enough." Specific implementation intentions remove that escape hatch.

**How to apply**:

Replace vague instructions with specific if-then rules:

**Before (vague)**:
```markdown
Read the transcript and improve the lecture notes.
```

**After (implementation intention)**:
```markdown
Read the transcript in 200-line chunks. For each chunk:
1. If a teaching point is explained in the transcript but missing from the lecture → add it
2. If a bullet point is oral/conversational → rewrite as concise written prose
3. If a concept has no example → add one from the transcript discussion
4. If a section has no h2 parent → create one

After all chunks: run the structure self-check (Practice 5).
```

---

## Practice 4: Concrete Examples Over Abstract Rules

> People follow examples more accurately than rules.

**Research**: LeFevre & Dixon (1986) showed that when instructions and examples conflict, people follow the **example** 80% of the time. Chi et al. (1989) *Self-Explanation Effect* — worked examples improve problem-solving transfer significantly more than abstract principles alone.

**Application to skills**: A skill that says "use h2 for major sections" is less effective than one that shows a complete before/after example of a well-structured lecture.

**How to apply**:

For every non-obvious instruction, include a concrete example:

```markdown
### Lecture Structure Rules

Every h3 must be under an h2. Here's what this means:

**Bad** (orphan h3):
```html
<h3>OpenClaw</h3>
<p>可能會偷偷做很多事情</p>
<h3>顯著性</h3>
```

**Good** (h3 under h2):
```html
<h2>AI 工具比較</h2>
<h3>OpenClaw</h3>
<p>可能會偷偷做很多事情</p>
<h2>統計概念</h2>
<h3>顯著性</h3>
```
```

---

## Practice 5: Self-Check Before Completion

> Verification at the end catches errors that execution momentum misses.

**Research**: Reason (1990) *Human Error* — most errors are **slips** (correct intention, wrong action) not **mistakes** (wrong intention). Slips are caught by post-completion checks. The aviation industry's mandatory checklist before landing (GUMPS check) exists because pilots who "feel done" skip critical steps.

**Application to skills**: Claude often marks a task complete and moves on without verifying. A structured self-check at the end of a skill forces a re-scan.

**How to apply**:

Add a verification checklist as the final step of any skill:

```markdown
## Verification (must pass ALL before marking complete)

Run through this checklist. If any item fails, fix it before proceeding.

- [ ] No orphan h3 (every h3 has an h2 parent)
- [ ] Has "重點整理" section
- [ ] Has "課後作業" section
- [ ] No `/Users/` absolute paths in content
- [ ] All links resolve (href targets exist)
```

**Key**: The checklist must be **checkable** (yes/no), not subjective ("content is good enough").

---

## Practice 6: Salient Labeling for Critical Steps

> What you name a step determines whether it gets attention.

**Research**: Tversky & Kahneman (1981) *Framing Effects* — identical choices framed differently produce different decisions. Mayer (2009) *Signaling Principle* in multimedia learning — adding organizational cues (headings, emphasis) improves learning and retention by directing attention.

**Application to skills**: A step named "Process content" gets less attention than one named "**Read full transcript and enrich lecture (most important step — takes 30+ min)**". The label signals importance.

**How to apply**:

For the most critical step in a skill, use explicit importance markers:

```markdown
## Step 3: Read Transcript and Enrich Lecture Content

⚠️ **This is the most important step.** It takes the longest and requires the most judgment.
Do not rush through this. The output quality depends entirely on this step.

...specific instructions...
```

---

## How to Use This Skill

### Audit an existing skill
```
/skill-best-practices path/to/SKILL.md
```
Reads the skill and checks each practice. Reports which practices are applied and which are missing.

### When writing a new skill
Invoke this skill before writing. Use the practices as a checklist for the skill you're about to create.

### When a skill isn't performing
If Claude keeps skipping steps or producing shallow output, check:
1. Is there a TaskCreate instruction? (Practice 1)
2. Are mechanical and creative steps separated? (Practice 2)
3. Are instructions specific enough? (Practice 3)
4. Are there concrete examples? (Practice 4)
5. Is there a self-check? (Practice 5)
6. Is the critical step labeled as important? (Practice 6)
