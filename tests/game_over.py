from controls_preservation import CONTROLS_ASSETS, assert_controls_asset, without_controls_ui
from item_monster_preservation import assert_item_asset
from scoring_preservation import SCORE_ASSETS,assert_scoring_asset,without_scoring_ui
from selection_bgm_preservation import BGM_ASSET,assert_selection_bgm_asset,without_selection_bgm_changes
"""Actual three-second last-frame lifecycle, input, audio and stale-result regression."""
import argparse,json,shutil,threading,hashlib,subprocess
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from progression_preservation import without_progression_changes,without_progression_ui
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'limits':['Native Chromium fullscreen and touch emulation; physical Galaxy, Samsung Internet and speaker listening are not tested.']}
def passed(message):report['passed'].append(message);print('PASS:',message,flush=True)
source=(root/'index.html').read_text()
assert without_progression_changes(source).encode()==subprocess.check_output(['git','show','9c3c5a8:index.html'],cwd=root)
for path in (root/'assets').rglob('*'):
 if path.is_file() and str(path.relative_to(root)) in CONTROLS_ASSETS:
     assert_controls_asset(path);continue
 if path.is_file() and str(path.relative_to(root)).startswith('assets/item_monster/'):
  assert_item_asset(path);continue
 if str(path.relative_to(root)) in SCORE_ASSETS:
  assert_scoring_asset(path);continue
 if path.is_file():
  if str(path.relative_to(root))==BGM_ASSET:
   assert_selection_bgm_asset();continue
  name=str(path.relative_to(root));actual=without_progression_ui(path.read_text(),name).encode() if path.suffix in ('.js','.css') else path.read_bytes()
  assert actual==subprocess.check_output(['git','show','9c3c5a8:'+name],cwd=root)
passed('After reversing reviewed selection-BGM changes, reviewed Tanko combat and progression deltas are the only source/UI differences from 9c3c5a8; all images/audio and unrelated behavior remain byte-identical.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
  page=context.new_page();errors=[];dialogs=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load')
  page.locator('#startSelected').tap();page.wait_for_function('started&&!!document.fullscreenElement')
  page.evaluate('spawn=999;transition=0;runScore=3700;window.deathAt=0;window.returnAt=0;window.deathEvents=0;document.addEventListener("gameover",()=>{deathAt=performance.now();deathEvents++});new MutationObserver(()=>{if(!menu.classList.contains("hidden"))returnAt=performance.now()}).observe(menu,{attributes:true,attributeFilter:["class"]})')
  # Lethal actual collision, plus a collocated heal that must not revive the player.
  page.evaluate('''() => {hp=1;invuln=0;items=[{x:player.x,y:player.y,type:'hp',life:8,r:13,t:0,vx:0,vy:0,turn:99}];enemyBullets=[{x:player.x,y:player.y,vx:0,vy:0,r:5,life:3}];update(.001)}''')
  expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_hidden()
  expect(page.locator('#gameOverScore')).to_have_text('🏆 3,700점')
  assert page.evaluate('!started&&!gameAudioStarted&&hp===0&&gameOverPending&&!!document.fullscreenElement&&items.length===1')
  snapshot='JSON.stringify({player,bullets,enemyBullets,enemies,warnings,items,particles,worldScroll,rotorSpin,runScore,hp,phase,stage})'
  before=page.evaluate(snapshot);canvas=page.evaluate('canvas.toDataURL()')
  page.evaluate('beginGameOver();beginGameOver();keys.fire=true;keys.left=true;tilt.x=1;update(.04);document.getElementById("exitGame").click();')
  page.wait_for_timeout(400)
  assert page.evaluate(snapshot)==before and page.evaluate('canvas.toDataURL()')==canvas
  assert page.evaluate('deathEvents===1&&!gameExitDialogOpen')
  page.screenshot(path=str(args.artifacts/'game-over-915x412.png'))
  passed('Lethal collision immediately stops simulation and BGM flag, preserves the last canvas, blocks simultaneous healing/exit/input, and produces one overlay/timer with the correct stars.')
  page.wait_for_function('performance.now()-deathAt>=2700')
  expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_hidden()
  expect(page.locator('#menu')).to_be_visible(timeout=1500);expect(page.locator('#gameOverOverlay')).to_be_hidden()
  timing=page.evaluate('returnAt-deathAt');report['return_delay_ms']=timing;assert 2990<=timing<3400,timing
  assert page.evaluate('!gameOverPending&&gameOverTimer===null&&!!document.fullscreenElement&&menu.querySelector("h1").textContent==="🚁 귀염 헬기 슈팅"')
  expect(page.locator('#selectionResult')).to_have_text('');page.screenshot(path=str(args.artifacts/'clean-selection-after-game-over.png'))
  passed('Overlay remains at 2.7 seconds and returns at three seconds to the original title/three-character selection with no residual result and fullscreen intact.')
  # Even legacy title mutations must never repopulate selectionResult.
  page.evaluate('menu.querySelector("h1").textContent="게임 오버! ⭐ 999"');expect(page.locator('#selectionResult')).to_have_text('')
  page.locator('.select-hit[data-heli="1"]').tap();page.locator('#startSelected').tap()
  assert page.evaluate('started&&player.type===1&&hp===6&&!gameOverPending&&!keys.fire&&!keys.left&&tilt.x===0')
  passed('Legacy death headings cannot leak into selectionResult; normal character restart clears frozen input and restores gameplay.')
  # Programmatic lifecycle cancellation is defensive; no stale timeout may end a newer game.
  page.evaluate('hp=0;update(0);start(2);spawn=999;invuln=999')
  page.wait_for_timeout(3100)
  assert page.evaluate('started&&player.type===2&&!gameOverPending&&gameOverTimer===null&&menu.classList.contains("hidden")')
  passed('Restart cancels the pending return timer; a stale game-over timeout cannot pull a new game back into selection.')
  for w,h in [(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.evaluate('hp=0;update(0)')
   expect(page.locator('#gameOverOverlay')).to_be_visible();box=page.locator('.game-over-panel').bounding_box()
   assert 0<=box['x'] and 0<=box['y'] and box['x']+box['width']<=w and box['y']+box['height']<=h
   page.screenshot(path=str(args.artifacts/f'game-over-{w}x{h}.png'))
   expect(page.locator('#menu')).to_be_visible(timeout=4000)
   page.locator('#startSelected').tap();page.evaluate('spawn=999;invuln=999')
  passed('Three landscape sizes fit the centered overlay and return normally through repeated death/restart cycles.')
  page.evaluate('stage=3;phase=5;nextPhase()');expect(page.locator('#selectionResult')).to_contain_text('모든 지역 클리어')
  assert page.evaluate('!gameOverPending&&gameOverTimer===null&&!!document.fullscreenElement')
  assert not errors and not dialogs,(errors,dialogs)
  passed('Final-clear results and native fullscreen are retained; no browser dialogs or uncaught JavaScript errors occur.')
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
