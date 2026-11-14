## 1. Catalogue check and its tests

- [x] 1.1 Requirement "Plugin names are unique": a catalogue check function in tests/test_marketplace.py returns a problem naming a duplicated plugin name. Verified by a test marked `spec-example: marketplace-catalogue / two entries named model-effort`, which fails before the function exists.
- [x] 1.2 Requirement "A plugin in this repository is listed by a relative path": the check reports a name mismatch, a missing manifest and a path outside the repository, and reports nothing for the current entries. Verified by a test marked `spec-example: marketplace-catalogue / relative sources and their outcomes`.
- [x] 1.3 Requirement "A plugin in another repository is listed by git-subdir": the check reports a url that is not https, a missing path and a version in the entry. Verified by a test marked `spec-example: marketplace-catalogue / git-subdir entries and their outcomes`, which fails on the current shorthand url.
- [x] 1.4 Requirement "Every entry uses one of the two source forms": the check reports an empty object, a github object and a number as unknown source forms. Verified by a test marked `spec-example: marketplace-catalogue / unknown source forms`.
- [x] 1.5 Requirement "An unpinned entry is disclosed in the README": the check reports a git-subdir entry without sha whose README row lacks the words default branch. Verified by a test marked `spec-example: marketplace-catalogue / livedocs without a sha`, which fails on the current README.
- [x] 1.6 Requirement "The README lists the same plugins as the marketplace": the check compares the Plugins table, the Install block and marketplace.json, and requires `<name>@claude-code-logos` in each install command. Verified by a test marked `spec-example: marketplace-catalogue / livedocs missing from the Install block`.
- [x] 1.7 Requirement "The README states what each plugin rests on and where it lives": the check reports an empty Rests on or Lives in cell. Verified by a test marked `spec-example: marketplace-catalogue / a row with no Rests on cell`.
- [x] 1.8 Requirement "The README states the platform limit and the executable download of livedocs": the check reports a livedocs row without macOS or without downloads. Verified by a test marked `spec-example: marketplace-catalogue / a livedocs row without macOS`, which fails on the current README.
- [x] 1.9 The test file reads its two inputs as UTF-8 and one test runs the whole check on the real files and expects no problem. Verified by `python3 -m pytest tests/test_marketplace.py`. [after: 1.8]

## 2. Marketplace entry and documents

- [x] 2.1 The livedocs entry's url is https://github.com/PsychQuant/livedocs.git, so the real-files test passes the git-subdir requirement. Verified by `python3 -m pytest tests/test_marketplace.py` and `claude plugin validate .`. [after: 1.9]
- [x] 2.2 The README livedocs row says the plugin is installed from the default branch of its repository and is not reviewed in this one, runs on macOS only, and downloads an executable; a sentence under the Install block tells someone with livedocs@livedocs-marketplace to remove that marketplace first. Verified by the real-files test and by reading the rendered table. [after: 1.9]
- [x] 2.3 The README model-effort Rests on cell says each recommendation is tagged with its source and the skill states the date its facts were checked. Verified by reading the cell against plugins/model-effort/skills/model-effort/SKILL.md. [after: 2.2]
- [x] 2.4 CLAUDE.md install commands carry @claude-code-logos, and the rule for a plugin from another repository names the https url, the unpinned form, the sha fallback, and that the unpinned form is for repositories with the same maintainers; it points to the marketplace-catalogue spec. Verified by content review of the 開發規範 section. [after: 2.1]

## 3. Install test and records

- [x] 3.1 livedocs@claude-code-logos installs from this branch with the https url in an isolated config directory: version 0.9.0 is shown and the MCP server answers initialize and tools/list. Verified by running the install and the probe and recording the output. [after: 2.1]
- [x] 3.2 The whole suite passes. Verified by `python3 -m pytest -q` showing no failure. [after: 2.4]
