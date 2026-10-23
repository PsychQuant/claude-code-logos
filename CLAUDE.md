# Claude Code Logos

Science-backed plugins that make Claude Code work better.

## 專案結構

```
claude-code-logos/
├── plugins/                    ← 公開 plugin（在 marketplace.json 裡）
│   └── skill-best-practices/   ← 全部 8 個 practice，日常使用（skill ＋ hooks）
├── lab/                        ← 實驗用 plugin（不在 marketplace.json 裡）
│   ├── checklist-visibility/   ← 介入 1：TaskCreate 清單
│   ├── interruption-cost/      ← 介入 8：只在答案會改變下一步時提問（SessionStart hook）
│   ├── separate-phases/        ← 介入 2：機械/創意分離（待建）
│   └── ...                     ← 其他介入（待建）
└── docs/                       ← 研究筆記、實驗設計、數據
```

## 公開 vs 實驗

| 目錄 | 在 marketplace.json | 安裝方式 | 用途 |
|------|---------------------|---------|------|
| `plugins/` | 是 | `claude plugin install skill-best-practices` | 一般使用者，全部 practice 一起裝 |
| `lab/` | 否 | `claude --plugin-dir ./lab/checklist-visibility` | 實驗用，只載入單一介入 |

## 實驗設計

每個 `lab/` 下的 plugin 是**一個獨立的介入（intervention）**。

> ⚠️ **plugin 的 `rules/` 不會被載入**（2026-10-21 查證，見 #1）。plugin 能提供的元件類型裡沒有 `rules/`，plugin 根目錄的 `CLAUDE.md` 也不會被載入（[plugins reference](https://code.claude.com/docs/en/plugins-reference.md)，"Standard layout"）。所以只含 `rules/` 的 lab plugin，用 `--plugin-dir` 載入後，模型收到的內容與 baseline 相同。**在此之前用 rule-only 的 lab plugin 跑出的 treatment 結果，量到的不是介入效果，不能當處理組數據。** 介入要經會載入的元件送達：`SessionStart`／`PreToolUse` hook 的 `additionalContext`，或 skill。`skill-best-practices` 0.2.0 的 `hooks/` 是可參考的寫法。

實驗流程：
1. **Baseline**：不裝任何 lab plugin，正常使用 Claude Code 完成任務
2. **Treatment**：用 `--plugin-dir` 載入單一介入，完成同類型任務
3. **測量**：比較 baseline vs treatment 的任務完成率、步驟跳過率、輸出品質

同時裝 `skill-best-practices`（公開版）和 `lab/` plugin 會造成 rule 重複，實驗時只用 `lab/` 版本。

## 目前的介入

| # | Plugin | Practice | 研究來源 | 狀態 |
|---|--------|----------|---------|------|
| 1 | `checklist-visibility` | TaskCreate 清單防止跳步 | Gawande (2009); Hales & Pronovost (2006) | ⚠ 只有 `rules/`，載入後送不到模型；改成 hook 前不能當處理組（#5） |
| 2 | `separate-phases` | 機械/創意步驟分離 | Sweller (1988); Monsell (2003) | 待建 |
| 3 | `implementation-intentions` | 具體的 if-then 指示 | Gollwitzer (1999) | 待建 |
| 4 | `concrete-examples` | 用範例代替抽象規則 | LeFevre & Dixon (1986); Chi et al. (1989) | 待建 |
| 5 | `self-check` | 完成前驗證清單 | Reason (1990) | 待建 |
| 6 | `salient-labeling` | 關鍵步驟的醒目標記 | Tversky & Kahneman (1981); Mayer (2009) | 待建 |
| 8 | `interruption-cost` | 只在答案會改變下一步時提問，不可逆的動作一次確認 | Horvitz (1999); Mark et al. (2008); Altmann & Trafton (2002); Ancker et al. (2017) | ✅ 可測試（SessionStart hook；量測與流程見該目錄 README） |

## 公開 plugin 的具體 template

`skill-best-practices` 是八個 practice 的合集，其中 **Practice #1 Checklist visibility** 不只給抽象原則，也提供具體的 **Step 0 Bootstrap Stage Task List template**：

- 格式：YAML frontmatter 後、第一個執行步驟前，放一段 `TaskCreate(name=..., description=...)` × N，每個 phase 一個 task
- 寫法：必須含「**為什麼強制**」段落說明此 skill 特定的 silent failure 風險
- 實證：已在 `issue-driven-dev` (11 skills)、`plugin-tools` v1.12.0 (6 skills)、`mcp-tools` v1.14.0 (13 skills) 共 60+ skill 驗證

這是 rule #3「concrete examples over abstract rules」的自我應用——抽象的 checklist 原則本身也要有具體 template，否則 skill 作者各寫各的 checklist 格式，擴散效果被稀釋。

更新記錄：
- `skill-writing.md` 加入 Step 0 template（[commit `e75eae7`](https://github.com/PsychQuant/claude-code-logos/commit/e75eae7)）

## 開發規範

- 每個 lab plugin 只做**一件事**（一個介入），這樣才能隔離變項
- 介入必須經會載入的元件送達（hook 或 skill）；只放 `rules/` 等於沒有介入（見上方〈實驗設計〉的警語）
- 介入的文字裡必須包含 `## Why` section 說明研究根據
- hook 腳本要有測試：以合成的 hook JSON 餵 stdin，檢查 stdout
- 公開的 `skill-best-practices` 是全部 practice 的合集，更新時要同步
