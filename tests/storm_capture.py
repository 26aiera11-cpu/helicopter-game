"""Reproduce controlled, unretouched Storm Sky gameplay captures (not a device photo)."""
import argparse,json,shutil,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
source=(ROOT/'tests/storm_sky.py').read_text();helpers=source.split("helpers=r'''",1)[1].split("'''",1)[0]
def ids(seed):
 result=[]
 for _ in range(4):
  seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff;seed&=0xffffffff
  n=seed/4294967296*100;result.append(0 if n<10 else 1 if n<35 else 2 if n<65 else 3)
 return result
seed=next(s for s in range(1,10000) if len(set(ids(s)))==4)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();rows=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':915,'height':412},has_touch=True);page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('gameStormSky.ready()');page.evaluate(helpers)
  def shot(name):
   page.screenshot(path=str(args.artifacts/name));rows.append({'file':name,'state':page.evaluate('({stage,phase,score:runScore,hp,type:player.type,boss:gameStormBoss.snapshot(),species:enemies.map(e=>e.stormSpeciesId)})')})
  page.evaluate('seed=>ssRun(()=>{ssBegin(0,4);gameStormSpawns.reset(seed);for(let i=0;i<4;i++)ssSpawn();enemies.sort((a,b)=>gameStormConfig.ids.indexOf(a.stormSpeciesId)-gameStormConfig.ids.indexOf(b.stormSpeciesId));enemies.forEach((e,i)=>{e.x=W*(.2+i*.19);e.y=H*.45;e.shot=999;});gameStormSky.observe(enemies,null);draw();})',seed);shot('storm-normal-mixed.png')
  page.evaluate("ssRun(()=>{ssBegin();ssSelect('barrage');ssAdvance(gameStormBoss.snapshot().remaining+.45+.5);})");shot('storm-barrage.png')
  page.evaluate('ssRun(()=>{ssBegin();boss.hp=10;update(0);ssAdvance(.8);})');shot('storm-awakening.png')
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);page.evaluate("ssRun(()=>{ssBegin();ssSelect('laser');ssAdvance(gameStormBoss.snapshot().remaining+.25);})");shot(f'storm-boss-{w}x{h}.png')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'capture-fixtures.json').write_text(json.dumps({'seed':seed,'method':'Actual game Canvas/UI; controlled coordinates/time/invulnerability, no image editing','captures':rows},ensure_ascii=False,indent=2)+'\n')
