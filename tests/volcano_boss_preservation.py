"""Exact Issue19 dragon-only deltas ahead of the previous preservation layers."""
import hashlib,json
from pathlib import Path
from volcano_breath_preservation import BREATH_ASSETS,without_volcano_breath,assert_volcano_breath_asset
from volcano_mixed_preservation import VOLCANO_MIXED_ASSETS,assert_volcano_mixed_asset
ROOT=Path(__file__).resolve().parents[1]
BOSS_ASSETS={'assets/volcano/boss_combat.js'}|BREATH_ASSETS|VOLCANO_MIXED_ASSETS
def assert_volcano_boss_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in VOLCANO_MIXED_ASSETS:assert_volcano_mixed_asset(name);return
    if name in BREATH_ASSETS:assert_volcano_breath_asset(name);return
    assert name in BOSS_ASSETS
    assert hashlib.sha256(without_volcano_breath((ROOT/name).read_text(),name).encode()).hexdigest()==json.loads((ROOT/'tests/volcano_boss_asset_hashes.json').read_text())[name],name
def without_volcano_boss(source,name):
    source=without_volcano_breath(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_boss_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100]);source=source.replace(new,old)
    return source
