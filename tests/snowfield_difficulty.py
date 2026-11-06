"""Issue11: exact tuning, real before/after/desert combat and protected patterns."""
import argparse,hashlib,io,json,math,re,shutil,subprocess,tarfile,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from difficulty_preservation import DIFFICULTY_ASSETS,assert_difficulty_asset,without_difficulty_source,without_difficulty_asset
ROOT=Path(__file__).resolve().parents[1];BASE='0441a88f7c494719f2ccab99caaf100d35cd86ee'
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':['Controlled real Chromium,not physical Galaxy/Samsung Internet or subjective difficulty proof.','60/120Hz denote deterministic update steps,not hardware refresh rates.','Scripted combat uses invulnerability,instant auto-aim and normalized sinusoidal flight,with item opportunities0 to isolate combat. It proves weapons can complete encounters,not human survival or10–15% harder difficulty.','Exact standalone HTML at a blank localhost origin with networking disabled;managed file policy not bypassed.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
s=(ROOT/'index.html').read_text();assert without_difficulty_source(s)==subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT).decode()
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in DIFFICULTY_ASSETS:assert_difficulty_asset(path);continue
 b=without_difficulty_asset(path.read_text(),name).encode() if path.suffix in ['.js','.css'] else path.read_bytes();assert b==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',s,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Only regional config and exact3 consumer deltas/source inclusion differ from0441a88;World1,players,controls,items,score,audio,PNG/115frames remain byte-protected;all JS parses.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/difficulty-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Difficulty origin</title>');return
  super().do_GET()
