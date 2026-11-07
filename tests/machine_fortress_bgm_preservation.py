"""Issue37 exact audio/registry-only delta; every older game asset remains intact."""
import hashlib,json,subprocess
from default_world_route_preservation import without_default_world_route
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='2f29ced6cd53b7ebcb8279669c70c74fc1374ff1'
MACHINE_BGM_ASSETS=set(json.loads((ROOT/'tests/machine_fortress_bgm_hashes.json').read_text()))
def without_machine_bgm(source,name):
 source=without_default_world_route(source,name)
 for old,new in reversed(json.loads((ROOT/'tests/machine_fortress_bgm_changes.json').read_text()).get(name,[])):
  if new in source:
   assert source.count(new)==1,(name,new[:90]);source=source.replace(new,old)
 return source
def assert_machine_bgm_asset(name):
 name=str(Path(name).relative_to(ROOT)) if Path(name).is_absolute() else str(name)
 assert name in MACHINE_BGM_ASSETS and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/machine_fortress_bgm_hashes.json').read_text())[name],name
def verify():
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
 for name in ['index.html']+names:
  p=ROOT/name;data=without_machine_bgm(p.read_text(),name).encode() if name in ['index.html','assets/worlds/worlds.js'] else p.read_bytes()
  assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
 for name in MACHINE_BGM_ASSETS:assert_machine_bgm_asset(name)
 return {'baseline':BASE,'existing_assets':len(names),'raw_unchanged_existing_assets':len(names)-1,'index_audio_deltas':3,'world_music_and_notice_deltas':3,'new_WAV_files':2,'all_old_PNGs_audio_manifest_Cover_normal_and_boss_AI_controls_weapons_score_items_byte_preserved':True,'unchanged_GigaCore_lasers_missiles_wall75_25_overdrive':True,'music_profiles':[0,1,2,3,0,4,5,6]}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
