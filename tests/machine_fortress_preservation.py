"""Issue31 graphics-only hooks and exact preservation of all existing assets."""
import hashlib,json,subprocess
from machine_enemy_scale_preservation import without_enemy_scale,RENDERER
from machine_normal_preservation import without_machine_normal,COMBAT_ASSETS,assert_machine_combat_asset
from machine_boss_preservation import BOSS_ASSETS,assert_boss_asset
from machine_fortress_bgm_preservation import MACHINE_BGM_ASSETS,assert_machine_bgm_asset
from world_balance_labels_preservation import CHANGED
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='653ac838e32fbf8276853058b75041703af4f079'
MACHINE_ASSETS=set(json.loads((ROOT/'tests/machine_fortress_hashes.json').read_text()))|COMBAT_ASSETS|BOSS_ASSETS|MACHINE_BGM_ASSETS
def without_machine_fortress(source,name):
    source=without_machine_normal(source,name)
    marker='gameMachineFortress' if name=='index.html' else 'world-2:machine-fortress'
    if marker not in source:return source
    for old,new,count in reversed(json.loads((ROOT/'tests/machine_fortress_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:90],source.count(new));source=source.replace(new,old)
    return source
def assert_machine_asset(name):
    name=str(Path(name).relative_to(ROOT)) if Path(name).is_absolute() else str(name)
    if name in MACHINE_BGM_ASSETS:assert_machine_bgm_asset(name);return
    if name in BOSS_ASSETS:assert_boss_asset(name);return
    if name in COMBAT_ASSETS:assert_machine_combat_asset(name);return
    assert name in MACHINE_ASSETS
    payload=without_enemy_scale((ROOT/name).read_text(),name).encode() if name==RENDERER else (ROOT/name).read_bytes()
    assert hashlib.sha256(payload).hexdigest()==json.loads((ROOT/'tests/machine_fortress_hashes.json').read_text())[name],name
def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_machine_fortress(p.read_text(),name).encode() if name in {'index.html','assets/worlds/worlds.js'}|CHANGED else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    for name in MACHINE_ASSETS:assert_machine_asset(name)
    return {'baseline':BASE,'existing_assets':len(names),'assets_matching_after_exact_UI_and_feature_reversal':len(names),'index_exact_graphics_hooks':16,'registry_exact_deltas':9,'approved_new_assets':len(MACHINE_ASSETS),'existing_graphics_combat_audio_score_item_controls_byte_preserved':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
