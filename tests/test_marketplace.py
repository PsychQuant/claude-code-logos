"""Checks for the marketplace catalogue (spec: marketplace-catalogue, #18).

`catalogue_problems` takes the parsed marketplace file, the README text and the
repository root, and returns a list of problem strings. The tests feed it the
real files (no problem expected) and small synthetic inputs (one named problem
expected), so each requirement of the spec has a test that can fail.
"""
import copy
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_NAME = "claude-code-logos"


def load_marketplace():
    return json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))


def load_readme():
    return (ROOT / "README.md").read_text(encoding="utf-8")


def section(readme, heading):
    """Text under a `## heading` line, up to the next `## ` line. '' if absent."""
    match = re.search(rf"^## {re.escape(heading)}[ \t]*$", readme, flags=re.M)
    if not match:
        return ""
    rest = readme[match.end():]
    end = re.search(r"^## ", rest, flags=re.M)
    return rest[: end.start()] if end else rest


def plugin_rows(readme):
    """Plugins table as {name: {column header: cell}}, plus the list of names in order."""
    lines = [l for l in section(readme, "Plugins").splitlines() if l.startswith("|")]
    if len(lines) < 2:
        return {}, []
    headers = [c.strip() for c in lines[0].strip("|").split("|")]
    rows, names = {}, []
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        name = re.fullmatch(r"`([^`]+)`", cells[0])
        if not name:
            continue
        names.append(name.group(1))
        rows[name.group(1)] = dict(zip(headers, cells + [""] * (len(headers) - len(cells))))
    return rows, names


def install_ids(readme):
    """`<name>@<marketplace>` (or a bare name) from each install command in the Install block."""
    return re.findall(r"^claude plugin install (\S+)[ \t]*$", section(readme, "Install"), flags=re.M)


def source_problems(entry, root):
    name, source = entry.get("name"), entry.get("source")
    if isinstance(source, str):
        if not source.startswith("./"):
            return [f"{name}: relative source does not start with ./"]
        target = (root / source).resolve()
        if not target.is_relative_to(root.resolve()):
            return [f"{name}: source is outside the repository"]
        manifest = target / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            return [f"{name}: no manifest at {source}"]
        manifest_name = json.loads(manifest.read_text(encoding="utf-8")).get("name")
        if manifest_name != name:
            return [f"{name}: name mismatch, the manifest says {manifest_name}"]
        return []
    if isinstance(source, dict) and source.get("source") == "git-subdir":
        problems = []
        if not str(source.get("url", "")).startswith("https://"):
            problems.append(f"{name}: url is not https")
        if not source.get("path"):
            problems.append(f"{name}: no path")
        if "version" in entry:
            problems.append(f"{name}: version in entry")
        return problems
    return [f"{name}: unknown source form"]


def catalogue_problems(marketplace, readme, root=ROOT):
    problems = []
    entries = marketplace.get("plugins", [])
    names = [e.get("name") for e in entries]
    for name, count in Counter(names).items():
        if count > 1:
            problems.append(f"{name}: listed {count} times")
    for entry in entries:
        problems += source_problems(entry, root)

    rows, table_names = plugin_rows(readme)
    ids = install_ids(readme)
    installed = [i.split("@", 1)[0] for i in ids]
    for i in ids:
        if not i.endswith(f"@{MARKETPLACE_NAME}"):
            problems.append(f"{i}: install command does not name @{MARKETPLACE_NAME}")
    places = {"marketplace.json": names, "the Plugins table": table_names, "the Install block": installed}
    everything = set(names) | set(table_names) | set(installed)
    for place, listed in places.items():
        for name in sorted(everything - set(listed), key=str):
            problems.append(f"{name}: missing from {place}")

    for name, row in rows.items():
        for column in ("Rests on", "Lives in"):
            if not row.get(column):
                problems.append(f"{name}: empty {column} cell")

    for entry in entries:
        source = entry.get("source")
        if isinstance(source, dict) and source.get("source") == "git-subdir" and not source.get("sha"):
            row_text = " ".join(rows.get(entry.get("name"), {}).values())
            if "default branch" not in row_text:
                problems.append(f"{entry.get('name')}: README row does not say the entry follows the default branch")

    if "livedocs" in rows:
        row_text = " ".join(rows["livedocs"].values())
        if "macOS" not in row_text:
            problems.append("livedocs: README row does not state the macOS limit")
        if "downloads" not in row_text:
            problems.append("livedocs: README row does not state that it downloads an executable")
    return problems


# --- helpers for synthetic inputs -------------------------------------------

LIVEDOCS_ROW_OK = (
    "| `livedocs` | An MCP server and a look-up skill. macOS only; the plugin downloads an executable "
    "| The primary source | PsychQuant/livedocs, installed from its default branch |"
)


def readme_with(rows, installs):
    table = "\n".join(["| Plugin | What it does | Rests on | Lives in |", "|---|---|---|---|", *rows])
    commands = "\n".join(f"claude plugin install {i}" for i in installs)
    return f"# T\n\n## Install\n\n```bash\n{commands}\n```\n\n## Plugins\n\n{table}\n\n## License\n"


