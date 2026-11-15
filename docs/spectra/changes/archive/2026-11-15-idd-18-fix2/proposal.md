## Why

Verify round 2 of issue #18 found that two tests enforce decisions the `marketplace-catalogue` spec does not state, that one marked test does not match its Example, and that several checks pass by keyword or by a narrow parser. The maintainer also decided that `livedocs` comes into this repository as a git submodule, which replaces the `git-subdir` form the spec described.

## What Changes

- `PsychQuant/livedocs` becomes a git submodule at plugins/livedocs; the `livedocs` entry's source is the relative path ./plugins/livedocs/plugins/livedocs.
- **BREAKING** for the spec: the requirement for `git-subdir` entries and the requirement to disclose an unpinned entry are removed. A submodule records one commit, so there is no unpinned entry.
- Every entry's source is a relative path string; the two-form requirement is replaced.
- New requirement for a plugin that comes from a submodule: https url in .gitmodules, and the README row says it is a git submodule.
- New closed-list requirement for decisions about named plugins: `livedocs` is listed, `claude-hot-limit` is not.
- The relative-path Example is corrected; install commands are defined precisely; table rows are checked one by one, duplicates and unparsable rows included; the `livedocs` row states where the executable comes from.
- README.md and CLAUDE.md are rewritten for the submodule form.

## Non-Goals (optional)

- Changes in `PsychQuant/livedocs` itself. Removing its old marketplace file is the second half of issue #18.
- A requirement for the inclusion criterion (issue #22), for the contents of .claude (issue #23), or for unlisted directories under plugins (issue #24).
- Editing the block that `spectra init` generated in CLAUDE.md, or the files under the archive directory.
- Checking that a README sentence is true. The checks look for required phrases; a person reads the sentence.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `marketplace-catalogue`: entries are relative paths only; plugins from another repository come in as submodules; decisions about named plugins are a closed list; README checks are per row and per install command.

## Impact

- Affected specs: `marketplace-catalogue` (4 modified, 3 removed, 3 added requirements).
- Affected code:
  - .gitmodules
  - .claude-plugin/marketplace.json
  - README.md
  - CLAUDE.md
  - tests/test_marketplace.py
