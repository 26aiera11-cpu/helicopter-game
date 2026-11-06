"""Issue21 flame-first downward hold, one-time direction and exact360 sweep with original static art."""
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
  order=page.evaluate(r'''()=>vbRun(()=>{vbBegin(2);vbGo('breath_warning');enemyBullets=[];const p=gameVolcanoBoss.snapshot().center;player.x=p.x+150;player.y=p.y;player.vx=player.vy=0;
   const frame=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d'),original=g.drawImage;let png=0;g.drawImage=function(im,...a){if(im===document.getElementById('volcano-magma-breath'))png++;return original.call(g,im,...a);};gameVolcanoBoss.draw(g);return {...gameVolcanoBoss.snapshot(),png};};
   vbAdvance(.999);const warning=frame();vbAdvance(.001);const first=frame();vbAdvance(.199);const hold=frame();vbAdvance(.001);const zero=frame();vbAdvance(.001);const moving=frame();vbAdvance(.949);const quarter=frame();vbAdvance(.95);const half=frame();vbAdvance(.95);const threeQuarter=frame();vbAdvance(.949);const last=frame();vbAdvance(.001);const end=frame();return {warning,first,hold,zero,moving,quarter,half,threeQuarter,last,end};})''')
  assert order['warning']['phase']=='breath_warning' and order['warning']['png']==0 and order['warning']['angle']==0
  for name in ['first','hold']:assert order[name]['phase']=='breath_hold' and order[name]['png']==1 and order[name]['angle']==0 and order[name]['sweepDirection']==0,order
  assert order['zero']['phase']=='breath' and order['zero']['angle']==0 and order['zero']['sweepDirection']==-1 and order['moving']['angle']<0
  for key,value in [('quarter',-math.pi/2),('half',-math.pi),('threeQuarter',-math.pi*1.5)]:assert abs(order[key]['angle']-value)<1e-8 and order[key]['png']==1
  assert order['last']['phase']=='breath' and order['last']['png']==1 and order['end']['phase']=='rest' and order['end']['png']==0 and abs(order['end']['angle']+2*math.pi)<1e-8
  report['ordered_frames']=order
  passed('Actual effect draw calls: harmless downward warning -> full downward PNG at0s/.199s -> rotation after.2s ->90/180/270/360; PNG stops exactly at the downward360 endpoint.')
  early_damage=page.evaluate(r'''()=>vbRun(()=>{vbBegin(2);vbGo('breath_warning');enemyBullets=[];invuln=0;const geo=gameVolcanoBoss.frameGeometry(boss);player.x=geo.origin.x;player.y=geo.origin.y+geo.artScale*125;player.vx=player.vy=0;const before=hp;vbAdvance(.999);const warning=hp;vbAdvance(.001);const first=hp,state=gameVolcanoBoss.snapshot();vbAdvance(.199);return {before,warning,first,held:hp,phase:state.phase,calls:state.damageCalls};})''')
  assert early_damage=={'before':9,'warning':9,'first':8,'held':8,'phase':'breath_hold','calls':1},early_damage;report['initial_damage']=early_damage
  passed('Alpha damage begins in the same update as the first visible held PNG; warning causes0, initial fire causes1, existing invulnerability blocks repeated hold damage.')
  samples=page.evaluate(r'''()=>{const rows=[];for(const hz of [30,60,120])for(const side of ['left','right','up','down'])vbRun(()=>{vbBegin(2);vbGo('breath_warning',1/hz);const p=gameVolcanoBoss.snapshot().center;
   player.x=p.x-140;player.y=p.y;player.vx=player.vy=0;vbAdvance(1,1/hz);const hold=gameVolcanoBoss.snapshot();player.x=p.x+(side==='left'?-140:side==='right'?140:0);player.y=p.y+(side==='up'?-100:side==='down'?100:0);vbAdvance(.2,1/hz);const start=gameVolcanoBoss.snapshot(),observed=JSON.stringify(start.observedPlayer);let maxError=0,signChanges=0;
   for(let i=0;i<Math.round(3.8*hz);i++){player.x=p.x+(i%2?-140:140);player.y=p.y+(i%3?-70:70);player.vx=player.vy=0;update(1/hz);const state=gameVolcanoBoss.snapshot();maxError=Math.max(maxError,Math.abs(state.angle-start.sweepDirection*Math.PI*2*(i+1)/(3.8*hz)));if(state.sweepDirection!==start.sweepDirection||JSON.stringify(state.observedPlayer)!==observed)signChanges++;}
   const end=gameVolcanoBoss.snapshot();rows.push({hz,side,hold,start,end,maxError,signChanges});});return rows;}''')
  for row in samples:
   assert row['hold']['phase']=='breath_hold' and row['hold']['sweepDirection']==0 and row['hold']['observedPlayer'] is None
   assert row['start']['sweepDirection']==(-1 if row['side']=='right' else 1) and row['end']['phase']=='rest' and abs(row['end']['sweepProgress']-math.pi*2)<1e-8 and row['maxError']<1e-8 and row['signChanges']==0,row
  report['direction_samples']=samples
  passed('Sample is taken after the.2s hold, not during warning: left CW/right CCW/up-down ties CW; mid-sweep player teleports never change sign/angle rate or observation at30/60/120Hz.')
  returned=page.evaluate(r'''()=>vbRun(()=>{vbBegin(0);vbGo('breath_hold');vbAdvance(4);const start=gameVolcanoBoss.snapshot(),geo=gameVolcanoBoss.frameGeometry(boss);vbAdvance(2.8);return {start,end:gameVolcanoBoss.snapshot(),downward:Math.cos(geo.direction),vertical:Math.sin(geo.direction)};})''')
  assert returned['start']['phase']=='rest' and abs(returned['start']['remaining']-2.8)<1e-7 and abs(returned['downward'])<1e-8 and abs(returned['vertical']-1)<1e-8 and returned['end']['phase']=='fire_aim' and returned['end']['angle']==0,returned;report['return']=returned
  passed('At4.0s total fire time, full360 ends facing down with no residual flame; unchanged2.8s rest then original fireball aiming resumes, no extra home turn.')
  scenes=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   for kind in range(3):
    for side in ['left','right']:
     page.evaluate('({kind,side})=>vbRun(()=>{vbBegin(kind);vbGo("breath_warning");const p=gameVolcanoBoss.snapshot().center;player.x=p.x+(side==="right"?150:-150);player.y=p.y;player.vx=player.vy=0;enemyBullets=[];vbAdvance(1);})',{'kind':kind,'side':side})
     first=page.evaluate('gameVolcanoBoss.snapshot()');page.screenshot(path=str(args.artifacts/f'hold-{side}-{kind}-{width}x{height}.png'))
     page.evaluate('vbRun(()=>vbAdvance(.2+1.9))');half=page.evaluate('gameVolcanoBoss.snapshot()');page.screenshot(path=str(args.artifacts/f'half-{side}-{kind}-{width}x{height}.png'))
     assert first['phase']=='breath_hold' and first['angle']==0 and abs(half['angle']-(1 if side=='left' else -1)*math.pi)<1e-8;scenes.append({'viewport':[width,height],'kind':kind,'side':side,'first':first,'half':half})
  report['screens']=scenes
  passed('Actual screenshots3 heroes x3 landscape sizes x2 sides show downward PNG before rotation and correct half-turn body/flame, with original dimensions/alpha/UI clipping.')
  page.evaluate(r'''()=>{vbRun(()=>{vbBegin(2);vbGo('breath_warning');vbAdvance(.85);});window.sweepFrames=[];window.sweepDraw=ctx.drawImage;ctx.drawImage=function(im,...a){if(im===document.getElementById('volcano-magma-breath')){const s=gameVolcanoBoss.snapshot();sweepFrames.push({phase:s.phase,age:s.age,angle:s.angle,clock:performance.now()});}return sweepDraw.call(ctx,im,...a);};window.gameExitDialogOpen=false;}''')
  page.wait_for_function('sweepFrames.some(f=>Math.abs(f.angle)>.2)',timeout=5000)
  live=page.evaluate('()=>{window.gameExitDialogOpen=true;ctx.drawImage=sweepDraw;draw();return sweepFrames;}');assert live[0]['phase']=='breath_hold' and live[0]['angle']==0 and any(f['phase']=='breath' and abs(f['angle'])>0 for f in live);hold=[f for f in live if f['phase']=='breath_hold'];moving=[f for f in live if abs(f['angle'])>1e-8];assert len(hold)>=2 and min(f['age'] for f in moving)-hold[0]['age']>=.2-1/30,live;report['real_raf_frames']=live
  passed('Unpaused production requestAnimationFrame loop draws multiple full downward-PNG frames before the first moving frame; first visible fire is not pre-rotated.')
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
  failure=page.evaluate(r'''()=>vbRun(()=>{vbBegin(2);let angles=0;for(let n=0;n<1400;n++){update(1/60);const s=gameVolcanoBoss.snapshot();if(s.phase==='breath'||s.phase==='breath_warning'||s.phase==='breath_hold')angles++;}const s=gameVolcanoBoss.snapshot(),geo=gameVolcanoBoss.frameGeometry(boss);return {status:gameVolcanoBoss.artSnapshot(),angles,skipped:s.skipped,shots:s.shots,hit:gameVolcanoBoss.contains({x:geo.origin.x,y:geo.origin.y+20},geo),started};})''')
  assert failure['status']['status']=='failed' and not failure['status']['maskReady'] and failure['angles']==0 and failure['skipped']>=1 and failure['shots']>9 and not failure['hit'] and failure['started'] and not load_errors,failure
  report['failed_resource']=failure
  passed('Real invalid PNG load safely skips only breath, no invisible damage or crash; fireball/eruption cycles continue, native and fully offline.')
  fail.close();browser.close();report['all_passed']=True
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
