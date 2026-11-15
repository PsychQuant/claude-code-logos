"""Checks for the marketplace catalogue (spec: marketplace-catalogue, #18).

`catalogue_problems` takes the parsed marketplace file, the README text, the
repository root and the text of `.gitmodules`, and returns a list of problem
strings. The tests feed it the real files (no problem expected) and small
synthetic inputs (named problems expected), so each requirement of the spec has
a test that can fail.

The real-files tests need the submodules (`plugins/livedocs`, `plugins/archive-first`) checked out:
`git submodule update --init`.
"""
from __future__ import annotations

import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_NAME = "claude-code-logos"
LIVEDOCS_SOURCE = "./plugins/livedocs/plugins/livedocs"
LIVEDOCS_PHRASES = ("macOS only", "downloads an executable", "GitHub Releases")
UNREADABLE_ROW = "a row whose first cell is not a plugin name in backticks"


def load_marketplace() -> dict[str, Any]:
    return json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))


def load_readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def load_gitmodules() -> str:
    path = ROOT / ".gitmodules"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def section(readme: str, heading: str) -> str:
    """Text under a `## heading` line, up to the next `## ` line. '' if absent."""
    match = re.search(rf"^## {re.escape(heading)}[ \t]*$", readme, flags=re.M)
    if not match:
        return ""
    rest = readme[match.end():]
    end = re.search(r"^## ", rest, flags=re.M)
    return rest[: end.start()] if end else rest


