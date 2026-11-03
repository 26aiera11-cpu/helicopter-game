"""Exact approved touch/joystick deltas; earlier source and asset guards remain."""
import hashlib
import json
from pathlib import Path
from world_preservation import without_world_source, without_world_ui

ROOT = Path(__file__).resolve().parents[1]
CONTROLS_ASSETS = {'assets/controls/controls.js', 'assets/controls/controls.css'}


def assert_controls_asset(path):
    path = Path(path)
    name = str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    expected = json.loads((ROOT / 'tests/controls_asset_hashes.json').read_text())
    assert name in CONTROLS_ASSETS and hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected[name], name


def reverse(source, filename):
    for old, new in reversed(json.loads((ROOT / 'tests' / filename).read_text())):
        assert source.count(new) == 1, (filename, source.count(new), new[:80])
        source = source.replace(new, old, 1)
    return source


def without_controls_changes(source):
    source = without_world_source(source)
    return reverse(source, 'controls_changes.json')


def without_controls_ui(source, name):
    source = without_world_ui(source, name)
    return reverse(source, 'controls_ui_changes.json') if name == 'assets/selection/selection.js' else source
