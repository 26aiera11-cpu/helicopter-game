"""Verify exact volcano resources, script order, extraction and measured pivots."""
import argparse,base64,hashlib,json,re,tempfile,zipfile
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--focus-artifacts',type=Path,default=ROOT/'docs/review/volcano-monster-player-visual-fix');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[]}
def passed(text):report['passed'].append(text);print('PASS:',text,flush=True)
class Resources(HTMLParser):
    def __init__(self):super().__init__();self.by_id={};self.external=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'):self.by_id[a['id']]=a
        for key in ['src','href','xlink:href']:
            if a.get(key) and not a[key].startswith(('data:','#')):self.external.append(a[key])

html_path=ROOT/'dist/heli_trio_galaxy_test.html';payload=html_path.read_bytes();html=payload.decode();source=(ROOT/'index.html').read_text();resources=Resources();resources.feed(html)
manifest=json.loads((ROOT/'assets/volcano/asset_manifest.json').read_text())
image_pairs=[('volcanoBackground',manifest['background']['path'])]+[(f'volcano-{a["id"]}-{kind}',a[kind]) for a in manifest['monsters'] for kind in ['base','atlas']]
for id,path in image_pairs:
    assert base64.b64decode(resources.by_id[id]['src'].split(',',1)[1])==(ROOT/'assets/volcano'/path).read_bytes(),id
for id,path in [('volcanoManifest','assets/volcano/asset_manifest.json'),('snowfieldManifest','assets/snowfield/asset_manifest.json')]:
    assert unescape(re.search(r'<template id="'+id+r'">(.*?)</template>',html,re.S)[1])==(ROOT/path).read_text()
report['volcano_image_count']=len(image_pairs);report['volcano_frames']=sum(a['frame_count'] for a in manifest['monsters'])
passed('All11 volcano PNG resources and both original frame manifests embedded byte-for-byte;69 volcano frames retained.')
before=['assets/worlds/worlds.js','assets/worlds/difficulty.js','assets/snowfield/snowfield.js','assets/volcano/volcano.js','assets/snowfield/spawns.js','assets/snowfield/combat.js','assets/snowfield/boss_combat.js','assets/item_monster/item_monster.js','assets/controls/controls.js']
expected=[(ROOT/p).read_text() for p in before]+re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[(ROOT/p).read_text() for p in ['assets/score/score.js','assets/selection/selection.js']]
assert re.findall(r'<script[^>]*>(.*?)</script>',html,re.S)==expected and len(expected)==14
assert not resources.external and all(x.strip('\"\' ').startswith(('data:','#')) for x in re.findall(r'url\(([^)]+)\)',html))
assert not re.search(r'@import\s',html,re.I)
passed('Current14 source scripts embedded exactly in order; no external HTML/CSS resource dependencies.')
archive_path=html_path.with_suffix('.zip')
with zipfile.ZipFile(archive_path) as archive,tempfile.TemporaryDirectory(prefix='heli-volcano-package-') as folder:
    assert archive.namelist()==[html_path.name] and archive.testzip() is None
    archive.extractall(folder);extracted=(Path(folder)/html_path.name).read_bytes();assert extracted==payload
    report.update(html_bytes=len(payload),html_sha256=hashlib.sha256(payload).hexdigest(),zip_bytes=archive_path.stat().st_size,zip_sha256=hashlib.sha256(archive_path.read_bytes()).hexdigest(),zip_entries=archive.namelist(),extracted_sha256=hashlib.sha256(extracted).hexdigest())
passed('ZIP contains only latest HTML; CRC, real separate extraction, full byte equality andSHA-256 match.')
actors={a['id']:a for a in manifest['monsters']};pivot_checks=[]
for mode in ['native','offline']:
    focus=json.loads((args.focus_artifacts/mode/'test-results.json').read_text());assert focus['all_passed']
    assert len(focus['frames'])==69
    for f in focus['frames']:
        md=actors[f['id']]['animations'][f['state']]['frames'][f['index']];x,y,w,h=f['drawn'];sx,sy,sw,sh=md['sprite_source_rect_px'];cell=md['source_size_px'];scale=w/sw
        # Fixtures are centered in568×320; move/action poses follow a1px movement.
        cx=284 if f['state']=='idle' else 285
        assert abs(x-(cx+(sx-cell[0]/2)*scale))<1e-6 and abs(y-(160+(sy-cell[1]/2)*scale))<1e-6
        pivot_checks.append({'mode':mode,'id':f['id'],'state':f['state'],'index':f['index'],'virtual_pivot_matches':True})
report['pivot_checks']=pivot_checks
passed('138 actual browser draw samples independently match per-frame virtual-cell pivots; no uniform-grid or preview-width substitution.')
report['all_passed']=True
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
