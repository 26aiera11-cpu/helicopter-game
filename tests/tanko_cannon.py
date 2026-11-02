from item_monster_preservation import assert_item_asset
from scoring_preservation import SCORE_ASSETS,assert_scoring_asset,without_scoring_ui
from selection_bgm_preservation import BGM_ASSET,assert_selection_bgm_asset,without_selection_bgm_changes
from progression_preservation import without_progression_changes, without_progression_ui
"""Provided Tanko PNG identity and actual eight-direction gameplay rendering."""
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
from tanko_preservation import TANKO_ASSET, TANKO_BACKUP, TANKO_SHA256, TANKO_OLD_SHA256, assert_tanko_asset, without_tanko_restore

parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True)
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[1]
baseline='08f3bd87cde0bccd09f6a9ad31c46c0bc1ad34df'
source=(root/'index.html').read_text()
preserved_source=without_progression_changes(source)
original=subprocess.check_output(['git','show',baseline+':index.html'],cwd=root).decode()
assert without_tanko_restore(preserved_source)==original
for path in (root/'assets').rglob('*'):
    if path.is_file() and str(path.relative_to(root)).startswith('assets/item_monster/'):
     assert_item_asset(path);continue
    if str(path.relative_to(root)) in SCORE_ASSETS:
     assert_scoring_asset(path);continue
    if path.is_file() and str(path.relative_to(root))!=TANKO_ASSET:
        if str(path.relative_to(root))==BGM_ASSET:
            assert_selection_bgm_asset();continue
        assert (without_progression_ui(path.read_text(),str(path.relative_to(root))).encode() if path.suffix in ('.js','.css') else path.read_bytes())==subprocess.check_output(['git','show',baseline+':'+str(path.relative_to(root))],cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S):
    subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
report={'baseline_commit':baseline,'passed':[],'provided_png_sha256':TANKO_SHA256,'previous_png_sha256':TANKO_OLD_SHA256,'limits':[
    'Actual headless Chromium with native fullscreen/input; mobile viewport/touch emulation is not physical Galaxy/Samsung Internet.',
    'Review enlargements replay real body/rotor draw calls; health/aim are controlled for reproducible screenshots.',
    'Physical sensors, audible output, Android UI and device performance require device checks.'
]}


def passed(message):
    report['passed'].append(message);print('PASS:',message,flush=True)


passed('After reversing reviewed selection-BGM changes, after undoing the exact reviewed progression and Tanko combat deltas, the entire index differs only by gameplayHeliImages[2] PNG bytes; all rendering, rotation, propeller, movement, player collision, Trio/Bingle and selection assets are unchanged; syntax passes.')
new=Image.open(root/TANKO_ASSET);old=Image.open(root/TANKO_BACKUP)
assert new.size==old.size==(503,490) and new.mode==old.mode=='RGBA'
assert new.getchannel('A').getbbox()==old.getchannel('A').getbbox()==(6,6,497,484)
visible_outside=hidden_rgb_outside=restored=0
for y in range(new.height):
    for x in range(new.width):
        a,b=old.getpixel((x,y)),new.getpixel((x,y))
        in_roi=6<=x<90 and 365<=y<442
        if in_roi and a[3]<128<=b[3]:restored+=1
        if not in_roi and a!=b:
            if a[3] or b[3]:visible_outside+=1
            else:hidden_rgb_outside+=1
