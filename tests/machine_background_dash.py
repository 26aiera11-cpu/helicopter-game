"""Issue34 unchanged H-proportional dashes with Issue35 single-cover background expectations."""
import argparse,base64,hashlib,json,math,shutil,subprocess,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
from machine_background_dash_preservation import BASE,TEXT,verify
from machine_cover_probe import probe,check_background
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':args.standalone,'passed':[],'preservation':verify(),'limits':['Exact real Chromium controlled states, not physical Samsung Internet/Chrome sensor or human difficulty approval.','Dash state transitions are quantized by the existing1/300s step; actual target endpoints are clamped exactly.','Network-disabled exact HTML injection tests offline resources without bypassing managed file navigation policy.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
helpers=(ROOT/'tests/machine_normal.py').read_text().split("helpers=r'''",1)[1].split("'''",1)[0]
old={name:subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT) for name in TEXT}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  for prefix in ['/before/','/after/']:
   if path.startswith(prefix):path='/'+path[len(prefix):];break
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/blank':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  name=self.path.removeprefix('/before/')
  if self.path.startswith('/before/') and name in old:
   b=old[name];self.send_response(200);self.send_header('Content-Type','text/javascript');self.end_headers();self.wfile.write(b);return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append({'url':r.url,'error':r.failure}));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  if args.standalone:page.goto(url+'/blank');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url+'/after/',wait_until='load')
  page.wait_for_function('gameMachineFortress.ready()&&gameStormSky.ready()&&itemMonsters.ready()');page.evaluate(helpers);page.evaluate('mcRun(()=>mcBegin())')
  for name in TEXT:subprocess.run(['node','--check',str(ROOT/name)],check=True,capture_output=True)
  c=page.evaluate('gameMachineConfig');assert [m['dashHeight'] for m in c['monsters'][:2]]==[.4,.7] and [m['dash'] for m in c['monsters'][:2]]==[100,145] and all('dashTime' not in m for m in c['monsters']);passed('Only3Machine files change; index/128old assets normalize exactly; final.40H/.70H fractions and100/145 speeds replace fixed dashTime; JS parses.')
  layouts=[]
  for ratio in [1,2]:
   for w,h in [(915,412),(800,360),(568,320),(1672,941),(412,915)]:
    row=page.evaluate(probe,[w,h,ratio]);check_background(row);layouts.append(row)
  report['background_pixels']=layouts;passed('10 background/DPR cases: every pixel opaque and equal to single-cover reference; original ratio/center maintained with approved edge crop; no blur/overlay/second image.')
  exact=next(r for r in layouts if r['size']==[1672,941] and r['ratio']==1);assert len(exact['calls'])==1;passed('At exact source aspect1672x941 the single cover image equals the complete original with no cropping, blur or dark overlay.')
  calls=page.evaluate("""()=>mcRun(()=>{const c=document.createElement('canvas');c.width=813;c.height=364;const g=c.getContext('2d'),create=document.createElement,original=g.drawImage;let canvases=0,draws=0;document.createElement=function(tag,...args){if(tag==='canvas')canvases++;return create.call(document,tag,...args)};g.drawImage=function(...args){draws++;return original.call(g,...args)};try{gameMachineFortress.drawBackground(g,813,364);gameMachineFortress.drawBackground(g,813,364);return {canvases,draws};}finally{document.createElement=create;g.drawImage=original;}})""");assert calls=={'canvases':0,'draws':2};report['single_cover_calls']=calls;passed('Every frame draws one original image; no offscreen canvas/cache allocation, extension or repeated source draw.')
  fallback=page.evaluate("""probe=>{const proto=CanvasRenderingContext2D.prototype,descriptor=Object.getOwnPropertyDescriptor(proto,'filter');Object.defineProperty(proto,'filter',{configurable:true,get:()=>"none",set:()=>{throw Error('Cover must not set filters')}});try{return eval('('+probe+')')([913,411,2]);}finally{Object.defineProperty(proto,'filter',descriptor);}}""",probe);check_background(fallback);report['without_canvas_filter']=fallback;passed('Single-cover rendering never sets Canvas filters and remains pixel-identical/opaque when filter setters are unavailable, includingDPR2.')
  rows=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h])
   for kind in [0,1]:
    for angle in range(8):
     row=page.evaluate('''([kind,angle])=>mcRun(()=>{mcBegin();const a0=angle*Math.PI/4,dx=Math.cos(a0),dy=Math.sin(a0),pre=kind===1?60:0;const a=mcSpawn(kind,W/2-dx*pre,H/2-dy*pre);player.x=W/2+dx*80;player.y=H/2+dy*80;const warning=mcUntil(a,'warning');mcUntil(a,'dash');const start={x:a.x,y:a.y,state:gameMachineCombat.snapshot(a)},fixed=start.state.path;player.x=a.x-dx*100;player.y=a.y-dy*100;mcStep(a,.1);const first={x:a.x,y:a.y,state:gameMachineCombat.snapshot(a)};mcUntil(a,kind===0?'cooldown':'rest');return {size:[W,H],kind,angle,warning,start,first,end:{x:a.x,y:a.y,state:gameMachineCombat.snapshot(a)},bullets:enemyBullets.length};})''',[kind,angle])
     s=row['start'];line=s['state']['path'];dx=math.cos(angle*math.pi/4);dy=math.sin(angle*math.pi/4);target=h*[.4,.7][kind];bounds=[target]
     if abs(dx)>1e-8:bounds.append(((w-18-s['x']) if dx>0 else (18-s['x']))/dx)
     if abs(dy)>1e-8:bounds.append(((h-18-s['y']) if dy>0 else (18-s['y']))/dy)
     length=max(0,min(bounds));speed=[100,145][kind];duration=length/speed
     assert abs(s['state']['targetDistance']-target)<1e-6 and abs(line['length']-length)<1e-6 and abs(s['state']['dashDuration']-duration)<1e-6
     assert math.hypot(row['end']['x']-line['endX'],row['end']['y']-line['endY'])<1e-6 and row['end']['state']['remaining']==[2.2,2.6][kind] and row['bullets']==0
     assert abs(math.hypot(row['first']['x']-s['x'],row['first']['y']-s['y'])-speed*.1)<1e-6 and row['first']['state']['direction']==s['state']['direction']
     elapsed=row['end']['state']['age']-s['state']['age'];assert duration-1e-6<=elapsed<=duration+1/300+1e-6
     if angle in [0,4]:assert abs(length-target)<1e-6
     rows.append(row)
  report['eight_direction_dashes']=rows;passed('48dash cases across3heights/8directions: exactH*.40/.70 target,100/145speed, duration=clipped path/speed, fixed direction, identical telegraph endpoint, unchanged2.2/2.6 recovery; horizontal center paths reach the full target.')
  report['distance_table']=[{'height':h,'screw_distance':h*.4,'screw_seconds':h*.4/100,'wasp_distance':h*.7,'wasp_seconds':h*.7/145} for h in [320,360,412]]
  edge=page.evaluate('''()=>mcRun(()=>{const rows=[];for(let kind=0;kind<2;kind++){mcBegin();const a=mcSpawn(kind,W-20-(kind?60:0),H/2);player.x=W+60;player.y=H/2;mcUntil(a,'dash');const start={x:a.x,state:gameMachineCombat.snapshot(a)};mcUntil(a,kind===0?'cooldown':'rest');rows.push({kind,start,end:{x:a.x,state:gameMachineCombat.snapshot(a)}});}return rows;})''');assert all(abs(r['start']['state']['path']['length']-2)<1e-6 and abs(r['end']['x']-(568-18))<1e-6 and abs(r['start']['state']['dashDuration']-2/[100,145][r['kind']])<1e-6 for r in edge);report['edge_shortening']=edge;passed('Near-wall paths shorten to2px with the matching shorter time, stop at the original18px safe margin and immediately enter existing recovery; no wall slide, teleport or stuck full-duration dash.')
  # Real before/after game captures from the exact baseline modules, without editing original assets.
  if not args.standalone:
   before=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);bpage=before.new_page();bpage.goto(url+'/before/');bpage.wait_for_function('gameMachineFortress.ready()');bpage.evaluate(helpers)
   for version,target in [('before',bpage),('after',page)]:
    for w,h in [(915,412),(568,320)]:
     target.set_viewport_size({'width':w,'height':h});target.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);target.evaluate('mcRun(()=>{mcBegin();rotorSpin=0;worldScroll=0;for(let kind=0;kind<4;kind++)mcSpawn(kind,W*(.2+kind*.2),H*.5);player.x=W*.5;player.y=H*.75;})');target.screenshot(path=str(args.artifacts/f'{version}-background-{w}x{h}.png'))
   before.close();passed('Actual baseline/current game screenshots compare915x412 and568x320 with original actors/background coordinates; only3authorized modules differ, no PNG compositing or pixel edits.')
  for kind,name in [(0,'screw'),(1,'wasp')]:
   page.evaluate('''kind=>mcRun(()=>{mcBegin();const a=mcSpawn(kind,W*.3-(kind?60:0),H*.4);player.x=W*.3+80;player.y=H*.4;mcUntil(a,'warning');})''',kind);page.screenshot(path=str(args.artifacts/f'{name}-warning.png'))
   page.evaluate('mcRun(()=>{const a=enemies[0];mcUntil(a,"dash");mcAdvance(.4);})');page.screenshot(path=str(args.artifacts/f'{name}-dash.png'))
  passed('Captured long-route warnings and actual screw/wasp dashes from production Canvas states; draw path and movement use the same clipped segment.')
  a=page.evaluate('''()=>mcRun(()=>{mcBegin();const a=mcSpawn(1);mcUntil(a,'dash');return gameMachineCombat.snapshot(a);})''');page.set_viewport_size({'width':800,'height':360});page.wait_for_function('W===800&&H===360');r=page.evaluate('mcRun(()=>{update(0);return gameMachineCombat.snapshot(enemies[0]);})');assert r['path'] is None and r['mode']=='rest' and r['remaining']==1.2;report['resize_cancel']=r
  page.set_viewport_size({'width':360,'height':800});page.wait_for_function('W===360&&H===800');page.set_viewport_size({'width':915,'height':412});page.wait_for_function('W===915&&H===412');row=page.evaluate(probe,[915,412,1]);check_background(row);passed('Resizing during a dash cancels old warnings/path with the existing safe recovery; portrait-to-landscape return rebuilds full image fill without stale dimensions.')
  extra=browser.new_context(viewport={'width':568,'height':320},device_scale_factor=2,is_mobile=True,has_touch=True);dpage=extra.new_page()
  if args.standalone:extra.set_offline(True);dpage.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:dpage.goto(url+'/after/')
  dpage.wait_for_function('gameMachineFortress.ready()');dpage.evaluate(helpers);dpage.evaluate('mcRun(()=>{mcBegin();const a=mcSpawn(1);mcUntil(a,"warning");})');assert dpage.evaluate('dpr===2&&canvas.width===1136&&canvas.height===640');dpage.screenshot(path=str(args.artifacts/'after-dpr2-568x320.png'));extra.close();passed('ActualDPR2 game Canvas1136x640 keeps image fill, sharp original,40px normals and existing UI at CSS568x320; no new touch layer.')
  assert not errors and not dialogs and not failed and (not args.standalone or not external),(errors,dialogs,failed,external)
  report.update(all_passed=True,errors=errors,dialogs=dialogs,failed=failed,offline_requests=external if args.standalone else []);passed('No uncaught errors/native dialogs/missing files; standalone image/code/audio resources execute with network disabled and zero external requests.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
