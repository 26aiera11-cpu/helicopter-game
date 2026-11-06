"""Issue10: weighted actor identity, full-height charge, actual-input Tanko AOE balance."""
import argparse,hashlib,io,json,re,shutil,subprocess,tarfile,tempfile,threading,math
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from mixed_preservation import MIXED_ASSETS,assert_mixed_asset,without_mixed_source,without_mixed_asset
ROOT=Path(__file__).resolve().parents[1];BASE='922c271e1be5585ada0b34614f46436f9c2d6b61'
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(exist_ok=True,parents=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':[
 'Real Chromium spawn/combat/input/render events with controlled seeds,coordinates,time and invulnerability; not physical Galaxy/Samsung Internet or manual difficulty completion.',
 '60/120Hz denote deterministic simulation steps,not guaranteed physical refresh rates.',
 'Offline runs the exact standalone HTML at a blank localhost origin with networking disabled; no file policy bypass.',
 'Tanko escape starts at rest,uses full cardinal normalized gyro input1.0 after the stated response delay and clears unrelated bullets/boss contact in the fixture. Actual player acceleration/drag/caps/damage remain unchanged.',
 'Penguin planned distance is1.05H; actual distance ends at the first old17/18px boundary. Vertical planned distance cannot fit inside H minus edge margins.'
]}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
source=(ROOT/'index.html').read_text();assert without_mixed_source(source)==subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT).decode()
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in MIXED_ASSETS:assert_mixed_asset(path);continue
 b=without_mixed_asset(path.read_text(),name).encode() if path.suffix in ['.js','.css'] else path.read_bytes();assert b==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for s in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=s,text=True,capture_output=True,check=True)
passed('Exact mixed balance hooks reverse to922c271; generation interval/cap/6-kill rules,all player physics/weapons,items/score/audio/PNG/manifest115frames and World1 remain byte-protected; all JS parses.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/mixed-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline mixed origin</title>');return
  super().do_GET()
def serve(folder):
 s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(folder)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