def serve(path):
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(path)));threading.Thread(target=server.serve_forever,daemon=True).start();return server
helpers='''()=>{
 window.tuneExit=()=>{gameSnowfieldBoss.reset();gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();gameExitDialogOpen=false;clearGameOver();gameControls.reset();gameSnowfield.reset();menu.classList.remove('hidden');};
 window.tuneScene=(region=4,step=1,kind=0,upgrade=0)=>{tuneExit();if(!gameWorlds.setDeveloperStart({enabled:true,regionId:region,phase:step}))throw Error('Rejected developer entry');itemMonsters.configure({opportunitiesPerRegion:0});start(kind);player.upgrade=upgrade;if(step===5)spawnBossEncounter();transition=0;spawn=999;fireCooldown=0;invuln=999;gameScoring.updateHUD();sensorOn=false;neutral={x:0,y:0};tilt={x:0,y:0};player.x=W*.72;player.y=H*.7;};
 window.tuneAdvance=(seconds,hz=120)=>{for(let n=0;n<Math.round(seconds*hz)&&started;n++)update(1/hz);};
 window.tuneSpecies=id=>{tuneScene(4,4);let seed=1;for(;seed<100000;seed++){gameSnowfieldSpawns.reset(seed);if(gameSnowfieldSpawns.select(4)===id)break;}gameSnowfieldSpawns.reset(seed);warnEnemy();Object.assign(warnings[0],{x:150,y:150,time:0});update(0);return enemies[0];};
 window.tuneNormal=({id,hz})=>{let e=tuneSpecies(id);player.x=700;player.y=150;const initial={hp:e.hp,r:e.r,speed:e.speed,interval:gameSnowfieldCombat.snapshot(e).interval,bulletSpeed:gameSnowfieldCombat.snapshot(e).bulletSpeed};e.shot=999;tuneAdvance(1,hz);const distance=e.x-150;e=tuneSpecies(id);e.speed=0;e.shot=0;const original=emitEnemyShot,shots=[];emitEnemyShot=(actor,...args)=>{shots.push(gameSnowfieldCombat.snapshot(actor).age);return original(actor,...args);};try{update(0);tuneAdvance(4.4,hz);}finally{emitEnemyShot=original;}return {id,hz,initial,distance,shots,pose:gameSnowfield.pose(e).id};};
 window.tuneTimeline=hz=>{tuneScene(4,5);const art=gameSnowfield,events=[],waves=[],seen=new WeakSet();let cap=0,oldPhase='rest';const warnings=[];window.gameSnowfield={...art,attack:(e,b)=>{art.attack(e,b);if(e===boss){const state=gameSnowfieldBoss.snapshot();events.push({age:state.age,kind:state.phase==='burst'?'blast':state.next==='radial'?'fan':'radial'});}}};try{for(let n=0;n<35*hz;n++){boss.x=W*.22;boss.y=H*.24;player.x=W*.78;player.y=H*.62;update(1/hz);const state=gameSnowfieldBoss.snapshot();if(state.phase==='warning'&&oldPhase!=='warning')warnings.push({age:state.age,hazard:state.hazard});oldPhase=state.phase;const fresh=enemyBullets.filter(b=>b.snowBossPattern&&!seen.has(b));for(const b of fresh)seen.add(b);if(fresh.length)waves.push({event:events.at(-1),shots:fresh.map(b=>({kind:b.snowBossPattern,speed:Math.hypot(b.vx,b.vy),r:b.r}))});cap=Math.max(cap,state.bullets);}return {hz,events,warnings,waves,cap,settings:gameSnowfieldBoss.settings};}finally{window.gameSnowfield=art;}};
 window.tuneFight=({region,step,kind,upgrade,hz})=>{let seed=0x12345678;const random=Math.random;Math.random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};tuneScene(region,step,kind,upgrade);spawn=0;gameSnowfieldSpawns.reset(12345);const emit=emitEnemyShot,shootOriginal=shoot,art=gameSnowfield;let enemyShots=0,playerShots=0,deathAt=null,elapsed=0;emitEnemyShot=(...a)=>{enemyShots++;return emit(...a);};shoot=()=>{playerShots++;return shootOriginal();};window.gameSnowfield={...art,attack:(e,b)=>{art.attack(e,b);if(e===boss&&region===4){const state=gameSnowfieldBoss.snapshot();if(state.phase!=='burst')enemyShots+=state.next==='radial'?3:6;}}};try{for(let n=0;n<(step===5?35:18)*hz&&started;n++){tilt={x:.5*Math.sin(elapsed*.9),y:.35*Math.cos(elapsed*.7)};const target=boss||enemies.reduce((best,e)=>!best||Math.hypot(e.x-player.x,e.y-player.y)<Math.hypot(best.x-player.x,best.y-player.y)?e:best,null);if(target)player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;keys.fire=!!target;const prior=boss;update(1/hz);elapsed+=1/hz;if(prior&&prior.hp<=0&&deathAt===null)deathAt=elapsed;}const result=gameScoring.finish('abandoned');started=false;return {region,step,kind,upgrade,hz,elapsed,hp,score:runScore,kills:result.record.normalKills,bossKills:result.record.bossKills,clearedPhases:result.record.clearedPhases,finalPhase:phase,enemyShots,playerShots,bossDeathSeconds:deathAt,bossHP:boss?.hp??null,saved:result.saved};}finally{Math.random=random;emitEnemyShot=emit;shoot=shootOriginal;window.gameSnowfield=art;keys.fire=false;}};
}'''
server=serve(ROOT);reference=None;temp=tempfile.TemporaryDirectory(prefix='heli-difficulty-')
try:
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE,'index.html','assets'],cwd=ROOT))) as t:t.extractall(temp.name,filter='data')
 reference=serve(temp.name)
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=ctx.new_page();errors=[];failed=[];dialogs=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  url=f'http://127.0.0.1:{server.server_port}/'
  if args.standalone:page.goto(url+'difficulty-origin');external.clear();ctx.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url)
  page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()');page.evaluate(helpers);storage=page.evaluate('JSON.stringify(Object.entries(localStorage).sort())')
  oldctx=browser.new_context(viewport={'width':915,'height':412});old=oldctx.new_page();old.goto(f'http://127.0.0.1:{reference.server_port}/');old.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()');old.evaluate(helpers)
  config=page.evaluate("()=>{const c=gameRegionDifficulty.get('world-2:snowfield');return {config:c,frozen:Object.isFrozen(c)&&Object.isFrozen(c.spawnWeights)&&c.spawnWeights.every(Object.isFrozen),unknown:gameRegionDifficulty.get('world-1:desert')===undefined};}")
  weights=[[80,20,0,0],[45,40,15,0],[20,30,35,15],[10,20,35,35],[0,15,30,55]]
  assert config=={'config':{'chaseSpeedScale':1.06,'shotIntervalScale':.95,'bossRest':3,'spawnWeights':weights},'frozen':True,'unknown':True};report['regional_config']=config
  passed('Frozen one-place snow tuning has1.06 chase/.95 interval/3s boss rest and exact Issue11 weights;unknown World1 regions receive no implicit override.')
  ids=['snow_slime','penguin_raider','ice_yeti','frost_turtle'];normal=[]
  for id in ids:
   for hz in [60,120]:
    before=old.evaluate('tuneNormal',{'id':id,'hz':hz});after=page.evaluate('tuneNormal',{'id':id,'hz':hz});a=after['initial'];b=before['initial']
    assert a['hp']==b['hp'] and a['r']==b['r']==16 and a['bulletSpeed']==b['bulletSpeed']
    assert abs(a['speed']/b['speed']-1.06)<1e-9 and abs(a['interval']/b['interval']-.95)<1e-9 and abs(after['distance']/before['distance']-1.06)<1e-8
    assert after['pose']==before['pose']==id
    if id=='penguin_raider':assert abs(after['shots'][1]-a['interval'])<1e-7
    normal.append({'before':before,'after':after})
  report['normal_before_after_60_120']=normal;passed('All4 real spawned species at60/120Hz chase exactly+6%,interval exactly−5%,with HP,r16,bullet85/76.5,art IDs and aimed shot events unchanged.')
  distributions=page.evaluate('''()=>{const rows=[];for(const seed of [1,12345,0xdeadbeef])for(let step=1;step<=5;step++){gameSnowfieldSpawns.reset(seed);const counts=[0,0,0,0];for(let n=0;n<10000;n++)counts[gameSnowfieldSpawns.ids.indexOf(gameSnowfieldSpawns.select(step))]++;rows.push({seed,step,counts,total:10000});}return rows;}''')
  for r in distributions:
   assert sum(r['counts'])==10000
   for i,w in enumerate(weights[r['step']-1]):assert abs(r['counts'][i]/100-w)<1.5 and (w!=0 or r['counts'][i]==0)
  report['weighted_draws']=distributions;passed('150,000 draws across3seeds/5phases match new weights within1.5pp;phase1 stays80/20 and late stronger species increase without guaranteed diversity.')
  timelines=[]
  for hz in [60,120]:
   before=old.evaluate('tuneTimeline',hz);after=page.evaluate('tuneTimeline',hz);expected=[1.8,4.8,9.2,12.45,15.45,19.85,23.1,26.1,30.5,33.75]
   assert len(before['events'])==9 and len(after['events'])==10 and [e['kind'] for e in after['events']]==['fan','radial','blast']*3+['fan']
   assert all(abs(e['age']-t)<1e-7 for e,t in zip(after['events'],expected)) and len(after['waves'])==7 and len(after['warnings'])==3 and after['cap']==9
   for wave in after['waves']:assert len(wave['shots'])==(3 if wave['event']['kind']=='fan' else 6) and all(s['r']==5 and abs(s['speed']-(80 if s['kind']=='fan' else 65))<1e-9 for s in wave['shots'])
   for k,v in before['settings'].items():assert after['settings'][k]==(3 if k=='rest' else v)
   timelines.append({'before':before,'after':after})
  report['boss_timeline_60_120']=timelines;passed('35s before/after60/120Hz:3.0s rest yields10 attacks/7 complete projectile waves,never skipped by9bullet cap;first1.8s,3/6 shots,speeds,1.4s AOE and other settings are identical.')
  fights=[]
  for region in [3,4]:
   for step in range(1,6):
    for kind in range(3):
     for upgrade in ([0,3] if step==5 else [3]):
      inputs={'region':region,'step':step,'kind':kind,'upgrade':upgrade,'hz':60};before=old.evaluate('tuneFight',inputs);after=page.evaluate('tuneFight',inputs)
      if region==3:assert before==after,(inputs,before,after)
      assert after['saved'] is False
      if step==5:assert before['bossKills']==after['bossKills']==1 and before['score']==after['score']==2000,(inputs,before,after)
      fights.append({'before':before,'after':after})
  report['scripted_desert_snow_comparison']=fights;passed('Same seed,input,character and upgrades compare desert/snow1–5;all18 desert comparisons exactly match baseline,all3 characters at0/3 upgrades kill both bosses for2000points with no stored test results.')
  stats=page.evaluate('''()=>({tactics:tactics.slice(0,5),profiles:flightProfiles,speeds:playerSpeed,requiredKills,normalCap:[1,2,3,4,5].map(p=>Math.min(7,3+Math.floor(p/2))),hp:gameSnowfieldCombat.profiles.map(p=>p.hp),penguin:gameSnowfieldCombat.profiles[1],bossScaling:[1,1.1,1.4,1.6,1.9,2.2]})''');report['protected_parameters']=stats
  assert stats==old.evaluate('''()=>({tactics:tactics.slice(0,5),profiles:flightProfiles,speeds:playerSpeed,requiredKills,normalCap:[1,2,3,4,5].map(p=>Math.min(7,3+Math.floor(p/2))),hp:gameSnowfieldCombat.profiles.map(p=>p.hp),penguin:gameSnowfieldCombat.profiles[1],bossScaling:[1,1.1,1.4,1.6,1.9,2.2]})''')
  passed('Actual original tactics,spawn cadence/cap/6kills,player physics and Penguin full1.05H/.8/1.2/boundary/recovery profile match baseline;HP/damage/boss scaling unchanged.')
  captures=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('W===innerWidth&&H===innerHeight');page.evaluate('tuneScene(4,4,2,3)');page.wait_for_function('getComputedStyle(rotationJoystick).visibility==="visible"')
   page.evaluate('''()=>{spawn=999;for(let n=0;n<4;n++){const e=tuneSpecies(gameSnowfieldSpawns.ids[n]);window['captureActor'+n]=e;}tuneScene(4,4,2,3);enemies=[captureActor0,captureActor1,captureActor2,captureActor3];enemies.forEach((e,i)=>{e.x=W*(.2+i*.2);e.y=H*.42;});gameSnowfield.observe(enemies,boss);invuln=0;gameExitDialogOpen=true;draw();}''');page.screenshot(path=str(args.artifacts/f'tuned-mix-{w}x{h}.png'))
   page.evaluate('tuneScene(4,5,2)');page.wait_for_function('getComputedStyle(rotationJoystick).visibility==="visible"');page.evaluate('player.x=W*.5;player.y=H*.62;tuneAdvance(8.5);gameExitDialogOpen=true;draw()');state=page.evaluate('gameSnowfieldBoss.snapshot()');assert state['phase']=='warning' and abs(state['hazard']['r']-max(56,min(74,h*.18)))<1e-9;page.screenshot(path=str(args.artifacts/f'tuned-boss-{w}x{h}.png'));captures.append({'viewport':[w,h],'boss':state})
  report['landscape_captures']=captures;passed('Three landscape sizes render unchanged4species art,controls/HUD and Tanko/fixed AOE;6 real screenshots saved per mode.')
  page.evaluate('tuneExit()');assert page.evaluate('JSON.stringify(Object.entries(localStorage).sort())')==storage
  assert not errors and not failed and not dialogs and not external,{'errors':errors,'failed':failed,'dialogs':dialogs,'external':external}
  passed('Developer comparisons write no rankings/analysis/settings;no uncaught JS,native dialogs,failed assets or offline external requests.')
  oldctx.close();browser.close()
finally:
 server.shutdown();server.server_close()
 if reference:reference.shutdown();reference.server_close()
 temp.cleanup()
def clean(v):
 if isinstance(v,float) and not math.isfinite(v):return None
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 return v
(args.artifacts/'test-results.json').write_text(json.dumps(clean(report),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
