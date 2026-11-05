"""Issues19/20 actual dragon cycle, fixed-direction sweep/mouth/PNG alpha, lifecycle and offline checks."""
import argparse,hashlib,json,re,shutil,subprocess,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from volcano_boss_preservation import BOSS_ASSETS,assert_volcano_boss_asset,without_volcano_boss

ROOT=Path(__file__).resolve().parents[1];BASE='78148480330e48a64dd77191006ddb0f0c5e785b'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true')
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':[
 'Chromium mobile/touch emulation; not physical Galaxy/Samsung Internet, sensor hardware, heat/performance or speaker listening.',
 'Real production spawn/update/shoot/hurt/art paths with controlled time/position/invulnerability; separate raster/trajectory fixtures.',
 'Tanko escape uses actual unchanged acceleration/drag from a scripted tilt value, not a claim about human reaction or sensor permission.'
]}
def passed(value):report['passed'].append(value);print('PASS:',value,flush=True)
def old(name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
source=(ROOT/'index.html').read_text();assert without_volcano_boss(source,'index.html').encode()==old('index.html')
asset_hashes={}
for p in (ROOT/'assets').rglob('*'):
 if not p.is_file():continue
 name=str(p.relative_to(ROOT))
 if name in BOSS_ASSETS:assert_volcano_boss_asset(name)
 else:assert (without_volcano_boss(p.read_text(),name).encode() if p.suffix=='.js' else p.read_bytes())==old(name),name
 asset_hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
report['asset_hashes']=asset_hashes
passed('Exact dragon-only hooks/UI notices/ghost transform; all existing PNGs/manifests, normal combat, snow, player/control/score/audio bytes protected; JavaScript parses.')
manifest=json.loads((ROOT/'assets/volcano/asset_manifest.json').read_text());dragon=next(s for s in manifest['monsters'] if s['id']=='magma_dragon');anchors=json.loads((ROOT/'tests/volcano_dragon_mouth_anchors.json').read_text())
with Image.open(ROOT/'assets/volcano'/dragon['atlas']) as atlas:
 for row in anchors['samples']:
  x,y,w,h=row['rect'];ax,ay=row['mouth_in_crop'];px,py=row['atlas_xy']
  assert 0<=ax<w and 0<=ay<h and atlas.getpixel((round(px),round(py)))[3]>=8,row
assert len(anchors['samples'])==21
passed('All21 approved frame mouth landmarks lie on visible source pixels; original atlas SHA, per-frame crop/pivot and132px rendering width retained.')

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
helpers=r'''()=>{
 window.vbKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];
 window.vbStorage=()=>vbKeys.map(k=>localStorage.getItem(k));
 window.vbBegin=(kind=0)=>{window.vbTrace=[];window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}
  gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:5});start(kind);transition=0;spawn=999;invuln=999;keys.fire=false;tilt={x:0,y:0};player.x=W*.5;player.y=H*.8;player.vx=player.vy=0;itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();};
 window.vbRun=fn=>{window.gameExitDialogOpen=false;try{return fn();}finally{window.gameExitDialogOpen=true;draw();}};
 window.vbAdvance=(seconds,step=1/60)=>{let left=seconds;while(left>1e-9&&started){const dt=Math.min(step,left,gameVolcanoBoss.snapshot()?.remaining>1e-9?gameVolcanoBoss.snapshot().remaining:step);update(dt);left-=dt;}};
 window.vbGo=(phase,step=1/60)=>{let steps=0;while(gameVolcanoBoss.snapshot()?.phase!==phase&&steps++<4800&&started){const before=gameVolcanoBoss.snapshot();update(Math.min(step,before?.remaining>1e-9?before.remaining:step));const after=gameVolcanoBoss.snapshot();if(after&&(after.phase!==before.phase||after.shots!==before.shots)){const cfg=gameVolcanoBoss.settings,durations={rest:cfg.rest,fire_aim:cfg.fireAim,fire_burst:cfg.fireGap,eruption_warning:cfg.eruptionWarning,eruption_burst:cfg.eruptionBurst,position:cfg.positionLimit,breath_warning:cfg.breathWarning,breath_hold:cfg.breathHold,breath:cfg.breathDuration};vbTrace.push({phase:after.phase,time:after.age-(durations[after.phase]-after.remaining),age:after.age,remaining:after.remaining,shots:after.shots});}}if(steps>=4800||!started)throw Error('Pattern stalled: '+phase+' '+JSON.stringify(gameVolcanoBoss.snapshot()));return gameVolcanoBoss.snapshot();};
 window.vbHit=()=>{bullets=[];shoot();bullets=[bullets[0]];Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(0);};
 window.vbBodyCall=()=>{let result=null;const original=ctx.drawImage;ctx.drawImage=function(im,...a){result={size:[im.width,im.height],a,m:[ctx.getTransform().a,ctx.getTransform().b,ctx.getTransform().c,ctx.getTransform().d,ctx.getTransform().e,ctx.getTransform().f]};return original.call(ctx,im,...a);};
  try{gameVolcanoBoss.drawActor(ctx,boss);}finally{ctx.drawImage=original;}return result;};
}'''
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
  page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
  if args.standalone:
   page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.wait_for_function('gameVolcanoBoss.artSnapshot().status==="ready"&&gameVolcano.ready()&&gameSnowfield.ready()&&sprites.length===3&&sprites.every(i=>i.complete&&i.naturalWidth>0)');page.evaluate(helpers)
  assert page.evaluate('gameVolcanoBoss.mouthAnchors')==anchors['anchors'];initial=page.evaluate('vbStorage()')
  page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('5');page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap()
  starts=[]
  for kind in range(3):
   page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap()
   state=page.evaluate('({stage,phase,type:player.type,hp:boss.maxHp,enemies:enemies.length,warnings:warnings.length,pattern:gameVolcanoBoss.snapshot().phase})');assert state=={'stage':5,'phase':5,'type':kind,'hp':20,'enemies':0,'warnings':0,'pattern':'rest'},state;starts.append(state)
   page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
  report['ui_starts']=starts
  passed('Actual developer Help -> World2 Volcano5 directly starts all3 selected characters withHP20 dragon, no normal prelude, unchanged fullscreen/exit UI.')
  entries=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   for kind in range(3):
    page.evaluate('(kind)=>vbRun(()=>vbBegin(kind))',kind)
    aim=page.evaluate("vbRun(()=>vbGo('fire_aim'))")
    assert abs(aim['age']-1.8)<1e-7 and aim['shots']==0,aim
    first=page.evaluate("vbRun(()=>{vbGo('fire_burst');return {state:gameVolcanoBoss.snapshot(),bullets:enemyBullets.map(b=>({speed:Math.hypot(b.vx,b.vy),life:b.life,r:b.r,tag:b.volcanoBossPattern}))};})")
    assert len(first['bullets'])==3 and first['state']['shots']==3 and all(abs(b['speed']-88)<1e-7 and b['r']==5.5 and b['tag']=='fireball' and 0<b['life']<=3.2 for b in first['bullets']),first
    if kind==0:page.screenshot(path=str(args.artifacts/f'fireball-{width}x{height}.png'))
    warning=page.evaluate("vbRun(()=>vbGo('eruption_warning'))");assert warning['shots']==9 and warning['volleys']==3 and warning['hazard'] and not warning['hazard']['resolved'],warning
    assert page.evaluate('s=>gameVolcanoBoss.safeCircle(s.hazard.x,s.hazard.y,s.hazard.r)',warning)
    if kind==0:page.screenshot(path=str(args.artifacts/f'eruption-warning-{width}x{height}.png'))
    burst=page.evaluate("vbRun(()=>vbGo('eruption_burst'))");assert burst['hazard']['resolved'] and burst['damageCalls']==0
    if kind==0:page.screenshot(path=str(args.artifacts/f'eruption-burst-{width}x{height}.png'))
    breath_warning=page.evaluate("vbRun(()=>vbGo('breath_warning'))");assert breath_warning['center'] and breath_warning['skipped']==0,breath_warning
    if kind==0:page.screenshot(path=str(args.artifacts/f'breath-warning-{width}x{height}.png'))
    beginning=page.evaluate("vbRun(()=>{vbGo('breath_hold');return {state:gameVolcanoBoss.snapshot(),actor:[boss.x,boss.y],geo:gameVolcanoBoss.frameGeometry(boss)};})");assert beginning['state']['center']
    if kind==0:page.screenshot(path=str(args.artifacts/f'breath-000-{width}x{height}.png'))
    half=page.evaluate('vbRun(()=>{vbAdvance(.2+1.9);return {state:gameVolcanoBoss.snapshot(),actor:[boss.x,boss.y],geo:gameVolcanoBoss.frameGeometry(boss)};})');assert half['actor']==beginning['actor'] and abs(abs(half['state']['angle'])-3.141592653589793)<1e-8
    assert beginning['geo']['origin']['y']>beginning['geo']['pivot']['y'] and half['geo']['origin']['y']<half['geo']['pivot']['y']
    if kind==0:page.screenshot(path=str(args.artifacts/f'breath-180-{width}x{height}.png'))
    end=page.evaluate('vbRun(()=>{vbAdvance(1.9);return {state:gameVolcanoBoss.snapshot(),actor:[boss.x,boss.y]};})');assert abs(end['state']['sweepProgress']-6.283185307179586)<1e-8 and end['state']['phase']=='rest' and end['actor']==beginning['actor'] and end['state']['shots']==9,end
    if kind==0:page.screenshot(path=str(args.artifacts/f'breath-360-{width}x{height}.png'))
    repeated=page.evaluate("vbRun(()=>vbGo('fire_aim'))");assert repeated['next']=='eruption' and repeated['shots']==9
    entries.append({'viewport':[width,height],'kind':kind,'aim':aim,'fire':first,'eruption':warning,'breathWarning':breath_warning,'start':beginning,'half':half,'end':end})
  report['entries']=entries
  passed('9 full real cycles at3 landscape sizes x3 characters:1.8s intro,3x3 aimed bursts only, safe static eruption,1s harmless cue,downward hold.2s then3.8s exact360deg fixed-direction sweep, rest then repeat.')
  render=page.evaluate('''()=>vbRun(()=>{vbBegin(0);vbGo('breath');const rows=[];for(let i=0;i<8;i++){
    const selected=gameVolcano.pose(boss,true),spec=gameVolcano.species.find(s=>s.id==='magma_dragon'),frame=spec.animations[selected.name].frames[selected.index];
    const geo=gameVolcanoBoss.frameGeometry(boss),call=vbBodyCall(),anchor=gameVolcanoBoss.mouthAnchors[selected.name][selected.index],px=call.a[0]+anchor[0]*call.a[2]/frame.rect_px[2],py=call.a[1]+anchor[1]*call.a[3]/frame.rect_px[3],m=call.m;
    const mouth={x:m[0]*px+m[2]*py+m[4],y:m[1]*px+m[3]*py+m[5]};
    if(Math.hypot(mouth.x-geo.origin.x,mouth.y-geo.origin.y)>1e-4||Math.abs(m[0]*m[3]-m[1]*m[2]-1)>1e-9||Math.abs(call.a[2]/frame.rect_px[2]-call.a[3]/frame.rect_px[3])>1e-10)throw Error('Mouth/scale/whole-frame rotation mismatch');
    const transform=ctx.getTransform();if(transform.a!==1||transform.b!==0||transform.c!==0||transform.d!==1||transform.e!==0||transform.f!==0)throw Error('Transform leaked');
    rows.push({angle:gameVolcanoBoss.snapshot().angle,mouth,origin:geo.origin,pivot:geo.pivot,selected:{name:selected.name,index:selected.index},call});vbAdvance(.475);
   }return rows;})''')
  assert len(render)==8;report['render']=render
  passed('8 actual boss draw matrices rotate the whole cached frame without squashing; transformed source-mouth pixels equal flame origins and canvas transform restores exactly.')
  raster=page.evaluate(r'''()=>vbRun(()=>{vbBegin(0);vbGo('breath');const art=gameVolcanoBoss.breathArt,im=document.getElementById('volcano-magma-breath'),source=document.createElement('canvas');source.width=im.naturalWidth;source.height=im.naturalHeight;const sg=source.getContext('2d');sg.drawImage(im,0,0);const alpha=sg.getImageData(0,0,source.width,source.height).data,rows=[];
    for(let n=0;n<8;n++){
     const geo=gameVolcanoBoss.frameGeometry(boss),rects=gameVolcanoBoss.blockedRects(),probe=document.createElement('canvas');probe.width=W;probe.height=H;const g=probe.getContext('2d');gameVolcanoBoss.draw(g);const pixels=g.getImageData(0,0,W,H).data;let checked=0,mismatch=0,transparent=0,lit=0;
     for(let y=2;y<H-2;y+=2)for(let x=2;x<W-2;x+=2){const q={x:x+.5,y:y+.5},dx=q.x-geo.origin.x,dy=q.y-geo.origin.y,c=Math.cos(geo.direction),sn=Math.sin(geo.direction),px=Math.floor((dx*c+dy*sn)/geo.artScale+35),py=Math.floor((-dx*sn+dy*c)/geo.artScale+158),inside=px>=0&&px<768&&py>=0&&py<230,ui=rects.some(b=>q.x>=b.left&&q.x<=b.right&&q.y>=b.top&&q.y<=b.bottom),expected=inside&&!ui&&alpha[(py*768+px)*4+3]>=96,hit=gameVolcanoBoss.contains(q,geo,rects);
      if(expected!==hit)mismatch++;checked++;
      if(!inside||ui||px<3||py<3||px>764||py>226)continue;
      let min=255,max=0;for(let yy=py-2;yy<=py+2;yy++)for(let xx=px-2;xx<=px+2;xx++){const v=alpha[(yy*768+xx)*4+3];min=Math.min(min,v);max=Math.max(max,v);}
      if(min>=150){if(pixels[(y*W+x)*4+3]<96)mismatch++;lit++;}if(max===0){if(pixels[(y*W+x)*4+3]>=96||hit)mismatch++;transparent++;}
     }
     if(mismatch)throw Error('PNG alpha/draw/hit mismatch '+mismatch);rows.push({angle:geo.angle,checked,mismatch,transparent,lit});player.x=geo.pivot.x+Math.cos(n*Math.PI/4)*150;player.y=geo.pivot.y+Math.sin(n*Math.PI/4)*100;vbAdvance(.2);
    }return rows;})''')
  report['raster']=raster;assert sum(r['checked'] for r in raster)>10000 and sum(r['transparent'] for r in raster)>1000
  passed('Independent original PNG alpha inverse-transform oracle matches damage; opaque interiors render and transparent holes remain harmless across8 orientations, including UI masks.')
  eruption=page.evaluate('''()=>vbRun(()=>{vbBegin(2);vbGo('eruption_warning');const before=gameVolcanoBoss.snapshot(),h=before.hazard;enemyBullets=[];player.x=h.x;player.y=h.y;invuln=0;const hpBefore=hp;
    vbAdvance(before.remaining-.0001);const warningHP=hp;player.x+=3;const unchanged=JSON.stringify(gameVolcanoBoss.snapshot().hazard)===JSON.stringify(h);player.x=h.x;vbAdvance(.0001);const burstHP=hp,s=gameVolcanoBoss.snapshot();vbAdvance(.25);return {hpBefore,warningHP,burstHP,finalHP:hp,unchanged,damageCalls:s.damageCalls,resolved:s.hazard.resolved};})''')
  assert eruption=={'hpBefore':9,'warningHP':9,'burstHP':8,'finalHP':8,'unchanged':True,'damageCalls':1,'resolved':True},eruption
  report['eruption_damage']=eruption
  passed('Standing inside eruption warning gives0 damage; fixed target does not track movement; exactly one1HP detonation, no repeated burst damage.')
  fps=page.evaluate(r'''()=>{const rows=[];for(const hz of [30,60,120])for(const outside of [false,true])vbRun(()=>{
    vbBegin(2);vbGo('breath',1/hz);const direction=gameVolcanoBoss.snapshot().sweepDirection;invuln=0;enemyBullets=[];const before=hp;let elapsed=0;
    while(elapsed<3.8-1e-9){const dt=Math.min(1/hz,3.8-elapsed),state=gameVolcanoBoss.snapshot(),next=gameVolcanoBoss.frameGeometry(boss,gameVolcano.pose(boss,true),direction*Math.PI*2*Math.min(1,(elapsed+dt)/3.8),state.center);
      if(outside){player.x=W-14;player.y=next.pivot.y;}else{const distance=next.artScale*(160-35);player.x=next.origin.x+Math.cos(next.direction)*distance;player.y=next.origin.y+Math.sin(next.direction)*distance;}
      player.vx=player.vy=0;update(dt);elapsed+=dt;
    }
    const state=gameVolcanoBoss.snapshot();rows.push({hz,outside,hpBefore:before,hpAfter:hp,angle:state.angle,progress:state.sweepProgress,damageCalls:state.damageCalls,phase:state.phase,trace:[...vbTrace]});
   });return rows;}''')
  for row in fps:assert row['phase']=='rest' and abs(row['progress']-2*3.141592653589793)<1e-8 and row['hpBefore']-row['hpAfter']==(0 if row['outside'] else 3) and row['damageCalls']==(0 if row['outside'] else 3),row
  for row in fps:
   events=row['trace'];volleys=[e for e in events if e['shots'] in [3,6,9] and e['phase'] in ['fire_burst','rest']][:3]
   assert len(volleys)==3 and all(abs(e['time']-t)<1e-7 for e,t in zip(volleys,[2.2,2.52,2.84])),volleys
   times={e['phase']:e['time'] for e in events};assert abs(times['eruption_burst']-times['eruption_warning']-1.25)<1e-7 and abs(times['breath_hold']-times['breath_warning']-1)<1e-7 and abs(times['breath']-times['breath_hold']-.2)<1e-7,times
  report['fps_damage']=fps
  passed('30/60/120Hz preserve volley/eruption timing,1s warning,.2s flame-first hold,3.8s exact2pi; flame core retains3 invulnerable-spaced hits, screen-safe far point takes0.')
  directions=page.evaluate(r'''()=>{const rows=[];for(const hz of [30,60,120])for(const side of ['left','right','up','down'])vbRun(()=>{
    vbBegin(2);vbGo('breath_warning',1/hz);const p=gameVolcanoBoss.snapshot().center;player.x=p.x+(side==='left'?-140:side==='right'?140:0);player.y=p.y+(side==='up'?-100:side==='down'?100:0);player.vx=player.vy=0;
    vbAdvance(1.2,1/hz);const start=gameVolcanoBoss.snapshot(),observed=JSON.stringify(start.observedPlayer);player.x=p.x+(side==='right'?-140:140);player.y=p.y;vbAdvance(1.9,1/hz);const half=gameVolcanoBoss.snapshot();vbAdvance(1.9,1/hz);const end=gameVolcanoBoss.snapshot();rows.push({hz,side,start,half,end,observedUnchanged:JSON.stringify(end.observedPlayer)===observed});
   });return rows;}''')
  for row in directions:
   sign=-1 if row['side']=='right' else 1
   assert row['start']['phase']=='breath' and row['start']['sweepDirection']==sign and abs(row['start']['angle'])<1e-8 and row['half']['sweepDirection']==sign and abs(row['half']['angle']-sign*3.141592653589793)<1e-8 and row['end']['phase']=='rest' and abs(row['end']['angle']-sign*2*3.141592653589793)<1e-8 and row['observedUnchanged'],row
  report['sweep_directions']=directions
  passed('Left->CW, right->CCW, up/down ties->CW at rotation start; opposite-side movement cannot change direction, midpoint pi or exact2pi completion at30/60/120Hz.')
  dynamic=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   row=page.evaluate(r'''()=>vbRun(()=>{vbBegin(2);vbGo('breath_warning');enemyBullets=[];invuln=0;const geo=gameVolcanoBoss.frameGeometry(boss);player.x=geo.pivot.x+160;player.y=geo.pivot.y;player.vx=player.vy=0;tilt={x:1,y:0};const start={x:player.x,y:player.y,hp};vbAdvance(1);const cue={x:player.x,y:player.y,hp,angle:gameVolcanoBoss.snapshot().angle};vbAdvance(4);return {viewport:[W,H],length:geo.length,start,cue,end:{x:player.x,y:player.y,hp,angle:gameVolcanoBoss.snapshot().angle},calls:gameVolcanoBoss.snapshot().damageCalls};})''')
   assert row['length']==max(165,min(205,height*.52)) and row['start']['hp']==row['cue']['hp']==row['end']['hp']==9 and row['calls']==0 and row['cue']['x']>row['start']['x']+80 and row['end']['x']>row['start']['x']+90,row
   dynamic.append(row)
  report['tanko_escape']=dynamic
  passed('166.4/187.2/205px visual reach scales with landscape height; actual unchanged Tanko acceleration/drag can escape the full sweep from160px center-distance with lateral tilt at all3 sizes,0HP loss.')
  capacity=page.evaluate('''()=>vbRun(()=>{vbBegin(0);enemyBullets=Array.from({length:18},()=>({x:40,y:H*.4,vx:0,vy:0,life:3.2,r:5.5,volcanoBossPattern:'fireball'}));vbGo('fire_burst');const capped={count:enemyBullets.filter(b=>b.volcanoBossPattern).length,shots:gameVolcanoBoss.snapshot().shots};
    enemyBullets.forEach(b=>b.life=0);vbAdvance(.32);const resumed=gameVolcanoBoss.snapshot().shots;vbBegin(0);enemyBullets=Array.from({length:28},()=>({x:40,y:H*.4,vx:0,vy:0,life:999,r:5,volcanoFire:'ember_bean'}));vbGo('fire_burst');const separate={normal:enemyBullets.filter(b=>b.volcanoFire).length,boss:enemyBullets.filter(b=>b.volcanoBossPattern).length};enemyBullets=enemyBullets.filter(b=>b.volcanoBossPattern);vbAdvance(4);return {capped,resumed,separate,expired:enemyBullets.filter(b=>b.volcanoBossPattern&&b.life>0).length};})''')
  assert capacity=={'capped':{'count':18,'shots':0},'resumed':3,'separate':{'normal':28,'boss':3},'expired':0},capacity
  report['capacity']=capacity
  passed('Boss fireballs cap at18 separately from normal28, resume after expiration and disappear by finite life; no legacy unmarked boss shot duplicates.')
  skip=page.evaluate('''()=>vbRun(()=>{vbBegin(0);vbGo('fire_burst');while(gameVolcanoBoss.snapshot().phase!=='rest')update(.01);const el=document.getElementById('rotationJoystick'),old=el.getAttribute('style');el.style.cssText='position:fixed!important;left:0!important;top:0!important;width:100vw!important;height:100vh!important;display:block!important';
    vbAdvance(gameVolcanoBoss.snapshot().remaining);const s=gameVolcanoBoss.snapshot();if(old===null)el.removeAttribute('style');else el.setAttribute('style',old);return {phase:s.phase,skipped:s.skipped,hazard:s.hazard};})''')
  assert skip=={'phase':'rest','skipped':1,'hazard':None},skip
  report['no_safe_area']=skip
  passed('A forced no-safe-circle UI fixture skips eruption safely instead of placing a warning/damage under controls; shipped UI unchanged.')
  deaths=[]
  for kind in range(3):
   row=page.evaluate('''kind=>vbRun(()=>{vbBegin(kind);if(kind===0){vbGo('breath');vbAdvance(1.9);}const actor=boss,angle=gameVolcanoBoss.snapshot().angle;let hits=0;while(boss&&hits++<50)vbHit();if(boss)throw Error('Boss kill stalled');
    const immediate={started,score:runScore,state:gameVolcanoBoss.snapshot(),death:gameVolcanoBoss.deathSnapshot(),advancing:gameVolcano.snapshot().advancing,angle};grantBossReward(actor);gameScoring.bossDefeated(actor);vbAdvance(.93);const waiting=started;vbAdvance(.02);return {kind,hits,immediate,waiting,after:{started,score:runScore,state:gameVolcanoBoss.snapshot(),death:gameVolcanoBoss.deathSnapshot()}};})''',kind)
   assert row['immediate']['started'] and row['immediate']['score']==2000 and row['immediate']['state'] is None and row['immediate']['advancing'] and row['waiting'] and row['after']=={'started':False,'score':2000,'state':None,'death':None},row
   if kind==0:assert abs(row['immediate']['death']['angle']-row['immediate']['angle'])<1e-8
   deaths.append(row)
  report['deaths']=deaths
  passed('All3 characters kill the dragon through actual bullets; death immediately cancels hazards/rotation, preserves last angle and.94s art outro, awards2000/reward once and leaves developer records unsaved.')
  # Pausing is tested through actual engine gating and real dialog buttons.
  page.evaluate("vbRun(()=>{vbBegin(0);vbGo('breath');})")
  hidden=page.evaluate('''()=>{const before=gameVolcanoBoss.snapshot();Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});window.gameExitDialogOpen=false;update(.5);const after=gameVolcanoBoss.snapshot();delete document.hidden;window.gameExitDialogOpen=true;return {before,after};}''');assert hidden['before']==hidden['after']
  page.evaluate('window.gameExitDialogOpen=false');page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();paused=page.evaluate('gameVolcanoBoss.snapshot()');page.wait_for_timeout(150);assert page.evaluate('gameVolcanoBoss.snapshot()')==paused
  page.locator('#gameExitCancel').tap();page.wait_for_timeout(70);assert page.evaluate('gameVolcanoBoss.snapshot().age')>paused['age']
  page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();assert page.evaluate('gameVolcanoBoss.snapshot()===null&&gameVolcanoBoss.deathSnapshot()===null&&!enemyBullets.some(b=>b.volcanoBossPattern)')
  passed('Hidden-tab fixture and real exit dialog freeze angle/time/damage; Continue resumes, confirmed exit clears hazard state and boss bullets without native dialogs.')
  page.evaluate("vbRun(()=>{vbBegin(0);vbGo('breath');vbAdvance(.95);})")
  fatal=page.evaluate('''()=>{window.gameExitDialogOpen=false;const angle=gameVolcanoBoss.snapshot().angle;hp=0;window.vbFatal=performance.now();update(0);return {angle,stopped:!started,state:gameVolcanoBoss.snapshot(),pending:gameOverPending};}''');assert fatal['stopped'] and fatal['pending'] and fatal['state'] is None
  expect(page.locator('#gameOverOverlay')).to_be_visible();page.screenshot(path=str(args.artifacts/'boss-game-over.png'));elapsed=page.evaluate('performance.now()-vbFatal');page.wait_for_timeout(max(0,2400-elapsed));expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_visible(timeout=4000)
  assert page.evaluate('performance.now()-vbFatal')>=2990 and page.locator('#selectionResult').inner_text()=='' and page.evaluate('gameVolcanoBoss.snapshot()===null&&gameVolcanoBoss.deathSnapshot()===null')
  report['game_over']=fatal
  passed('HP0 clears active attacks immediately and keeps existing3s GAME OVER then clean selection; no stale boss state or result text.')
  assert page.evaluate('vbStorage()')==initial
  assert not errors and not dialogs and not failed,(errors,dialogs,failed)
  if args.standalone:assert not external,external
  report.update(page_errors=errors,native_dialogs=dialogs,failed_requests=failed,offline_external_requests=external if args.standalone else [],all_passed=True)
  passed('Four ranking/history keys remain byte-unchanged in developer tests; native/offline resources load with0 JS/dialog errors and offline external requests0.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
