from controls_preservation import CONTROLS_ASSETS, assert_controls_asset, without_controls_ui
from item_monster_preservation import assert_item_asset
from scoring_preservation import SCORE_ASSETS,assert_scoring_asset,without_scoring_ui
from selection_bgm_preservation import BGM_ASSET,assert_selection_bgm_asset,without_selection_bgm_changes
from progression_preservation import without_progression_changes, without_progression_ui
"""Final PNG byte identity, native aspect/anchor and actual gameplay regression."""
import argparse
import base64
import hashlib
import json
import math
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import expect, sync_playwright
from final_trio_preservation import FINAL_TRIO_ASSET, FINAL_TRIO_SHA256, assert_final_trio_asset, without_final_trio_changes
from tanko_preservation import TANKO_ASSET, assert_tanko_asset, without_tanko_restore

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args();args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
baseline = 'e12666ee90cf7e905ffa4c41de13b1c337a37641'
before = subprocess.check_output(['git', 'show', baseline + ':index.html'], cwd=root).decode()
source = (root / 'index.html').read_text()
preserved_source = without_progression_changes(source)
data = assert_final_trio_asset()
new_url = 'data:image/png;base64,' + base64.b64encode(data).decode()
old_url = 'data:image/png;base64,' + base64.b64encode((root / 'assets/gameplay/trio-body-pointed.png').read_bytes()).decode()
report = {'baseline_commit': baseline, 'final_asset': FINAL_TRIO_ASSET, 'png_sha256': FINAL_TRIO_SHA256, 'passed': [], 'limits': [
    'Actual headless Chromium and native input/fullscreen; viewport/touch emulation, not a physical Galaxy.',
    'Review enlargements replay real body/rotor draw calls; actual mobile gameplay screenshots are also provided.',
    'Speaker/sensor/performance/Android UI testing requires a physical device.'
]}


def passed(message):
    report['passed'].append(message);print('PASS:', message, flush=True)


