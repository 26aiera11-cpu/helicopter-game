"""Exact Issue15 integration deltas before all historical byte guards."""
import hashlib
import json
from pathlib import Path
from visual_fix_preservation import VISUAL_FIX_ASSETS,assert_visual_fix_asset,without_visual_fix_asset
from volcano_boss_preservation import without_volcano_boss

ROOT=Path(__file__).resolve().parents[1]
VOLCANO_ASSETS=set(json.loads((ROOT/'tests/volcano_asset_hashes.json').read_text()))|VISUAL_FIX_ASSETS


def assert_volcano_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in VISUAL_FIX_ASSETS:assert_visual_fix_asset(path);return
    assert name in VOLCANO_ASSETS
    data=without_volcano_boss((ROOT/name).read_text(),name).encode() if (ROOT/name).suffix=='.js' else (ROOT/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==json.loads((ROOT/'tests/volcano_asset_hashes.json').read_text())[name],name


def without_volcano_asset(source,name):
    source=without_visual_fix_asset(source,name)
    if name=='index.html':
        block=(ROOT/'tests/volcano_html_block.txt').read_text()
        assert source.count(block)==1,'Exact volcano manifest/image block'
        source=source.replace(block,'',1)
        changes=json.loads((ROOT/'tests/volcano_changes.json').read_text())
    else:
        changes=json.loads((ROOT/'tests/volcano_asset_changes.json').read_text()).get(name,[])
    for old,new,count in reversed(changes):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source