def table_rows(readme: str) -> list[dict[str, str]]:
    """Every data row of the Plugins table, in order, as {column header: cell}.

    The first cell is kept as written under the key 'Plugin', so the caller can
    tell a name in backticks from anything else. Nothing is dropped or merged.
    """
    lines = [line for line in section(readme, "Plugins").splitlines() if line.startswith("|")]
    if len(lines) < 2:
        return []
    headers = [cell.strip() for cell in lines[0].strip().strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        cells += [""] * (len(headers) - len(cells))
        rows.append(dict(zip(headers, cells)))
    return rows


def row_name(row: dict[str, str]) -> str | None:
    match = re.fullmatch(r"`([^`]+)`", row.get("Plugin", ""))
    return match.group(1) if match else None


def install_lines(readme: str) -> list[str]:
    """What follows `claude plugin install` on each such line of the fenced block in Install."""
    fence = re.search(r"^```[^\n]*\n(.*?)^```", section(readme, "Install"), flags=re.M | re.S)
    if not fence:
        return []
    found = []
    for line in fence.group(1).splitlines():
        if line.startswith("claude plugin install"):
            found.append(line[len("claude plugin install"):].strip())
    return found


def install_name(rest: str) -> str | None:
    """The plugin name if `rest` is exactly `<name>@claude-code-logos`, else None."""
    match = re.fullmatch(rf"([^@\s]+)@{re.escape(MARKETPLACE_NAME)}", rest)
    return match.group(1) if match else None


def submodules(gitmodules: str) -> dict[str, str]:
    """{path: url} for each submodule in the text of .gitmodules."""
    found: dict[str, str] = {}
    for block in re.split(r"^\[submodule [^\]]*\]\s*$", gitmodules, flags=re.M)[1:]:
        path = re.search(r"^\s*path\s*=\s*(\S+)\s*$", block, flags=re.M)
        url = re.search(r"^\s*url\s*=\s*(\S+)\s*$", block, flags=re.M)
        if path:
            found[path.group(1)] = url.group(1) if url else ""
    return found


def source_problems(entry: dict[str, Any], root: Path) -> list[str]:
    name, source = entry.get("name"), entry.get("source")
    if not isinstance(source, str):
        return [f"{name}: source is not a relative path string"]
    if not source.startswith("./"):
        return [f"{name}: relative source does not start with ./"]
    target = (root / source).resolve()
    if not target.is_relative_to(root.resolve()):
        return [f"{name}: source is outside the repository"]
    manifest = target / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return [f"{name}: no manifest at {source}"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    if not isinstance(data, dict):
        return [f"{name}: manifest is not a JSON object"]
    if data.get("name") != name:
        return [f"{name}: name mismatch, the manifest says {data.get('name')}"]
    return []


def submodule_of(source: str, modules: dict[str, str]) -> str | None:
    """The submodule path that is the source directory or a directory above it."""
    relative = source[2:].rstrip("/") if source.startswith("./") else source
    for path in modules:
        if relative == path or relative.startswith(path + "/"):
            return path
    return None


def catalogue_problems(
    marketplace: dict[str, Any], readme: str, root: Path = ROOT, gitmodules: str = ""
) -> list[str]:
    problems: list[str] = []
    entries = marketplace.get("plugins") or []
    names = [entry.get("name") for entry in entries]
    for name, count in Counter(names).items():
        if count > 1:
            problems.append(f"{name}: listed {count} times")
    for entry in entries:
        problems += source_problems(entry, root)

    # Decisions about named plugins (closed list, issue #18).
    livedocs = [entry for entry in entries if entry.get("name") == "livedocs"]
    if not livedocs:
        problems.append("livedocs: is not listed")
    elif livedocs[0].get("source") != LIVEDOCS_SOURCE:
        problems.append("livedocs: has another source")
    if "claude-hot-limit" in names:
        problems.append("claude-hot-limit: is listed")

    rows = table_rows(readme)
    table_names = []
    for row in rows:
        name = row_name(row)
        if name is None:
            problems.append(UNREADABLE_ROW)
            continue
        table_names.append(name)
        for column in ("Rests on", "Lives in"):
            if not row.get(column):
                problems.append(f"{name}: empty {column} cell")
    for name, count in Counter(table_names).items():
        if count > 1:
            problems.append(f"{name}: listed in {count} rows")

    installed = []
    for rest in install_lines(readme):
        name = install_name(rest)
        if name is None:
            problems.append(f"install command '{rest}': not in the form name@{MARKETPLACE_NAME}")
        else:
            installed.append(name)

    places = {"marketplace.json": names, "the Plugins table": table_names, "the Install block": installed}
    everything = {name for listed in places.values() for name in listed if isinstance(name, str)}
    for place, listed in places.items():
        for name in sorted(everything - set(listed)):
            problems.append(f"{name}: missing from {place}")

    def row_text(plugin: str) -> str:
        return " ".join(" ".join(row.values()) for row in rows if row_name(row) == plugin)

    modules = submodules(gitmodules)
    for entry in entries:
        source = entry.get("source")
        if not isinstance(source, str):
            continue
        module = submodule_of(source, modules)
        if module is None:
            continue
        if not modules[module].startswith("https://"):
            problems.append(f"{entry.get('name')}: submodule url is not https")
        # A plugin with no row is already reported as missing from the table.
        if entry.get("name") in table_names and "git submodule" not in row_text(entry.get("name")):
            problems.append(f"{entry.get('name')}: README row does not say git submodule")

    if "livedocs" in table_names:
        text = row_text("livedocs")
        for phrase in LIVEDOCS_PHRASES:
            if phrase not in text:
                problems.append(f"livedocs: README row lacks '{phrase}'")
    return problems


# --- helpers for synthetic inputs -------------------------------------------

GITMODULES_OK = '[submodule "plugins/livedocs"]\n\tpath = plugins/livedocs\n\turl = https://github.com/PsychQuant/livedocs.git\n'
ROW_OK = (
    "| `livedocs` | An MCP server and a look-up skill. macOS only; the plugin downloads an executable "
    "from GitHub Releases | The primary source | PsychQuant/livedocs, a git submodule |"
)


def readme_with(rows: list[str], installs: list[str]) -> str:
    table = "\n".join(["| Plugin | What it does | Rests on | Lives in |", "|---|---|---|---|", *rows])
    commands = "\n".join(f"claude plugin install {rest}" for rest in installs)
    return f"# T\n\n## Install\n\n```bash\n{commands}\n```\n\n## Plugins\n\n{table}\n\n## License\n"


def livedocs_only(row: str = ROW_OK, gitmodules: str = GITMODULES_OK, install: str = "livedocs@claude-code-logos") -> list[str]:
    marketplace = {"plugins": [{"name": "livedocs", "source": LIVEDOCS_SOURCE}]}
    return catalogue_problems(marketplace, readme_with([row], [install]), ROOT, gitmodules)


def real() -> tuple[dict[str, Any], str, str]:
    return copy.deepcopy(load_marketplace()), load_readme(), load_gitmodules()


def entry_named(marketplace: dict[str, Any], name: str) -> dict[str, Any]:
    return next(entry for entry in marketplace["plugins"] if entry["name"] == name)


# --- the real files ---------------------------------------------------------


def test_real_files_have_no_problem() -> None:
    marketplace, readme, gitmodules = real()
    assert catalogue_problems(marketplace, readme, ROOT, gitmodules) == []


def test_empty_catalogue_is_a_problem() -> None:
    # An empty marketplace and an empty README agree with each other; the named
    # decisions are what make that a problem.
    assert catalogue_problems({"plugins": []}, readme_with([], [])) == ["livedocs: is not listed"]


# --- one test per spec Example ----------------------------------------------


def test_two_entries_named_model_effort() -> None:
    # spec-example: marketplace-catalogue / two entries named model-effort
    marketplace, readme, gitmodules = real()
    marketplace["plugins"].append(copy.deepcopy(entry_named(marketplace, "model-effort")))
    assert catalogue_problems(marketplace, readme, ROOT, gitmodules) == ["model-effort: listed 2 times"]


def test_relative_sources_and_their_outcomes(tmp_path: Path) -> None:
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

    manifest = tmp_path / "broken" / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    for content in ("not json", "[]"):
        manifest.write_text(content, encoding="utf-8")
        assert source_problems({"name": "broken", "source": "./broken"}, tmp_path) == [
            "broken: manifest is not a JSON object"
        ], content


def test_sources_that_are_not_strings() -> None:
    # spec-example: marketplace-catalogue / sources that are not strings
    git_subdir = {"source": "git-subdir", "url": "https://github.com/PsychQuant/livedocs.git", "path": "plugins/livedocs"}
    for source in ({}, git_subdir, 42):
        assert source_problems({"name": "x", "source": source}, ROOT) == ["x: source is not a relative path string"], source
    assert source_problems({"name": "x"}, ROOT) == ["x: source is not a relative path string"]


def test_submodule_plugins_and_their_outcomes() -> None:
    # spec-example: marketplace-catalogue / submodule plugins and their outcomes
    no_phrase = ROW_OK.replace(", a git submodule", "")
    ssh = GITMODULES_OK.replace("https://github.com/", "git@github.com:")
    assert livedocs_only() == []
    assert livedocs_only(gitmodules=ssh) == ["livedocs: submodule url is not https"]
    assert livedocs_only(row=no_phrase) == ["livedocs: README row does not say git submodule"]
    assert livedocs_only(row=no_phrase, gitmodules="") == []


def test_named_plugins_and_their_outcomes() -> None:
    # spec-example: marketplace-catalogue / named plugins and their outcomes
    marketplace, readme, gitmodules = real()
    assert catalogue_problems(marketplace, readme, ROOT, gitmodules) == []

    without = copy.deepcopy(marketplace)
    without["plugins"] = [entry for entry in without["plugins"] if entry["name"] != "livedocs"]
    assert "livedocs: is not listed" in catalogue_problems(without, readme, ROOT, gitmodules)

    moved = copy.deepcopy(marketplace)
    entry_named(moved, "livedocs")["source"] = "./plugins/model-effort"
    assert "livedocs: has another source" in catalogue_problems(moved, readme, ROOT, gitmodules)

    extra = copy.deepcopy(marketplace)
    extra["plugins"].append({"name": "claude-hot-limit", "source": "./plugins/model-effort"})
    assert "claude-hot-limit: is listed" in catalogue_problems(extra, readme, ROOT, gitmodules)


def test_names_missing_from_one_of_the_three_lists() -> None:
    # spec-example: marketplace-catalogue / names missing from one of the three lists
    marketplace, readme, gitmodules = real()

    no_install = readme.replace("claude plugin install livedocs@claude-code-logos\n", "")
    assert no_install != readme
    assert catalogue_problems(marketplace, no_install, ROOT, gitmodules) == ["livedocs: missing from the Install block"]

    no_row = "\n".join(line for line in readme.splitlines() if not line.startswith("| `livedocs` |")) + "\n"
    assert no_row != readme
    assert catalogue_problems(marketplace, no_row, ROOT, gitmodules) == ["livedocs: missing from the Plugins table"]

    no_entry = copy.deepcopy(marketplace)
    no_entry["plugins"] = [entry for entry in no_entry["plugins"] if entry["name"] != "livedocs"]
    assert catalogue_problems(no_entry, readme, ROOT, gitmodules) == [
        "livedocs: is not listed",
        "livedocs: missing from marketplace.json",
    ]


def test_install_command_forms() -> None:
    # spec-example: marketplace-catalogue / install command forms
    assert livedocs_only(install="livedocs@claude-code-logos") == []
    for rest in (
        "livedocs",
        "livedocs@other@claude-code-logos",
        "livedocs@claude-code-logos --scope user",
        "livedocs@another-marketplace",
    ):
        assert livedocs_only(install=rest) == [
            f"install command '{rest}': not in the form name@claude-code-logos",
            "livedocs: missing from the Install block",
        ], rest


def test_table_rows_and_their_outcomes() -> None:
    # spec-example: marketplace-catalogue / table rows and their outcomes
    text = "An MCP server. macOS only; downloads an executable from GitHub Releases"
    no_rests = f"| `livedocs` | {text} |  | PsychQuant/livedocs, a git submodule |"
    no_lives = f"| `livedocs` | {text}, a git submodule | The primary source |  |"
    empty = "| `livedocs` | Something |  |  |"
    assert livedocs_only(row=no_rests) == ["livedocs: empty Rests on cell"]
    assert livedocs_only(row=no_lives) == ["livedocs: empty Lives in cell"]

    marketplace = {"plugins": [{"name": "livedocs", "source": LIVEDOCS_SOURCE}]}
    doubled = readme_with([empty, ROW_OK], ["livedocs@claude-code-logos"])
    assert catalogue_problems(marketplace, doubled, ROOT, GITMODULES_OK) == [
        "livedocs: empty Rests on cell",
        "livedocs: empty Lives in cell",
        "livedocs: listed in 2 rows",
    ]

    unquoted = readme_with([ROW_OK, "| surprise | Something | Research | this repository |"], ["livedocs@claude-code-logos"])
    assert catalogue_problems(marketplace, unquoted, ROOT, GITMODULES_OK) == [UNREADABLE_ROW]


def test_livedocs_rows_and_the_phrases_they_lack() -> None:
    # spec-example: marketplace-catalogue / livedocs rows and the phrases they lack
    def row(text: str) -> str:
        return f"| `livedocs` | {text} | The primary source | PsychQuant/livedocs, a git submodule |"

    def lacks(*phrases: str) -> list[str]:
        return [f"livedocs: README row lacks '{phrase}'" for phrase in phrases]

    assert livedocs_only(row=row("An MCP server and a look-up skill")) == lacks(*LIVEDOCS_PHRASES)
    assert livedocs_only(row=row("macOS only; downloads an executable")) == lacks("GitHub Releases")
    assert livedocs_only(row=row("Runs on macOS; downloads documentation from GitHub Releases")) == lacks(
        "macOS only", "downloads an executable"
    )


def test_archive_first_comes_in_as_a_submodule_of_its_own_repository() -> None:
    # Issue #17. The general rules it must meet are in the marketplace-catalogue spec
    # (relative path, same three lists, Rests on and Lives in, git submodule).
    entries = [entry for entry in load_marketplace()["plugins"] if entry.get("name") == "archive-first"]
    assert len(entries) == 1
    assert entries[0]["source"] == "./plugins/archive-first"
    # The version is in the plugin's own manifest; a copy here would go stale at its next release.
    assert "version" not in entries[0]
    assert submodules(load_gitmodules()).get("plugins/archive-first") == "https://github.com/PsychQuant/archive-first.git"
    rows = [row for row in table_rows(load_readme()) if row_name(row) == "archive-first"]
    assert len(rows) == 1
    assert "git submodule" in rows[0]["Lives in"]
    assert "archive-first@claude-code-logos" in install_lines(load_readme())