assert visible_outside==0 and restored>0
report['png']={'width':503,'height':490,'mode':'RGBA','alpha_bounds':[6,6,497,484],'bytes':len(assert_tanko_asset()),'visible_outside_roi_differences':visible_outside,'transparent_hidden_rgb_differences_in_supplied_file':hidden_rgb_outside,'restored_opaque_pixels':restored,'cannon_roi':[6,365,90,442]}
passed('The supplied PNG is byte-identical to the approved hash and retains the original size/alpha bounds; visible changes are limited to the left cannon ROI. Hidden RGB differences in fully transparent supplied pixels do not affect rendering.')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1280,'height':800},is_mobile=True,has_touch=True)
        page=context.new_page();errors=[];dialogs=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('dialog',lambda dialog:(dialogs.append(dialog.type),dialog.dismiss()))
        page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
        uri='data:image/png;base64,'+base64.b64encode(assert_tanko_asset()).decode()
        page.wait_for_function('src=>sprites[2]?.src===src&&sprites.every(i=>i.complete&&i.naturalWidth)&&rotorImages.every(i=>i.complete&&i.naturalWidth)',arg=uri)
        page.locator('.select-hit[data-heli="2"]').tap();page.locator('#startSelected').tap()
        page.wait_for_function('started&&player.type===2&&!!document.fullscreenElement')
        assert page.evaluate('player.a===Math.PI&&hp===9&&playerSpeed[2]===204')
        page.evaluate('''() => {
            spawn=999;invuln=999;transition=0;rotorSpin=.35;
            window.captureTanko=()=>{
                const calls=[],original=ctx.drawImage;
                ctx.drawImage=function(image,...args){
                    if(image===sprites[2]||image===rotorImages[2]){const m=this.getTransform();calls.push({kind:image===sprites[2]?'body':'rotor',args,m:[m.a,m.b,m.c,m.d,m.e,m.f]})}
                    return original.call(this,image,...args);
                };
                try{draw()}finally{ctx.drawImage=original}
                return {calls,x:player.x,y:player.y,dpr};
            };
        }''')
        passed('The actual active Tanko sprite loads the supplied 503×490 PNG and starts in native fullscreen at 12 o’clock with the original 9 HP and speed 204.')

        samples=page.evaluate('''() => {
            const result=[];gameExitDialogOpen=true;
            for(let i=0;i<8;i++){
                player.a=Math.PI+i*Math.PI/4;player.upgrade=0;bullets=[];shoot();
                const b=bullets[0],capture=captureTanko();
                const body=new DOMMatrix(capture.calls[0].m),rotor=new DOMMatrix(capture.calls[1].m),local=body.inverse().multiply(rotor);
                const cannon=body.transformPoint(new DOMPoint(-16.33+(6+90)/2/503*32.67,-16.33+(365+442)/2/490*32.67));
                result.push({i,a:player.a,...capture,rotorLocal:[local.e,local.f],cannonCenter:[cannon.x,cannon.y],shot:{dx:b.x-player.x,dy:b.y-player.y,vx:b.vx,vy:b.vy,kind:b.kind,damage:b.damage,pierce:b.pierce}});
            }
            window.tankoSamples=result;player.a=Math.PI;bullets=[];gameExitDialogOpen=false;return result;
        }''')
        for value in samples:
            assert value['calls'][0]['args']==[-16.33,-16.33,32.67,32.67]
            assert value['calls'][1]['args']==[-19,-19,38,38]
            assert abs(value['rotorLocal'][0])<1e-4 and abs(value['rotorLocal'][1]+3.2)<1e-4
            for actual,expected in [(value['shot']['dx'],-math.sin(value['a'])*19),(value['shot']['dy'],math.cos(value['a'])*19),(value['shot']['vx'],-math.sin(value['a'])*410),(value['shot']['vy'],math.cos(value['a'])*410)]:assert abs(actual-expected)<1e-8
            assert value['shot']['kind']==2 and value['shot']['damage']==1.5 and value['shot']['pierce']==2
            assert value['cannonCenter'][0]>30 and value['cannonCenter'][1]>30
        report['eight_direction_draws']=samples
        passed('Eight actual draw samples preserve the exact body/rotor rectangles, center/axis and 19px muzzle/410 projectile direction; left-cannon coordinates rotate with the body without cropping.')

        old_url='data:image/png;base64,'+base64.b64encode((root/TANKO_BACKUP).read_bytes()).decode()
        page.evaluate('''async oldSource=>{
            const old=new Image();old.src=oldSource;await old.decode();const shot=tankoSamples[0],call=shot.calls[0];
            const overlay=document.createElement('div');overlay.id='tankoReview';overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:#07192e;color:white;padding:20px;font-family:system-ui;text-align:center';
            overlay.innerHTML='<h1 style="margin:0">탱코 기관포 복원 · 같은 크기·중심·12시 방향</h1><p style="color:#c5d7eb">원본 기준 왼쪽 기관포가 기체와 함께 회전 · 청록 표시가 복원 영역 · 본체 12배 확대</p><div style="display:flex;justify-content:center;gap:24px"></div>';
            for(const [title,image] of [['적용 전',old],['제공 복원 PNG',sprites[2]]]){
                const cell=document.createElement('div');cell.innerHTML='<p style="font-size:20px;font-weight:800">'+title+'</p>';
                const c=document.createElement('canvas');c.width=540;c.height=540;c.style.cssText='width:540px;height:540px;max-width:43vw;background:#122e45;border-radius:16px';
                const t=c.getContext('2d');t.setTransform(12/shot.dpr,0,0,12/shot.dpr,270-12*shot.x,270-12*shot.y);t.transform(...call.m);t.drawImage(image,...call.args);
                t.strokeStyle='#63fff5';t.lineWidth=.12;t.strokeRect(-16.33+6/503*32.67,-16.33+365/490*32.67,84/503*32.67,77/490*32.67);
                cell.append(c);overlay.lastElementChild.append(cell);
            }
            document.body.append(overlay);
        }''',old_url)
        page.screenshot(path=str(args.artifacts/'tanko-cannon-before-after.png'));page.evaluate('document.getElementById("tankoReview").remove()')
        page.evaluate('''() => {
            const overlay=document.createElement('div');overlay.id='tankoReview';overlay.style.cssText='position:fixed;inset:0;z-index:1000;background:#07192e;color:white;padding:20px;font-family:system-ui;text-align:center';
            overlay.innerHTML='<h1 style="margin:0">탱코 복원 기관포 · 8방향 실제 draw 확인</h1><p style="color:#c5d7eb">기존 본체·프로펠러 크기와 축 유지 · 청록 표시: 원본 왼쪽 기관포</p><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px"></div>';
            for(const shot of tankoSamples){
                const cell=document.createElement('div'),c=document.createElement('canvas');c.width=280;c.height=250;c.style.cssText='display:block;width:280px;height:250px;max-width:100%;margin:auto';
                const t=c.getContext('2d'),scale=5;
                for(const call of shot.calls){t.setTransform(scale/shot.dpr,0,0,scale/shot.dpr,140-scale*shot.x,125-scale*shot.y);t.transform(...call.m);t.drawImage(call.kind==='body'?sprites[2]:rotorImages[2],...call.args)}
                t.setTransform(scale/shot.dpr,0,0,scale/shot.dpr,140-scale*shot.x,125-scale*shot.y);t.transform(...shot.calls[0].m);t.strokeStyle='#63fff5';t.lineWidth=.2;t.strokeRect(-16.33+6/503*32.67,-16.33+365/490*32.67,84/503*32.67,77/490*32.67);
                const label=document.createElement('div');label.textContent=shot.i===0?'12시 · 시작':shot.i*45+'°';cell.append(c,label);overlay.lastElementChild.append(cell);
            }
            document.body.append(overlay);
        }''')
        page.screenshot(path=str(args.artifacts/'tanko-cannon-eight-directions.png'));page.evaluate('document.getElementById("tankoReview").remove()')
        passed('Saved enlarged before/after and eight-angle screenshots replaying real body/propeller draw calls, with the restored anatomical-left cannon region marked only in review overlays.')

        page.set_viewport_size({'width':915,'height':412})
        page.evaluate('player.x=W/2;player.y=H/2;player.a=Math.PI;player.vx=player.vy=0;tilt={x:0,y:0};transition=0;invuln=0;spawn=999;worldScroll=0;rotorSpin=.35;bullets=[];enemyBullets=[];enemies=[];warnings=[];items=[];gameExitDialogOpen=true')
        page.evaluate('''async src=>{const old=new Image();old.src=src;await old.decode();window.restoredTanko=sprites[2];sprites[2]=old;draw()}''',old_url)
        page.screenshot(path=str(args.artifacts/'tanko-gameplay-before.png'))
        page.evaluate('sprites[2]=window.restoredTanko;draw()')
        page.screenshot(path=str(args.artifacts/'tanko-gameplay-after.png'))
        page.evaluate('gameExitDialogOpen=false;delete window.restoredTanko;invuln=999')
        cdp=context.new_cdp_session(page)
        def hold(control,condition):
            box=page.locator('#'+control).bounding_box();cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':box['x']+box['width']/2,'y':box['y']+box['height']/2,'id':1}]});page.wait_for_function(condition,timeout=15000);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        old_spin=page.evaluate('rotorSpin');hold('right','player.a>Math.PI+.4');assert page.evaluate('rotorSpin')>old_spin
        page.evaluate('player.a=Math.PI;bullets=[];fireCooldown=0');hold('fire','bullets.length>0')
        assert page.evaluate('bullets.every(b=>b.kind===2&&Math.abs(b.vx)<1e-8&&b.vy<0)')
        x,y=page.evaluate('[W/2,H/2]');old_x=page.evaluate('player.x')
        cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+75,'y':y,'id':1}]});page.wait_for_function('x=>player.x>x+4',arg=old_x);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        passed('Actual mobile touch rotation, rotor animation, upward Tanko fire and drag movement remain usable at the existing gameplay size.')

        collision=page.evaluate('''() => {
            const test=d=>{player.x=W/2;player.y=H/2;player.vx=player.vy=0;tilt={x:0,y:0};hp=9;invuln=0;bullets=[];enemies=[];warnings=[];boss=null;enemyBullets=[{x:player.x+d,y:player.y,vx:0,vy:0,life:3,r:5}];update(.001);return hp};
            const outside=test(17.1),inside=test(16.9);hp=9;invuln=999;enemyBullets=[];return {outside,inside};
        }''')
        assert collision=={'outside':9,'inside':8}
        report['collision']=collision
        passed('The unchanged player hit radius still rejects a 5px enemy bullet at 17.1px and accepts it at 16.9px, with Tanko health 9→8.')
        for width,height in [(800,360),(568,320)]:
            page.set_viewport_size({'width':width,'height':height});page.evaluate('player.x=W/2;player.y=H/2;player.a=Math.PI;invuln=0;spawn=999;transition=0;bullets=[];warnings=[];enemies=[]')
            page.screenshot(path=str(args.artifacts/f'tanko-gameplay-{width}.png'))
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!!document.fullscreenElement')
        assert page.evaluate('src=>sprites[2].src===src',uri)
        assert not errors and not dialogs,(errors,dialogs)
        passed('Three mobile landscape sizes and fullscreen exit-to-selection pass; the restored sprite remains active, with no native dialogs or uncaught JS errors.')
        browser.close()
finally:server.shutdown();server.server_close()

(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
