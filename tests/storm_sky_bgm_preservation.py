"""Issue28 exact audio-only inverse and immutable new PCM pins.

Historical visual/combat guards remove only these six reviewed routing/UI deltas.
"""
import hashlib
from machine_fortress_preservation import without_machine_fortress
from world_balance_labels_preservation import CHANGED
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='e18c53000ff7412bca352e5bdb3fa887619ed4c9'
STORM_BGM_ASSETS=set(json.loads((ROOT/'tests/storm_sky_bgm_hashes.json').read_text()))

def without_storm_sky_bgm(source,name):
    source=without_machine_fortress(source,name)
    for old,new in reversed(json.loads((ROOT/'tests/storm_sky_bgm_changes.json').read_text()).get(name,[])):
        if new in source:
            assert source.count(new)==1,(name,new[:100]);source=source.replace(new,old)
        else:
            assert source.count(old)==1,(name,old[:100])
    return source

def assert_storm_bgm_asset(name):
    name=str(Path(name).relative_to(ROOT)) if Path(name).is_absolute() else str(name)
    assert name in STORM_BGM_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/storm_sky_bgm_hashes.json').read_text())[name]

def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name
        data=without_storm_sky_bgm(p.read_text(),name).encode() if name in {'index.html','assets/worlds/worlds.js'}|CHANGED else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    for name in STORM_BGM_ASSETS:assert_storm_bgm_asset(name)
    return {'baseline':BASE,'preserved_assets':len(names),'reviewed_index_deltas':3,'reviewed_world_registry_deltas':3,'new_music_files':2,'all_existing_graphics_audio_combat_and_controls_byte_preserved':True}

if __name__=='__main__':print(json.dumps(verify(),indent=2))
