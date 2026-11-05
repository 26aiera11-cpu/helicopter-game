"""Issue20 actual static PNG matrices, bounded dynamic tracking and safe failure."""
import argparse,ast,hashlib,json,math,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'standalone':args.standalone,'limits':['Controlled Chromium gameplay fixtures; no physical Galaxy Samsung Internet, hardware tilt, finger input or performance/heat measurements.','Alpha96 collision ignores weak glow/antialias fringe; player center uses original hurt/invulnerability rules.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
tree=ast.parse((ROOT/'tests/volcano_boss.py').read_text());helpers=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
  context.add_init_script('''window.breathReads=0;const original=CanvasRenderingContext2D.prototype.getImageData;CanvasRenderingContext2D.prototype.getImageData=function(...a){if(this.canvas.width===768&&this.canvas.height===230)window.breathReads++;return original.apply(this,a);};''')
  page=context.new_page();errors=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
  if args.standalone:
   page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.wait_for_function('gameVolcanoBoss.artSnapshot().status==="ready"&&gameVolcano.ready()');page.evaluate(helpers)
  state=page.evaluate('({art:gameVolcanoBoss.artSnapshot(),metadata:gameVolcanoBoss.breathArt,reads:breathReads})');assert state['art']=={'status':'ready','width':768,'height':230,'maskReady':True} and state['reads']==1,state;report['asset']=state
  assert hashlib.sha256((ROOT/'assets/volcano/effects/magma_dragon_breath_static.png').read_bytes()).hexdigest()=='a9600ff8d4c827d8d5ac200c5c508ff636d008398ec985a5fb259c65913fa979'
  passed('Supplied SHA256/768x230 RGBA resource loads intact; source alpha read exactly once and cached, no per-frame getImageData.')
  matrices=page.evaluate(r'''()=>vbRun(()=>{vbBegin(0);vbGo('breath');const rows=[];for(let n=0;n<12;n++){
   const geo=gameVolcanoBoss.frameGeometry(boss),probe=document.createElement('canvas');probe.width=W;probe.height=H;const g=probe.getContext('2d'),original=g.drawImage;let flame;
   g.drawImage=function(im,...a){if(im===document.getElementById('volcano-magma-breath')){const m=g.getTransform();flame={a,m:[m.a,m.b,m.c,m.d,m.e,m.f]};}return original.call(g,im,...a);};gameVolcanoBoss.draw(g);
   const m=flame.m,anchor={x:m[0]*(35+flame.a[0])+m[2]*(158+flame.a[1])+m[4],y:m[1]*(35+flame.a[0])+m[3]*(158+flame.a[1])+m[5]},tip={x:m[0]*(766+flame.a[0])+m[2]*(158+flame.a[1])+m[4],y:m[1]*(766+flame.a[0])+m[3]*(158+flame.a[1])+m[5]},ratio=Math.hypot(m[0],m[1]),ratioY=Math.hypot(m[2],m[3]);
   if(Math.hypot(anchor.x-geo.origin.x,anchor.y-geo.origin.y)>.0001||Math.abs(ratio-ratioY)>1e-6||Math.abs(Math.hypot(tip.x-anchor.x,tip.y-anchor.y)-geo.length)>.0001||Math.abs(Math.atan2(m[1],m[0])-Math.atan2(Math.sin(geo.direction),Math.cos(geo.direction)))>1e-6)throw Error('PNG mouth/tip/rotation/ratio mismatch');
   const transform=g.getTransform();if(transform.a!==1||transform.b||transform.c||transform.d!==1||transform.e||transform.f)throw Error('Effect transform leaked');
   rows.push({angle:geo.angle,direction:geo.direction,origin:geo.origin,anchor,tip,length:geo.length,scale:ratio,matrix:flame});player.x=geo.pivot.x+(n<6?-180:180);player.y=geo.pivot.y;vbAdvance(.12);
  }return {rows,reads:breathReads};})''')
  assert matrices['reads']==1;report['matrices']=matrices
  passed('12 real drawImage matrices: original static image, uniform aspect scale, anchor exactly at animated mouth, visible tip at configured reach, body/flame direction identical; Canvas restored.')
  warning=page.evaluate(r'''()=>vbRun(()=>{vbBegin(2);vbGo('breath_warning');enemyBullets=[];invuln=0;const s=gameVolcanoBoss.snapshot(),geo=gameVolcanoBoss.frameGeometry(boss);player.x=geo.origin.x;player.y=geo.origin.y+40;player.vx=player.vy=0;const before=hp;vbAdvance(.99);return {before,after:hp,phase:gameVolcanoBoss.snapshot().phase,remaining:gameVolcanoBoss.snapshot().remaining};})''');assert warning['before']==warning['after']==9 and warning['phase']=='breath_warning' and abs(warning['remaining']-.01)<1e-7;report['warning']=warning
  passed('Standing in the upcoming fire silhouette during0.99s warning causes no damage; full1.0s warning retained.')
  paths=page.evaluate(r'''()=>{const rows=[];for(const hz of [30,60,120])vbRun(()=>{vbBegin(2);vbGo('breath',1/hz);const s=gameVolcanoBoss.snapshot(),pivot=s.center;let prev=s.angle,maxSpeed=0,pos=0,neg=0;const samples=[];
   for(let i=0;i<Math.round(3.6*hz);i++){
    const t=i/hz,a=t<1.2?-Math.PI/2:t<2.4?Math.PI/2:-Math.PI/2;
    player.x=pivot.x+Math.cos(a)*140;player.y=pivot.y+Math.sin(a)*120;player.vx=player.vy=0;update(1/hz);const st=gameVolcanoBoss.snapshot(),delta=st.angle-prev;maxSpeed=Math.max(maxSpeed,Math.abs(delta)*hz);if(delta>1e-8)pos++;if(delta< -1e-8)neg++;if(i%Math.round(hz*.3)===0)samples.push({time:(i+1)/hz,angle:st.angle,target:st.targetAngle,phase:st.phase});prev=st.angle;
   }return rows.push({hz,maxSpeed,pos,neg,angle:prev,samples});});return rows;}''')
  for row in paths:assert row['pos']>0 and row['neg']>0 and row['maxSpeed']<=70*math.pi/180+1e-7 and all(s['phase']=='breath' for s in row['samples']),row
  assert max(r['angle'] for r in paths)-min(r['angle'] for r in paths)<1e-6,paths;report['dynamic_paths']=paths
  passed('Dynamic player reversals during active breath turn both ways at<=70deg/s; deterministic final angle matches30/60/120Hz without mandatory full revolution.')
  jitter=page.evaluate(r'''()=>vbRun(()=>{vbBegin(0);vbGo('breath');const s=gameVolcanoBoss.snapshot(),angle=s.angle,p=s.center;for(let i=0;i<90;i++){const a=angle+Math.PI/2+(i%2?1:-1)*.25*Math.PI/180;player.x=p.x+Math.cos(a)*140;player.y=p.y+Math.sin(a)*140;player.vx=player.vy=0;update(1/60);}return {before:angle,after:gameVolcanoBoss.snapshot().angle};})''');assert abs(jitter['before']-jitter['after'])<1e-9;report['jitter']=jitter
  passed('Alternating target jitter inside0.5deg deadzone does not rotate the dragon; no direction noise near a stationary player.')
  returned=page.evaluate(r'''()=>vbRun(()=>{vbBegin(0);vbGo('breath_warning');const p=gameVolcanoBoss.snapshot().center;player.x=p.x-150;player.y=p.y;player.vx=player.vy=0;vbAdvance(4.8);const start=gameVolcanoBoss.snapshot();let previous=start.angle,maxSpeed=0;for(let i=0;i<168;i++){update(1/60);const angle=gameVolcanoBoss.snapshot().angle,difference=Math.atan2(Math.sin(angle-previous),Math.cos(angle-previous));maxSpeed=Math.max(maxSpeed,Math.abs(difference)*60);previous=angle;}return {start,end:gameVolcanoBoss.snapshot(),maxSpeed};})''')
  assert returned['start']['phase']=='rest' and abs(returned['start']['remaining']-2.8)<1e-7 and returned['maxSpeed']<=70*math.pi/180+1e-7 and abs(returned['end']['angle'])<1e-8 and returned['end']['phase']=='fire_aim',returned;report['return']=returned
  passed('After3.8s fire stops immediately; whole body returns smoothly at<=70deg/s during unchanged2.8s rest, then original fireball aiming resumes without a heading snap.')
  scenes=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   for kind in range(3):
    page.evaluate('kind=>vbRun(()=>{vbBegin(kind);vbGo("breath");enemyBullets=[];const p=gameVolcanoBoss.snapshot().center;player.x=p.x+150;player.y=p.y;player.vx=player.vy=0;vbAdvance(1.2);})',kind)
    right=page.evaluate('gameVolcanoBoss.snapshot()');page.screenshot(path=str(args.artifacts/f'tracking-right-{kind}-{width}x{height}.png'))
    page.evaluate('vbRun(()=>{const p=gameVolcanoBoss.snapshot().center;player.x=p.x-150;player.y=p.y;player.vx=player.vy=0;vbAdvance(1.4);})')
    left=page.evaluate('gameVolcanoBoss.snapshot()');page.screenshot(path=str(args.artifacts/f'tracking-left-{kind}-{width}x{height}.png'))
    assert left['angle']>right['angle'] and right['phase']==left['phase']=='breath';scenes.append({'viewport':[width,height],'kind':kind,'right':right,'left':left})
  report['screens']=scenes
  passed('Actual current game captures3 heroes x3 landscape sizes: active breath turns right then reverses left with the whole dragon; PNG/UI clipping at screen boundaries is safe.')
  assert not errors,(errors,external)
  if args.standalone:assert not external,external
  context.close()
  # Separate broken-resource context exercises fail-safe through real image loading.
  fail=browser.new_context(viewport={'width':568,'height':320});page=fail.new_page();load_errors=[];page.on('pageerror',lambda e:load_errors.append(str(e)))
  if args.standalone:
   page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');fail.set_offline(True)
   html=(ROOT/'dist/heli_trio_galaxy_test.html').read_text();import re
   html,n=re.subn(r'(<img id="volcano-magma-breath" src=")[^"]+',r'\g<1>data:image/png;base64,AAAA',html);assert n==1;page.set_content(html,wait_until='load')
  else:
   page.route('**/effects/magma_dragon_breath_static.png',lambda route:route.fulfill(status=200,content_type='image/png',body=b'broken-png'));page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.wait_for_function('gameVolcanoBoss.artSnapshot().status==="failed"&&gameVolcano.ready()');page.evaluate(helpers)
  failure=page.evaluate(r'''()=>vbRun(()=>{vbBegin(2);let angles=0;for(let n=0;n<1400;n++){update(1/60);const s=gameVolcanoBoss.snapshot();if(s.phase==='breath'||s.phase==='breath_warning')angles++;}const s=gameVolcanoBoss.snapshot(),geo=gameVolcanoBoss.frameGeometry(boss);return {status:gameVolcanoBoss.artSnapshot(),angles,skipped:s.skipped,shots:s.shots,hit:gameVolcanoBoss.contains({x:geo.origin.x,y:geo.origin.y+20},geo),started};})''')
  assert failure['status']['status']=='failed' and not failure['status']['maskReady'] and failure['angles']==0 and failure['skipped']>=1 and failure['shots']>9 and not failure['hit'] and failure['started'] and not load_errors,failure
  report['failed_resource']=failure
  passed('Real invalid PNG load safely skips only breath, no invisible damage or crash; fireball/eruption cycles continue, native and fully offline.')
  fail.close();browser.close();report['all_passed']=True
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
