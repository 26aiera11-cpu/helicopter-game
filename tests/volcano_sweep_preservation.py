"""Issue21 exact sweep deltas ahead of every previous source/asset guard."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def without_volcano_sweep(source,name):
    for old,new,count in reversed(json.loads((ROOT/'tests/volcano_sweep_changes.json').read_text()).get(name,[])):
        assert source.count(new)==count,(name,source.count(new),new[:100])
        source=source.replace(new,old)
    return source
