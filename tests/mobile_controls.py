"""Native Pointer Events/CDP multitouch and baseline sensor/flight comparisons."""
import argparse
import io
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from controls_preservation import CONTROLS_ASSETS, assert_controls_asset, without_controls_changes, without_controls_ui

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'da8c0e8f58b62bf1f6061d93db72ca29cf70ca60'
parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
parser.add_argument('--standalone', action='store_true')
args = parser.parse_args();args.artifacts.mkdir(parents=True, exist_ok=True)
report = {'baseline': BASELINE, 'standalone': args.standalone, 'passed': [], 'limits': [
    'Real Chromium pointer/touch/fullscreen/media state; not physical Galaxy or Samsung Internet browser chrome.',
    'Sensor matrix dispatches controlled orientation/motion events and simulates permission results; hardware sensors/permissions remain device checks.',
    'Offline injects the actual standalone HTML; managed file:// policy is not bypassed.'
]}


def passed(message):
    report['passed'].append(message);print('PASS:', message, flush=True)


source = (ROOT / 'index.html').read_text()
assert without_controls_changes(source) == subprocess.check_output(['git', 'show', BASELINE + ':index.html'], cwd=ROOT).decode()
for path in (ROOT / 'assets').rglob('*'):
    if not path.is_file():continue
    name = str(path.relative_to(ROOT))
    if name in CONTROLS_ASSETS:assert_controls_asset(path);continue
    actual = without_controls_ui(path.read_text(), name).encode() if path.suffix in ('.js', '.css') else path.read_bytes()
    assert actual == subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S) + [(ROOT / 'assets/controls/controls.js').read_text()]:
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
passed('Seven exact control/help deltas and one exit-input reset reverse to the latest remote baseline; sensor/flight/attack, item manager, images, scores and audio stay byte-identical; syntax passes.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *unused):pass
    def do_GET(self):
        if self.path == '/controls-offline-origin':
            payload=b'<!doctype html><html lang="ko"><title>Offline test origin</title></html>'
            self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload);return
        super().do_GET()


def server(directory):
    s = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(directory)))
    threading.Thread(target=s.serve_forever, daemon=True).start();return s


class Touch:
    def __init__(self, context, page):self.cdp = context.new_cdp_session(page);self.points = {}
    def send(self, name):self.cdp.send('Input.dispatchTouchEvent', {'type': name, 'touchPoints': list(self.points.values())})
    def down(self, id, x, y):self.points[id] = {'id': id, 'x': x, 'y': y};self.send('touchStart')
    def move(self, id, x, y):self.points[id].update(x=x, y=y);self.send('touchMove')
    def up(self, id):
        # CDP touchEnd identifies the contacts being lifted, not those remaining.
        point=self.points.pop(id)
        self.cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[point]})
    def cancel(self):self.points.clear();self.send('touchCancel')


