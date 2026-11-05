"""Issue20 exact reversible deltas; do not relax any historical protected bytes."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BREATH_ASSETS={'assets/volcano/effects/magma_dragon_breath_static.png'}
def without_volcano_breath(source,name):
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_breath_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source
def assert_volcano_breath_asset(name):
    assert name in BREATH_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()=='a9600ff8d4c827d8d5ac200c5c508ff636d008398ec985a5fb259c65913fa979'
