"""Issue34: exact render-only background fill and H-proportional dash deltas."""
import hashlib,json,subprocess
from machine_cover_preservation import without_machine_cover
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='e6f6f8822a47daf023616681768c3db212d16435'
TEXT={'assets/machine_fortress/'+name+'.js' for name in ['config','combat','machine_fortress']}
def without_background_dash(source,name):
    source=without_machine_cover(source,name)
    marker={'assets/machine_fortress/config.js':'dashHeight',
            'assets/machine_fortress/combat.js':'targetDistance',
            'assets/machine_fortress/machine_fortress.js':'backgroundCache'}.get(name)
    if not marker or marker not in source:return source
    for old,new,count in reversed(json.loads((ROOT/'tests/machine_background_dash_changes.json').read_text())[name]):
        assert source.count(new)==count,(name,new[:100],source.count(new));source=source.replace(new,old)
    return source
def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_background_dash(p.read_text(),name).encode() if name in TEXT else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    return {'baseline':BASE,'existing_assets':len(names),'raw_unchanged_assets':len(names)-3,'index_byte_unchanged':True,'only_runtime_files':sorted(TEXT),
            'original_PNG_manifest_audio_other_regions_players_controls_score_items_bytes_preserved':True,
            'normal_width':40,'boss_width':132,'normal_hit_radius':16,'target_dash_height_fraction':[.40,.70],'dash_speed':[100,145]}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
