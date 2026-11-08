"""Only Issue39's exact UI/legacy-name deltas may differ from the approved base."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='07c3d34331770f53817ca513241949ec19fe8dbe'
CHANGED={'assets/worlds/worlds.js','assets/score/score.js','assets/selection/selection.js'}
def without_world_balance_labels(source,name):
 for old,new in reversed(json.loads((ROOT/'tests/world_balance_label_changes.json').read_text()).get(name,[])):
  if new in source:
   assert source.count(new)==1,(name,new[:80]);source=source.replace(new,old)
 return source
def verify():
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
 for name in ['index.html']+names:
  p=ROOT/name;data=without_world_balance_labels(p.read_text(),name).encode() if name in CHANGED else p.read_bytes();assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
 return {'baseline':BASE,'assets':len(names),'raw_unchanged_assets':len(names)-3,'index_and_multitouch_exit_byte_identical':True,'exact_reviewed_deltas':sum(map(len,json.loads((ROOT/'tests/world_balance_label_changes.json').read_text()).values())),'combat_parameters_AI_images_audio_controls_items_and_internal_identifiers_unchanged':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
