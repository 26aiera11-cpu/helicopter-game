"""Reverse only the two approved native kill/region-entry hooks."""
import json
from pathlib import Path


def without_item_spawn_changes(source):
    for old, new in reversed(json.loads(Path(__file__).with_name('item_spawn_changes.json').read_text())):
        assert source.count(new) == 1, new
        source = source.replace(new, old, 1)
    return source
