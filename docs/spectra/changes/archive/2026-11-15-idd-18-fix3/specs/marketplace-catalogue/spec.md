## MODIFIED Requirements

### Requirement: Plugin names are unique

No two entries in the `plugins` array of `.claude-plugin/marketplace.json` SHALL have the same `name`. This requirement is about the entries that are listed; it does not say which plugins are listed.

#### Scenario: A name is listed twice

- **WHEN** two entries in the `plugins` array have the same `name`
- **THEN** the catalogue check reports the duplicated name

##### Example: two entries named model-effort

- **GIVEN** the real `plugins` array with a second copy of the `model-effort` entry appended
- **WHEN** the catalogue check runs
- **THEN** it reports exactly one problem, which names `model-effort`

### Requirement: A plugin from another repository comes in as a git submodule

When an entry's `source` is, as written, a path at or under a path listed in `.gitmodules`, the `url` of that submodule SHALL start with `https://`, and the README row of that plugin SHALL contain the phrase `git submodule`. When such a source has no manifest because the submodule is not checked out, the problem reported for it SHALL name the command `git submodule update --init`.

#### Scenario: The submodule url is not https

- **WHEN** the submodule that holds an entry's source has a `url` that does not start with `https://`
- **THEN** the catalogue check reports the entry

#### Scenario: The README row does not say the plugin is a submodule

- **WHEN** an entry's source is inside a submodule and the README row of that plugin lacks the phrase `git submodule`
- **THEN** the catalogue check reports the plugin

#### Scenario: The submodule is not checked out

- **WHEN** an entry's source is inside a submodule path and the directory holds no manifest
- **THEN** the reported problem contains `git submodule update --init`

##### Example: submodule plugins and their outcomes

| .gitmodules text given to the check | README row contains git submodule | Expected |
| ----------------------------------- | --------------------------------- | -------- |
| url = https://github.com/PsychQuant/livedocs.git | yes | no problem |
| url = git@github.com:PsychQuant/livedocs.git | yes | problem: submodule url is not https |
| url = https://github.com/PsychQuant/livedocs.git | no | problem: README row does not say git submodule |
| empty text, so the source is under no submodule path | no | no problem |

##### Example: a submodule that is not checked out

- **GIVEN** a temporary root with an empty directory `plugins/livedocs`, a `.gitmodules` text that lists `plugins/livedocs`, and an entry `livedocs` with source `./plugins/livedocs/plugins/livedocs`
- **WHEN** the source check runs
- **THEN** it reports one problem that contains `no manifest` and `git submodule update --init`

## ADDED Requirements

### Requirement: A submodule that holds a plugin is pinned to a tagged commit

The commit this repository records for a submodule that holds a listed plugin SHALL be a commit that at least one tag of the submodule's repository points at.

#### Scenario: The recorded commit has no tag

- **WHEN** no tag of the submodule's repository points at the checked-out commit
- **THEN** the catalogue check reports the submodule path and says it is not at a tagged commit

##### Example: tags at the checked-out commit

| Tags pointing at the commit | Expected |
| --------------------------- | -------- |
| v0.9.0 | no problem |
| v0.9.0 and another tag | no problem |
| (none) | problem: plugins/livedocs is not at a tagged commit |

### Requirement: Archived change metadata holds no email address

No `.openspec.yaml` file under `docs/spectra/` SHALL contain the character `@`.

#### Scenario: A metadata file names a person with an address

- **WHEN** an `.openspec.yaml` under `docs/spectra/` contains `@`
- **THEN** the catalogue check reports that file

##### Example: metadata text and its outcome

| Line in .openspec.yaml | Expected |
| ---------------------- | -------- |
| created_by: A Person | no problem |
| created_by: A Person <person@example.invalid> | problem: the file holds an email address |
