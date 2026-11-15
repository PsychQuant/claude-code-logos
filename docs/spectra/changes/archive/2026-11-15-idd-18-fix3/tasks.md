## 1. Checks and tests

- [x] 1.1 Requirement "A submodule that holds a plugin is pinned to a tagged commit": a function returns a problem when given no tags for a submodule path, and the real-files test asks git for the tags at the checked-out commit of plugins/livedocs. Verified by a test marked `spec-example: marketplace-catalogue / tags at the checked-out commit`; the real-files test fails while the submodule is at the untagged commit and passes at v0.9.0.
- [x] 1.2 Requirement "Archived change metadata holds no email address": a function reports text containing @, and the real-files test reads every .openspec.yaml under docs/spectra. Verified by a test marked `spec-example: marketplace-catalogue / metadata text and its outcome`.
- [x] 1.3 Requirement "A plugin from another repository comes in as a git submodule": a source under a submodule path with no manifest is reported with the words git submodule update --init, and every marketplace test fails with that one message when the submodule is not checked out. Verified by tests marked `spec-example: marketplace-catalogue / a submodule that is not checked out` and `spec-example: marketplace-catalogue / submodule plugins and their outcomes`, and by running the suite on a copy without the submodule.
- [x] 1.4 Requirement "Plugin names are unique": wording and Example match the test fixture. Verified by the test marked `spec-example: marketplace-catalogue / two entries named model-effort`.

## 2. Files

- [x] 2.1 The livedocs submodule is at the v0.9.0 tag, so the installed look-up skill is the one released with the 0.9.0 executable. Verified by `git -C plugins/livedocs describe --tags --exact-match` printing v0.9.0 and by the real-files test. [after: 1.1]
- [x] 2.2 The README livedocs row says the recorded commit covers the plugin files and that the executable is fetched from GitHub Releases and is not fixed by that commit. Verified by the real-files test and by reading the row against the wrapper script. [after: 2.1]
- [x] 2.3 CLAUDE.md tells the maintainer to check out a release tag in the submodule, names the Spectra skill steps that act without a further question, and lists what the spec does not cover; .gitignore ignores .claude/settings.json; docs/spectra/specs/.gitkeep is removed. Verified by content review and `git status`. [after: 2.1]

## 3. Install test

- [x] 3.1 livedocs@claude-code-logos installs from the working tree in an isolated config directory at version 0.9.0 and the MCP server answers initialize and tools/list. Verified by running the install and the probe. [after: 2.1]
- [x] 3.2 The whole suite passes. Verified by `python3 -m pytest -q`. [after: 2.3]
