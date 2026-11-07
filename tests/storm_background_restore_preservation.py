"""Issue27 approved complete PNG replacement only; keep all other historic guards."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='4549b4993ba8ca19d1a8c5845c4774014a0caa24'
BACKGROUND='assets/storm_sky/storm_sky_background_1920x864.png'
TEXT_ASSETS={'index.html','assets/storm_sky/asset_manifest.json','assets/storm_sky/prepare_assets.py'}
def pins():return json.loads((ROOT/'tests/storm_background_restore_hashes.json').read_text())
def assert_restored_background():
    data=(ROOT/BACKGROUND).read_bytes();p=pins()
    assert len(data)==p['approved_png_bytes'] and hashlib.sha256(data).hexdigest()==p['approved_png_sha256']
    return data

def without_background_restore(source,name):
    for old,new in reversed(json.loads((ROOT/'tests/storm_background_restore_changes.json').read_text()).get(name,[])):
        if new in source:
            assert source.count(new)==1,(name,new[:100]);source=source.replace(new,old)
        else:assert source.count(old)==1,(name,old[:100])
    return source

def verify():
    files=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+files:
        if name==BACKGROUND:assert_restored_background();continue
        f=ROOT/name;data=without_background_restore(f.read_text(),name).encode() if name in TEXT_ASSETS else f.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    return {'baseline':BASE,'existing_asset_count':len(files),'authorized_png_replacement':BACKGROUND,'approved_png_sha256':pins()['approved_png_sha256'],'all_other_images_audio_and_combat_bytes_unchanged':True,'contain_renderer_and_controls_world_registry_bytes_unchanged':True,'metadata_deltas':['background SHA in manifest','background SHA in native embedded manifest','asset generator strict validation/approved background option']}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
