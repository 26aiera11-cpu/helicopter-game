"""Exact Issue10 deltas/owned selector ahead of every historical protection layer."""
import hashlib,json
from difficulty_preservation import DIFFICULTY_ASSETS,assert_difficulty_asset,without_difficulty_source,without_difficulty_asset
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MIXED_ASSETS={'assets/snowfield/spawns.js'}|DIFFICULTY_ASSETS
def assert_mixed_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in DIFFICULTY_ASSETS:assert_difficulty_asset(path);return
    assert name in MIXED_ASSETS and hashlib.sha256(without_difficulty_asset((ROOT/name).read_text(),name).encode()).hexdigest()==json.loads((ROOT/'tests/mixed_asset_hashes.json').read_text())[name],name
def without_mixed_source(source):
    source=without_difficulty_source(source)
    for old,new,count in reversed(json.loads((ROOT/'tests/mixed_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:100]);source=source.replace(new,old)
    return source
def without_mixed_asset(source,name):
    source=without_difficulty_asset(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/mixed_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:100]);source=source.replace(new,old)
    return source