assert without_final_trio_changes(without_tanko_restore(preserved_source)) == before
for path in (root / 'assets').rglob('*'):
    if path.is_file() and str(path.relative_to(root)) in CONTROLS_ASSETS:
        assert_controls_asset(path);continue
    if path.is_file() and str(path.relative_to(root)).startswith('assets/item_monster/'):
     assert_item_asset(path);continue
    if str(path.relative_to(root)) in SCORE_ASSETS:
     assert_scoring_asset(path);continue
    if path.is_file() and str(path.relative_to(root)) != FINAL_TRIO_ASSET:
        if str(path.relative_to(root))==BGM_ASSET:
            assert_selection_bgm_asset();continue
        if str(path.relative_to(root)) == TANKO_ASSET:
            assert_tanko_asset()
            continue
        assert (without_progression_ui(path.read_text(),str(path.relative_to(root))).encode() if path.suffix in ('.js','.css') else path.read_bytes()) == subprocess.check_output(['git', 'show', baseline + ':' + str(path.relative_to(root))], cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S):
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
passed('After reversing reviewed selection-BGM changes, only authorized Tanko combat/progression/game-over, Trio/Tanko PNG replacements and the Trio draw rectangle differ; other game/reward/audio/fullscreen/exit code and selection assets are unchanged; syntax passes.')
png = Image.open(root / FINAL_TRIO_ASSET)
assert png.size == (1402, 1122) and png.mode == 'RGBA' and png.getchannel('A').getextrema() == (0, 255)
bounds = png.getchannel('A').point(lambda value: 255 if value >= 128 else 0).getbbox()
assert bounds == (207, 20, 1195, 1075)
report['png'] = {'width': png.width, 'height': png.height, 'mode': png.mode, 'bytes': len(data), 'alpha128_bounds': bounds, 'native_ratio': png.width / png.height}
passed('The final 1402×1122 RGBA PNG matches the exact approved file hash; no image edits, cropping, resampling or square conversion are applied to the asset.')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1280, 'height': 800}, is_mobile=True, has_touch=True)
        page = context.new_page();errors=[];dialogs=[]
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.wait_for_function('src=>sprites[0]?.src===src&&sprites.every(i=>i.complete&&i.naturalWidth)&&rotorImages.every(i=>i.complete&&i.naturalWidth)', arg=new_url)
        page.locator('#startSelected').tap();page.wait_for_function('started&&player.type===0')
        assert page.evaluate('player.a===Math.PI&&hp===4&&playerSpeed[0]===265')
        page.evaluate('''() => {
            spawn=999;invuln=999;transition=0;rotorSpin=.35;
            window.captureTrio=()=>{
                const result=[],original=ctx.drawImage;
                ctx.drawImage=function(image,...args){
                    if(image===sprites[player.type]||image===rotorImages[player.type]) {
                        const m=this.getTransform();result.push({kind:image===sprites[player.type]?'body':'rotor',args,m:[m.a,m.b,m.c,m.d,m.e,m.f]});
                    }
                    return original.call(this,image,...args);
                };
                try{draw()}finally{ctx.drawImage=original}
                return {calls:result,x:player.x,y:player.y,dpr,angle:player.a};
            };
        }''')
        passed('The actual active sprite is the final PNG; Trio still starts facing 12 o’clock at Math.PI with the original HP, speed and player center.')
        capture = page.evaluate('captureTrio()')
        body, rotor = capture['calls'];x,y,width,height=body['args']
        scale = width / 1402
        assert len(body['args']) == 4 and abs(scale - height / 1122) < 1e-12
        assert abs(width / height - 1402 / 1122) < 1e-12 and width != height
        assert abs(x + 701 * scale) < 1e-9 and abs(y + 547.5 * scale) < 1e-9
        occupied_height = (bounds[3] - bounds[1]) * scale
        previous_height = 470 / 484 * 32.67
        assert abs(occupied_height - previous_height) < .1
        assert rotor['args'] == [-19, -19, 38, 38]
        assert abs(rotor['m'][4] - body['m'][4]) < 1e-4 and abs(rotor['m'][5] - body['m'][5] - 3.2 * capture['dpr']) < 1e-4
        report['draw'] = {'body_args': body['args'], 'scale_x': scale, 'scale_y': height / 1122, 'visible_height': occupied_height, 'previous_visible_height': previous_height, 'rotor_source_anchor': [(0-x)/scale,(-3.2-y)/scale]}
        passed('Actual drawing uses equal X/Y scale and the original 1.24955 ratio; visible-body center stays at the player, visible height stays within 0.1px, and the original rotor size/anchor remains unchanged.')

        directions = page.evaluate('''() => {
            const result=[];gameExitDialogOpen=true;
            for(let i=0;i<=16;i++) {
                player.a=Math.PI+i*Math.PI/8;player.upgrade=0;bullets=[];shoot();
                const shot=bullets[0];result.push({i,a:player.a,shot:{dx:shot.x-player.x,dy:shot.y-player.y,vx:shot.vx,vy:shot.vy},...captureTrio()});
            }
            window.trioReviewCaptures=result;player.a=Math.PI;bullets=[];gameExitDialogOpen=false;return result;
        }''')
        for value in directions:
            a, shot = value['a'], value['shot']
            for actual, expected in [(shot['dx'], -math.sin(a)*19),(shot['dy'], math.cos(a)*19),(shot['vx'], -math.sin(a)*535),(shot['vy'], math.cos(a)*535)]:
                assert abs(actual-expected)<1e-8
            matrix=value['calls'][0]['m']
            assert abs(math.hypot(matrix[0],matrix[1])-math.hypot(matrix[2],matrix[3]))<1e-6
        report['rotation_samples']=[{'degrees':v['i']*22.5,'angle':v['a'],'shot':v['shot']} for v in directions]
        passed('Seventeen samples across a full 360° keep uniform image scale, circular gun proportions and the original forward 19px muzzle/535 projectile direction, including the 12 o’clock start and full-turn endpoint.')

        page.evaluate('''async oldSource=>{
            const old=new Image();old.src=oldSource;await old.decode();const current=captureTrio(),call=current.calls[0];
            const overlay=document.createElement('div');overlay.id='trioReview';overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:#07192e;color:white;padding:22px;font-family:system-ui;text-align:center';
            overlay.innerHTML='<h1 style="margin:0;font-size:26px">트리오 최종 PNG 적용 · 12시 방향</h1><p style="color:#c5d7eb">동일한 플레이어 중심과 보이는 높이 · 12배 확대 · 본체 윤곽 비교를 위해 날개 생략</p><div style="display:flex;justify-content:center;gap:24px"></div>';
            const grid=overlay.lastElementChild;
            for(const [title,image,args] of [['적용 전',old,[-16.33,-16.33,32.67,32.67]],['최종 PNG · 원본 비율 유지',sprites[0],call.args]]) {
                const cell=document.createElement('div');cell.innerHTML='<p style="font-size:20px;font-weight:800">'+title+'</p>';
                const c=document.createElement('canvas');c.width=540;c.height=540;c.style.cssText='width:540px;height:540px;max-width:43vw;background:#122e45;border-radius:16px';
                const t=c.getContext('2d');t.setTransform(12/current.dpr,0,0,12/current.dpr,270-12*current.x,270-12*current.y);t.transform(...call.m);t.drawImage(image,...args);t.resetTransform();t.fillStyle='#ff83cf';t.fillRect(268,268,4,4);
                cell.append(c);grid.append(cell);
            }
            document.body.append(overlay);
        }''',old_url)
        page.screenshot(path=str(args.artifacts/'trio-final-before-after-12.png'))
        page.evaluate('document.getElementById("trioReview").remove()')
        page.evaluate('''() => {
            const overlay=document.createElement('div');overlay.id='trioReview';overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:#07192e;color:white;padding:20px;font-family:system-ui;text-align:center';
            overlay.innerHTML='<h1 style="margin:0;font-size:25px">최종 트리오 · 360° 회전·프로펠러·발사 방향</h1><p style="color:#c5d7eb">실제 draw 호출 재생 · 노란 선은 기존 발사 방향 · 정사각형 변형 없음</p><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px"></div>';
            const grid=overlay.lastElementChild;
            for(let i=0;i<=16;i+=2) {
                const shot=trioReviewCaptures[i],cell=document.createElement('div'),c=document.createElement('canvas');c.width=250;c.height=180;c.style.cssText='display:block;width:250px;height:180px;max-width:100%;margin:auto';
                const t=c.getContext('2d'),scale=3.8;
                for(const call of shot.calls){t.setTransform(scale/shot.dpr,0,0,scale/shot.dpr,125-scale*shot.x,90-scale*shot.y);t.transform(...call.m);t.drawImage(call.kind==='body'?sprites[0]:rotorImages[0],...call.args)}
                t.setTransform(scale,0,0,scale,125,90);t.strokeStyle='#ffe16c';t.lineWidth=.6;t.beginPath();t.moveTo(shot.shot.dx,shot.shot.dy);t.lineTo(shot.shot.dx*1.22,shot.shot.dy*1.22);t.stroke();
                const label=document.createElement('div');label.textContent=i===0?'12시 · 시작':i*22.5+'°';cell.append(c,label);grid.append(cell);
            }
            document.body.append(overlay);
        }''')
        page.screenshot(path=str(args.artifacts/'trio-final-360.png'))
        page.evaluate('document.getElementById("trioReview").remove()')

        page.set_viewport_size({'width':915,'height':412})
        page.evaluate('spawn=999;invuln=999;transition=0;player.a=Math.PI;bullets=[];fireCooldown=0')
        cdp=context.new_cdp_session(page)
        def hold(control,condition):
            box=page.locator('#'+control).bounding_box();cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+(box['width']-26 if control=='rotationJoystick' else box['width']/2),'y':box['y']+box['height']/2,'id':1}]})
            page.wait_for_function(condition,timeout=15000);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        old_spin=page.evaluate('rotorSpin')
        hold('rotationJoystick','player.a>=Math.PI+Math.PI*2')
        assert page.evaluate('rotorSpin')>old_spin
        page.evaluate('player.a=Math.PI;bullets=[];fireCooldown=0')
        hold('fire','bullets.length>0')
        assert page.evaluate('bullets.every(b=>b.kind===0&&Math.abs(b.vx)<1e-8&&b.vy<0)')
        passed('Actual held touch rotates through a full 360° while the rotor keeps animating; releasing and firing at 12 o’clock retains the original upward projectiles.')

        collision=page.evaluate('''() => {
            const test=distance=>{hp=4;invuln=0;player.x=W/2;player.y=H/2;player.vx=player.vy=0;tilt={x:0,y:0};enemies=[];warnings=[];bullets=[];boss=null;
                enemyBullets=[{x:player.x+distance,y:player.y,vx:0,vy:0,life:3,r:5}];update(.001);return hp};
            const outside=test(17.1),inside=test(16.9);hp=4;invuln=999;enemyBullets=[];return {outside,inside};
        }''')
        assert collision=={'outside':4,'inside':3}
        passed('The original hit radius remains independent of the visual rectangle: a 5px enemy bullet at 17.1px is safe and at 16.9px damages Trio.')

        for width,height in [(915,412),(800,360),(568,320)]:
            page.set_viewport_size({'width':width,'height':height})
            page.evaluate('player.a=Math.PI;player.x=W/2;player.y=H/2;rotorSpin=.35;invuln=0;spawn=999;transition=0;bullets=[];enemyBullets=[];enemies=[];warnings=[]')
            page.screenshot(path=str(args.artifacts/f'trio-final-gameplay-{width}.png'))
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        for kind,name in [(1,'bingle'),(2,'tanko')]:
            page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();page.wait_for_function(f'started&&player.type==={kind}')
            result=page.evaluate('transition=0;invuln=0;spawn=999;captureTrio()')
            assert result['calls'][0]['args']==[-16.33,-16.33,32.67,32.67]
            page.screenshot(path=str(args.artifacts/f'unchanged-{name}.png'))
            page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        passed('Bingle and Tanko retain their exact original draw rectangle; Bingle PNG stays unchanged and the approved Tanko restoration is isolated; gameplay and exit flows remain usable.')
        assert not errors and not dialogs,(errors,dialogs)
        passed('Saved enlarged before/after, nine-angle rotation and three mobile landscape gameplay screenshots; no native dialogs or uncaught JavaScript errors.')
        browser.close()
finally:server.shutdown();server.server_close()

(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
