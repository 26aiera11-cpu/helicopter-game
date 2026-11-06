"""Issue27: exact background-only inverse; all historical guards remain strict."""
import json,subprocess,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='6c3446b7ad079822df80db5045c1f727051d47e4'
TEXT_ASSETS={'assets/storm_sky/storm_sky.js','assets/storm_sky/asset_manifest.json','assets/storm_sky/prepare_assets.py'}
def without_background_fit(source,name):
    if name=='index.html':
        m=re.search(r'(<template id="stormSkyManifest">)(.*?)(</template>)',source,re.S)
        if m:
            body=m[2];old='"render_mode": "cover"';new='"render_mode": "contain"'
            assert body.count(old)+body.count(new)==1
            source=source[:m.start(2)]+body.replace(new,old)+source[m.end(2):]
    elif name in TEXT_ASSETS:
        old,new=json.loads((ROOT/'tests/storm_background_fit_changes.json').read_text())[name]
        assert source.count(old)+source.count(new)==1,(name,old,new)
        source=source.replace(new,old)
    return source

def verify():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+names:
        p=ROOT/name;data=without_background_fit(p.read_text(),name).encode() if name=='index.html' or name in TEXT_ASSETS else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    assert 'Math.min(w/backgroundImage.naturalWidth,h/backgroundImage.naturalHeight)' in (ROOT/'assets/storm_sky/storm_sky.js').read_text()
    assert json.loads((ROOT/'assets/storm_sky/asset_manifest.json').read_text())['background']['render_mode']=='contain'
    return {'baseline':BASE,'protected_existing_assets':len(names),'runtime_change':'Storm drawBackground scale max→min only','metadata_changes':['Storm manifest render_mode','native embedded Storm manifest','asset preparation render_mode'],'all_png_audio_bytes_unchanged':True,'all_combat_controls_world_registry_bytes_unchanged':True,'background_sha256':hashlib.sha256((ROOT/'assets/storm_sky/storm_sky_background_1920x864.png').read_bytes()).hexdigest()}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