def livedocs_entry(**overrides):
    entry = {
        "name": "livedocs",
        "source": {
            "source": "git-subdir",
            "url": "https://github.com/PsychQuant/livedocs.git",
            "path": "plugins/livedocs",
        },
    }
    entry.update(overrides)
    return entry


def only_livedocs(entry, row=LIVEDOCS_ROW_OK):
    return catalogue_problems({"plugins": [entry]}, readme_with([row], ["livedocs@claude-code-logos"]))


# --- the real files ---------------------------------------------------------


def test_real_files_have_no_problem():
    assert catalogue_problems(load_marketplace(), load_readme()) == []


def test_claude_hot_limit_is_not_listed():
    # Decided on #18: claude-hot-limit keeps its own marketplace.
    assert "claude-hot-limit" not in [p["name"] for p in load_marketplace()["plugins"]]


def test_livedocs_entry_is_not_pinned():
    # Decided on #18: the entry follows the default branch of PsychQuant/livedocs.
    # The README says so (spec: an unpinned entry is disclosed). If a livedocs
    # commit ever breaks installs, the fallback is to add `sha` here and change
    # this test in the same commit.
    source = next(p for p in load_marketplace()["plugins"] if p["name"] == "livedocs")["source"]
    assert "sha" not in source and "ref" not in source


# --- one test per spec Example ----------------------------------------------


def test_two_entries_named_model_effort():
    # spec-example: marketplace-catalogue / two entries named model-effort
    marketplace = copy.deepcopy(load_marketplace())
    marketplace["plugins"].append(copy.deepcopy(marketplace["plugins"][1]))
    problems = catalogue_problems(marketplace, load_readme())
    assert problems == ["model-effort: listed 2 times"]


def test_relative_sources_and_their_outcomes():
    # spec-example: marketplace-catalogue / relative sources and their outcomes
    cases = {
        "./plugins/model-effort": [],
        "./plugins/skill-best-practices": ["model-effort: name mismatch, the manifest says skill-best-practices"],
        "./plugins/missing": ["model-effort: no manifest at ./plugins/missing"],
        "../elsewhere": ["model-effort: relative source does not start with ./"],
        "./../elsewhere": ["model-effort: source is outside the repository"],
    }
    for source, expected in cases.items():
        assert source_problems({"name": "model-effort", "source": source}, ROOT) == expected, source


def test_git_subdir_entries_and_their_outcomes():
    # spec-example: marketplace-catalogue / git-subdir entries and their outcomes
    assert only_livedocs(livedocs_entry()) == []
    shorthand = livedocs_entry()
    shorthand["source"]["url"] = "PsychQuant/livedocs"
    assert only_livedocs(shorthand) == ["livedocs: url is not https"]
    no_path = livedocs_entry()
    del no_path["source"]["path"]
    assert only_livedocs(no_path) == ["livedocs: no path"]
    assert only_livedocs(livedocs_entry(version="0.9.0")) == ["livedocs: version in entry"]


def test_unknown_source_forms():
    # spec-example: marketplace-catalogue / unknown source forms
    for source in ({}, {"source": "github", "repo": "PsychQuant/livedocs"}, 42):
        assert source_problems({"name": "x", "source": source}, ROOT) == ["x: unknown source form"], source


def test_livedocs_without_a_sha():
    # spec-example: marketplace-catalogue / livedocs without a sha
    row = "| `livedocs` | An MCP server. macOS only; downloads an executable | The primary source | PsychQuant/livedocs |"
    assert only_livedocs(livedocs_entry(), row) == [
        "livedocs: README row does not say the entry follows the default branch"
    ]
    pinned = livedocs_entry()
    pinned["source"]["sha"] = "f4c0c3c"
    assert only_livedocs(pinned, row) == []


def test_livedocs_missing_from_the_install_block():
    # spec-example: marketplace-catalogue / livedocs missing from the Install block
    marketplace = load_marketplace()
    readme = load_readme().replace("claude plugin install livedocs@claude-code-logos\n", "")
    assert catalogue_problems(marketplace, readme) == ["livedocs: missing from the Install block"]
    bare = load_readme().replace("install livedocs@claude-code-logos", "install livedocs")
    assert catalogue_problems(marketplace, bare) == ["livedocs: install command does not name @claude-code-logos"]


def test_a_row_with_no_rests_on_cell():
    # spec-example: marketplace-catalogue / a row with no Rests on cell
    row = "| `livedocs` | An MCP server. macOS only; downloads an executable |  | PsychQuant/livedocs, default branch |"
    assert only_livedocs(livedocs_entry(), row) == ["livedocs: empty Rests on cell"]


def test_a_livedocs_row_without_macos():
    # spec-example: marketplace-catalogue / a livedocs row without macOS
    row = "| `livedocs` | An MCP server and a look-up skill | The primary source | PsychQuant/livedocs, default branch |"
    assert only_livedocs(livedocs_entry(), row) == [
        "livedocs: README row does not state the macOS limit",
        "livedocs: README row does not state that it downloads an executable",
    ]
