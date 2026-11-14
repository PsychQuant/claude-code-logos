## Purpose

The marketplace catalogue is the list of plugins in `.claude-plugin/marketplace.json` together with what `README.md` tells a reader about each of them. It exists so that a plugin is listed in one known form, and so that a reader can see where each plugin lives, what its claims rest on, and what installing it brings in.

## ADDED Requirements

### Requirement: Plugin names are unique

Each plugin SHALL appear in `.claude-plugin/marketplace.json` exactly once. Two entries MUST NOT share a `name`.

#### Scenario: A name is listed twice

- **WHEN** two entries in the `plugins` array have the same `name`
- **THEN** the catalogue check reports the duplicated name

##### Example: two entries named model-effort

- **GIVEN** a `plugins` array with entries named `skill-best-practices`, `model-effort`, `model-effort`
- **WHEN** the catalogue check runs
- **THEN** it reports one problem that names `model-effort`

### Requirement: A plugin in this repository is listed by a relative path

An entry for a plugin whose files are in this repository SHALL have a string `source` that starts with `./`, resolves to a directory inside the repository, and holds `.claude-plugin/plugin.json`. The `name` in that manifest SHALL equal the entry's `name`.

#### Scenario: The entry name differs from the manifest name

- **WHEN** an entry's relative `source` holds a manifest whose `name` is not the entry's `name`
- **THEN** the catalogue check reports the entry

##### Example: relative sources and their outcomes

| Entry name | source | Manifest name at source | Expected | Notes |
| ---------- | ------ | ----------------------- | -------- | ----- |
| model-effort | ./plugins/model-effort | model-effort | no problem | the current entry |
| model-effort | ./plugins/skill-best-practices | skill-best-practices | problem: name mismatch | wrong directory |
| model-effort | ./plugins/missing | (no manifest) | problem: no manifest | directory absent |
| model-effort | ../elsewhere | (outside the repository) | problem: outside the repository | path escapes the root |

### Requirement: A plugin in another repository is listed by git-subdir

An entry for a plugin whose files are in another repository SHALL have an object `source` with `source` equal to `git-subdir`, a `url` that starts with `https://`, and a `path`. The entry MUST NOT carry a `version`; the plugin's own manifest carries it.

#### Scenario: The url is an owner/repo shorthand

- **WHEN** a `git-subdir` entry's `url` does not start with `https://`
- **THEN** the catalogue check reports the entry

##### Example: git-subdir entries and their outcomes

| url | path | version in entry | Expected | Notes |
| --- | ---- | ---------------- | -------- | ----- |
| https://github.com/PsychQuant/livedocs.git | plugins/livedocs | absent | no problem | the livedocs entry |
| PsychQuant/livedocs | plugins/livedocs | absent | problem: url is not https | shorthand needs an SSH key for some users |
| https://github.com/PsychQuant/livedocs.git | (absent) | absent | problem: no path | |
| https://github.com/PsychQuant/livedocs.git | plugins/livedocs | 0.9.0 | problem: version in entry | goes stale without a warning |

### Requirement: Every entry uses one of the two source forms

An entry's `source` SHALL be either a relative path string or a `git-subdir` object. Any other value MUST be reported.

#### Scenario: The source is neither form

- **WHEN** an entry's `source` is an object whose `source` field is not `git-subdir`, or is not a string or object
- **THEN** the catalogue check reports the entry

##### Example: unknown source forms

| source | Expected |
| ------ | -------- |
| {} | problem: unknown source form |
| {"source": "github", "repo": "PsychQuant/livedocs"} | problem: unknown source form |
| 42 | problem: unknown source form |

### Requirement: An unpinned entry is disclosed in the README

For every `git-subdir` entry without a `sha`, the README row of that plugin SHALL state that the plugin is installed from the default branch of its repository.

#### Scenario: The README row is silent about the default branch

- **WHEN** a `git-subdir` entry has no `sha` and the README row of that plugin does not contain the words `default branch`
- **THEN** the catalogue check reports the plugin

##### Example: livedocs without a sha

- **GIVEN** the `livedocs` entry has no `sha`, and a README whose `livedocs` row says only "PsychQuant/livedocs"
- **WHEN** the catalogue check runs
- **THEN** it reports that the `livedocs` row does not say the entry follows the default branch

### Requirement: The README lists the same plugins as the marketplace

The plugin names in the README Plugins table, the plugin names in the README Install block, and the plugin names in `.claude-plugin/marketplace.json` SHALL be the same set. Each install command in the Install block SHALL name the plugin as `<name>@claude-code-logos`.

#### Scenario: A plugin is missing from one of the three places

- **WHEN** a name is in one of the three lists and not in another
- **THEN** the catalogue check reports the name and the list it is missing from

##### Example: livedocs missing from the Install block

- **GIVEN** `marketplace.json` and the Plugins table both list `skill-best-practices`, `model-effort`, `livedocs`, and the Install block has install commands for the first two only
- **WHEN** the catalogue check runs
- **THEN** it reports that `livedocs` is missing from the Install block

### Requirement: The README states what each plugin rests on and where it lives

Each row of the README Plugins table SHALL have a non-empty "Rests on" cell and a non-empty "Lives in" cell.

#### Scenario: A cell is empty

- **WHEN** a Plugins table row has an empty "Rests on" or "Lives in" cell
- **THEN** the catalogue check reports the plugin and the empty column

##### Example: a row with no Rests on cell

- **GIVEN** a Plugins table row for `livedocs` whose "Rests on" cell is empty
- **WHEN** the catalogue check runs
- **THEN** it reports `livedocs` and the column `Rests on`

### Requirement: The README states the platform limit and the executable download of livedocs

The README row of `livedocs` SHALL state that the plugin runs on macOS only and that it downloads an executable.

#### Scenario: The livedocs row omits the platform or the download

- **WHEN** the `livedocs` row does not contain `macOS`, or does not contain `downloads`
- **THEN** the catalogue check reports what is missing

##### Example: a livedocs row without macOS

- **GIVEN** a `livedocs` row that says "An MCP server and a look-up skill" and nothing about the platform
- **WHEN** the catalogue check runs
- **THEN** it reports that the `livedocs` row does not state the macOS limit
