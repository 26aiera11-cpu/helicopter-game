"""Exact Issue19 dragon-only deltas ahead of the previous preservation layers."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOSS_ASSETS={'assets/volcano/boss_combat.js'}
def assert_volcano_boss_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    assert name in BOSS_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/volcano_boss_asset_hashes.json').read_text())[name],name
def without_volcano_boss(source,name):
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_boss_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100]);source=source.replace(new,old)
    return source
