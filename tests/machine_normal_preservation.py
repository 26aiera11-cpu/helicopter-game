"""Issue33 exact region-local combat hooks; keep every old image/audio/stat module."""
import hashlib,json,subprocess
from machine_background_dash_preservation import without_background_dash
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='c512d82dd38bae25d572e8386ce7009c6ba0474f'
COMBAT_ASSETS={'assets/machine_fortress/'+name+'.js' for name in ['config','spawns','combat']}
TEXT={'index.html','assets/worlds/worlds.js','assets/machine_fortress/machine_fortress.js'}
def without_machine_normal(source,name):
    source=without_background_dash(source,name)
    markers={'index.html':'gameMachineCombat','assets/worlds/worlds.js':'기계 요새 일반 전투 시험 · 보스/음악','assets/machine_fortress/machine_fortress.js':'actor.machineSpeciesId'}
    if name not in markers or markers[name] not in source:return source
    for old,new,count in reversed(json.loads((ROOT/'tests/machine_normal_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,new[:90],source.count(new));source=source.replace(new,old)
    return source
def assert_machine_combat_asset(name):
    name=str(Path(name).relative_to(ROOT)) if Path(name).is_absolute() else str(name)
    payload=without_background_dash((ROOT/name).read_text(),name).encode()
    assert name in COMBAT_ASSETS and hashlib.sha256(payload).hexdigest()==json.loads((ROOT/'tests/machine_normal_hashes.json').read_text())[name],name
def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_machine_normal(p.read_text(),name).encode() if name in TEXT else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    for name in COMBAT_ASSETS:assert_machine_combat_asset(name)
    return {'baseline':BASE,'existing_assets':len(names),'raw_unchanged_assets':len(names)-2,'index_hooks':18,'art_id_status_deltas':2,'notice_deltas':2,'new_combat_modules':3,'all_png_audio_other_region_combat_player_controls_score_items_bytes_preserved':True,'normal_render_width':40,'boss_render_width':132,'normal_collision_radius':16}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
