"""Exact Issue10 deltas/owned selector ahead of every historical protection layer."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MIXED_ASSETS={'assets/snowfield/spawns.js'}
def assert_mixed_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    assert name in MIXED_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/mixed_asset_hashes.json').read_text())[name],name
def without_mixed_source(source):
    for old,new,count in reversed(json.loads((ROOT/'tests/mixed_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:100]);source=source.replace(new,old)
    return source
def without_mixed_asset(source,name):
    for old,new,count in reversed(json.loads((ROOT/'tests/mixed_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:100]);source=source.replace(new,old)
    return source
