"""Verify one gameplay sprite replacement and capture enlarged browser comparisons."""
import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright
from reward_preservation import without_boss_reward_changes, without_reward_notice

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
baseline = '5d7c7a8721d7eec7dd257fb5ee46d8f50e060d40'
before = subprocess.check_output(['git', 'show', baseline + ':index.html'], cwd=root).decode()
after = (root / 'index.html').read_text()
old_path = root / 'backups/trio-gameplay.before-pointed-nose.png'
new_path = root / 'assets/gameplay/trio-body-pointed.png'
old_bytes, new_bytes = old_path.read_bytes(), new_path.read_bytes()
old_url = 'data:image/png;base64,' + base64.b64encode(old_bytes).decode()
new_url = 'data:image/png;base64,' + base64.b64encode(new_bytes).decode()
report = {'baseline_commit': baseline, 'passed': [], 'limits': [
    'Actual Chromium, with mobile touch/viewport emulation; physical Galaxy/Samsung Internet remains untested.',
    'Enlarged comparison canvases use the exact gameplay body draw size/rotation; actual gameplay screenshots are also supplied.'
], 'original_png_sha256': hashlib.sha256(old_bytes).hexdigest(),
    'new_png_sha256': hashlib.sha256(new_bytes).hexdigest()}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


assert report['original_png_sha256'] == '9dae3f9454696cee4c8470ff909895c22b8a546a3013c01faa58dee096cf16bd'
expected = before.replace(old_url, new_url, 1)
old_stop = "if(hp<=0){started=false;menu.classList.remove('hidden');"
new_stop = "if(hp<=0){started=false;window.gameAudioStarted=false;gameAudio.pause();menu.classList.remove('hidden');"
assert before.count(old_url) == 1 and expected.count(old_stop) == 1
assert without_boss_reward_changes(after) == expected.replace(old_stop, new_stop, 1)
for name in ['assets/selection/selection.js', 'assets/selection/selection.css'] + [str(p.relative_to(root)) for p in (root / 'assets/selection').glob('*.png')]:
    actual = without_reward_notice((root / name).read_text(), name).encode() if name.endswith(('.js', '.css')) else (root / name).read_bytes()
    assert actual == subprocess.check_output(['git', 'show', baseline + ':' + name], cwd=root)
passed('Only authorized Trio/BGM/boss-reward changes differ from the baseline; other rendering/gameplay/audio/fullscreen/exit code and image assets remain byte-identical.')

old, new = Image.open(old_path), Image.open(new_path)
assert old.size == new.size == (506, 484) and old.mode == new.mode == 'RGBA'
assert old.getchannel('A').getbbox() == new.getchannel('A').getbbox() == (6, 6, 500, 478)
outside = face = 0
for y in range(old.height):
    for x in range(old.width):
        a, b = old.getpixel((x, y)), new.getpixel((x, y))
        if a[3] == 255 and a != b:
            outside += not (60 <= x < 446 and 410 <= y <= 477)
            face += ((145 <= x <= 360 and 350 <= y <= 435) or (233 <= x <= 277 and 400 <= y <= 449))
assert outside == face == 0
widths = []
for y in [430, 440, 450, 460, 470, 476]:
    row = [x for x in range(new.width) if new.getpixel((x, y))[3] >= 128]
    widths.append(max(row) - min(row) + 1)
    assert abs((min(row) + max(row)) / 2 - 253) <= 2
