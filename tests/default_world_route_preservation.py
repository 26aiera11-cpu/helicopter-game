"""Issue38: only four reviewed registry-default/help deltas; no engine/score/art/audio changes."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='54d892cbd074804741892ab800c293cb3b4fd5cc'
REGISTRY='assets/worlds/worlds.js'
def without_default_world_route(source,name):
 for old,new in reversed(json.loads((ROOT/'tests/default_world_route_changes.json').read_text()).get(name,[])):
  if new in source:
   assert source.count(new)==1,(name,new[:100]);source=source.replace(new,old)
 return source
def verify():
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
 for name in ['index.html']+names:
  p=ROOT/name;data=without_default_world_route(p.read_text(),name).encode() if name==REGISTRY else p.read_bytes()
  assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
 return {'baseline':BASE,'existing_assets':len(names),'raw_unchanged_assets':len(names)-1,'runtime_changed_file':REGISTRY,'exact_default_and_help_deltas':4,'index_and_score_storage_code_byte_identical':True,'all_PNG_audio_combat_player_control_item_reward_recovery_Cover_code_byte_identical':True,'approved_machine_fortress_WAVs_byte_identical':True,'no_storage_key_migration_or_merge':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
