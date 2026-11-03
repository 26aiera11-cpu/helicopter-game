"""Exact art-only hooks, original ZIP assets and runtime byte guards."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SNOWFIELD_ASSETS=set(json.loads((ROOT/'tests/snowfield_asset_hashes.json').read_text()))
def assert_snowfield_asset(path):
    path=Path(path);name=str(path.relative_to(ROOT)) if path.is_absolute() else str(path)
    assert name in SNOWFIELD_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/snowfield_asset_hashes.json').read_text())[name],name

def without_snowfield_source(source):
    for old,new,count in reversed(json.loads((ROOT/'tests/snowfield_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:120]);source=source.replace(new,old)
    return source

def without_snowfield_asset(source,name):
    for old,new in reversed(json.loads((ROOT/'tests/snowfield_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==1,(name,new[:120]);source=source.replace(new,old,1)
    return source
