"""Real Chromium fullscreen transitions plus simulated unsupported/denied paths."""
import argparse
import json
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

parser=argparse.ArgumentParser()
parser.add_argument('--artifacts',type=Path,required=True)
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[1]
report={'passed':[],'limits':['Headless Chromium with real standard Fullscreen API; physical Galaxy Chrome/Samsung Internet address-bar behavior and permissions require device testing.']}


def passed(message):
    report['passed'].append(message);print('PASS:',message,flush=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('dialog',lambda dialog:(errors.append('Unexpected native dialog: '+dialog.type),dialog.dismiss()))
        url=f'http://127.0.0.1:{server.server_port}/'
        page.goto(url,wait_until='load')
        assert page.evaluate('document.fullscreenEnabled&&!document.fullscreenElement')
        toggle=page.locator('#fullscreenToggle')
        expect(toggle).to_be_visible();expect(toggle).to_have_attribute('aria-pressed','false')
        passed('Selection screen provides a small fullscreen control and does not request fullscreen automatically.')
        toggle.tap();page.wait_for_function('document.fullscreenElement===document.documentElement')
        expect(toggle).to_have_attribute('aria-pressed','true')
        report['real_fullscreen_entry']=page.evaluate('({active:!!document.fullscreenElement,width:innerWidth,height:innerHeight})')
        page.screenshot(path=str(args.artifacts/'fullscreen-selection.png'))
        passed('A real touch gesture enters native document-element fullscreen from the selection screen.')

        for kind in range(3):
            page.locator(f'.select-hit[data-heli="{kind}"]').tap()
            assert page.evaluate('!!document.fullscreenElement')
        page.locator('#startSelected').tap();page.wait_for_function('started&&player.type===2')
        assert page.evaluate('!!document.fullscreenElement&&hp===9')
        controls=page.evaluate('''() => {
            const r=id=>{const b=document.getElementById(id).getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,right:b.right,bottom:b.bottom}};
            return {full:r('fullscreenToggle'),exit:r('exitGame'),hud:r('hud'),fire:r('fire'),right:r('right'),W,H};
        }''')
        assert controls['hud']['right']<=controls['full']['x'] and controls['full']['right']<controls['exit']['x']
        for key in ['full','fire','right']:
            b=controls[key];assert b['x']>=0 and b['y']>=0 and b['right']<=controls['W']+1 and b['bottom']<=controls['H']+1
        cdp=context.new_cdp_session(page)
        def hold(id,condition):
            b=page.locator('#'+id).bounding_box()
            cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':b['x']+b['width']/2,'y':b['y']+b['height']/2,'id':1}]})
            page.wait_for_function(condition)
            cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        angle=page.evaluate('player.a')
        hold('right',f'player.a>{angle}+.1')
        hold('fire','bullets.length>0')
        page.screenshot(path=str(args.artifacts/'fullscreen-gameplay.png'))
        passed('Character selection and game start retain fullscreen; touch rotation/fire work and the fullscreen control does not overlap HUD/exit controls.')

        toggle.tap();page.wait_for_function('!document.fullscreenElement')
        assert page.evaluate('started&&player.type===2')
        toggle.tap();page.wait_for_function('!!document.fullscreenElement')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!!document.fullscreenElement&&!started')
        toggle.tap();page.wait_for_function('!document.fullscreenElement')
        expect(toggle).to_have_attribute('aria-pressed','false')
        passed('Exit/re-enter fullscreen during play preserves the game; returning to selection keeps fullscreen; the selection control exits it normally.')

        for width,height in [(915,412),(800,360),(568,320),(1024,768)]:
            page.set_viewport_size({'width':width,'height':height})
            toggle.tap();page.wait_for_function('!!document.fullscreenElement')
            assert page.locator('.character-details').evaluate_all('els=>els.every(e=>e.scrollHeight<=e.clientHeight&&e.scrollWidth<=e.clientWidth)')
            box=toggle.bounding_box();assert box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width
            assert page.locator('.heli-stage').count()==3 and page.locator('.podium-light').count()==3
            if width==800:page.screenshot(path=str(args.artifacts/'fullscreen-compact.png'))
            toggle.tap();page.wait_for_function('!document.fullscreenElement')
        page.set_viewport_size({'width':412,'height':915})
        expect(page.locator('#rotateNotice')).to_be_visible()
        passed('Four landscape aspect ratios retain controls, panel fit and selection effects in fullscreen; portrait rotation notice remains intact.')

        for mode in ['unsupported','denied']:
            fallback=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
            patch = "undefined" if mode=='unsupported' else "function(){return Promise.reject(new DOMException('Denied for test','NotAllowedError'))}"
            fallback.add_init_script('''(() => {
                for(const proto of [Element.prototype,HTMLElement.prototype]) {
                    Object.defineProperty(proto,'requestFullscreen',{configurable:true,value:''' + patch + '''});
                    Object.defineProperty(proto,'webkitRequestFullscreen',{configurable:true,value:undefined});
                }
            })()''')
            other=fallback.new_page();other.on('pageerror',lambda error:errors.append(str(error)))
            other.on('dialog',lambda dialog:(errors.append('Unexpected native dialog: '+dialog.type),dialog.dismiss()));other.goto(url,wait_until='load')
            if mode=='unsupported':expect(other.locator('#fullscreenToggle')).to_be_disabled()
            else:
                other.locator('#fullscreenToggle').tap()
                expect(other.locator('#fullscreenStatus')).to_contain_text('현재 화면에서 계속',timeout=5000)
                expect(other.locator('#fullscreenToggle')).to_be_enabled()
            other.locator('#startSelected').tap();other.wait_for_function('started&&player.type===0')
            assert other.evaluate('!document.fullscreenElement&&hp===4')
            other.locator('#exitGame').tap();other.locator('#gameExitConfirm').tap();expect(other.locator('#menu')).to_be_visible()
            fallback.close()
        passed('Simulated unsupported and rejected API paths allow normal-screen game start/return without crashes or automatic retry loops.')
        assert not errors,errors
        passed('No uncaught JavaScript errors; no browser policy, security flags or fullscreen permissions were bypassed.')
        browser.close()
finally:
    server.shutdown();server.server_close()

(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
