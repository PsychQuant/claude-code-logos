# marketplace-catalogue Specification

## Purpose

The marketplace catalogue is the list of plugins in `.claude-plugin/marketplace.json` together with what `README.md` tells a reader about each of them. It exists so that a plugin is listed in one known form, and so that a reader can see where each plugin lives, what its claims rest on, and what installing it brings in.

## Requirements

### Requirement: Plugin names are unique

Each plugin SHALL appear in `.claude-plugin/marketplace.json` exactly once. Two entries MUST NOT share a `name`.

#### Scenario: A name is listed twice

- **WHEN** two entries in the `plugins` array have the same `name`
- **THEN** the catalogue check reports the duplicated name

##### Example: two entries named model-effort

- **GIVEN** a `plugins` array with entries named `skill-best-practices`, `model-effort`, `model-effort`
- **WHEN** the catalogue check runs
- **THEN** it reports one problem that names `model-effort`


<!-- @trace
source: idd-18-livedocs-marketplace
updated: 2026-11-15
code:
  - .claude-plugin/marketplace.json
  - tests/test_marketplace.py
-->

---
### Requirement: A plugin in this repository is listed by a relative path

Every entry SHALL have a string `source` that starts with `./`, resolves to a directory inside the repository, and holds `.claude-plugin/plugin.json`. That manifest SHALL be a JSON object whose `name` equals the entry's `name`. A source that does not start with `./` is reported as such before any other check; a source that starts with `./` and resolves outside the repository is reported as outside the repository.

#### Scenario: The entry name differs from the manifest name

- **WHEN** an entry's relative `source` holds a manifest whose `name` is not the entry's `name`
- **THEN** the catalogue check reports the entry

#### Scenario: The manifest cannot be read as a JSON object

- **WHEN** the file at `.claude-plugin/plugin.json` is not valid JSON, or is valid JSON that is not an object
- **THEN** the catalogue check reports the entry and does not raise

##### Example: relative sources and their outcomes

| Entry name | source | Manifest at source | Expected | Notes |
| ---------- | ------ | ------------------ | -------- | ----- |
| model-effort | ./plugins/model-effort | name model-effort | no problem | the current entry |
| model-effort | ./plugins/skill-best-practices | name skill-best-practices | problem: name mismatch | wrong directory |
| model-effort | ./plugins/missing | (no file) | problem: no manifest | directory absent |
| model-effort | ../elsewhere | (not looked at) | problem: does not start with ./ | reported first |
| model-effort | ./../elsewhere | (not looked at) | problem: outside the repository | path escapes the root |
| broken | ./broken | the text `not json` | problem: manifest is not a JSON object | temporary directory |
| broken | ./broken | the JSON value `[]` | problem: manifest is not a JSON object | temporary directory |


<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - .claude-plugin/marketplace.json
  - tests/test_marketplace.py
-->

---
### Requirement: The README lists the same plugins as the marketplace

The plugin names in the README Plugins table, the plugin names in the install commands of the README Install section, and the plugin names in `.claude-plugin/marketplace.json` SHALL be the same set. An install command is a line of the fenced code block in the Install section that begins with `claude plugin install`. The rest of such a line SHALL be exactly `<name>@claude-code-logos`, where `<name>` contains no `@`. Text of the Install section outside the fenced code block is not an install command.

#### Scenario: A plugin is missing from one of the three places

- **WHEN** a name is in one of the three lists and not in another
- **THEN** the catalogue check reports the name and the list it is missing from

#### Scenario: An install command is not in the required form

- **WHEN** the rest of an install command line is not exactly `<name>@claude-code-logos`
- **THEN** the catalogue check reports that line

##### Example: names missing from one of the three lists

| Change to the real files | Expected |
| ------------------------ | -------- |
| the `livedocs` install command is removed | problem: livedocs missing from the Install block |
| the `livedocs` table row is removed | problem: livedocs missing from the Plugins table |
| the `livedocs` entry is removed from marketplace.json | problem: livedocs missing from marketplace.json |

##### Example: install command forms

| Install command line | Expected |
| -------------------- | -------- |
| claude plugin install livedocs@claude-code-logos | no problem |
| claude plugin install livedocs | problem: not in the form name@claude-code-logos |
| claude plugin install livedocs@other@claude-code-logos | problem: not in the form name@claude-code-logos |
| claude plugin install livedocs@claude-code-logos --scope user | problem: not in the form name@claude-code-logos |
| claude plugin install livedocs@another-marketplace | problem: not in the form name@claude-code-logos |


<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - .claude-plugin/marketplace.json
  - README.md
  - tests/test_marketplace.py
-->

---
### Requirement: The README states what each plugin rests on and where it lives

Every data row of the README Plugins table SHALL have a first cell that is a plugin name in backticks, a non-empty "Rests on" cell and a non-empty "Lives in" cell. A plugin name SHALL appear in one row only. The check reads every row; a later row does not replace an earlier one.

#### Scenario: A cell is empty

