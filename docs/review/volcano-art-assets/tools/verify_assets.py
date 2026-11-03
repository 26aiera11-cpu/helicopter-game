"""Read-only PNG/atlas validation. Run from any working directory; requires Pillow/numpy."""
from pathlib import Path
import hashlib
import json
import subprocess
import zlib
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
ASSET = ROOT / 'assets/volcano'
REVIEW = ROOT / 'docs/review/volcano-art-assets'
BASE = 'b5eeb114452956786b831c5589428ceb777e052e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_crc(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', path
    offset = 8
    while offset < len(raw):
        size = int.from_bytes(raw[offset:offset+4], 'big')
        payload = raw[offset+4:offset+8+size]
        crc = int.from_bytes(raw[offset+8+size:offset+12+size], 'big')
        assert zlib.crc32(payload) & 0xffffffff == crc, path
        offset += 12 + size
    assert offset == len(raw), path
    with Image.open(path) as im:
        im.verify()


def main():
    m = json.loads((ASSET / 'asset_manifest.json').read_text())
    checks, actors = [], []
    def passed(name):
        checks.append(name)
    assert not m['game_runtime_integration']
    for p in sorted(ASSET.rglob('*.png')):
        png_crc(p)
    passed('All resource PNG chunks CRC and Pillow decode')
    bg = m['background']
    assert Image.open(ASSET / bg['path']).size == (1920, 864)
    assert sha(ASSET / bg['path']) == bg['sha256']
    assert sha(ASSET / bg['source']) == bg['source_sha256']
    assert bg['seamless'] is False
    passed('Exact background dimensions, export/source hashes, non-tiled cover metadata')
    for ref in m['references']:
        assert sha((ASSET / ref['path']).resolve()) == ref['sha256']
    passed('All four uploaded reference files preserved by hash')
    frames_total = 0
    for actor in m['monsters']:
        report = {'id':actor['id'], 'states':{}, 'warnings':[]}
        for field, hash_field, size_field in [('base','base_sha256','base_pixels'),('atlas','atlas_sha256','atlas_pixels')]:
            path = ASSET / actor[field]
            assert sha(path) == actor[hash_field]
            im = Image.open(path)
            assert im.mode == 'RGBA' and list(im.size) == actor[size_field]
            a = np.asarray(im)[:,:,3]
            assert a.min() == 0 and a.max() == 255
            assert (a == 0).mean() > 0.35
            report[field+'_alpha_1_to_7_pixels'] = int(((a > 0) & (a < 8)).sum())
            border = np.r_[a[0,:],a[-1,:],a[:,0],a[:,-1]]
            assert border.max() < 8, (actor['id'],field,'visible canvas clipping')
        a = np.asarray(Image.open(ASSET / actor['atlas']))[:,:,3]
        h,w=a.shape; covered = np.zeros((h,w),dtype=bool); indices=[]; centers=[]
        for state, animation in actor['animations'].items():
            assert animation['frame_count'] == len(animation['frames'])
            assert animation['frame_duration_ms'] > 0
            assert animation['loop'] == (state in ('idle','move'))
            stats=[]
            for frame in animation['frames']:
                x,y,fw,fh=frame['rect_px']; dx,dy,dw,dh=frame['sprite_source_rect_px']
                assert all(isinstance(n,int) for n in (x,y,fw,fh))
                assert min(x,y) >= 0 and fw>0 and fh>0 and x+fw<=w and y+fh<=h
                assert fw==dw and fh==dh and dx>=0 and dy>=0 and dx+dw<=320 and dy+dh<=320
                assert not covered[y:y+fh,x:x+fw].any(), ('overlap',actor['id'],state)
                covered[y:y+fh,x:x+fw]=True
                frame_a = a[y:y+fh,x:x+fw]; yy,xx=np.where(frame_a>=8)
                assert len(xx)>0, ('empty',actor['id'],state)
                margin=min(int(xx.min()),int(yy.min()),fw-int(xx.max())-1,fh-int(yy.max())-1)
                assert margin>=8, ('visible rect clipping',actor['id'],state,margin)
                stats.append({'index':frame['index'],'visible_pixels':len(xx),'minimum_visible_padding_px':margin})
                if state in ('idle','move'):
                    centers.append([float(dx+(xx.min()+xx.max()+1)/2),float(dy+(yy.min()+yy.max()+1)/2)])
                indices.append(frame['index']);frames_total+=1
            report['states'][state]=stats
        assert sorted(indices)==list(range(actor['frame_count']))
        assert not (a[~covered]>=8).any(), ('unmapped visible pixels',actor['id'])
        expected=[4,6,4,3,4] if actor['kind']=='boss' else [1,4,1,2,4]
        assert [x['frame_count'] for x in actor['animations'].values()]==expected
        assert actor['view']=='top_down_face_down' and actor['has_propeller'] is False
        report['idle_move_visible_center_range_px']={
            'x':[min(p[0] for p in centers),max(p[0] for p in centers)],
            'y':[min(p[1] for p in centers),max(p[1] for p in centers)],
            'note':'Visible silhouette bounds, not face/body landmarks; includes intended flame/wing/leg motion. Final micro-alignment needs visual approval.'}
        report['warnings'].append('Alpha1–7 source antialias/noise is retained; thresholds measure visible bounds only.')
        actors.append(report);passed(actor['id']+': RGBA, 5states, all frame bounds/pivots/padding/mapping/counts')
    assert frames_total == 69 and len(actors)==5
    passed('Total 69 frames / 5 distinct actors')
    changed=subprocess.check_output(['git','diff','--name-only',BASE,'--'],cwd=ROOT,text=True).splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    def allowed(p):
        return p=='DEVELOPMENT_LOG.md' or p.startswith(('assets/volcano/','docs/review/volcano-art-assets/'))
    assert all(allowed(p) for p in changed+untracked), ('out of scope',changed,untracked)
    passed('Existing game code/assets/sound/dist/test files unchanged against Ppyoko base')
    output={'passed':True,'check_groups':checks,'actors':actors,'total_frames':frames_total,'base_commit':BASE,
            'scope_checked':changed+untracked,'threshold_alpha':8,
            'limitations':['Visual reference matching/no text/no propellers/wings-up are manual review checks, not image recognition assertions.','Not a game integration, combat or physical Galaxy test.','Generated animation is a review draft, not final approved hand-keyed animation.']}
    (REVIEW / 'asset-validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'groups':len(checks),'actors':5,'frames':frames_total},ensure_ascii=False))


if __name__=='__main__':
    main()
