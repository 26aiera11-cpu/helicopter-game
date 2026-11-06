from pathlib import Path
import ast,json,subprocess,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[3];O=R/'docs/review/volcano-bgm/touch-fixture-diagnostic';O.mkdir(exist_ok=True);BASE='d9f538e7e335a72b8140aebc77f7e3bfb31b25cc'
sources={n:subprocess.check_output(['git','show',BASE+':'+n],cwd=R) for n in ['index.html','assets/worlds/worlds.js']}
tree=ast.parse((R/'tests/worlds.py').read_text());helpers=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  mode,_,name=self.path.strip('/').partition('/');name=name or 'index.html'
  if mode=='before' and name in sources:
   data=sources[name];self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8' if name=='index.html' else 'text/javascript; charset=utf-8');self.end_headers();self.wfile.write(data);return
  if mode in ['before','after']:self.path='/'+name
  super().do_GET()
s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(R)));threading.Thread(target=s.serve_forever,daemon=True).start();rows=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  for mode in ['before','after']:
   for last_point in [False,True]:
    for attempt in range(2):
     c=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);p=c.new_page();p.goto(f'http://127.0.0.1:{s.server_port}/{mode}/');p.wait_for_function('gameVolcano.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');p.evaluate(helpers);p.locator('#fullscreenToggle').tap();p.evaluate('gameWorlds.setTrialEnabled(true)');cdp=c.new_cdp_session(p);points={}
     p.evaluate('''()=>{window.trace=[];for(const n of ['pointerdown','pointerup','pointercancel','click','touchstart','touchend'])window.addEventListener(n,e=>trace.push({type:n,target:e.target.id||e.target.tagName,id:e.pointerId,touches:e.touches?.length,changed:e.changedTouches?.length}),true)}''')
     def down(id,x,y):points[id]={'id':id,'x':x,'y':y};cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':list(points.values())})
     def move(id,x,y):points[id].update(x=x,y=y);cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':list(points.values())})
     def up(id):point=points.pop(id);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[point] if last_point or points else []})
     def tap(selector):b=p.locator(selector).bounding_box();down(50,b['x']+b['width']/2,b['y']+b['height']/2);p.wait_for_timeout(60);up(50)
     tap('#startSelected');p.wait_for_function('started');p.evaluate('worldSnow();invuln=999;spawn=999;transition=0;player.x=W/2;player.y=H*.55;draw()');p.wait_for_function('!worldPrototypeNotice.hidden');j=p.locator('#rotationJoystick').bounding_box();f=p.locator('#fire').bounding_box();cx=j['x']+j['width']/2;cy=j['y']+j['height']/2;travel=p.evaluate('rotationJoystick.offsetWidth/2-parseFloat(getComputedStyle(rotationJoystick).getPropertyValue("--stick-inset"))')
     down(1,cx,cy);move(1,cx+travel*.07,cy);move(1,cx+travel,cy);down(2,f['x']+f['width']/2,f['y']+f['height']/2);down(3,915*.55,412*.4);move(3,915*.55+75,412*.4);p.wait_for_function('tilt.x>0&&keys.fire&&drag!==null&&gameControls.rotation()>.99');up(1);up(2);up(3);p.wait_for_timeout(550);p.evaluate('document.getElementById("game").dispatchEvent(new Event("contextmenu",{cancelable:true,bubbles:true}));phase=5;phaseKills=requiredKills;update(0);transition=0;draw()');p.screenshot(path=str(O/f'{mode}-{last_point}-{attempt}-before-exit.png'));tap('#exitGame');p.wait_for_timeout(200);row=p.evaluate('({open:gameExitDialogOpen,controls:gameControls.snapshot(),trace})');rows.append({'version':mode,'finalTouchEndIncludesLiftedPoint':last_point,'attempt':attempt,**row});print(mode,last_point,attempt,row['open'],flush=True);c.close()
  browser.close()
finally:s.shutdown();(O/'results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
