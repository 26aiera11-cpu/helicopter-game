"""Reverse only exact approved Issue39 UI and Issue40 boss-HP deltas."""
import json,subprocess
from pathlib import Path
from world2_boss_hp_preservation import without_world2_boss_hp
ROOT=Path(__file__).resolve().parents[1];BASE='07c3d34331770f53817ca513241949ec19fe8dbe'
CHANGED={'assets/worlds/worlds.js','assets/score/score.js','assets/selection/selection.js'}
def without_world_balance_labels(source,name):
 source=without_world2_boss_hp(source,name)
 for old,new in reversed(json.loads((ROOT/'tests/world_balance_label_changes.json').read_text()).get(name,[])):
  if new in source:
   assert source.count(new)==1,(name,new[:80]);source=source.replace(new,old)
 return source
def verify():
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
 for name in ['index.html']+names:
  p=ROOT/name;data=without_world_balance_labels(p.read_text(),name).encode() if name in CHANGED or name=='index.html' else p.read_bytes();assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
 return {'baseline':BASE,'assets':len(names),'raw_unchanged_assets':len(names)-3,'index_after_exact_HP_inverse_and_multitouch_exit_preserved':True,'exact_reviewed_deltas':sum(map(len,json.loads((ROOT/'tests/world_balance_label_changes.json').read_text()).values())),'all_other_combat_AI_images_audio_controls_items_and_internal_identifiers_unchanged':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
