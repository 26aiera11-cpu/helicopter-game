"""Issue17 approved two-species art and two player-loader deltas only."""
import hashlib,json
from pathlib import Path
from volcano_combat_preservation import COMBAT_ASSETS,assert_volcano_combat_asset,without_volcano_combat

ROOT=Path(__file__).resolve().parents[1]
VISUAL_FIX_ASSETS=set(json.loads((ROOT/'tests/visual_fix_asset_hashes.json').read_text()))|COMBAT_ASSETS

def assert_visual_fix_asset(path):
    name=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
    if name in COMBAT_ASSETS:assert_volcano_combat_asset(path);return
    assert name in VISUAL_FIX_ASSETS
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==json.loads((ROOT/'tests/visual_fix_asset_hashes.json').read_text())[name],name

def without_visual_fix_asset(source,name):
    source=without_volcano_combat(source,name)
    if name=='index.html':
        assert_visual_fix_asset('assets/volcano/asset_manifest.json')
        current=(ROOT/'assets/volcano/asset_manifest.json').read_text()
        old=(ROOT/'tests/visual_fix_manifest_before.json').read_text()
        new_tag='<template id="volcanoManifest">'+current+'</template>'
        assert source.count(new_tag)==1,'Exact updated volcano template'
        source=source.replace(new_tag,'<template id="volcanoManifest">'+old+'</template>',1)
        for before,after,count in reversed(json.loads((ROOT/'tests/visual_fix_changes.json').read_text())):
            assert source.count(after)==count,(source.count(after),after[:100])
            source=source.replace(after,before)
    return source
