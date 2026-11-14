## Why

The marketplace now lists a plugin whose files live in another repository, and the README states an inclusion criterion and what each plugin's claims rest on. None of this is written down as a requirement, so the first verify of issue #18 could not check it and found gaps: an entry form that fails for users without a GitHub SSH key, no statement that the entry follows another repository's default branch, and no statement that the plugin runs only on macOS and downloads an executable.

## What Changes

- New capability `marketplace-catalogue` stating how a plugin is listed in `.claude-plugin/marketplace.json` and what `README.md` says about each listed plugin.
- The `livedocs` entry's `url` becomes a full `https://` URL.
- `README.md` gains, for `livedocs`: that the entry is not pinned and follows the default branch of its repository, that it runs on macOS only, that its wrapper downloads an executable, and what someone with the old `livedocs@livedocs-marketplace` install does first.
- `README.md`: the `model-effort` "Rests on" cell states one checked date for the skill, not one per recommendation.
- `CLAUDE.md`: install commands carry `@claude-code-logos`; the rule for plugins from another repository names the `https://` URL, the unpinned form and its `sha` fallback.
- `tests/test_marketplace.py` checks every requirement of the capability.

## Non-Goals (optional)

- Pinning the `livedocs` entry to a commit. The maintainer decided not to pin; the requirement is to say so.
- Changes in `PsychQuant/livedocs` (install instructions, removing its old marketplace file). That is the second half of issue #18.
- Listing `claude-hot-limit`. It keeps its own marketplace.
- Deciding issue #17 (how `archive-first` is brought in).
- A design document. The change is small and follows the plan approved on issue #18.

## Capabilities

### New Capabilities

- `marketplace-catalogue`: which plugins the marketplace lists, the entry form for a plugin in this repository and for a plugin in another repository, and what the README states about each listed plugin.

### Modified Capabilities

(none)

## Impact

- Affected specs: new `marketplace-catalogue`.
- Affected code:
  - .claude-plugin/marketplace.json
  - README.md
  - CLAUDE.md
  - tests/test_marketplace.py
