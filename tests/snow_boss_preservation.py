"""Exact Issue9 hooks and owned new module before every previous guard."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BOSS_ASSETS={'assets/snowfield/boss_combat.js'}
def assert_boss_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    assert name in BOSS_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/snow_boss_asset_hashes.json').read_text())[name],name
def without_snow_boss_source(source):
    for old,new,count in reversed(json.loads((ROOT/'tests/snow_boss_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:100]);source=source.replace(new,old)
    return source
def without_snow_boss_asset(source,name):
    for old,new,count in reversed(json.loads((ROOT/'tests/snow_boss_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:100]);source=source.replace(new,old)
    return source
