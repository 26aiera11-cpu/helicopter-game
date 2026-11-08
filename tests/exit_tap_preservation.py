"""Issue30: reverse only the reviewed exit-button handler; preserve every approved asset."""
from world_balance_labels_preservation import without_world_balance_labels,CHANGED
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='3c085442bba6490bfa41cae64ac4007af570ba2e'
def without_exit_tap(source,name):
 source=without_world_balance_labels(source,name)
 for old,new in reversed(json.loads((ROOT/'tests/exit_tap_changes.json').read_text()).get(name,[])):
  if new in source:
   assert source.count(new)==1,(name,'exit tap hook count');source=source.replace(new,old)
 return source
def verify():
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
 for name in ['index.html']+names:
  p=ROOT/name;data=without_exit_tap(p.read_text(),name).encode() if name=='index.html' or name in CHANGED else p.read_bytes()
  assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
 changes=json.loads((ROOT/'tests/exit_tap_changes.json').read_text())['index.html'];old,new=changes[0]
 callback=old[old.index('showGameExitDialog(')+len('showGameExitDialog('):old.rindex(')});')]
 assert new.count(callback)==1,'Exit cleanup callback must remain byte-identical'
 return {'baseline':BASE,'assets_matching_after_reviewed_UI_reversal':len(names),'only_runtime_delta':'index.html exit button handler','exit_cleanup_callback_unchanged':True,'all_other_engine_source_unchanged':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
