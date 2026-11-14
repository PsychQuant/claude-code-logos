"""The marketplace file and the README must list the same plugins (#18)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
PLUGINS = {p["name"]: p for p in MARKETPLACE["plugins"]}
README = (ROOT / "README.md").read_text()


def readme_plugin_names():
    section = README.split("## Plugins", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"^\| `([^`]+)` \|", section, flags=re.M)


def test_plugin_names_are_unique():
    names = [p["name"] for p in MARKETPLACE["plugins"]]
    assert len(names) == len(set(names))


def test_relative_sources_exist_and_are_plugins():
    for plugin in MARKETPLACE["plugins"]:
        source = plugin["source"]
        if isinstance(source, str):
            assert (ROOT / source / ".claude-plugin" / "plugin.json").is_file(), source


def test_livedocs_is_listed_from_its_own_repository():
    entry = PLUGINS["livedocs"]
    assert entry["source"] == {
        "source": "git-subdir",
        "url": "PsychQuant/livedocs",
        "path": "plugins/livedocs",
    }
    # The plugin's own plugin.json carries the version; repeating it here
    # would need a commit in this repository for every livedocs release.
    assert "version" not in entry


def test_claude_hot_limit_is_not_listed():
    assert "claude-hot-limit" not in PLUGINS


def test_readme_table_and_marketplace_list_the_same_plugins():
    assert sorted(readme_plugin_names()) == sorted(PLUGINS)


def test_readme_no_longer_claims_every_plugin_is_research_grounded():
    assert "Every plugin in this marketplace is grounded in published research" not in README
