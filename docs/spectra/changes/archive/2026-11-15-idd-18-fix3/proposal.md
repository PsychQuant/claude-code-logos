## Why

Verify round 3 of issue #18 found the livedocs submodule pinned 36 commits after the `v0.9.0` tag, so the installed skill was ahead of the released executable. It also found two Examples whose tests use a different fixture, a failure message that does not help someone who cloned without submodules, and a rule about email addresses in archived metadata that nothing checks.

## What Changes

- The livedocs submodule is pinned to the `v0.9.0` tag.
- New requirement: the commit recorded for a submodule that holds a plugin is one that a tag of that repository points at.
- New requirement: archived change metadata holds no email address.
- The submodule requirement gains a scenario for a submodule that is not checked out; the message names the command to run.
- The uniqueness requirement is worded as "no two entries share a name", and its Example and the fourth row of the submodule Example describe the fixtures the tests use.
- README.md states that the recorded commit covers the plugin files and does not bind the executable.
- CLAUDE.md: the routine for moving the pointer checks out a release tag; it names the Spectra skill steps that act without a further question and what the spec does not cover.

## Non-Goals (optional)

- Hardening the checker against unusual git-config and Markdown forms (issue #26).
- A requirement for the inclusion criterion (issue #22), for test collection (conftest.py) or for .gitignore. These are named in CLAUDE.md as outside the spec.
- A minimum Claude Code version in the README. The marketplace reference says versions before v2.1.295 fetch every submodule, so the plugin is fetched there as well.
- Editing the first archived tasks.md.
- A design document.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `marketplace-catalogue`: a submodule plugin is pinned to a tagged commit; a submodule that is not checked out is reported with the command to run; uniqueness is stated per entry; archived change metadata holds no email address.

## Impact

- Affected specs: `marketplace-catalogue` (2 modified, 2 added requirements).
- Affected code:
  - plugins/livedocs
  - tests/test_marketplace.py
  - README.md
  - CLAUDE.md
  - .gitignore
  - docs/spectra/specs/.gitkeep
