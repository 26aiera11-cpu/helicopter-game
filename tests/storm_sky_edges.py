"""Boundary/behavior checks supplement the production-browser Storm Sky suite."""
import argparse,json,math,shutil,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();a.artifacts.mkdir(parents=True,exist_ok=True);out={'passed':[]}
def passed(s):out['passed'].append(s);print('PASS:',s,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
# Use the same fixture controls as the primary suite without importing/running it.
source=(ROOT/'tests/storm_sky.py').read_text();helpers=source.split("helpers=r'''",1)[1].split("'''",1)[0]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':800,'height':360},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('gameStormSky.ready()');page.evaluate(helpers)
  dash=page.evaluate('''ssRun(()=>{ssBegin(0,4);gameStormSpawns.reset(23);let e;for(let i=0;i<100;i++){e=ssSpawn();if(e.stormSpeciesId==='lightning_bat')break;}enemies=[e];e.x=W*.4;e.y=H*.4;e.shot=999;player.x=W*.8;player.y=H*.7;let n=0;while(gameStormCombat.snapshot(e).mode!=='warning'&&n++<1000)gameStormCombat.update(e,1/120);const warning=gameStormCombat.snapshot(e);const p={x:e.x,y:e.y};player.x=30;player.y=H-30;while(gameStormCombat.snapshot(e).mode!=='dash'&&n++<2000)gameStormCombat.update(e,1/120);gameStormCombat.update(e,.3);return {warning,after:gameStormCombat.snapshot(e),dx:e.x-p.x,dy:e.y-p.y};})''')
  assert dash['warning']['mode']=='warning' and dash['after']['mode']=='dash' and dash['after']['shots']==0
  assert abs(dash['dx']-.3*155*dash['warning']['direction'][0])<1e-6 and abs(dash['dy']-.3*155*dash['warning']['direction'][1])<1e-6
  out['bat_dash']=dash;passed('Bat holds its warning-time vector through a player side swap and moves exactly155px/s during dash; warning/dash emit no bullets.')
  rate=page.evaluate('''ssRun(()=>{const rows=[];for(const phase2 of [false,true]){ssBegin();if(phase2){boss.hp=10;update(0);ssAdvance(2);}const rest=gameStormBoss.snapshot().remaining;ssSelect('laser');const warning=gameStormBoss.snapshot().remaining;ssAdvance(warning);const beam=gameStormBoss.snapshot().remaining;rows.push({phase2,rest,warning,beam});}return rows;})''')
  assert rate[1]['rest']>=1.5 and abs(rate[0]['warning']/rate[1]['warning']-1.2)<1e-6 and abs(rate[0]['beam']/rate[1]['beam']-1.2)<1e-6
  out['phase_rates']=rate;passed('Measured phase2 laser charge and active duration are exactly1/1.2 of phase1; minimum rest1.5s remains enforced.')
  muzzle=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('laser');const rows=[];for(const dt of [.01,.1,.1]){ssAdvance(dt);if(rows.length===2)gameStormSky.hit(boss,true);let call;const drawImage=ctx.drawImage;ctx.drawImage=function(im,...args){if(im.id==='storm-storm_overlord')call={args,m:ctx.getTransform()};return drawImage.call(ctx,im,...args);};try{gameStormSky.drawActor(ctx,boss,true);}finally{ctx.drawImage=drawImage;}const points=[[330,460],[1200,460]].map(([x,y])=>{const [sx,sy,sw,sh,dx,dy,dw,dh]=call.args,px=dx+(x-sx)*dw/sw,py=dy+(y-sy)*dh/sh,m=call.m;return {x:(m.a*px+m.c*py+m.e)/dpr,y:(m.b*px+m.d*py+m.f)/dpr};});rows.push({points,lasers:gameStormBoss.snapshot().lasers});}return rows;})''')
  out['turbine_origins']=muzzle
  for row in muzzle:
   for point,beam in zip(row['points'],row['lasers']):assert math.hypot(point['x']-beam['x'],point['y']-beam['y'])<1e-4
  out['turbine_origins']=muzzle;passed('Six actual Canvas draw-matrix turbine anchors agree with laser collision/draw origins within0.0001px (Canvas transform rounding) through attack and hit keyframes.')
  no_space=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('tornado');ssAdvance(gameStormBoss.snapshot().remaining);const w=gameStormBoss.snapshot().winds[0];player.x=w.x;player.y=w.y;hp=4;invuln=0;const old=hud.style.cssText;hud.style.cssText='position:fixed;left:0;top:0;width:100vw;height:100vh;max-width:none';try{update(.001);return {hp,state:gameStormBoss.snapshot(),x:player.x,y:player.y,expected:{x:w.x,y:w.y}};}finally{hud.style.cssText=old;}})''')
  assert no_space['hp']==4 and no_space['state']['teleports']==0 and abs(no_space['x']-no_space['expected']['x'])<1e-6 and abs(no_space['y']-no_space['expected']['y'])<1e-6
  out['no_safe_space']=no_space;passed('A deliberate full-arena UI blocker causes wind transport to skip safely with unchangedHP/location, rather than teleport into UI or loop forever.')
  frozen=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('laser');ssAdvance(gameStormBoss.snapshot().remaining+.1);const before=gameStormBoss.snapshot();Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});try{update(.3);}finally{delete document.hidden;}return {before,after:gameStormBoss.snapshot()};})''');assert frozen['before']==frozen['after'];passed('Hidden-document update freezes the full active laser lifecycle and all wind/age timers.')
  page.set_viewport_size({'width':568,'height':320});page.wait_for_function('W===568&&H===320');resized=page.evaluate('ssRun(()=>{update(0);return gameStormBoss.snapshot();})');assert resized['phase']=='rest' and resized['winds']==[] and resized['lasers']==[];passed('Resize cancels active laser/wind geometry and resumes a safe rest using current UI bounds, with no invisible offscreen damage.')
  assert not errors;out.update(all_passed=True,errors=errors);browser.close()
finally:
 server.shutdown();(a.artifacts/'test-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
