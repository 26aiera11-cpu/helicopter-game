"""Exact developer-entry/startup/volatile-score deltas, before older guards."""
import json
from pathlib import Path
from snow_combat_preservation import without_snow_combat_source,without_snow_combat_asset
ROOT=Path(__file__).resolve().parents[1]
def without_developer_start_source(source):
    source=without_snow_combat_source(source)
    for old,new,count in reversed(json.loads((ROOT/'tests/developer_start_changes.json').read_text())):
        assert source.count(new)==count,(source.count(new),new[:120]);source=source.replace(new,old)
    return source

def without_developer_start_asset(source,name):
    source=without_snow_combat_asset(source,name)
    for old,new in reversed(json.loads((ROOT/'tests/developer_start_asset_changes.json').read_text()).get(name,[])):
        assert source.count(new)==1,(name,new[:120]);source=source.replace(new,old,1)
    return source
