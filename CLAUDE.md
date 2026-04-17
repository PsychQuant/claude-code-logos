# Claude Code Logos

Science-backed plugins that make Claude Code work better.

## 專案結構

```
claude-code-logos/
├── plugins/                    ← 公開 plugin（在 marketplace.json 裡）
│   └── skill-best-practices/   ← 全部 6 個 practice，日常使用
├── lab/                        ← 實驗用 plugin（不在 marketplace.json 裡）
│   ├── checklist-visibility/   ← 介入 1：TaskCreate 清單
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

每個 `lab/` 下的 plugin 是**一個獨立的介入（intervention）**，只包含一個 rule。

實驗流程：
1. **Baseline**：不裝任何 lab plugin，正常使用 Claude Code 完成任務
2. **Treatment**：用 `--plugin-dir` 載入單一介入，完成同類型任務
3. **測量**：比較 baseline vs treatment 的任務完成率、步驟跳過率、輸出品質

同時裝 `skill-best-practices`（公開版）和 `lab/` plugin 會造成 rule 重複，實驗時只用 `lab/` 版本。

## 目前的介入

| # | Plugin | Practice | 研究來源 | 狀態 |
|---|--------|----------|---------|------|
| 1 | `checklist-visibility` | TaskCreate 清單防止跳步 | Gawande (2009); Hales & Pronovost (2006) | ✅ 可測試 |
| 2 | `separate-phases` | 機械/創意步驟分離 | Sweller (1988); Monsell (2003) | 待建 |
| 3 | `implementation-intentions` | 具體的 if-then 指示 | Gollwitzer (1999) | 待建 |
| 4 | `concrete-examples` | 用範例代替抽象規則 | LeFevre & Dixon (1986); Chi et al. (1989) | 待建 |
| 5 | `self-check` | 完成前驗證清單 | Reason (1990) | 待建 |
| 6 | `salient-labeling` | 關鍵步驟的醒目標記 | Tversky & Kahneman (1981); Mayer (2009) | 待建 |

## 公開 plugin 的具體 template

`skill-best-practices` 是六個 practice 的合集，其中 **Practice #1 Checklist visibility** 不只給抽象原則，也提供具體的 **Step 0 Bootstrap Stage Task List template**：

- 格式：YAML frontmatter 後、第一個執行步驟前，放一段 `TaskCreate(name=..., description=...)` × N，每個 phase 一個 task
- 寫法：必須含「**為什麼強制**」段落說明此 skill 特定的 silent failure 風險
- 實證：已在 `issue-driven-dev` (11 skills)、`plugin-tools` v1.12.0 (6 skills)、`mcp-tools` v1.14.0 (13 skills) 共 60+ skill 驗證

這是 rule #3「concrete examples over abstract rules」的自我應用——抽象的 checklist 原則本身也要有具體 template，否則 skill 作者各寫各的 checklist 格式，擴散效果被稀釋。

更新記錄：
- `skill-writing.md` 加入 Step 0 template（[commit `e75eae7`](https://github.com/PsychQuant/claude-code-logos/commit/e75eae7)）

## 開發規範

- 每個 lab plugin 只做**一件事**（一個 rule），這樣才能隔離變項
- rule 檔案裡必須包含 `## Why` section 說明研究根據
- 公開的 `skill-best-practices` 是全部 practice 的合集，更新時要同步
