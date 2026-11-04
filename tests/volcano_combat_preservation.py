"""Undo exact Issue18 hooks; preserve every pre-existing asset and combat branch."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMBAT_ASSETS={'assets/volcano/combat.js'}

def assert_volcano_combat_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    assert name in COMBAT_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/volcano_combat_asset_hashes.json').read_text())[name],name

def without_volcano_combat(source,name):
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_combat_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source
