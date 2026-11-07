"""Issue26 exact inverse hooks and reviewed fixed new assets; old guards stay strict."""
from storm_background_fit_preservation import without_background_fit,TEXT_ASSETS
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE='c2d03f8306557c72be7f61666198919c2412b2ae'
STORM_ASSETS=set(json.loads((ROOT/'tests/storm_sky_asset_hashes.json').read_text()))
def without_storm(source,name):
    source=without_background_fit(source,name)
    for old,new,count in reversed(json.loads((ROOT/'tests/storm_sky_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source

def assert_storm_asset(name):
    name=str(Path(name).relative_to(ROOT)) if Path(name).is_absolute() else str(name)
    assert name in STORM_ASSETS
    data=without_background_fit((ROOT/name).read_text(),name).encode() if name in TEXT_ASSETS else (ROOT/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==json.loads((ROOT/'tests/storm_sky_asset_hashes.json').read_text())[name],name

def verify():
    old_names=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'assets'],cwd=ROOT,text=True).splitlines()
    for name in ['index.html']+old_names:
        p=ROOT/name;data=without_storm(p.read_text(),name).encode() if name in ['index.html','assets/worlds/worlds.js'] else p.read_bytes()
        assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
    for name in STORM_ASSETS:assert_storm_asset(name)
    return {'base':BASE,'preserved_existing_assets':len(old_names),'reviewed_index_hooks':32,'reviewed_registry_hooks':9,'new_assets':len(STORM_ASSETS)}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
