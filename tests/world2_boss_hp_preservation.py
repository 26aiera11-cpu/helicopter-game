"""Issue40 allows exactly one boss-base-HP delta; all other bytes stay fixed."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='98676edd011147d59219590e4254c307e7ff6f07'
OLD='const bossHP=(20+profile*15)*[1,1.1,1.4,1.6,1.9,2.2][player.upgrade];'
NEW="const bossBaseHP=({'world-2:snowfield':72,'world-2:volcano':80,'world-2:storm-sky':90,'world-2:machine-fortress':100}[gameWorlds.region(stage).key]??(20+profile*15));const bossHP=bossBaseHP*[1,1.1,1.4,1.6,1.9,2.2][player.upgrade];"
def without_world2_boss_hp(source,name):
 if name=='index.html' and NEW in source:
  assert source.count(NEW)==1;return source.replace(NEW,OLD)
 return source
def verify():
 source=(ROOT/'index.html').read_text();assert source.count(NEW)==1
 assert without_world2_boss_hp(source,'index.html').encode()==subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT)
 assets=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
 for name in assets:assert (ROOT/name).read_bytes()==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
 for name in ['README.md','boss-encounters.json','boss-times.csv','route-samples.json']:
  path='docs/review/world-balance-audit/'+name;assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path
 return {'baseline':BASE,'exact_index_delta':1,'unchanged_assets':len(assets),'all_other_engine_bytes_unchanged':True,'Issue39_analysis_reused_unchanged':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
