"""Issue22 exact spawn-only deltas before every historical preservation layer."""
from pathlib import Path
import json,hashlib
from volcano_bgm_preservation import without_volcano_bgm
ROOT=Path(__file__).resolve().parents[1]
VOLCANO_MIXED_ASSETS={'assets/volcano/spawns.js'}
def without_volcano_mixed(source,name):
    source=without_volcano_bgm(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_mixed_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source
def assert_volcano_mixed_asset(name):
    assert name in VOLCANO_MIXED_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/volcano_mixed_asset_hashes.json').read_text())[name]