- **WHEN** a Plugins table row has an empty "Rests on" or "Lives in" cell
- **THEN** the catalogue check reports the plugin and the empty column

#### Scenario: A row cannot be read or is repeated

- **WHEN** a data row's first cell is not a name in backticks, or two rows have the same name
- **THEN** the catalogue check reports the row

##### Example: table rows and their outcomes

| Row | Expected |
| --- | -------- |
| livedocs row with an empty Rests on cell | problem: livedocs, empty Rests on cell |
| livedocs row with an empty Lives in cell | problem: livedocs, empty Lives in cell |
| two livedocs rows, the first with both cells empty, the second complete | problems: livedocs listed in 2 rows; empty Rests on cell; empty Lives in cell |
| a row whose first cell is `surprise` without backticks | problem: a row whose first cell is not a plugin name in backticks |


<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - README.md
  - tests/test_marketplace.py
-->

---
### Requirement: The README states the platform limit and the executable download of livedocs

The README row of `livedocs` SHALL contain the phrases `macOS only`, `downloads an executable` and `GitHub Releases`. The check is on the presence of the three phrases. That the sentence around them is true is read by a person before merge; the check does not decide it.

#### Scenario: The livedocs row omits one of the phrases

- **WHEN** the `livedocs` row lacks `macOS only`, `downloads an executable` or `GitHub Releases`
- **THEN** the catalogue check reports each missing phrase

##### Example: livedocs rows and the phrases they lack

| Row text | Expected |
| -------- | -------- |
| An MCP server and a look-up skill | three problems: macOS only; downloads an executable; GitHub Releases |
| macOS only; downloads an executable | one problem: GitHub Releases |
| Runs on macOS; downloads documentation from GitHub Releases | two problems: macOS only; downloads an executable |


<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - README.md
  - tests/test_marketplace.py
-->

---
### Requirement: Every entry's source is a relative path string

An entry's `source` SHALL be a string. An object, a number or a missing `source` MUST be reported.

#### Scenario: The source is not a string

- **WHEN** an entry's `source` is an object, a number, or absent
- **THEN** the catalogue check reports the entry as having a source that is not a relative path string

##### Example: sources that are not strings

| source | Expected |
| ------ | -------- |
| {} | problem: source is not a relative path string |
| {"source": "git-subdir", "url": "https://github.com/PsychQuant/livedocs.git", "path": "plugins/livedocs"} | problem: source is not a relative path string |
| 42 | problem: source is not a relative path string |
| (absent) | problem: source is not a relative path string |


<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - .claude-plugin/marketplace.json
  - tests/test_marketplace.py
-->

---
### Requirement: A plugin from another repository comes in as a git submodule

When an entry's `source` resolves to a directory at or under a path listed in `.gitmodules`, the `url` of that submodule SHALL start with `https://`, and the README row of that plugin SHALL contain the phrase `git submodule`.

#### Scenario: The submodule url is not https

- **WHEN** the submodule that holds an entry's source has a `url` that does not start with `https://`
- **THEN** the catalogue check reports the entry

#### Scenario: The README row does not say the plugin is a submodule

- **WHEN** an entry's source is inside a submodule and the README row of that plugin lacks the phrase `git submodule`
- **THEN** the catalogue check reports the plugin

##### Example: submodule plugins and their outcomes

| .gitmodules entry for plugins/livedocs | README row contains git submodule | Expected |
| -------------------------------------- | --------------------------------- | -------- |
| url = https://github.com/PsychQuant/livedocs.git | yes | no problem |
| url = git@github.com:PsychQuant/livedocs.git | yes | problem: submodule url is not https |
| url = https://github.com/PsychQuant/livedocs.git | no | problem: README row does not say git submodule |
| (no entry; the source is an ordinary directory) | no | no problem |


<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - .gitmodules
  - .claude-plugin/marketplace.json
  - README.md
  - tests/test_marketplace.py
-->

---
### Requirement: Decisions about named plugins

The marketplace SHALL list `livedocs` with the source `./plugins/livedocs/plugins/livedocs`. The marketplace SHALL NOT list `claude-hot-limit`, which keeps its own marketplace. This is a closed list of two decisions taken on issue #18; a decision about another plugin is added here by a change to this requirement, not inferred from these two.

#### Scenario: A named decision is not followed

- **WHEN** `livedocs` is absent or has another source, or `claude-hot-limit` is listed
- **THEN** the catalogue check reports the plugin

##### Example: named plugins and their outcomes

| plugins array | Expected |
| ------------- | -------- |
| the real array | no problem |
| the real array without livedocs | problem: livedocs is not listed |
| the real array with livedocs at ./plugins/model-effort | problem: livedocs has another source |
| the real array plus an entry named claude-hot-limit | problem: claude-hot-limit is listed |

<!-- @trace
source: idd-18-fix2
updated: 2026-11-15
code:
  - .claude-plugin/marketplace.json
  - tests/test_marketplace.py
-->