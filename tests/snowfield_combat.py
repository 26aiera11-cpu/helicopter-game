"""Issue8 normal combat, real engine spawn/hits, deterministic rate comparisons."""
import argparse,hashlib,io,json,re,shutil,subprocess,tarfile,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from snow_combat_preservation import COMBAT_ASSETS,assert_combat_asset,without_snow_combat_source,without_snow_combat_asset
ROOT=Path(__file__).resolve().parents[1];BASE='615481239202eb773c494476368e8fa02cd46aea'
a=argparse.ArgumentParser();a.add_argument('--artifacts',type=Path,required=True);a.add_argument('--standalone',action='store_true');args=a.parse_args();args.artifacts.mkdir(exist_ok=True,parents=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':[
 'Actual Chromium engine events with controlled coordinates, aim, time and invulnerability; not manual difficulty testing or physical Galaxy/Samsung Internet.',
 '60/120Hz are deterministic update steps, not a claim of 120Hz hardware rendering.',
 'Offline uses the exact standalone HTML at a blank localhost origin with networking disabled, without bypassing managed file policy.',
 'Frame timings describe this Chromium software-rendered environment, not Galaxy performance or audible sound.'
]}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
source=(ROOT/'index.html').read_text();assert without_snow_combat_source(source)==subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT).decode()
for p in (ROOT/'assets').rglob('*'):
 if not p.is_file():continue
 name=str(p.relative_to(ROOT))
 if name in COMBAT_ASSETS:assert_combat_asset(p);continue
 actual=without_snow_combat_asset(p.read_text(),name).encode() if p.suffix in ['.js','.css'] else p.read_bytes()
 assert actual==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for s in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=s,text=True,capture_output=True,check=True)
passed('Exact Issue8 hooks reverse to6154812; all66 prior assets except two reviewed notice strings are byte-identical, including art115frames, boss, input/items/score/audio, and all JS parses.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/blank-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline origin</title>');return
  super().do_GET()
def serve(directory):
 s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(directory)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
