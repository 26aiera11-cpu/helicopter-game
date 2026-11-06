"""Exact Issue13 name/title deltas; old gameplay and original art stay protected."""
import hashlib,json
from pathlib import Path
from volcano_preservation import VOLCANO_ASSETS,assert_volcano_asset,without_volcano_asset
ROOT=Path(__file__).resolve().parents[1]
PPYOKO_ASSETS={'assets/selection/title/hel-corrected.png'}|VOLCANO_ASSETS
def assert_ppyoko_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in VOLCANO_ASSETS:assert_volcano_asset(path);return
    assert name in PPYOKO_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/ppyoko_asset_hashes.json').read_text())[name],name
def without_ppyoko_asset(source,name):
    source=without_volcano_asset(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/ppyoko_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:90]);source=source.replace(new,old)
    return source
def without_ppyoko_source(source):
    return without_ppyoko_asset(source,'index.html')
