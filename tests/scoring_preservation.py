"""Reverse exact reviewed score/UI deltas without relaxing gameplay asset guards."""
import hashlib
import json
from pathlib import Path
from developer_start_preservation import without_developer_start_asset
from item_monster_preservation import without_item_monsters
from controls_preservation import without_controls_ui

ROOT = Path(__file__).resolve().parents[1]
SCORE_ASSETS = {'assets/score/score.js', 'assets/score/score.css'}


def assert_scoring_asset(path):
    relative = str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    expected = json.loads((ROOT / 'tests/scoring_asset_hashes.json').read_text())
    assert relative in SCORE_ASSETS
    assert hashlib.sha256(without_developer_start_asset((ROOT / relative).read_text(),relative).encode()).hexdigest() == expected[relative]


def reverse(source, filename):
    for old, new in reversed(json.loads((ROOT / 'tests' / filename).read_text())):
        assert source.count(new) == 1, new[:100]
        source = source.replace(new, old, 1)
    return source


def without_scoring_changes(source):
    source=without_item_monsters(source)
    return reverse(source, 'scoring_changes.json')


def without_scoring_ui(source, name):
    source = without_controls_ui(source, name)
    return reverse(source, 'scoring_ui_changes.json') if name == 'assets/selection/selection.js' else source