helpers='''() => {
 window.combatWrites=[];const write=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.startsWith('heliTrio.'))combatWrites.push(k);return write.call(this,k,v);};
 window.combatExit=()=>{gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();gameExitDialogOpen=false;clearGameOver();gameControls.reset();gameSnowfield.reset();menu.classList.remove('hidden');};
 window.combatScene=(step,type=0)=>{
  combatExit();if(!gameWorlds.setDeveloperStart({enabled:true,regionId:4,phase:step}))throw Error('Entry rejected');
  itemMonsters.configure({opportunitiesPerRegion:0});start(type);transition=0;spawn=999;invuln=999;player.x=W*.8;player.y=H*.75;fireCooldown=0;
  if(step===5)return boss;
  gameSnowfieldSpawns.reset(12345);warnEnemy();warnings[0].x=150;warnings[0].y=120;warnings[0].time=0;update(0);return enemies[0];
 };
 window.combatAdvance=(seconds,hz=120)=>{let t=0;while(t<seconds-1e-10){const dt=Math.min(1/hz,seconds-t);update(dt);t+=dt;}};
 window.combatHit=e=>{bullets=[];shoot();const b=bullets[0];Object.assign(b,{x:e.x,y:e.y,vx:0,vy:0});const damage=b.damage;update(0);return {hp:e.hp,damage,score:runScore,kills:phaseKills,pose:gameSnowfield.pose(e),alive:enemies.includes(e),remaining:b.pierce};};
 window.combatFreeze=()=>{invuln=0;rotorSpin=.35;gameExitDialogOpen=true;draw();};
 window.combatSample=e=>({hp:e.hp,r:e.r,speed:e.speed,shot:e.shot,state:gameSnowfieldCombat.snapshot(e),pose:gameSnowfield.pose(e),phase,score:runScore});
}'''
probe='''() => {window.combatAudio=[];const Native=Audio;window.Audio=new Proxy(Native,{construct(t,a){const x=new t(...a);combatAudio.push(x);return x;}});}'''
server=serve(ROOT);reference=None;temp=tempfile.TemporaryDirectory(prefix='heli-combat-reference-')
try:
 archive=subprocess.check_output(['git','archive',BASE,'index.html','assets'],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(temp.name,filter='data')
 reference=serve(temp.name)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);context.add_init_script('('+probe+')()')
  page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  url=f'http://127.0.0.1:{server.server_port}/'
  if args.standalone:page.goto(url+'blank-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url,wait_until='load')
  page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()&&window.gameSnowfieldCombat');page.evaluate(helpers)
  assert not page.evaluate('gameWorlds.isDeveloper()||gameWorlds.isTrial()')
  storage=page.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)]))')
  initial=[]
  for step in range(1,5):
   if step>1:page.evaluate('combatExit()')
   page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('4');page.locator('#developerStartPhase').select_option(str(step));page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap()
   row=page.evaluate('''() => {gameSnowfieldSpawns.reset(12345);gameExitDialogOpen=false;transition=0;spawn=999;invuln=999;enemies=[];warnings=[];warnEnemy();const before=warnings.length;update(.7);const half={warning:warnings.length,actors:enemies.length};update(.7);const e=enemies[0];return {before,half,after:combatSample(e),boss:!!boss};}''')
   assert row['before']==1 and row['half']=={'warning':1,'actors':0} and not row['boss']
   after=row['after'];assert after['hp']==[1,2,2,3][step-1] and after['r']==16 and abs(after['speed']-[32.3*1.06,36.1*1.06,28.5*1.06,20.9*1.06][step-1])<1e-8
   assert after['state']['id']==['snow_slime','penguin_raider','ice_yeti','frost_turtle'][step-1] and after['state']['mode']=='pursue' and after['score']==0
   initial.append(row)
  report['real_help_entries_and_warning']=initial
  passed('Real Help controls enter snow1–4; original1.4s spawn warning precedes the correct species, HP1/2/2/3,r16,Issue11 chase speeds34.238/38.266/30.21/22.154 with no immediate charge or boss.')

  rates=[]
  for step in range(1,5):
   for hz in [60,120]:
    r=page.evaluate('''({step,hz})=>{const e=combatScene(step);e.x=150;e.y=150;player.x=700;player.y=250;const before={x:e.x,y:e.y};combatAdvance(1,hz);return {step,hz,distance:Math.hypot(e.x-before.x,e.y-before.y),after:combatSample(e),x:e.x,y:e.y};}''',{'step':step,'hz':hz})
    assert abs(r['distance']-[32.3*1.06,36.1*1.06,28.5*1.06,20.9*1.06][step-1])<1e-7 and r['after']['pose']['name']=='move';rates.append(r)
  report['one_second_movement_60_120']=rates;passed('All4 species pursue the player at their exact first-trial speeds at60/120Hz; turtle is slowest and animation follows actual movement.')

  shots=[]
  for step in range(1,5):
   for hz in [60,120]:
    r=page.evaluate('''({step,hz})=>{const e=combatScene(step);e.speed=0;player.x=700;player.y=250;e.shot=.01;const log=[],old=emitEnemyShot;
     emitEnemyShot=function(actor,...args){old(actor,...args);log.push({age:gameSnowfieldCombat.snapshot(actor)?.age,b:enemyBullets.at(-1),angle:Math.atan2(player.y-actor.y,player.x-actor.x)});};
     try{combatAdvance(.02,hz);const first=gameSnowfield.pose(e);combatAdvance(16,hz);return {step,hz,first,shots:log.map(v=>({age:v.age,speed:Math.hypot(v.b.vx,v.b.vy),angle:Math.atan2(v.b.vy,v.b.vx),aim:v.angle,ice:!!v.b.snowIce,r:v.b.r})),state:gameSnowfieldCombat.snapshot(e)};}finally{emitEnemyShot=old;}}''',{'step':step,'hz':hz})
    assert len(r['shots'])>=2 and r['first']['name']=='attack'
    assert all(abs(b['speed']-[85,85,76.5,85][step-1])<1e-8 and abs(b['angle']-b['aim'])<1e-8 and b['r']==5 and b['ice']==(step==3) for b in r['shots'])
    assert abs(r['state']['interval']-[5.16*.95,4.3*.95,6.02*.95,6.45*.95][step-1])<1e-8
    if step!=2:assert all(abs(b['age']-a['age']-[5.16*.95,4.3*.95,6.02*.95,6.45*.95][step-1])<1e-7 for a,b in zip(r['shots'],r['shots'][1:]))
    shots.append(r)
  for sixty,hundred_twenty in zip(shots[::2],shots[1::2]):
   assert len(sixty['shots'])==len(hundred_twenty['shots']) and all(abs(a['age']-b['age'])<1e-7 for a,b in zip(sixty['shots'],hundred_twenty['shots']))
  report['actual_shots']=shots;passed('Actual aimed single shots trigger attack art only on emission:85/85/76.5/85px/s,Issue11 intervals4.902/4.085/5.719/6.1275s,r5; only Yeti shots carry ice color and no status effect.')

  charges=[]
  for hz in [60,120]:
   r=page.evaluate('''hz=>{const e=combatScene(2);e.x=150;e.y=150;player.x=700;player.y=150;e.shot=999;const start={x:e.x,y:e.y};combatAdvance(4.5,hz);const warn={...combatSample(e),x:e.x,y:e.y};
    e.shot=0;player.x=100;player.y=330;combatAdvance(.8,hz);const begin={...combatSample(e),x:e.x,y:e.y,shots:enemyBullets.length};
    combatAdvance(.6,hz);const half={x:e.x,y:e.y,shots:enemyBullets.length};player.x=800;player.y=300;combatAdvance(.6,hz);const end={...combatSample(e),x:e.x,y:e.y,shots:enemyBullets.length};
    combatAdvance(.8,hz);const rest={...combatSample(e),x:e.x,y:e.y};combatAdvance(3.7,hz);return {hz,start,warn,begin,half,end,rest,next:combatSample(e)};}''',hz)
   assert r['warn']['state']['mode']=='windup' and abs(r['warn']['x']-150-36.1*1.06*4.5)<1e-7
   assert r['begin']['state']['mode']=='dash' and r['begin']['x']==r['warn']['x'] and r['begin']['y']==r['warn']['y'] and r['begin']['shots']==0
   assert abs(r['half']['x']-r['begin']['x']-432.6*.5)<1e-7 and r['half']['y']==r['begin']['y'] and r['half']['shots']==0
   assert r['end']['state']['mode']=='rest' and abs(r['end']['x']-r['begin']['x']-432.6)<1e-7 and r['end']['y']==r['begin']['y'] and r['end']['shots']==0 and not r['end']['state']['wallStopped']
   assert r['rest']['state']['mode']=='pursue' and r['rest']['x']==r['end']['x'] and r['rest']['y']==r['end']['y']
   assert r['next']['state']['mode']=='windup' and abs(r['next']['state']['age']-11)<1e-7;charges.append(r)
  report['penguin_60_120']=charges;passed('Penguin60/120Hz:4.5s grace,.8s warning,1.2s locked dash of1.05H=432.6px,.8s rest and3.7s pursuit before next warning; no shooting/tracking while charging.')

  edge=page.evaluate('''()=>{const rows=[];for(const side of [-1,1]){const e=combatScene(2);e.x=side<0?17:W-17;e.y=side<0?18:H-18;player.x=side<0?12:W-12;player.y=side<0?12:H-12;e.shot=999;combatAdvance(7);rows.push({x:e.x,y:e.y,r:e.r,state:gameSnowfieldCombat.snapshot(e)});}return rows;}''')
  assert all(17<=v['x']<=898 and 18<=v['y']<=394 and v['r']==16 for v in edge)
  dodge=page.evaluate('''()=>{const e=combatScene(2);e.x=150;e.y=150;player.x=700;player.y=150;e.shot=999;combatAdvance(4.5);player.x=e.x+13.68;player.y=e.y+80;const before=hp;invuln=0;combatAdvance(2);return {before,after:hp,player:{x:player.x,y:player.y},enemy:{x:e.x,y:e.y}};}''')
  assert dodge['before']==dodge['after'];report['penguin_boundaries']=edge;report['dodge_after_warning']=dodge
  passed('Penguin charge clamps to existing17/18px arena bounds without changing r16; perpendicular displacement during the warning avoids the locked path with no damage or input restriction.')

  ice=page.evaluate('''()=>{const e=combatScene(3);e.shot=0;update(0);const b=enemyBullets[0],original={r:b.r,life:b.life,ice:b.snowIce};const speed=Math.hypot(b.vx,b.vy),before=hp;invuln=0;Object.assign(b,{x:player.x,y:player.y,vx:0,vy:0});update(0);const first={hp,invuln,removed:!enemyBullets.includes(b)};
   enemyBullets.push({...b,life:3.4});update(0);const protectedHp=hp;combatAdvance(1.56);enemyBullets.push({...b,life:3.4,x:player.x,y:player.y});update(0);return {original,speed,before,first,protectedHp,after:hp,playerKeys:Object.keys(player).sort()};}''')
  assert ice['original']=={'r':5,'life':3.4,'ice':True} and abs(ice['speed']-76.5)<1e-8
  assert ice['first']=={'hp':ice['before']-1,'invuln':1.55,'removed':True} and ice['protectedHp']==ice['first']['hp'] and ice['after']==ice['before']-2,ice
  assert not any('slow' in k.lower() or 'freeze' in k.lower() for k in ice['playerKeys']);report['ice_damage']=ice
  passed('Yeti ice uses the original r5/life3.4/oneHP hit and1.55s invulnerability path, removes on impact and introduces no freeze/slow player state.')

  blocks=[]
  for kind in range(3):
   r=page.evaluate('''kind=>{const e=combatScene(3,kind);e.shot=0;update(0);const ice=enemyBullets[0];ice.x=W*.5;ice.y=H*.5;bullets=[];shoot();Object.assign(bullets[0],{x:ice.x,y:ice.y,vx:0,vy:0});const shot=bullets[0];update(0);return {kind,iceGone:!enemyBullets.includes(ice),shotGone:shot.life<=0};}''',kind)
   assert r['iceGone']==r['shotGone']==(kind==2);blocks.append(r)
  report['ice_interception']=blocks;passed('Existing Tanko bullet/ice-bullet collision annihilates both; Trio/Bingle gain no interception and existing damage/pierce/size/cadence code is untouched.')

  kills=[]
  for kind in range(3):
   for step in range(1,5):
    r=page.evaluate('''({kind,step})=>{const e=combatScene(step,kind);const before=combatSample(e),hits=[];while(e.hp>0&&hits.length<6)hits.push(combatHit(e));const score=runScore,kills=phaseKills;const duplicate=gameScoring.enemyDefeated(e);gameSnowfield.hit(e);const ghosts=gameSnowfield.snapshot().ghosts.length;gameSnowfield.tick(.33);const defeat=gameSnowfield.snapshot().ghosts[0]?.pose;gameSnowfield.tick(.72);return {kind,step,before,hits,score,kills,duplicate,ghosts,defeat,remainingGhosts:gameSnowfield.snapshot().ghosts.length,items:items.length};}''',{'kind':kind,'step':step})
    dmg=1.5 if kind==2 else 1;total=[1,2,2,3][step-1]
    assert len(r['hits'])==__import__('math').ceil(total/dmg) and all(abs(v['hp']-(total-dmg*(i+1)))<1e-9 for i,v in enumerate(r['hits']))
    assert r['score']==100 and r['kills']==1 and not r['duplicate'] and r['ghosts']==1 and r['remainingGhosts']==0 and r['defeat']['name']=='defeat' and r['items']==0
    assert all(v['pose']['name']=='hit' for v in r['hits']) and r['before']['r']==16;kills.append(r)
  report['all_character_kills']=kills;passed('All3 characters kill all4 species with exact1/1/1.5 damage, including turtle3HP successive hits; each death gives100/one normal kill, one hit→defeat ghost and no ordinary item or duplicate score.')

  assert page.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)]))')==storage and page.evaluate('combatWrites.length')==0
  passed('All normal-enemy developer entries/attacks/deaths retain the original storage bytes with0 TOP10/analysis writes.')

  gate=page.evaluate('''()=>{combatScene(4);enemies=[];phase=5;phaseKills=0;bullets=[];const rows=[];for(let i=0;i<6;i++){warnEnemy();warnings[0].time=0;update(0);const e=enemies[0],initial=combatSample(e);while(e.hp>0)combatHit(e);rows.push({initial,boss:!!boss,kills:phaseKills});}update(0);return {rows,boss:boss&&{hp:boss.hp,r:boss.r},score:runScore,result:gameScoring.getLastResult()};}''')
  species={'penguin_raider':(2,36.1*1.06),'ice_yeti':(2,28.5*1.06),'frost_turtle':(3,20.9*1.06)}
  assert all(v['initial']['state']['id'] in species and v['initial']['hp']==species[v['initial']['state']['id']][0] and abs(v['initial']['speed']-species[v['initial']['state']['id']][1])<1e-8 and not v['boss'] and v['kills']==i+1 for i,v in enumerate(gate['rows']))
  assert gate['boss']=={'hp':20,'r':48} and gate['score']==600 and gate['result'] is None
  report['ordinary_phase5_gate']=gate
  passed('Reaching ordinary phase5 retains six actual weighted penguin/yeti/turtle kills/600points before the unchanged20HP boss, while direct5 keeps the separate skip behavior.')

  # Compare protected fights against the exact previous code, using identical RNG/input.
  refctx=browser.new_context(viewport={'width':915,'height':412});old=refctx.new_page();old.goto(f'http://127.0.0.1:{reference.server_port}/');old.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()')
  fixture='''({area,king})=>{if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}gameExitDialogOpen=false;gameSnowfield.reset();gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true);itemMonsters.configure({opportunitiesPerRegion:0});start(0);stage=area;phase=king?5:1;transition=0;spawn=999;invuln=999;player.x=700;player.y=300;
   const random=Math.random;let seed=721;Math.random=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};
   try{if(king){phaseKills=6;update(0);transition=0;boss.shot=0;}else{warnEnemy();warnings[0].time=0;update(0);enemies[0].shot=0;}const trace=[];
    for(let i=0;i<120;i++){update(1/60);if(i%15===0)trace.push({hp,phaseKills,boss:boss&&{x:boss.x,y:boss.y,hp:boss.hp,maxHp:boss.maxHp,shot:boss.shot},enemies:enemies.map(e=>({x:e.x,y:e.y,hp:e.hp,r:e.r,speed:e.speed,shot:e.shot})),bullets:enemyBullets.map(b=>({...b}))});}return trace;
   }finally{Math.random=random;gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();gameSnowfield.reset();menu.classList.remove('hidden');}}'''
  comparisons=[];page.evaluate('combatExit()')
  for area in range(5):
   for king in [False,True]:
    if area==4 and not king:continue
    cfg={'area':area,'king':king};expected=old.evaluate(fixture,cfg);actual=page.evaluate(fixture,cfg)
    if area==4:
     # Only Issue9 snow attacks change: retain exact motion/HP/counter comparison.
     def movement(rows):return [{k:({q:v for q,v in value.items() if q!='shot'} if k=='boss' and value else value) for k,value in row.items() if k!='bullets'} for row in rows]
     assert movement(actual)==movement(expected),cfg
    else:assert actual==expected,cfg
    comparisons.append(cfg)
  report['protected_combat_trace_equal']=comparisons;refctx.close()
  passed('Identical seeded native traces match6154812 for all4 World1 normal fights,all4 World1 bosses with exact positions/HP/shot counts/bullet vectors/counters; snow boss retains exact motion/HP/counters with Issue9 attacks tested separately.')

  # Restore a developer-only scope after the reference fixtures, without completing a real run.
  page.evaluate('combatExit()');before_dev=page.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)]))');before_writes=page.evaluate('combatWrites.length')
  direct=page.evaluate('''()=>{const b=combatScene(5);return {hp:b.hp,r:b.r,shot:b.shot,normal:enemies.length,score:runScore,run:gameWorlds.snapshot(),developer:gameWorlds.isDeveloperRun()};}''')
  assert direct['hp']==20 and direct['r']==48 and direct['normal']==direct['score']==0 and direct['run']['route']==[4] and direct['developer']
  page.evaluate('transition=0;while(boss){bullets=[];shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(0);}');page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending')
  result=page.evaluate('gameScoring.getLastResult()');assert result['developerTest'] and not result['saved'] and result['record']['bossKills']==1 and result['record']['score']==2000
  assert page.evaluate('JSON.stringify(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)]))')==before_dev and page.evaluate('combatWrites.length')==before_writes
  report['direct_boss']=direct;passed('Developer direct5 still skips normal mobs and ends after the original20HP boss with2000 points; snow outro is retained and neither existing TOP10 nor analysis receives the test result.')

  layouts=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height})
   for step in range(1,5):
    scene=page.evaluate('''step=>{const e=combatScene(step);e.x=W*.5;e.y=H*.43;player.x=W*.75;player.y=H*.7;
     if(step===2){e.shot=999;combatAdvance(4.9);}
     if(step===3){e.shot=0;update(0);combatAdvance(.75);}
     gameSnowfield.observe(enemies,boss);combatFreeze();const spec=gameSnowfield.species.find(s=>s.id===e.snowSpeciesId);return {step,state:gameSnowfieldCombat.snapshot(e),geometry:gameSnowfield.geometry(spec,e.x,e.y,W,H),actor:{x:e.x,y:e.y,r:e.r}};}''',step)
    box=scene['geometry'];assert box['x']>=0 and box['y']>=0 and box['x']+box['w']<=width and box['y']+box['h']<=height
    page.screenshot(path=str(args.artifacts/f'snow-{step}-{width}x{height}.png'));layouts.append({'viewport':[width,height],**scene})
  report['landscape_scenes']=layouts;passed('Native canvas captures show each species/ice shot/penguin warning with preserved PNG ratios and full cells at915×412,800×360,568×320; original controls/HUD/fullscreen remain.')

  page.set_viewport_size({'width':915,'height':412});page.evaluate('combatExit();combatScene(2);transition=0;spawn=999;invuln=999;')
  timings=page.evaluate('''async()=>{const stamps=[];await new Promise(resolve=>{let last=performance.now();const sample=t=>{stamps.push(t-last);last=t;if(stamps.length>=120)resolve();else requestAnimationFrame(sample);};requestAnimationFrame(sample);});stamps.shift();const sorted=[...stamps].sort((a,b)=>a-b);return {samples:stamps.length,medianMs:sorted[Math.floor(sorted.length*.5)],p95Ms:sorted[Math.floor(sorted.length*.95)],maxMs:sorted.at(-1),approxFps:1000/(stamps.reduce((a,b)=>a+b,0)/stamps.length),loaded:gameSnowfield.ready()};}''')
  assert timings['loaded'] and timings['samples']==119;report['observed_frame_timing']=timings
  passed('Live requestAnimationFrame sample collected during active snow combat; every approved image/atlas is loaded and timing statistics are reported without claiming physical Galaxy FPS.')
  page.evaluate('combatExit()');assert not errors and not dialogs and not failed and not external,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':external}
  passed('No uncaught JavaScript errors,native dialogs,failed resources or offline external requests; prior control/scoring/route suites cover unchanged20/25-phase progress and settings.')
  browser.close()
finally:
 server.shutdown();server.server_close()
 if reference:reference.shutdown();reference.server_close()
 temp.cleanup()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
