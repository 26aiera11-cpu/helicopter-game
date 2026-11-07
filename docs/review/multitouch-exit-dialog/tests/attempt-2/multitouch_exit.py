"""Issue30: trusted CDP/Playwright input, button-local fallback and stale-click safety."""
import argparse,json,shutil,threading,time
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from exit_tap_preservation import verify
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'preservation':verify(),'standalone':args.standalone,'passed':[],'cases':[],'limits':['Chromium touch emulation; physical Galaxy/Samsung Internet and real sensors not exercised.','Dropped/delayed click tests are explicit fault injection, not evidence that a browser necessarily drops that event.','Baseline worlds failure is reproduced, but simplified native-button comparisons do not identify a unique browser or CDP root cause.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
probe=r'''()=>{
 window.exitAudit=[];window.exitOpenCount=0;window.exitDropNext=false;window.exitRawClicks=0;
 for(const type of ['pointerdown','pointerup','pointercancel','lostpointercapture','click'])window.addEventListener(type,e=>{
  if(e.target.id!=='exitGame')return;
  exitAudit.push({type,id:e.pointerId,pointer:e.pointerType,primary:e.isPrimary,trusted:e.isTrusted,x:e.clientX,y:e.clientY,time:performance.now(),prevented:e.defaultPrevented,path:e.composedPath().slice(0,4).map(n=>n.id||n.tagName||n.constructor.name),owners:window.gameControls?.snapshot()});
  if(exitAudit.length>300)exitAudit.shift();
  if(type==='click'){exitRawClicks++;if(exitDropNext){exitDropNext=false;e.stopImmediatePropagation();}}
 },true);
}'''
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-exit-origin':
   self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline test origin</title>');return
  super().do_GET()
class Touch:
 def __init__(self,ctx,page,end='empty'):self.cdp=ctx.new_cdp_session(page);self.page=page;self.points={};self.end=end;self.serial=100
 def down(self,i,x,y):self.points[i]={'id':i,'x':x,'y':y};self.cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':list(self.points.values())})
 def move(self,i,x,y):self.points[i].update(x=x,y=y);self.cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':list(self.points.values())})
 def up(self,i):p=self.points.pop(i);self.cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[p] if self.end=='point' or self.points else []})
 def cancel(self):self.cdp.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]});self.points.clear()
 def center(self,selector):r=self.page.locator(selector).bounding_box();return r['x']+r['width']/2,r['y']+r['height']/2
 def tap(self,selector,fresh=True,hold=60):
  self.serial+=1;i=self.serial if fresh else 50;x,y=self.center(selector);self.down(i,x,y);self.page.wait_for_timeout(hold);self.up(i)
 def controls(self,count=3):
  x,y=self.center('#rotationJoystick');self.down(1,x,y);self.move(1,x+45,y)
  x,y=self.center('#fire');self.down(2,x,y)
  if count>=3:self.down(3,self.page.viewport_size['width']*.55,150);self.move(3,self.page.viewport_size['width']*.55+75,150)
  if count>=4:self.down(4,200,180)
  self.page.wait_for_timeout(40)
  assert self.page.evaluate('keys.fire&&gameControls.rotation()>0')
  if count>=3:assert self.page.evaluate('drag!==null')
  for i in range(1,count+1):self.up(i)
  assert self.page.evaluate('!keys.fire&&drag===null&&gameControls.rotation()===0')
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
errors=[];dialogs=[];requests=[];page=None
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);report['browser']=browser.version
  for width,height in [(915,412),(800,360),(568,320)]:
   for dpr in [1,2]:
    ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=dpr,is_mobile=True,has_touch=True);ctx.add_init_script('('+probe+')()');page=ctx.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
    if args.standalone:
     page.goto(url+'offline-exit-origin');ctx.set_offline(True);page.on('request',lambda r:requests.append(r.url) if r.url.startswith('http') else None);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
    else:page.goto(url,wait_until='load')
    page.wait_for_function('gameMachineFortress.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');page.wait_for_function("[...document.querySelectorAll('audio')].every(a=>!a.error&&a.readyState>=2)")
    page.evaluate('''()=>{const show=showGameExitDialog;window.showGameExitDialog=cb=>{exitOpenCount++;return show(cb)}}''');t=Touch(ctx,page)
    if width==915 and dpr==1:page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement')
    def start(hero=0,region=4):
     page.evaluate('([h,r])=>{gameWorlds.setDeveloperStart({enabled:true,regionId:r,phase:5});chosen=h;drawChoices()}',[hero,region]);page.locator('#startSelected').tap();page.wait_for_function('started');page.evaluate('spawn=999;transition=0;invuln=999;enemyBullets=[];player.x=W/2;player.y=H*.6')
    def close(confirm=False):
     page.locator('#gameExitConfirm' if confirm else '#gameExitCancel').tap();page.wait_for_function('!gameExitDialogOpen');assert page.evaluate('!keys.fire&&drag===null&&gameControls.rotation()===0')
    for i in range(25):
     hero=i%3;region=[0,4,7][(i//3)%3];start(hero,region);t.end=['empty','point'][i%2];t.controls([2,3,4][i%3]);delay=[0,100,300,550][i%4];page.wait_for_timeout(delay)
     force_missing=i%5==0;page.evaluate('(v)=>exitDropNext=v',force_missing);before=page.evaluate('({opens:exitOpenCount,clicks:exitRawClicks,time:performance.now()})')
     if i%2:t.tap('#exitGame',fresh=i%4!=1)
     else:page.locator('#exitGame').tap()
     expect(page.locator('#gameExitDialog')).to_be_visible(timeout=1500);page.wait_for_timeout(140)
     after=page.evaluate('({opens:exitOpenCount,clicks:exitRawClicks,time:performance.now(),trace:exitAudit.slice(-6),controls:gameControls.snapshot()})');assert after['opens']==before['opens']+1,after
     assert page.evaluate('gameExitDialogOpen&&started&&!keys.fire&&drag===null&&gameControls.rotation()===0')
     report['cases'].append({'viewport':[width,height],'dpr':dpr,'hero':hero,'region':region,'contacts':[2,3,4][i%3],'end':t.end,'post_gesture_delay_ms':delay,'method':'cdp' if i%2 else 'playwright','drop_click_fault_injection':force_missing,'raw_clicks':after['clicks']-before['clicks'],'opens':1})
     if i==0:
      snap=page.evaluate('JSON.stringify({player,hp,bullets,enemyBullets,worldScroll})');page.wait_for_timeout(60);assert snap==page.evaluate('JSON.stringify({player,hp,bullets,enemyBullets,worldScroll})')
      page.screenshot(path=str(args.artifacts/f'exit-dialog-{width}x{height}-dpr{dpr}.png'))
     close();expect(page.locator('#exitGame')).to_be_focused()
     # A deliberately late compatibility click for the already consumed touch must not reopen.
     event=next(e for e in reversed(after['trace']) if e['type']=='pointerup')
     page.evaluate('(e)=>exitGame.dispatchEvent(new PointerEvent("click",{bubbles:true,pointerType:"touch",pointerId:e.id,clientX:e.x,clientY:e.y,detail:1}))',event)
     page.wait_for_timeout(30);assert page.evaluate('!gameExitDialogOpen')
     # A genuinely new tap immediately after Cancel remains accepted.
     page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();assert page.evaluate('exitOpenCount')==before['opens']+2;close(True)
     assert page.evaluate('!started&&!gameExitDialogOpen&&!menu.classList.contains("hidden")&&gameControls.rotation()===0')
    passed(f'{width}x{height} DPR{dpr}:25 post-multitouch exits +25 immediate reopens, 2/3/4 contacts, three heroes and regions0/4/7, both release forms; no duplicate dialog.')
    # Negative and accessibility cases once per viewport/DPR, using trusted native pointer events.
    start();t.end='empty';base=page.evaluate('exitOpenCount');x,y=t.center('#exitGame')
    t.down(90,x,y);page.wait_for_timeout(180);assert page.evaluate('!gameExitDialogOpen');t.cancel();page.wait_for_timeout(120);assert page.evaluate('!gameExitDialogOpen')
    t.down(91,x,y);page.wait_for_timeout(810);t.up(91);page.wait_for_timeout(140);assert page.evaluate('!gameExitDialogOpen')
    t.down(92,x,y);t.move(92,x-45,y+70);t.move(92,x,y);t.up(92);page.wait_for_timeout(140);assert page.evaluate('!gameExitDialogOpen')
    t.down(93,x,y);t.down(94,width*.5,height*.5);t.up(93);t.up(94);page.wait_for_timeout(140);assert page.evaluate('!gameExitDialogOpen')
    assert page.evaluate('exitOpenCount')==base
    for action in ["window.dispatchEvent(new Event('blur'))","window.dispatchEvent(new Event('resize'))","document.dispatchEvent(new Event('gameover'))","menu.classList.remove('hidden');menu.classList.add('hidden')"]:
     page.evaluate('exitDropNext=true');t.tap('#exitGame');page.evaluate(action);page.wait_for_timeout(160);assert page.evaluate('!gameExitDialogOpen'),action;page.evaluate('exitDropNext=false')
    page.locator('#exitGame').click();expect(page.locator('#gameExitDialog')).to_be_visible();close()
    for key in ['Enter','Space']:
     page.locator('#exitGame').focus();page.keyboard.press(key);expect(page.locator('#gameExitDialog')).to_be_visible();expect(page.locator('#gameExitCancel')).to_be_focused();page.keyboard.press('Tab');expect(page.locator('#gameExitConfirm')).to_be_focused();page.keyboard.press('Shift+Tab');expect(page.locator('#gameExitCancel')).to_be_focused();page.keyboard.press('Enter');expect(page.locator('#exitGame')).to_be_focused()
    if width==915 and dpr==1:assert page.evaluate('!!document.fullscreenElement')
    page.locator('#exitGame').click();close(True)
    passed(f'{width}x{height} DPR{dpr}: down-only/cancel/long press/drag/multifinger/pending interruption rejected; mouse, Enter, Space, focus loop and cancel/confirm work.')
    ctx.close()
  assert not errors and not dialogs and not requests,{'errors':errors,'native_dialogs':dialogs,'offline_requests':requests}
  passed('No uncaught JS error or native browser dialog; offline runs issue zero HTTP requests. All131 approved assets and all non-exit engine source stay byte-identical.')
  browser.close()
except Exception:
 if page and not page.is_closed():
  try:report['failure']=page.evaluate('({trace:exitAudit,open:window.gameExitDialogOpen,started,controls:gameControls.snapshot()})');page.screenshot(path=str(args.artifacts/'failure.png'))
  except Exception:pass
 raise
finally:
 report.update(errors=errors,native_dialogs=dialogs,offline_requests=requests);(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');server.shutdown();server.server_close()
