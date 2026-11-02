"""Undo only reviewed progression changes for historical byte-preservation checks."""
import json
from tanko_combat_preservation import without_tanko_combat_changes
from pathlib import Path
from scoring_preservation import without_scoring_ui


def without_progression_changes(source):
    source=without_tanko_combat_changes(source)
    for changes in reversed(list(json.loads(Path(__file__).with_name('progression_changes.json').read_text()).values())):
        for old, new in reversed(changes):
            assert source.count(new) == 1, new[:90]
            source = source.replace(new, old, 1)
    return source


def without_progression_ui(source, name):
    source=without_scoring_ui(source,name)
    markers = {
        'assets/selection/selection.js': '\n/* Game-over presentation only;',
        'assets/selection/selection.css': '\n/* Last-frame game-over overlay;',
    }
    marker = markers.get(name)
    if marker:
        assert source.count(marker) == 1
        source = source[:source.index(marker)]
    if name.endswith('selection.js'):
        assert source.count('/모든 지역 클리어/') == 1
        source = source.replace('/모든 지역 클리어/', '/게임 오버|모든 지역 클리어/', 1)
    return source
