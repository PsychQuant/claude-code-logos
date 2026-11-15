"""Root pytest configuration.

`plugins/livedocs` is a git submodule holding another repository with its own
test suite; running `pytest` here must not collect it.
"""
collect_ignore = ["plugins/livedocs"]
