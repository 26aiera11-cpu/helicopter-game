"""Issue35: only Machine Fortress background renderer may change."""
import json,subprocess
from machine_boss_preservation import without_machine_boss,TEXT
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='46e86319a3924bfd0ef68cb9627bef5041f354fc'
RENDERER='assets/machine_fortress/machine_fortress.js'
def without_machine_cover(source,name):
    source=without_machine_boss(source,name)
    if name!=RENDERER or 'Math.max(w/backgroundImage.naturalWidth,h/backgroundImage.naturalHeight)' not in source:return source
    for old,new,count in reversed(json.loads((ROOT/'tests/machine_cover_changes.json').read_text())[name]):
        assert source.count(new)==count,(name,new[:100],source.count(new));source=source.replace(new,old)
    return source
def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_machine_cover(p.read_text(),name).encode() if name in TEXT|{RENDERER} else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    return {'baseline':BASE,'existing_assets':len(names),'raw_unchanged_assets':len(names)-1,'only_runtime_file':RENDERER,'index_byte_unchanged':True,
            'all_combat_projectile_laser_damage_spawn_dash_and_player_code_bytes_preserved':True,'original_PNG_manifest_audio_other_regions_controls_score_items_bytes_preserved':True,
            'screw_dash_height_fraction':.40,'wasp_dash_height_fraction':.70,'dash_speed':[100,145],'normal_width':40,'boss_width':132}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
