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

## Practice 7: Search Locates, Reading Decides

> A search can show where a passage is. Only reading the passage shows what it says.

**Research**: Simon (1956) described *satisficing*: a decision-maker with limited capacity stops at the first option that meets an aspiration level instead of examining every option. Pirolli & Card (1999) *Information Foraging* modelled information search as foraging, where the searcher decides when to leave a patch of information and move on; leaving early is cheap at the moment and costly when the answer was further in. Klayman & Ha (1987) showed that people test a hypothesis by looking where they expect it to hold (the *positive test strategy*), which can miss the evidence that would disconfirm it.

**Application to skills**: An agent told to "check the document against the source" will usually search the source with a keyword pattern. All three failure modes then line up. It takes the first matching line that fits what it expected (satisficing), it stops at whatever the terminal shows (an early patch exit, made worse when the output is cut by `| head`), and it searches only for wording that would confirm its expectation (positive testing). One observed case: an agent twice declared a source did not support a statement. Both times the search was piped to `head`, and the deciding line matched but fell past the cut. In one of the two, the first match came from a passage restating someone else's position, while the passage where the source stated its own conclusion, never read, said the opposite.

**How to apply**:

Any skill step that verifies something against a source names the reading action, not just a search:

**Before (search only)**:
```markdown
3. Check each claim in the draft against the source document.
```

**After (search locates, reading decides)**:
```markdown
3. For each claim in the draft:
   a. Search the source to locate candidate passages. Search output is for locating only;
      never pipe it to head/tail and then conclude from what is visible.
   b. If the claim says the source *decided*, *concluded* or *confirmed* something, Read in
      full the section where the source states its own conclusion. A passage restating
      someone else's position is not that conclusion.
   c. Before writing "the source does not say X", search again with other wordings and
      Read the surrounding section.
   d. Quote the passage (file and line) that the verdict rests on.
```

**Runtime delivery**: this plugin also delivers Practice 7 while Claude works, not only when this skill is invoked. A `SessionStart` hook injects the short rule, and a `PreToolUse` hook on `Bash` adds a one-line reminder next to the result whenever a search is piped to `head`/`tail` or capped with `-m`. Neither hook blocks the command.

**Sources**:
- Klayman, J., & Ha, Y.-W. (1987). Confirmation, disconfirmation, and information in hypothesis testing. *Psychological Review, 94*(2), 211–228. https://doi.org/10.1037/0033-295X.94.2.211
- Pirolli, P., & Card, S. (1999). Information foraging. *Psychological Review, 106*(4), 643–675. https://doi.org/10.1037/0033-295X.106.4.643
- Simon, H. A. (1956). Rational choice and the structure of the environment. *Psychological Review, 63*(2), 129–138. https://doi.org/10.1037/h0042769

---

## Practice 8: Ask Only When the Answer Changes the Next Step

> Every question stops the user. Ask when the answer would change what happens next and there is no reasonable default.

**Research**: Horvitz (1999) lists *employing dialog to resolve key uncertainties* among the principles of mixed-initiative interfaces: a system that is uncertain about the user's intentions should be able to ask, "considering the costs of potentially bothering a user needlessly." His expected-utility analysis gives a system three options: do nothing, ask, or act. Asking before an action the user wants is worth less than simply taking it, so asking is the best option only in a middle band of uncertainty. Below the band the system does nothing; above it, it acts. The thresholds move with context: the less an unwanted action is worth to the user, the higher the threshold for acting. The cost of each question is real. Mark, Gudith & Klocke (2008) found that people compensated for interruptions by working faster, at the price of more stress, higher frustration, time pressure and effort. In Altmann & Trafton's (2002) goal-activation model, a suspended goal has to be retrieved against interference from older goals, with the help of cues, and the authors discuss what this implies for the effects of task interruption. Ancker et al. (2017) found that clinicians accepted fewer decision-support alerts as they received more of them, particularly repeated alerts: the likelihood of accepting a reminder fell by 30% for each additional reminder per encounter.