assert all(a > b for a, b in zip(widths, widths[1:])) and widths[-1] <= 6
report['nose_widths_at_rows_430_440_450_460_470_476'] = widths
report['unchanged_opaque_face_and_non_nose_pixels'] = True
passed('Canvas dimensions/bounds/center are unchanged; the front narrows to a centered short point while opaque face, guns, tail and non-nose artwork pixels stay identical.')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1280, 'height': 720}, has_touch=True)
        page = context.new_page()
        errors, dialogs = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.wait_for_function('(src)=>sprites[0]?.src===src && sprites.every(im=>im.complete&&im.naturalWidth)&&rotorImages.every(im=>im.complete&&im.naturalWidth)', arg=new_url)
        page.locator('#startSelected').click()
        page.wait_for_function('started && player.type === 0')
        assert page.evaluate('player.a === Math.PI && hp === 4 && playerSpeed[0] === 265')
        page.evaluate('spawn=999; invuln=999; transition=0')
        passed('The active gameplay sprite decodes correctly; Trio still starts at 12 o’clock with the original Math.PI angle, 4 HP and speed settings.')

        alignment = page.evaluate('''() => {
            const result=[];
            for(let i=0;i<8;i++) {
                player.a=Math.PI+i*Math.PI/4;player.upgrade=0;bullets=[];shoot();
                const shot=bullets[0], a=player.a;
                const forward={x:-Math.sin(a),y:Math.cos(a)};
                result.push({angle:a,spawnX:shot.x-player.x,spawnY:shot.y-player.y,
                    vx:shot.vx,vy:shot.vy,forward,kind:shot.kind});
            }
            player.a=Math.PI;bullets=[];
            const calls=[], original=ctx.drawImage;
            ctx.drawImage=function(image,...args) {
                if(image===sprites[0]||image===rotorImages[0]) {
                    const m=this.getTransform();calls.push({kind:image===sprites[0]?'body':'rotor',args,m:[m.a,m.b,m.c,m.d,m.e,m.f]});
                }
                return original.call(this,image,...args);
            };
            try{draw()}finally{ctx.drawImage=original}
            return {directions:result,calls,center:{x:player.x,y:player.y},dpr};
        }''')
        for shot in alignment['directions']:
            for axis in ['X', 'Y']:
                unit = shot['forward'][axis.lower()]
                assert abs(shot['spawn' + axis] - unit * 19) < 1e-8
                assert abs(shot['v' + axis.lower()] - unit * 535) < 1e-8
            assert shot['kind'] == 0
        body, rotor = alignment['calls']
        assert body['args'] == [-16.33, -16.33, 32.67, 32.67]
        assert rotor['args'] == [-19, -19, 38, 38]
        # Canvas transform storage has subpixel floating-point rounding.
        assert abs(rotor['m'][4] - body['m'][4]) < 1e-4
        assert abs(rotor['m'][5] - body['m'][5] - 3.2 * alignment['dpr']) < 1e-4
        report['render_and_shot_alignment'] = alignment
        passed('At eight rotations, body-forward and original 19px projectile origins/535 speed match; actual draw calls retain body size, center and the rotor’s original local (0,-3.2) offset.')

        collision = page.evaluate('''() => {
            const hpAt=distance=>{
                player.x=W/2;player.y=H/2;hp=4;invuln=0;player.vx=player.vy=0;tilt={x:0,y:0};
                enemies=[];boss=null;bullets=[];warnings=[];
                enemyBullets=[{x:player.x+distance,y:player.y,vx:0,vy:0,life:3,r:5}];
                update(.001);return hp;
            };
            const outside=hpAt(17.1),inside=hpAt(16.9);
            invuln=999;enemyBullets=[];hp=4;
            return {outside,inside};
        }''')
        assert collision == {'outside': 4, 'inside': 3}
        passed('Real update collision checks preserve the existing 12px player projectile-hit radius: distance 17.1 is safe and 16.9 damages against a 5px enemy bullet.')

        # Review-only overlay. Product DOM/CSS/assets remain unchanged.
        page.evaluate('''async oldSource => {
            const old=new Image();old.src=oldSource;await old.decode();
            const overlay=document.createElement('div');overlay.id='trioReview';
            overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:#07192e;color:white;padding:22px;box-sizing:border-box;font-family:system-ui;text-align:center';
            overlay.innerHTML='<h1 style="margin:0 0 8px;font-size:26px">트리오 앞부분 비교 · 12시 방향</h1><p style="margin:0 0 8px;color:#c5d7eb">동일한 크기·중심·방향 · 게임 본체 12배 확대 · 윤곽 비교를 위해 프로펠러 생략</p><div style="display:flex;justify-content:center;gap:30px"></div>';
            const grid=overlay.lastElementChild;
            for(const [title,image] of [['수정 전 · 둥근 앞끝',old],['수정 후 · 중앙 삼각 꼭짓점',sprites[0]]]) {
                const figure=document.createElement('figure');figure.style.cssText='margin:0;padding:12px;border:1px solid #47708c;border-radius:16px;background:#122e45';
                const label=document.createElement('figcaption');label.textContent=title;label.style.cssText='font-size:22px;font-weight:800';
                const c=document.createElement('canvas');c.width=500;c.height=500;c.style.cssText='width:500px;height:500px;max-width:42vw';
                const t=c.getContext('2d');t.strokeStyle='#7293ad55';t.setLineDash([4,6]);t.beginPath();t.moveTo(250,12);t.lineTo(250,488);t.stroke();
                t.save();t.translate(250,250);t.scale(12,12);t.rotate(Math.PI);t.drawImage(image,-16.33,-16.33,32.67,32.67);t.restore();
                t.fillStyle='#ff83cf';t.fillRect(248,248,4,4);
                figure.append(label,c);grid.append(figure);
            }
            document.body.append(overlay);
        }''', old_url)
        page.screenshot(path=str(args.artifacts / 'trio-before-after-12-o-clock.png'))
        page.evaluate('document.getElementById("trioReview").remove()')
        page.evaluate('''() => {
            const overlay=document.createElement('div');overlay.id='trioReview';overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:#07192e;color:white;padding:20px;font-family:system-ui;text-align:center';
            overlay.innerHTML='<h1 style="margin:0;font-size:25px">회전·발사 방향·프로펠러 정렬</h1><p style="margin:8px;color:#c5d7eb">실제 본체 32.67 · 프로펠러 38 · 축 오프셋 (0, −3.2) 유지 · 노란 선은 기존 발사 방향</p><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px"></div>';
            const grid=overlay.lastElementChild;
            for(let i=0;i<8;i++) {
                const cell=document.createElement('div');const c=document.createElement('canvas');c.width=250;c.height=235;
                c.style.cssText='width:250px;height:235px;max-width:100%;display:block;margin:auto';
                const t=c.getContext('2d'),a=Math.PI+i*Math.PI/4;t.translate(125,117);t.scale(4.5,4.5);
                t.save();t.rotate(a);t.drawImage(sprites[0],-16.33,-16.33,32.67,32.67);t.translate(0,-3.2);t.rotate(.35);t.drawImage(rotorImages[0],-19,-19,38,38);t.restore();
                t.strokeStyle='#ffe16c';t.lineWidth=.8;t.beginPath();t.moveTo(-Math.sin(a)*19,Math.cos(a)*19);t.lineTo(-Math.sin(a)*25,Math.cos(a)*25);t.stroke();
                const label=document.createElement('div');label.textContent=i===0?'12시 · 시작 방향':`${i*45}° 회전`;
                cell.append(c,label);grid.append(cell);
            }
            document.body.append(overlay);
        }''')
        page.screenshot(path=str(args.artifacts / 'trio-rotation-and-rotor.png'))
        page.evaluate('document.getElementById("trioReview").remove()')
        passed('Saved enlarged before/after screenshots facing 12 o’clock and an eight-angle body/rotor/firing-direction review sheet.')

        page.set_viewport_size({'width': 915, 'height': 412})
        page.evaluate('player.a=Math.PI;player.x=W/2;player.y=H/2;rotorSpin=.35;transition=0;invuln=0;spawn=999;enemies=[];warnings=[];gameExitDialogOpen=true')
        page.evaluate('''async src=>{
            const old=new Image();old.src=src;await old.decode();
            window.reviewPointedBody=sprites[0];sprites[0]=old;draw();
        }''',old_url)
        page.screenshot(path=str(args.artifacts / 'trio-gameplay-before.png'))
        page.evaluate('sprites[0]=window.reviewPointedBody;draw()')
        page.screenshot(path=str(args.artifacts / 'trio-gameplay-landscape.png'))
        page.evaluate('gameExitDialogOpen=false;delete window.reviewPointedBody')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        for kind in range(3):
            page.locator(f'.select-hit[data-heli="{kind}"]').tap()
            page.locator('#startSelected').tap();page.wait_for_function(f'started && player.type === {kind}')
            page.evaluate('transition=0;spawn=999;invuln=999')
            if kind:
                page.screenshot(path=str(args.artifacts / f'unchanged-{["trio","bingle","tanko"][kind]}.png'))
            page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        passed('Mobile landscape gameplay, all three character starts and internal exit confirmation remain usable; unchanged Bingle/Tanko screenshots saved.')
        assert not errors and not dialogs, (errors, dialogs)
        passed('No native confirm/alert dialogs or uncaught JavaScript errors occur in the new-body browser checks.')
        browser.close()
finally:
    server.shutdown();server.server_close()

(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
