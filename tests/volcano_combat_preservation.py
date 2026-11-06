"""Undo exact Issue18 hooks; preserve every pre-existing asset and combat branch."""
import hashlib,json
from pathlib import Path
from volcano_boss_preservation import BOSS_ASSETS,assert_volcano_boss_asset,without_volcano_boss

ROOT=Path(__file__).resolve().parents[1]
COMBAT_ASSETS={'assets/volcano/combat.js'}|BOSS_ASSETS

def assert_volcano_combat_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in BOSS_ASSETS:assert_volcano_boss_asset(path);return
    assert name in COMBAT_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/volcano_combat_asset_hashes.json').read_text())[name],name

def without_volcano_combat(source,name):
    source=without_volcano_boss(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_combat_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source
