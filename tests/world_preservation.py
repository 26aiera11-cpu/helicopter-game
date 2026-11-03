"""Undo exact approved world hooks before historical byte guards."""
import hashlib
import json
from pathlib import Path
from snowfield_preservation import SNOWFIELD_ASSETS, assert_snowfield_asset, without_snowfield_source, without_snowfield_asset
ROOT=Path(__file__).resolve().parents[1]
WORLD_ASSETS={'assets/worlds/worlds.js','assets/worlds/worlds.css'}|SNOWFIELD_ASSETS
def assert_world_asset(path):
    path=Path(path);name=str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    if name in SNOWFIELD_ASSETS:
        assert_snowfield_asset(path);return
    payload=without_snowfield_asset((ROOT/name).read_text(),name).encode()
    assert name in WORLD_ASSETS and hashlib.sha256(payload).hexdigest()==json.loads((ROOT/'tests/world_asset_hashes.json').read_text())[name],name
def without_world_source(source):
    source=without_snowfield_source(source)
    for old,new,count in reversed(json.loads((ROOT/'tests/world_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:90])
        source=source.replace(new,old)
    return source
def without_world_ui(source,name):
    for old,new in reversed(json.loads((ROOT/'tests/world_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==1,(name,new[:100]);source=source.replace(new,old,1)
    return source
