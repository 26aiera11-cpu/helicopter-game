"""Real touch cancellation/confirmation and restart during volcano boss art outro."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import argparse,json,shutil,threading
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
report={'passed':[],'limits':['Real Chromium touch/modal/fullscreen with controlled boss hits; not physical Galaxy.']}
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':568,'height':320},is_mobile=True,has_touch=True);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('gameVolcano.ready()&&gameSnowfield.ready()&&itemMonsters.ready()')
        page.evaluate('''()=>{
            window.lifeRewards=0;document.addEventListener('bossreward',()=>lifeRewards++);
            window.lifeDeath=()=>{lifeRewards=0;gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:5});start(0);transition=0;spawn=999;invuln=999;
              while(boss){bullets=[];shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(0);}draw();
            };
            window.lifeFrozen=()=>{const s=gameVolcano.snapshot();return {clock:s.clock,ghosts:s.ghosts,advancing:s.advancing};};
        }''')
        page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement')
        page.evaluate('lifeDeath()');page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible()
        frozen=page.evaluate('lifeFrozen()');page.wait_for_timeout(300);assert page.evaluate('lifeFrozen()')==frozen and frozen['advancing']
        page.screenshot(path=str(args.artifacts/'boss-outro-exit-568x320.png'))
        page.locator('#gameExitCancel').tap();expect(page.locator('#menu')).to_be_visible(timeout=3000)
        assert page.evaluate('!started&&runScore===2000&&lifeRewards===1&&!gameVolcano.snapshot().advancing&&gameVolcano.snapshot().ghosts.length===0&&!!document.fullscreenElement')
        report['paused_outro']=frozen;report['passed'].append('Exit modal freezes boss outro; Continue finishes the same once-only2000point/reward clear in fullscreen.')
        page.evaluate('lifeDeath()');page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!gameVolcano.snapshot().advancing&&gameVolcano.snapshot().ghosts.length===0')
        page.evaluate('gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:1});start(1);spawn=999;invuln=999;');page.wait_for_timeout(1200)
        assert page.evaluate('started&&player.type===1&&stage===5&&phase===1&&!boss&&!gameVolcano.snapshot().advancing&&menu.classList.contains("hidden")&&!!document.fullscreenElement')
        report['passed'].append('Confirm exit cancels pending advance; next Bingle run survives past old outro deadline without stale clear, ghost or fullscreen loss.')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();page.evaluate('lifeDeath();start(2);spawn=999;invuln=999;');page.wait_for_timeout(1200)
        assert page.evaluate('started&&player.type===2&&stage===5&&phase===5&&boss?.hp===20&&!gameVolcano.snapshot().advancing&&gameVolcano.snapshot().ghosts.length===0')
        assert not errors;report.update(page_errors=errors,all_passed=True)
        report['passed'].append('Defensive start during outro also cancels callback synchronously; fresh Tanko boss remains alive and new run is not terminated.')
        context.close();browser.close()
finally:
    server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS:',len(report['passed']),'boss outro lifecycle groups')
