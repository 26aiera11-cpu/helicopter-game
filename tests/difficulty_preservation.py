"""Exact Issue11 regional tuning changes before the historical protection layers."""
import hashlib,json
from ppyoko_preservation import PPYOKO_ASSETS,assert_ppyoko_asset,without_ppyoko_asset
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIFFICULTY_ASSETS={'assets/worlds/difficulty.js'}|PPYOKO_ASSETS
def assert_difficulty_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in PPYOKO_ASSETS:assert_ppyoko_asset(path);return
    assert name in DIFFICULTY_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/difficulty_asset_hashes.json').read_text())[name],name
def without_difficulty_asset(source,name):
    source=without_ppyoko_asset(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/difficulty_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:100]);source=source.replace(new,old)
    return source
def without_difficulty_source(source):
    return without_difficulty_asset(source,'index.html')
