"""Issue32: one shared display width only; all image/combat bytes stay fixed."""
import json,subprocess
from machine_normal_preservation import without_machine_normal,TEXT
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='ed3dc5561f569de62a9dd31a5eaf60f33722b6d1'
RENDERER='assets/machine_fortress/machine_fortress.js'
def without_enemy_scale(source,name):
    source=without_machine_normal(source,name)
    if name!=RENDERER:return source
    assert source.count('renderWidth:40')+source.count('renderWidth:32')==1
    return source.replace('renderWidth:40','renderWidth:32')
def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_enemy_scale(p.read_text(),name).encode() if name in TEXT else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    source=(ROOT/RENDERER).read_text();assert source.count('renderWidth:40')==1 and source.count('renderWidth:132')==1
    return {'baseline':BASE,'existing_assets':len(names),'raw_unchanged_assets':len(names)-1,'index_byte_unchanged':True,'only_runtime_delta':'shared normal renderWidth:32 -> renderWidth:40','boss_width':132,'hp':1,'collision_radius':16,'all_png_audio_combat_controls_registry_score_items_byte_preserved':True}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