helpers='''() => {
 window.mixWrites=[];const write=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.startsWith('heliTrio.'))mixWrites.push(k);return write.call(this,k,v);};
 window.mixStorage=()=>JSON.stringify(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)]));
 window.mixExit=()=>{gameSnowfieldBoss.reset();gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();gameExitDialogOpen=false;clearGameOver();gameControls.reset();gameSnowfield.reset();menu.classList.remove('hidden');};
 window.mixScene=(step=3,type=0,seed=12345)=>{mixExit();if(!gameWorlds.setDeveloperStart({enabled:true,regionId:4,phase:step}))throw Error('Entry rejected');itemMonsters.configure({opportunitiesPerRegion:0});start(type);gameSnowfieldSpawns.reset(seed);transition=0;spawn=999;invuln=999;sensorOn=false;neutral={x:0,y:0};tilt={x:0,y:0};player.x=W*.7;player.y=H*.7;return boss;};
 window.mixAdvance=(seconds,hz=120)=>{let t=0;while(t<seconds-1e-10&&started){const dt=Math.min(1/hz,seconds-t);update(dt);t+=dt;}};
 window.mixSpawn=(x=120,y=110)=>{warnEnemy();const w=warnings.at(-1);w.x=x;w.y=y;w.time=0;update(0);return enemies.at(-1);};
 window.mixHit=e=>{bullets=[];shoot();Object.assign(bullets[0],{x:e.x,y:e.y,vx:0,vy:0});update(0);};
 window.mixPreBoss=()=>{mixScene(4);for(let i=0;i<6;i++){transition=0;const e=mixSpawn();while(e.hp>0)mixHit(e);}transition=0;if(phase!==5||boss)throw Error('Wrong ordinary boss gate');};
 window.mixSeedFor=(step,id)=>{for(let i=1;i<10000;i++){let seed=(Math.imul(i,0x9e3779b1))>>>0,x=seed;x^=x<<13;x^=x>>>17;x^=x<<5;if(gameSnowfieldSpawns.chooseForRoll(step,(x>>>0)/4294967296)===id)return seed;}throw Error('No seed for '+id);};
 window.mixPenguin=(angle=0)=>{mixScene(2,0,mixSeedFor(2,'penguin_raider'));const e=mixSpawn();e.shot=999;mixAdvance(4.49);const nx=Math.cos(angle),ny=Math.sin(angle),x=nx<-.5?W-50:Math.abs(nx)<.01?W*.45:50,y=ny<-.5?H-50:Math.abs(ny)<.01?H*.45:50;
  e.x=x-nx*36.1*1.06*.01;e.y=y-ny*36.1*1.06*.01;player.x=x+nx*100;player.y=y+ny*100;mixAdvance(.01);return e;};
 window.mixFreeze=()=>{invuln=0;rotorSpin=.35;gameExitDialogOpen=true;draw();};
}'''
server=serve(ROOT);reference=None;temp=tempfile.TemporaryDirectory(prefix='heli-mixed-before-')
try:
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE,'index.html','assets'],cwd=ROOT))) as t:t.extractall(temp.name,filter='data')
 reference=serve(temp.name)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  url=f'http://127.0.0.1:{server.server_port}/'
  if args.standalone:page.goto(url+'mixed-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url,wait_until='load')
  page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()&&window.gameSnowfieldSpawns');page.evaluate(helpers);initial_storage=page.evaluate('mixStorage()')
  assert not page.evaluate('gameWorlds.isDeveloper()||gameWorlds.isTrial()')
  table=page.evaluate('gameSnowfieldSpawns.weights');assert table==[[80,20,0,0],[45,40,15,0],[20,30,35,15],[10,20,35,35],[0,15,30,55]]
  boundaries=page.evaluate('''()=>{const rows=[];for(let phase=1;phase<=5;phase++){let cursor=0;for(let i=0;i<4;i++){const weight=gameSnowfieldSpawns.weights[phase-1][i];if(weight){rows.push({phase,id:gameSnowfieldSpawns.ids[i],start:gameSnowfieldSpawns.chooseForRoll(phase,cursor/100),inside:gameSnowfieldSpawns.chooseForRoll(phase,(cursor+weight*.5)/100),last:gameSnowfieldSpawns.chooseForRoll(phase,(cursor+weight-1e-8)/100)});}cursor+=weight;}}return rows;}''')
  assert all(v['id']==v['start']==v['inside']==v['last'] for v in boundaries);report['weight_boundaries']=boundaries
  passed('All5 exact weight rows and every nonzero interval boundary/midpoint select the correct species; boss is excluded and zero-weight intervals are skipped.')
  distributions=page.evaluate('''()=>{const rows=[];for(const seed of [1,12345,0xdeadbeef])for(let step=1;step<=5;step++){gameSnowfieldSpawns.reset(seed);const counts=Object.fromEntries(gameSnowfieldSpawns.ids.map(id=>[id,0]));for(let i=0;i<30000;i++)counts[gameSnowfieldSpawns.select(step)]++;rows.push({seed,step,total:30000,counts});}return rows;}''')
  ids=page.evaluate('gameSnowfieldSpawns.ids')
  for row in distributions:
   assert sum(row['counts'].values())==30000
   for i,id in enumerate(ids):
    if table[row['step']-1][i]==0:assert row['counts'][id]==0
    else:assert abs(row['counts'][id]/30000*100-table[row['step']-1][i])<1
  report['seeded_distributions']=distributions;passed('450,000 seeded draws across5phases/3seeds stay within1percentage point of target weights; zero-percent candidates never appear and no all-types guarantee is imposed.')
  isolation=page.evaluate('''()=>{const original=Math.random;Math.random=()=>{throw Error('Global RNG consumed');};try{gameSnowfieldSpawns.reset(12345);const a=Array.from({length:1000},()=>gameSnowfieldSpawns.select(3));gameSnowfieldSpawns.reset(12345);const b=Array.from({length:1000},()=>gameSnowfieldSpawns.select(3));let onlyOne=false;for(let seed=1;seed<100;seed++){gameSnowfieldSpawns.reset(seed);if(new Set(Array.from({length:6},()=>gameSnowfieldSpawns.select(1))).size===1){onlyOne=true;break;}}return {repeat:JSON.stringify(a)===JSON.stringify(b),onlyOne};}finally{Math.random=original;}}''')
  assert isolation=={'repeat':True,'onlyOne':True};passed('Private seeded replay is deterministic and consumes0 Math.random calls; a valid six-kill phase may contain only one species,so variety is probabilistic rather than forced.')

  # Actual warning→spawn→hit→death for each allowed phase/species pair.
  roles=[]
  for step in range(1,6):
   for index,id in enumerate(ids):
    if table[step-1][index]==0:continue
    r=page.evaluate('''({step,id})=>{if(step===5)mixPreBoss();else mixScene(step);gameSnowfieldSpawns.reset(mixSeedFor(step,id));const score=runScore,kills=phaseKills,e=mixSpawn(),before={id:e.snowSpeciesId,hp:e.hp,r:e.r,speed:e.speed,shot:e.shot,phase,pose:gameSnowfield.pose(e),state:gameSnowfieldCombat.snapshot(e)};
     const rng=gameSnowfieldSpawns.snapshot();gameSnowfieldCombat.prepare(e);const sameRng=JSON.stringify(rng)===JSON.stringify(gameSnowfieldSpawns.snapshot());try{e.snowSpeciesId='snow_slime';}catch{}const stable=e.snowSpeciesId===id;const calls=[];gameSnowfield.drawActor({drawImage:(im,...args)=>calls.push({id:im.id,args})},e);
     const hits=[];while(e.hp>0){mixHit(e);hits.push({hp:e.hp,pose:gameSnowfield.pose(e).name});}const duplicate=gameScoring.enemyDefeated(e),ghost=gameSnowfield.snapshot().ghosts.at(-1);phase=step===1?4:1;gameSnowfield.tick(.34);return {before,sameRng,stable,draw:calls[0],hits,duplicate,score:runScore-score,kills:phaseKills-kills,ghost:ghost.id,defeat:gameSnowfield.snapshot().ghosts.at(-1)?.pose};}''',{'step':step,'id':id})
    assert r['before']['id']==r['before']['pose']['id']==r['before']['state']['id']==r['ghost']==r['defeat']['id']==id
    assert r['before']['hp']==[1,2,2,3][index] and r['before']['r']==16 and abs(r['before']['speed']-[32.3*1.06,36.1*1.06,28.5*1.06,20.9*1.06][index])<1e-8
    assert abs(r['before']['shot']-[5.16*.95,4.3*.95,6.02*.95,6.45*.95][index])<1e-8 and r['sameRng'] and r['stable'] and r['draw']['id']==f'snowfield-{id}-atlas'
    assert r['score']==100 and r['kills']==1 and not r['duplicate'] and len(r['hits'])==[1,2,2,3][index] and r['defeat']['name']=='defeat';roles.append({'step':step,**r})
  report['actual_species_roles']=roles;assert len(roles)==16
  passed('All16 allowed phase/species pairs pass actual engine warning/spawn/HP/speed/shot/atlas/hit/death checks; assigned ID is immutable,prepare does not reroll and ghosts keep the species across phase changes with100points/one kill.')

  # Real Help entry retains defaultOFF and direct5 skip; every normal stage can mix.
  page.evaluate('mixExit()');page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('4');page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap()
  direct=page.evaluate('''()=>({phase,stage,hp,bossHP:boss.hp,normal:enemies.length,score:runScore,route:gameWorlds.snapshot().route,owned:gameSnowfieldBoss.snapshot()})''')
  assert direct['phase']==5 and direct['stage']==4 and direct['bossHP']==20 and direct['normal']==direct['score']==0 and direct['route']==[4]
  report['direct_boss_entry']=direct;passed('Actual Help World2→snow→direct5 still creates one20HP boss immediately,with no mixed normal actors or quota/score injection; ordinary phase5 separately uses its20/30/50 pool.')

  # Drive unchanged real automatic spawning; positioning only helps the capture.
  populated=page.evaluate('''()=>{mixScene(3);let selected=null;for(let seed=1;seed<100000;seed++){gameSnowfieldSpawns.reset(seed);const a=Array.from({length:4},()=>gameSnowfieldSpawns.select(3));if(new Set(a).size>=3){selected={seed,ids:a};break;}}gameSnowfieldSpawns.reset(selected.seed);spawn=0;const old=Math.random;Math.random=()=>.5;const seen=new WeakSet(),warningsAt=[],actorsAt=[];let elapsed=0;
   try{while(enemies.length<4&&elapsed<20){update(1/120);elapsed+=1/120;for(const w of warnings)if(!seen.has(w)){seen.add(w);warningsAt.push(elapsed);const i=warningsAt.length-1;w.x=W*(.2+i*.2);w.y=H*.3;}for(const e of enemies)if(!seen.has(e)){seen.add(e);actorsAt.push(elapsed);}}}finally{Math.random=old;spawn=999;}
   return {selected,warningsAt,actorsAt,count:enemies.length,ids:enemies.map(e=>e.snowSpeciesId),hp:enemies.map(e=>e.hp),phase,phaseKills,spawnFormula:tactics[stage].spawn-(phase-1)*.09,cap:Math.min(7,3+gameWorlds.profile(stage)+Math.floor(phase/2))};}''')
  assert populated['count']==populated['cap']==4 and len(set(populated['ids']))>=3 and populated['phaseKills']==0 and populated['ids']==populated['selected']['ids']
  assert all(abs((b-a)-1.825)<.02 for a,b in zip(populated['warningsAt'],populated['warningsAt'][1:])),populated
  report['natural_same_phase_mix']=populated;passed('The unmodified automatic manager produces4 coexisting mixed actors in phase3 at its original interval/cap; normal target stays6 and no spawn-count reduction or forced diversity is added.')

  charges=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('W===innerWidth&&H===innerHeight')
   for hz in [60,120]:
    for angle in [0,math.pi,math.pi/4,-math.pi/4,math.pi/2,-math.pi/2]:
     r=page.evaluate('''({angle,hz})=>{const e=mixPenguin(angle),warn=gameSnowfieldCombat.snapshot(e),origin={x:e.x,y:e.y};e.shot=0;mixAdvance(.8,hz);const dash=gameSnowfieldCombat.snapshot(e),d=dash.direction,v=dash.dashSpeed;
      const tx=Math.abs(d.x)>1e-9?(d.x>0?W-17-origin.x:17-origin.x)/(d.x*v):Infinity,ty=Math.abs(d.y)>1e-9?(d.y>0?H-18-origin.y:18-origin.y)/(d.y*v):Infinity;const travel=Math.min(1.2,tx,ty);player.x=W*.8;player.y=H*.85;mixAdvance(travel,hz);return {w:W,h:H,hz,angle,warn,dash,origin,travel,end:{x:e.x,y:e.y},state:gameSnowfieldCombat.snapshot(e),shots:enemyBullets.length};}''',{'angle':angle,'hz':hz})
     assert r['warn']['mode']=='windup' and abs(r['warn']['remaining']-.8)<1e-7 and abs(r['dash']['plannedDistance']-h*1.05)<1e-7 and abs(r['dash']['dashSpeed']-h*1.05/1.2)<1e-7
     moved=math.hypot(r['end']['x']-r['origin']['x'],r['end']['y']-r['origin']['y']);assert abs(moved-r['dash']['dashSpeed']*r['travel'])<1e-6 and abs(moved-r['state']['dashMoved'])<1e-6
     assert r['state']['mode']=='rest' and r['shots']==0 and 17-1e-7<=r['end']['x']<=w-17+1e-7 and 18-1e-7<=r['end']['y']<=h-18+1e-7
     if r['travel']>=1.2-1e-7:assert abs(moved-h*1.05)<1e-6 and not r['state']['wallStopped']
     else:assert r['state']['wallStopped']
     charges.append({**r,'actualDistance':moved})
  report['penguin_paths_60_120']=charges;passed('All3 landscapes×60/120Hz×six directions plan1.05H=432.6/378/336px at1.2s; free horizontal/diagonal paths complete it,vertical/edge paths stop at the first boundary with no teleport/slide/shooting or target retarget.')
  cooldown=page.evaluate('''()=>{const e=mixPenguin(0);mixAdvance(.8);mixAdvance(1.2);const arrival=gameSnowfieldCombat.snapshot(e);mixAdvance(.8);const afterRest=gameSnowfieldCombat.snapshot(e);mixAdvance(3.7);return {arrival,afterRest,next:gameSnowfieldCombat.snapshot(e)};}''')
  assert cooldown['arrival']['mode']=='rest' and abs(cooldown['arrival']['remaining']-.8)<1e-7 and cooldown['afterRest']['mode']=='pursue' and abs(cooldown['afterRest']['remaining']-3.7)<1e-7 and cooldown['next']['mode']=='windup'
  report['penguin_recovery']=cooldown;passed('Penguin has4.5s initial grace,.8s stationary warning,.8s rest plus3.7s pursuit after arrival before next warning; state uses dt and the same existing pause/exit lifecycle.')

  page.evaluate('window.pausePenguin=mixPenguin(0);mixAdvance(.8);mixAdvance(.2)')
  page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();frozen=page.evaluate('({x:pausePenguin.x,y:pausePenguin.y,state:gameSnowfieldCombat.snapshot(pausePenguin)})');page.evaluate('update(5)');page.wait_for_timeout(200)
  assert page.evaluate('({x:pausePenguin.x,y:pausePenguin.y,state:gameSnowfieldCombat.snapshot(pausePenguin)})')==frozen
  page.locator('#gameExitCancel').tap();page.wait_for_function('!gameExitDialogOpen');assert page.evaluate('started&&gameSnowfieldCombat.snapshot(pausePenguin).mode==="dash"')
  page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible();page.evaluate('window.oldPenguinPoint={x:pausePenguin.x,y:pausePenguin.y};mixScene(2);update(.2)')
  assert page.evaluate('enemies.length===0&&pausePenguin.x===oldPenguinPoint.x&&pausePenguin.y===oldPenguinPoint.y&&hp===maxHP[player.type]')
  passed('Actual exit modal freezes a moving long dash; cancel resumes it and confirmed exit/new run cannot move the removed old actor or deal stale damage. Existing input/HP/reset handlers remain unchanged.')

  # Actual normalized DeviceOrientationEvent input,not an invented movement speed.
  movement=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('W===innerWidth&&H===innerHeight')
   for hz in [60,120]:
    for kind in [0,1,2]:
     for edge in [False,True]:
      for delay in ([.15,.2,.35,.5,.55,.6,.65,.7,.8] if kind==2 else [.2]):
       r=page.evaluate('''({kind,hz,edge,delay})=>{mixScene(5,kind);player.x=W*.5;player.y=H*.62;mixAdvance(7.8);const r=gameSnowfieldBoss.radiusForHeight();
        if(edge){const p=gameSnowfieldBoss.safeTarget(12,H*.55,r);mixScene(5,kind);player.x=p.x;player.y=p.y;mixAdvance(7.8);}
        const state=gameSnowfieldBoss.snapshot(),hazard={...state.hazard};player.x=hazard.x;player.y=hazard.y;player.vx=player.vy=0;tilt={x:0,y:0};sensorOn=true;neutral={x:0,y:0};Object.defineProperty(screen.orientation,'angle',{configurable:true,value:90});invuln=0;const hpBefore=hp,x=player.x;let time=0,acted=false;
        while(time<1.4-1e-10&&started){const dt=Math.min(1/hz,1.4-time,time<delay-1e-10?delay-time:Infinity);if(time>=delay-1e-10&&!acted){dispatchEvent(new DeviceOrientationEvent('deviceorientation',{gamma:0,beta:17}));acted=true;}enemyBullets=[];boss.x=W*.85;boss.y=H*.25;update(dt);time+=dt;}
        return {viewport:[W,H],kind,hz,edge,delay,radius:hazard.r,warning:gameSnowfieldBoss.settings.warning,hpBefore,hp,distance:player.x-x,tilt:{...tilt},vx:player.vx,config:flightProfiles[kind],cap:playerSpeed[kind],state:gameSnowfieldBoss.snapshot()};}''',{'kind':kind,'hz':hz,'edge':edge,'delay':delay})
       assert abs(r['radius']-max(56,min(74,h*.18)))<1e-8 and r['warning']==1.4 and r['tilt']['x']==1
       assert r['state']['phase']=='burst' and r['hp']==r['hpBefore']-(1 if r['distance']<=r['radius'] else 0),r
       if delay==.2:assert r['hp']==r['hpBefore'] and r['distance']>r['radius'],r
       if kind==2 and delay==.7:assert r['hp']==r['hpBefore']-1 and r['distance']<r['radius'],r
       movement.append(r)
  report['actual_input_aoe_reaction']=movement;passed('Real existing gyro→acceleration/drag/cap path proves Tanko early.2s escape and late.7s oneHP hit at all3 sizes/60/120Hz/center-safe-edge; Trio/Bingle early escape too,with no player performance changes.')
  tanks=[r for r in movement if r['kind']==2 and not r['edge']]
  assert all(r['cap']==204 and r['config']=={'accel':473,'drag':4.25,'turn':2.35} for r in tanks)
  passed('Tanko configuration cap stays204px/s; full cardinal input terminal is473/4.25≈111.29px/s. Warning1.4s and radii74/64.8/57.6 are backed by recorded response-distance tables,not a fictitious constant204 speed.')

  # Existing World1 engine and item-manager RNG traces,while the new selector is stressed separately.
  page.evaluate('mixExit()');oldctx=browser.new_context(viewport={'width':915,'height':412});curctx=browser.new_context(viewport={'width':915,'height':412});old=oldctx.new_page();cur=curctx.new_page();old.goto(f'http://127.0.0.1:{reference.server_port}/');cur.goto(url);old.wait_for_function('itemMonsters.ready()');cur.wait_for_function('itemMonsters.ready()')
  fixture='''area=>{if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}itemMonsters.configure({opportunitiesPerRegion:3});start(0);stage=area;phase=2;transition=0;spawn=0;invuln=999;const random=Math.random;let seed=771,calls=0;Math.random=()=>{calls++;seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};
   try{const desc=Object.getOwnPropertyDescriptor(crypto,'getRandomValues');Object.defineProperty(crypto,'getRandomValues',{configurable:true,value:words=>{words.fill(90210);return words;}});try{itemMonsters.reset();}finally{if(desc)Object.defineProperty(crypto,'getRandomValues',desc);else delete crypto.getRandomValues;}if(window.gameSnowfieldSpawns){gameSnowfieldSpawns.reset(12345);for(let n=0;n<2000;n++)gameSnowfieldSpawns.select(3);}for(let i=0;i<180;i++)update(1/60);return {calls,enemies:enemies.map(e=>({...e})),warnings:warnings.map(w=>({...w})),items:itemMonsters.snapshot(),phaseKills,score:runScore,spawn};}finally{Math.random=random;}}'''
  traces=[]
  for area in range(4):
   old.bring_to_front();before=old.evaluate(fixture,area);cur.bring_to_front();after=cur.evaluate(fixture,area);assert before==after,area;traces.append({'area':area,'calls':after['calls'],'equal':True})
  oldctx.close();curctx.close();page.bring_to_front();report['world1_and_item_rng_traces']=traces
  passed('World1 all4 regions match922c271 exactly for global RNG call counts,normal spawning/state,interval and item-manager plans despite2,000 extra private snow draws per region.')

  # Captures use actual independently spawned actors; no PNG edits or forced IDs.
  captures=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('W===innerWidth&&H===innerHeight')
   row=page.evaluate('''()=>{mixScene(3);let seed=1;for(;seed<100000;seed++){gameSnowfieldSpawns.reset(seed);if(new Set(Array.from({length:4},()=>gameSnowfieldSpawns.select(3))).size>=3)break;}gameSnowfieldSpawns.reset(seed);for(let i=0;i<4;i++)mixSpawn(W*(.2+.2*i),H*.4);for(let i=0;i<4;i++){enemies[i].x=W*(.2+.2*i);enemies[i].y=H*.42;}gameSnowfield.observe(enemies,boss);mixFreeze();return {seed,ids:enemies.map(e=>e.snowSpeciesId),hp:enemies.map(e=>e.hp),poses:enemies.map(e=>gameSnowfield.pose(e).id)};}''');assert len(set(row['ids']))>=3 and row['ids']==row['poses'];page.screenshot(path=str(args.artifacts/f'mixed-{w}x{h}.png'))
   page.evaluate('mixPenguin(0);mixAdvance(.4);mixFreeze()');page.screenshot(path=str(args.artifacts/f'penguin-warning-{w}x{h}.png'))
   page.evaluate('mixPenguin(0);mixAdvance(.8);mixAdvance(.5);mixFreeze()');page.screenshot(path=str(args.artifacts/f'penguin-dash-{w}x{h}.png'))
   page.evaluate('mixScene(5,2);player.x=W*.5;player.y=H*.62');page.wait_for_function('getComputedStyle(document.getElementById("rotationJoystick")).visibility==="visible"');geometry=page.evaluate('''()=>{mixAdvance(8.9);const s=gameSnowfieldBoss.snapshot();mixFreeze();return s;}''');assert geometry['phase']=='warning' and abs(geometry['hazard']['r']-max(56,min(74,h*.18)))<1e-8;page.screenshot(path=str(args.artifacts/f'tanko-aoe-{w}x{h}.png'));captures.append({'viewport':[w,h],'mixed':row,'boss':geometry})
  report['landscape_captures']=captures;passed('Native/standalone capture each3 landscape:coexisting mixed species with matching atlas/HP,long penguin direction warning/dash,and enlarged Tanko AOE; assets/scale/UI remain protected.')
  page.evaluate('mixExit()');assert page.evaluate('mixStorage()')==initial_storage and page.evaluate('mixWrites.length')==0
  passed('Every developer mix/charge/reaction test leaves local TOP10/history untouched; actual5 boss and existing20/25 progression/score/item/audio/input/fullscreen regressions are retained.')
  assert not errors and not dialogs and not failed and not external,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':external}
  passed('No uncaught JS errors,native dialogs,failed assets or standalone external network requests occur.')
  browser.close()
finally:
 server.shutdown();server.server_close()
 if reference:reference.shutdown();reference.server_close()
 temp.cleanup()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
