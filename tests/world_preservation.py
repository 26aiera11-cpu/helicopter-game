"""Undo exact approved world hooks before historical byte guards."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
WORLD_ASSETS={'assets/worlds/worlds.js','assets/worlds/worlds.css'}
def assert_world_asset(path):
    path=Path(path);name=str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    assert name in WORLD_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/world_asset_hashes.json').read_text())[name],name
def without_world_source(source):
    for old,new,count in reversed(json.loads((ROOT/'tests/world_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:90])
        source=source.replace(new,old)
    return source
def without_world_ui(source,name):
    for old,new in reversed(json.loads((ROOT/'tests/world_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==1,(name,new[:100]);source=source.replace(new,old,1)
    return source
