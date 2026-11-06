"""Only Issue23 hidden audio/track routing, music profile and notice deltas."""
from storm_sky_preservation import without_storm
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VOLCANO_BGM_ASSETS={'assets/audio/volcano_stage.wav','assets/audio/volcano_boss.wav'}

def without_volcano_bgm(source,name):
    source=without_storm(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_bgm_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source

def assert_volcano_bgm_asset(name):
    assert name in VOLCANO_BGM_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/volcano_bgm_asset_hashes.json').read_text())[name],name
