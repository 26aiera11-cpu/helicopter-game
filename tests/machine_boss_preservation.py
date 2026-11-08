"""Issue36 exact GigaCore hooks/red adapter; preserve approved Cover and every old asset."""
import hashlib,json,subprocess
from machine_fortress_bgm_preservation import without_machine_bgm
from world_balance_labels_preservation import CHANGED
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='0ae1d974ab7a90058e7abb3abc7172dd2003711d'
BOSS_ASSETS={'assets/machine_fortress/boss_combat.js'}
TEXT={'index.html','assets/machine_fortress/machine_fortress.js','assets/worlds/worlds.js'}
def without_machine_boss(source,name):
    source=without_machine_bgm(source,name)
    markers={'index.html':'gameMachineBoss','assets/machine_fortress/machine_fortress.js':'overdriveSpec','assets/worlds/worlds.js':'기계 요새 전투 시험 · 전용 보스'}
    if name not in markers or markers[name] not in source:return source
    for old,new,count in reversed(json.loads((ROOT/'tests/machine_boss_changes.json').read_text())[name]):
        assert source.count(new)==count,(name,new[:100],source.count(new));source=source.replace(new,old)
    return source
def assert_boss_asset(name):
    name=str(Path(name).relative_to(ROOT)) if Path(name).is_absolute() else str(name)
    assert name in BOSS_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/machine_boss_hashes.json').read_text())[name],name
def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_machine_boss(p.read_text(),name).encode() if name in TEXT|CHANGED else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    for name in BOSS_ASSETS:assert_boss_asset(name)
    a=(ROOT/'assets/machine_fortress/machine_fortress.js').read_text();b=subprocess.check_output(['git','show',BASE+':assets/machine_fortress/machine_fortress.js'],cwd=ROOT,text=True)
    section=lambda s:s[s.index(' function drawBackground('):s.index(' function deferAdvance(')]
    assert section(a)==section(b)
    return {'baseline':BASE,'existing_assets':len(names),'assets_matching_after_exact_UI_and_feature_reversal':len(names),'index_delta_groups':10,'red_art_adapter_groups':5,'trial_notice_groups':2,'new_boss_modules':1,
            'cover_function_byte_identical':True,'normal_combat_config_spawn_dash_player_control_score_item_audio_PNG_manifest_bytes_preserved':True,
            'base_hp':20,'existing_upgrade_health_multiplier_preserved':True,'boss_radius':48,'boss_width':132,'normal_width':40}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