reset = '''kind => {itemMonsters.configure({opportunitiesPerRegion:0});start(kind);spawn=999;invuln=999;transition=0;fireCooldown=0;neutral={x:0,y:0};sensorOn=false;tilt={x:0,y:0};}'''
sensor_matrix = '''() => {
 const rows=[];
 for(const type of [0,1,2])for(const angle of [0,90,180,270])for(const sample of [[8,-5],[-30,21],[0,0]]){
   start(type);spawn=999;invuln=999;transition=0;Object.defineProperty(screen.orientation,'angle',{configurable:true,value:angle});
   sensorOn=true;neutral={x:0,y:0};lastSensor=0;sensorKind='';
   dispatchEvent(new DeviceOrientationEvent('deviceorientation',{gamma:sample[0],beta:sample[1]}));
   const tiltValue={...tilt};player.vx=player.vy=0;moveHelicopter(1/60);
   const velocity=[player.vx,player.vy];lastSensor=0;sensorKind='';neutral={x:0,y:0};
   const motion=new Event('devicemotion');Object.defineProperty(motion,'accelerationIncludingGravity',{value:{x:sample[0]/3,y:sample[1]/3}});dispatchEvent(motion);
   rows.push({type,angle,sample,tilt:tiltValue,velocity,gravity:{...tilt}});
 }sensorOn=false;return rows;
}'''
web = server(ROOT)
try:
    with tempfile.TemporaryDirectory(prefix='heli-controls-baseline-') as directory, sync_playwright() as p:
        archive = subprocess.check_output(['git', 'archive', BASELINE, 'index.html', 'assets'], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(directory, filter='data')
        old_web = server(directory)
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        old_context = browser.new_context(viewport={'width':915,'height':412}, is_mobile=True, has_touch=True)
        old_page = old_context.new_page();old_page.goto(f'http://127.0.0.1:{old_web.server_port}/', wait_until='load')
        old_page.wait_for_function('window.gameScoring&&window.itemMonsters?.ready()')
        old_turns = old_page.evaluate('''() => [0,1,2].map(type=>{start(type);spawn=999;invuln=999;transition=0;keys.right=true;const a=player.a;update(.2);keys.right=false;return {type,rate:(player.a-a)/.2};})''')
        old_sensors = old_page.evaluate(sensor_matrix)
        context = browser.new_context(viewport={'width':915,'height':412}, is_mobile=True, has_touch=True)
        page = context.new_page();errors, dialogs, failed, external = [], [], [], []
        if args.standalone:
            # A normal blank localhost origin exposes the native sensor interfaces;
            # disconnect before injecting the self-contained game (as in scoring).
            page.goto(f'http://127.0.0.1:{web.server_port}/controls-offline-origin',wait_until='load')
            context.set_offline(True)
            report['offline_execution']='Identical HTML injected after disconnecting a blank localhost origin; no game/resource HTTP request.'
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: (dialogs.append(d.type), d.dismiss()))
        page.on('requestfailed', lambda r: failed.append(r.url))
        page.on('request', lambda r: external.append(r.url) if args.standalone and r.url.startswith('http') else None)
        if args.standalone:page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(), wait_until='load')
        else:page.goto(f'http://127.0.0.1:{web.server_port}/', wait_until='load')
        page.wait_for_function('window.gameControls&&window.itemMonsters?.ready()&&sprites.every(i=>i.complete&&i.naturalWidth)')
        assert page.locator('#left,#right').count() == 0
        slider = page.get_by_role('slider', name='헬기 회전', include_hidden=True);expect(slider).to_have_attribute('aria-orientation','horizontal')
        expect(slider).to_be_hidden();page.locator('#startSelected').tap();expect(slider).to_be_visible()
        passed('Old rotation buttons are removed; one labelled horizontal slider appears only in play and retains the existing fire/sensor controls.')
        touch = Touch(context, page)

        def joy():
            return page.evaluate('''() => {const r=rotationJoystick.getBoundingClientRect(),inset=parseFloat(getComputedStyle(rotationJoystick).getPropertyValue('--stick-inset'));return {x:r.x+r.width/2,y:r.y+r.height/2,travel:r.width/2-inset,left:r.left,right:r.right,top:r.top,bottom:r.bottom};}''')

        page.evaluate(reset, 0);g=joy()
        for raw in [0,.04,-.04,.079,-.079]:
            touch.down(1,g['x']+raw*g['travel'],g['y']);assert page.evaluate('gameControls.rotation()') == 0;touch.up(1)
        passed('Center and jitter inside the8% dead zone produce zero rotation input.')
        matrix=[]
        for kind in range(3):
            page.evaluate(reset, kind);g=joy()
            for raw in [-1,-.75,-.5,-.25,-.08,0,.08,.25,.5,.75,1]:
                touch.down(1,g['x']+raw*g['travel'],g['y'])
                sample=page.evaluate('''() => {const before=player.a,v=gameControls.rotation();update(.2);return {input:v,delta:player.a-before,state:gameControls.snapshot()};}''')
                expected=0 if abs(raw)<=.08 else (1 if raw>0 else -1)*(abs(raw)-.08)/.92
                assert abs(sample['input']-expected)<1e-6 and abs(sample['delta']-expected*old_turns[kind]['rate']*.2)<1e-6,(raw,sample)
                matrix.append({'type':kind,'raw':raw,**sample});touch.up(1)
        report['old_max_turns']=old_turns;report['analog_matrix']=matrix
        passed('Real touch positions yield signed, smoothly remapped analog speeds; all3 full-deflection rates exactly match baseline3.05/2.7/2.35rad/s.')
        g=joy();touch.down(1,g['right']-2,g['y'])
        assert page.evaluate('gameControls.rotation()')==1
        bounds=page.evaluate('''() => {const a=rotationJoystick.getBoundingClientRect(),b=document.querySelector('.rotation-knob').getBoundingClientRect();return b.left>=a.left&&b.right<=a.right;}''');assert bounds
        touch.up(1)
        passed('Overflow beyond the track inside the control clamps to1 and keeps the round knob within its track limits.')
        touch.down(1,g['x']+g['travel']*.6,g['y']);page.wait_for_timeout(120);touch.up(1)
        angle=page.evaluate('player.a');page.wait_for_timeout(200)
        assert page.evaluate('player.a')==angle and page.evaluate('gameControls.rotation()')==0
        knob=page.locator('.rotation-knob').bounding_box();assert abs(knob['x']+knob['width']/2-g['x'])<1
        passed('Release springs only the knob to center and leaves helicopter heading unchanged.')
        touch.down(1,g['x']+g['travel'],g['y']);touch.move(1,g['right']+40,g['y'])
        assert page.evaluate('gameControls.snapshot().rotationPointer===null&&gameControls.rotation()===0');touch.up(1)
        passed('Leaving the joystick bounds ends ownership and clears rotation even before finger release outside.')
        touch.down(1,g['x']+g['travel'],g['y']);touch.cancel()
        assert page.evaluate('gameControls.snapshot().rotationPointer===null&&gameControls.rotation()===0')
        touch.down(1,g['x']+g['travel'],g['y']);page.evaluate('rotationJoystick.releasePointerCapture(gameControls.snapshot().rotationPointer)');touch.move(1,g['x'],g['y']);touch.up(1)
        assert page.evaluate('gameControls.rotation()===0')
        passed('Native touchCancel and actual lost pointer capture both reset rotation without a held input.')
        touch.down(1,g['x']-g['travel'],g['y']);touch.down(2,g['x']+g['travel'],g['y']);touch.up(2)
        owned=page.evaluate('gameControls.snapshot()');assert abs(owned['value']+1)<1e-6,owned;touch.up(1)
        passed('A second joystick finger cannot steal or release the first pointer owner.')
        f=page.locator('#fire').bounding_box();fx=f['x']+f['width']/2;fy=f['y']+f['height']/2
        touch.down(1,fx,fy);touch.down(2,fx+3,fy+3);touch.up(2);assert page.evaluate('keys.fire');touch.up(1);assert not page.evaluate('keys.fire')
        passed('Fire also has one pointer owner; releasing another finger never stops the held shot control.')
        page.evaluate(reset, 0);g=joy();x,y=page.evaluate('[W*.55,H*.5]')
        touch.down(1,x,y);touch.move(1,x+75,y);drag_id=page.evaluate('drag.id')
        touch.down(2,g['x']+g['travel'],g['y']);touch.down(3,fx,fy)
        state=page.evaluate('gameControls.snapshot()');assert len({state['rotationPointer'],state['firePointer'],state['dragPointer']})==3
        old_x,old_a=page.evaluate('[player.x,player.a]');page.wait_for_function('keys.fire&&bullets.length>0');page.wait_for_timeout(140)
        assert page.evaluate('player.x')>old_x and page.evaluate('player.a')>old_a and page.evaluate('tilt.x')==1
        touch.down(4,x-40,y-40);touch.up(4);assert page.evaluate('drag.id')==drag_id
        touch.up(2);assert page.evaluate('keys.fire&&tilt.x===1&&drag!==null');touch.up(3);assert page.evaluate('tilt.x===1&&drag!==null');touch.up(1)
        assert page.evaluate('drag===null&&tilt.x===0&&!keys.fire&&gameControls.rotation()===0')
        report['three_pointer_owners']=state
        passed('Native three-finger drag+rotation+fire moves, rotates and shoots together; unrelated fingers/releases never overwrite auxiliary movement or other owners.')
        current_sensors=page.evaluate(sensor_matrix);assert current_sensors==old_sensors
        report['sensor_matrix']=current_sensors
        passed('All36 character/orientation/sample sensor mappings, gravity fallback and actual acceleration velocities exactly match the old browser page.')
        page.evaluate(reset, 0)
        page.evaluate("DeviceOrientationEvent.requestPermission=async()=> 'granted';DeviceMotionEvent.requestPermission=async()=> 'granted'")
        page.locator('#sensor').tap();assert page.evaluate('sensorOn');page.evaluate("neutral={x:0,y:0};dispatchEvent(new DeviceOrientationEvent('deviceorientation',{gamma:8,beta:-5}))")
        g=joy();touch.down(1,g['x']+g['travel'],g['y']);touch.down(2,fx,fy)
        before=page.evaluate('({x:player.x,y:player.y,a:player.a,tilt:{...tilt}})');page.wait_for_timeout(150)
        assert page.evaluate('player.a')>before['a'] and page.evaluate('Math.hypot(player.x-'+str(before['x'])+',player.y-'+str(before['y'])+')')>0
        assert page.evaluate('drag===null&&keys.fire') and page.evaluate('tilt')==before['tilt'];touch.up(1);touch.up(2)
        assert page.evaluate('tilt')==before['tilt']
        passed('Existing sensor activation/permission path plus orientation events drives movement while separate joystick/fire fingers rotate and shoot; their releases do not clear sensor tilt.')
        page.evaluate(reset, 1);page.evaluate("DeviceOrientationEvent.requestPermission=async()=> 'denied'");page.locator('#sensor').tap()
        assert not page.evaluate('sensorOn') and '거부' in page.locator('#sensorStatus').inner_text()
        x,y=page.evaluate('[W*.5,H*.5]');touch.down(1,x,y);touch.move(1,x+75,y);assert page.evaluate('tilt.x')==1;touch.cancel();assert page.evaluate('drag===null&&tilt.x===0')
        page.evaluate('''() => {window.savedSensorAPIs=[DeviceOrientationEvent,DeviceMotionEvent];window.DeviceOrientationEvent=undefined;window.DeviceMotionEvent=undefined;sensorOn=false;lastSensor=0;}''')
        page.locator('#sensor').tap();page.wait_for_timeout(1850)
        assert '신호 없음' in page.locator('#sensorStatus').inner_text()
        touch.down(1,x,y);touch.move(1,x+75,y);assert page.evaluate('tilt.x')==1;touch.up(1)
        page.evaluate('[window.DeviceOrientationEvent,window.DeviceMotionEvent]=savedSensorAPIs')
        passed('Denied permission or absent sensor interfaces leaves the original no-signal/drag fallback usable; canvas cancellation clears only its own drag.')
        g=joy();touch.down(1,g['x']+g['travel'],g['y']);page.evaluate("dispatchEvent(new Event('blur'))");assert page.evaluate('gameControls.rotation()===0&&!keys.fire');touch.up(1)
        passed('Window blur resets held inputs without changing sensor calibration, flight constants or character heading.')
        page.evaluate('''() => {
          window.menuEvents=[];for(const n of ['contextmenu','selectstart'])document.addEventListener(n,e=>menuEvents.push({type:n,id:e.target.id,prevented:e.defaultPrevented}));
          window.testText=document.createElement('input');testText.id='unrelatedInput';testText.value='editable';testText.style='position:fixed;left:300px;top:100px';document.body.append(testText);
        }''')
        scoped=page.evaluate('''() => {
          const targets=['game','rotationJoystick','fire','hud','sensor','exitGame','unrelatedInput','leaderboardDialog'];const rows=[];
          for(const id of targets)for(const type of ['contextmenu','selectstart']){const e=new Event(type,{bubbles:true,cancelable:true});document.getElementById(id).dispatchEvent(e);rows.push({id,type,prevented:e.defaultPrevented});}
          testText.remove();return rows;
        }''')
        assert all(r['prevented']==(r['id'] not in ['unrelatedInput','leaderboardDialog']) for r in scoped)
        page.mouse.click(350,170,button='right');x,y=page.evaluate('[W*.55,H*.4]');touch.down(1,x,y);page.wait_for_timeout(1200);touch.up(1)
        assert page.evaluate('getSelection().isCollapsed')
        report['long_press_event_scope']=scoped
        passed('Game-only contextmenu/selectstart are cancelled and CSS disables selection/callout; native right-click/long-touch leaves no text selection, while real inputs/ranking stay outside the event guard.')
        page.evaluate(reset,0);g=joy();touch.down(1,g['x']+g['travel'],g['y']);page.evaluate('hp=0;update(0)')
        expect(page.locator('#gameOverOverlay')).to_be_visible();assert page.evaluate('gameControls.rotation()===0&&gameControls.snapshot().rotationPointer===null')
        touch.up(1);game_over_scope=page.evaluate('''() => {const e=new Event('selectstart',{bubbles:true,cancelable:true});gameOverScore.dispatchEvent(e);return {blocked:e.defaultPrevented,selection:getComputedStyle(gameOverScore).userSelect};}''')
        assert game_over_scope=={'blocked':True,'selection':'none'}
        page.screenshot(path=str(args.artifacts/'game-over-no-selection.png'))
        expect(page.locator('#menu')).to_be_visible(timeout=5000);assert page.evaluate('gameControls.rotation()===0')
        passed('Fatal health immediately clears joystick/fire/drag, game-over text cannot select, and the existing3-second selection return completes.')
        if not page.evaluate('!!document.fullscreenElement'):page.locator('#fullscreenToggle').tap()
        page.wait_for_function('!!document.fullscreenElement');page.locator('#startSelected').tap();page.evaluate('spawn=999;invuln=999;transition=0')
        g=joy();touch.down(1,g['x']+g['travel'],g['y']);page.locator('#exitGame').evaluate('b=>b.click()');expect(page.locator('#gameExitDialog')).to_be_visible()
        assert page.evaluate('gameControls.rotation()===0&&!!document.fullscreenElement');touch.up(1)
        page.screenshot(path=str(args.artifacts/'exit-confirm.png'));page.locator('#gameExitCancel').tap();assert page.evaluate('started&&!!document.fullscreenElement&&gameControls.rotation()===0')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!!document.fullscreenElement&&gameControls.rotation()===0')
        passed('Exit modal resets held joystick before pausing; Continue and selection return buttons work with native fullscreen preserved.')
        page.evaluate(reset,0);g=joy();touch.down(1,g['x']+g['travel'],g['y']);page.evaluate('stage=3;phase=5;nextPhase()')
        expect(page.locator('#menu')).to_be_visible();page.wait_for_function('gameControls.rotation()===0');touch.up(1)
        expect(page.locator('#leaderboardDialog')).not_to_be_visible()
        passed('Existing final-clear return also clears joystick ownership and preserves the original result flow.')
        page.evaluate('''() => {for(let i=0;i<10;i++){start(i%3);runScore=1000+i;gameScoring.finish('game_over');}started=false;window.gameAudioStarted=false;gameAudio.pause();menu.classList.remove('hidden');}''')
        page.locator('#selectionSettings').tap();expect(page.locator('#leaderboardDialog')).to_be_visible()
        scroll=page.locator('.leaderboard-scroll');box=scroll.bounding_box();assert scroll.evaluate('e=>e.scrollHeight>e.clientHeight')
        touch.down(1,box['x']+box['width']/2,box['y']+box['height']-15)
        for i in range(1,9):touch.move(1,box['x']+box['width']/2,box['y']+box['height']-15-i*15)
        touch.up(1);page.wait_for_function('document.querySelector(".leaderboard-scroll").scrollTop>0')
        report['ranking_scroll_top']=scroll.evaluate('e=>e.scrollTop');assert page.evaluate('gameControls.snapshot().rotationPointer===null&&drag===null')
        page.locator('#leaderboardClose').tap();expect(page.locator('#leaderboardDialog')).not_to_be_visible()
        passed('TOP10 opens/closes and scrolls by an actual touch swipe; the new event guard/CSS does not consume ranking gestures or leak them to gameplay.')
        for kind,(width,height) in enumerate([(915,412),(800,360),(568,320)]):
            page.set_viewport_size({'width':width,'height':height});page.wait_for_function('W===innerWidth&&H===innerHeight');page.evaluate(reset,kind);g=joy()
            assert g['left']>=0 and g['right']<width and g['top']>height*.5 and g['bottom']<=height
            f=page.locator('#fire').bounding_box();assert g['right']<f['x']
            touch.down(1,g['x']+g['travel']*.7,g['y']);page.evaluate('draw()');page.screenshot(path=str(args.artifacts/f'joystick-{width}.png'));touch.up(1)
        passed('915×412,800×360,568×320 screenshots show the blue horizontal control/round thumb without overlap with fire or HUD; source selection and art stay unchanged.')
        slider.focus();page.keyboard.down('ArrowLeft');assert page.evaluate('gameControls.rotation()')==-1;page.keyboard.up('ArrowLeft');assert page.evaluate('gameControls.rotation()')==0
        page.keyboard.down('ArrowRight');assert page.evaluate('gameControls.rotation()')==1;page.keyboard.up('ArrowRight')
        expect(slider).to_have_attribute('aria-valuenow','0')
        passed('Focusable slider exposes direction/value text and supports momentary keyboard rotation with a separate visible focus marker.')
        assert not errors and not dialogs and not failed and not external,(errors,dialogs,failed,external)
        report.update(uncaught_errors=errors,native_dialogs=dialogs,failed_resources=failed,external_requests=external)
        passed('No uncaught errors, native dialogs or failed assets; standalone controls work offline with zero external requests.')
        browser.close();old_web.shutdown()
finally:web.shutdown()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
