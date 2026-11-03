"""Exact Issue8 deltas before every historical preservation layer."""
import hashlib,json
from pathlib import Path
from snow_boss_preservation import BOSS_ASSETS,assert_boss_asset,without_snow_boss_source,without_snow_boss_asset
ROOT=Path(__file__).resolve().parents[1]
COMBAT_ASSETS={'assets/snowfield/combat.js'}|BOSS_ASSETS
def assert_combat_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in BOSS_ASSETS:assert_boss_asset(path);return
    expected=json.loads((ROOT/'tests/snow_combat_asset_hashes.json').read_text())
    assert name in COMBAT_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected[name],name
def without_snow_combat_source(source):
    source=without_snow_boss_source(source)
    for old,new,count in reversed(json.loads((ROOT/'tests/snow_combat_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:100]);source=source.replace(new,old)
    return source
def without_snow_combat_asset(source,name):
    source=without_snow_boss_asset(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/snow_combat_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:100]);source=source.replace(new,old)
    return source
