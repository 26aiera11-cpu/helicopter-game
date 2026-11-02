"""Exact independent-item deltas and supplied asset byte guards."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def without_item_monsters(source):
    for old, new in reversed(json.loads((ROOT / 'tests/item_monster_changes.json').read_text())):
        assert source.count(new) == 1, (source.count(new), new[:120])
        source = source.replace(new, old, 1)
    return source


def assert_item_asset(path):
    path = Path(path)
    name = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    approved = json.loads((ROOT / 'tests/item_monster_asset_hashes.json').read_text())
    approved.update(json.loads((ROOT / 'tests/item_monster_module_hashes.json').read_text()))
    assert name in approved, name
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == approved[name], name