**Application to skills**: A question costs the agent one line and costs the user a stop. Two things push agents to ask too much. Skills say "confirm with the user" without saying which steps need it, and rules written for irreversible actions get applied to cheap, reversible ones. One observed case: an agent treated creating an issue in the user's own repository as an irreversible action and showed a four-item confirmation block. Later the user answered "push" to a block that listed several pending pushes; the agent pushed one repository and asked again, with a full block, about the others. Its status reports listed every option, including ones the user had nothing to decide about. In Horvitz's terms each of these questions was worth less than acting on the default. Ancker et al.'s finding suggests the cost compounds: the more often a confirmation appears, the less each one is attended to, including the ones that matter.

This is not "ask less". The same analysis keeps irreversible actions in the confirmation branch: when acting wrongly is costly, the threshold for acting without asking rises. Pushing code, sending a message, publishing, paying and deleting without a backup are still confirmed. The practice moves questions from where the answer does not matter to where it does.

**How to apply**:

A skill step that asks the user states what the answer changes, and the default to use when there is one. Irreversible steps are grouped so that one confirmation covers them.

**Before (asks at every step)**:
```markdown
4. Ask the user to confirm before each action: creating the issue, adding the label,
   pushing the branch, opening the pull request.
5. Report every check that passed and every option for what to do next.
```

**After (asks where the answer matters)**:
```markdown
4. Create the issue and add the label in the user's repository, then report them in one
   line. These are routine records; do not ask.
5. Pushing the branch and opening the pull request publish code. Ask once for both: list
   what will be pushed, to which remote, and the pull request title, then wait. One
   approval covers the batch; do not ask again about an item in it.
6. When a decision has a default (a convention, this skill's default, an earlier answer
   in the conversation), use it and say so in one line instead of asking.
7. Report what was done, where, and what is left for the user to decide. Leave out
   options the user has nothing to decide about.
```

Before a skill asks the user anything, check:
- Would any answer change what the agent does next? If not, do not ask.
- Is there a reasonable default? Use it and state it.
- Is the action irreversible, or does it send private content somewhere? Then ask, once, covering every action of that kind.
- Are there other questions for the user in this step? Ask them in the same message, not over several turns.
- Has the user already answered this? Do not ask again.

**Runtime delivery**: the `SessionStart` hook injects the short Practice 8 rule next to the Practice 7 rule. No hook watches questions. `PreToolUse` context is added alongside the tool result, so a reminder on `AskUserQuestion` would arrive after the user had already been asked, and most of these questions are plain text in a reply, which no tool hook sees.

**Sources**:
- Altmann, E. M., & Trafton, J. G. (2002). Memory for goals: An activation-based model. *Cognitive Science, 26*(1), 39–83. https://doi.org/10.1207/s15516709cog2601_2
- Ancker, J. S., Edwards, A., Nosal, S., Hauser, D., Mauer, E., & Kaushal, R. (2017). Effects of workload, work complexity, and repeated alerts on alert fatigue in a clinical decision support system. *BMC Medical Informatics and Decision Making, 17*, Article 36. https://doi.org/10.1186/s12911-017-0430-8
- Horvitz, E. (1999). Principles of mixed-initiative user interfaces. In *Proceedings of the SIGCHI Conference on Human Factors in Computing Systems* (pp. 159–166). ACM. https://doi.org/10.1145/302979.303030
- Mark, G., Gudith, D., & Klocke, U. (2008). The cost of interrupted work: More speed and stress. In *Proceedings of the SIGCHI Conference on Human Factors in Computing Systems* (pp. 107–110). ACM. https://doi.org/10.1145/1357054.1357072

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
7. Does every verification step name what to Read, not just what to search? (Practice 7)
8. Does every question the skill asks change what happens next, with irreversible steps confirmed once as a batch? (Practice 8)
