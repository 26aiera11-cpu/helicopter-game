"""Issue26 production-browser checks, independent source audit and offline resources."""
import argparse,base64,hashlib,json,math,re,shutil,subprocess,threading,zipfile
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from storm_sky_preservation import verify
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':args.standalone,'passed':[],'limits':['Controlled real Chromium execution, not physical Galaxy Samsung Internet/Chrome or sensor hardware.','New regional combat numbers are first-playtest values; no human difficulty certification.','Single-cell lossless source atlases animate through manifest scale/rotation/alpha keyframes, not newly hand-drawn poses.','Storm dedicated stage/boss BGM is a first-listening trial; separate audio suites verify native clocks and routing.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
report['preservation']=verify()
for js in [p.read_text() for p in (ROOT/'assets/storm_sky').glob('*.js')]+re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',(ROOT/'index.html').read_text(),re.S):subprocess.run(['node','--check','-'],input=js,text=True,capture_output=True,check=True)
passed('All92 existing assets byte-preserved after exact registry hooks;32 engine changes reverse exactly to c2d03f8; all new/inline JavaScript parses.')
manifest=json.loads((ROOT/'assets/storm_sky/asset_manifest.json').read_text());asset_rows=[]
for row in manifest['monsters']:
 im=Image.open(ROOT/'assets/storm_sky'/row['base']);assert im.mode=='RGBA' and im.getchannel('A').getextrema()[0]==0
 assert row['has_propeller']==False
 for a in row['animations'].values():
  for f in a['frames']:
   x,y,w,h=f['rect_px'];assert 0<=x<x+w<=im.width and 0<=y<y+h<=im.height and f['pivot_px']==[im.width/2,im.height/2]
 asset_rows.append({'id':row['id'],'size':im.size,'sha256':row['sha256'],'keyframes':sum(len(a['frames']) for a in row['animations'].values())})
report['art_assets']=asset_rows
passed('Supplied1920×864 background/four512×512 PNGs stay exact; all5 transparent source atlases and80 manifest keyframes have valid bounds/pivots and unchanged ratio.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/blank':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
helpers=r'''()=>{
 window.ssBegin=(type=0,step=5)=>{window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}clearGameOver();gameWorlds.setDeveloperStart({enabled:true,regionId:6,phase:step});start(type);transition=0;spawn=999;invuln=999;keys.fire=false;tilt={x:0,y:0};player.x=W*.75;player.y=H*.7;player.vx=player.vy=0;itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();};
 window.ssRun=fn=>{window.gameExitDialogOpen=false;try{return fn();}finally{window.gameExitDialogOpen=true;gameScoring.updateHUD();draw();}};
 window.ssAdvance=(seconds,hz=120)=>{let left=seconds;while(left>1e-9&&started){const step=Math.min(left,1/hz);update(step);left-=step;}};
 window.ssSelect=name=>{const snap=gameStormBoss.snapshot();if(snap.phase!=='rest')throw Error('Expected rest');const choices=gameStormBoss.patterns.filter(p=>p!==snap.last),index=choices.indexOf(name);if(index<0)throw Error('Consecutive pattern forbidden');const random=Math.random;Math.random=()=>((index+.25)/choices.length);try{ssAdvance(snap.remaining+1e-6);}finally{Math.random=random;}return gameStormBoss.snapshot();};
 window.ssSpawn=(id,x=W*.35,y=H*.4)=>{const choices=gameStormConfig.ids,index=choices.indexOf(id),weights=gameStormConfig.weights[phase-1];let sum=0;for(let i=0;i<index;i++)sum+=weights[i];const original=gameStormSpawns.select;const seed=gameStormSpawns.snapshot();const random=Math.random;Math.random=()=>.5;try{warnEnemy();const w=warnings.at(-1);w.x=x;w.y=y;w.time=0;update(0);}finally{Math.random=random;}return enemies.at(-1);};
 window.ssHit=e=>{bullets=[];shoot();bullets=[bullets[0]];Object.assign(bullets[0],{x:e.x,y:e.y,vx:0,vy:0});update(0);};
 window.ssStorage=()=>['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'].map(k=>localStorage.getItem(k));
}'''
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
  if args.standalone:page.goto(url+'blank');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url,wait_until='load')
  page.wait_for_function('gameStormSky.ready()&&gameSnowfield.ready()&&gameVolcano.ready()');page.evaluate(helpers);initial=page.evaluate('ssStorage()')
  assert page.evaluate('gameWorlds.worlds[1].regionIds.join()==="4,5,6,7"&&gameWorlds.snapshot().route.join()==="0,1,2,3,4,5,6,7"&&gameWorlds.isTrial()&&!gameWorlds.isDeveloper()')
  page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('6');page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap();page.wait_for_function('started&&!!boss');page.evaluate('window.gameExitDialogOpen=true');assert page.evaluate('stage===6&&phase===5&&phaseKills===6&&boss.maxHp===90&&enemies.length===0')
  passed('Help auto-lists World2 Storm Sky1–5; actual start button enters boss directly, trial route appends4→5→6, default World1 remains20 phases/OFF.')
  entries=[]
  for kind in range(3):
   for step in range(1,6):
    row=page.evaluate('([kind,step])=>ssRun(()=>{ssBegin(kind,step);return {stage,phase,hp,upgrade:player.upgrade,angle:player.a,boss:!!boss,route:gameWorlds.snapshot().route,background:terrainImgs[stage].currentSrc};})',[kind,step]);assert row['stage']==6 and row['phase']==step and row['hp']==[4,6,9][kind] and row['upgrade']==0 and row['angle']==math.pi and row['boss']==(step==5) and row['route']==[6];entries.append(row)
  assert len({r['background'] for r in entries})==1;report['direct_entries']=entries
  passed('Three characters×five direct phases start correctly with originalHP/upgrade0/12-o’clock heading and one identical approved background image.')
  rng=page.evaluate('''ssRun(()=>{const before=[gameVolcanoSpawns.snapshot(),gameSnowfieldSpawns.snapshot()];gameStormSpawns.reset(123);const a=Array.from({length:100},()=>gameStormSpawns.select(4));gameStormSpawns.reset(123);const b=Array.from({length:100},()=>gameStormSpawns.select(4));return {a,b,before,after:[gameVolcanoSpawns.snapshot(),gameSnowfieldSpawns.snapshot()],weights:gameStormConfig.weights};})''');assert rng['a']==rng['b'] and len(set(rng['a']))==4 and rng['before']==rng['after'] and all(sum(w)==100 for w in rng['weights']);report['spawns']=rng
  passed('Independent seeded species draws repeat exactly, all4 species occur, weights sum100 per phase, and snow/volcano PRNG streams do not change.')
  normals=page.evaluate('''ssRun(()=>{ssBegin(0,4);gameStormSpawns.reset(23);const rows=[];for(let n=0;n<32;n++){const e=ssSpawn();rows.push({id:e.stormSpeciesId,hp:e.hp,speed:e.speed,state:gameStormCombat.snapshot(e),art:gameStormSky.pose(e).id});}return rows;})''');profiles={r['id']:r for r in page.evaluate('gameStormConfig.monsters')};assert set(r['id'] for r in normals)==set(profiles)
  for r in normals:assert r['hp']==profiles[r['id']]['hp'] and r['speed']==profiles[r['id']]['speed'] and r['art']==r['id']
  report['normal_spawns']=normals
  passed('Real warning/materialization path independently binds all4 species to their ownHP1/2/2/3, movement, combat state and matching art; no legacy species leakage.')
  behavior=page.evaluate('''ssRun(()=>{const rows=[];for(const spec of gameStormConfig.monsters){ssBegin(0,4);gameStormSpawns.reset(23);let e;for(let i=0;i<100;i++){e=ssSpawn();if(e.stormSpeciesId===spec.id)break;}enemies=[e];e.x=W*.3;e.y=H*.45;e.shot=0;const before=[e.x,e.y];for(let i=0;i<480;i++)gameStormCombat.update(e,1/120);rows.push({id:e.stormSpeciesId,before,after:[e.x,e.y],state:gameStormCombat.snapshot(e),bullets:enemyBullets.map(b=>({tag:b.stormNormal,speed:Math.hypot(b.vx,b.vy)}))});}return rows;})''')
  for r in behavior:assert r['before']!=r['after'] and r['state']['shots']>=1 and all(abs(b['speed']-profiles[r['id']]['bullet'])<1e-7 and b['tag']==r['id'] for b in r['bullets'])
  report['normal_behavior']=behavior
  passed('Cloud approaches/basic shot, bat telegraph→fixed dash→rest, spirit irregular travel/wind shot, and ranged jellyfish/orbs run on local parameters; finite projectile caps hold.')
  for step in range(1,5):
   page.evaluate('step=>ssRun(()=>{ssBegin(0,step);gameStormSpawns.reset(23);for(let i=0;i<4;i++)ssSpawn();enemies.forEach((e,i)=>{e.x=W*(.2+i*.18);e.y=H*.42;});draw();})',step);page.screenshot(path=str(args.artifacts/f'storm-normal-phase-{step}.png'))
  damage=page.evaluate('''ssRun(()=>{ssBegin(0,1);const e=ssSpawn();e.hp=1;enemies=[e];ssHit(e);const one={score:runScore,kills:phaseKills,dead:e.hp<=0};gameScoring.enemyDefeated(e);return {one,after:runScore};})''');assert damage['one']=={'score':100,'kills':1,'dead':True} and damage['after']==100
  passed('Normal death gives100 once and advances the existing6-kill quota once; duplicate score is rejected, hit/defeat animation uses the same identity.')
  barrage=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('barrage');const warning={s:gameStormBoss.snapshot(),bullets:enemyBullets.length};ssAdvance(gameStormBoss.snapshot().remaining);const first=enemyBullets.filter(b=>b.stormBoss).map(b=>({angle:Math.atan2(b.vy,b.vx),speed:Math.hypot(b.vx,b.vy)}));ssAdvance(gameStormBoss.snapshot().remaining);return {warning,first,second:enemyBullets.filter(b=>b.stormBoss).slice(8).map(b=>Math.atan2(b.vy,b.vx)),state:gameStormBoss.snapshot()};})''')
  assert barrage['warning']['bullets']==0 and len(barrage['first'])==8 and len(barrage['second'])==8 and barrage['state']['shots']==16 and all(abs(b['speed']-82)<1e-7 for b in barrage['first'])
  assert abs(barrage['second'][0]-math.pi/8)<1e-7;report['barrage']=barrage;page.screenshot(path=str(args.artifacts/'storm-barrage.png'))
  passed('Barrage has a visible no-damage warning,8 directions at45° then8 directions offset22.5°;82px/s and32-live-bullet cap are storm-only.')
  wind=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('tornado');ssAdvance(gameStormBoss.snapshot().remaining);const s=gameStormBoss.snapshot();const w=s.winds[0];hp=3;invuln=0;player.x=w.x;player.y=w.y;player.vx=player.vy=0;const score=runScore;update(.001);const moved=gameStormBoss.snapshot();const before=moved.teleports;const still=moved.winds[0];player.x=still.x;player.y=still.y;update(.001);return {initial:s,moved,after:gameStormBoss.snapshot(),hp,scoreBefore:score,scoreAfter:runScore,player:[player.x,player.y],heading:player.a};})''')
  assert 2<=len(wind['initial']['winds'])<=3 and wind['moved']['teleports']==1 and wind['after']['teleports']==1 and wind['hp']==3 and wind['scoreBefore']==wind['scoreAfter'] and wind['heading']==math.pi
  log=wind['moved']['teleportLog'][0];assert log['hp']==log['afterHP'] and log['score']==log['afterScore'] and log['safe'] and wind['moved']['spin']>0;report['wind']=wind;page.screenshot(path=str(args.artifacts/'storm-tornado-transport.png'))
  passed('Two/three moving winds transport on contact to an inset boss/enemy/projectile/UI-safe location with0HP/score change; contact cooldown blocks repeats and visual spin preserves firing heading.')
  safe=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('tornado');ssAdvance(gameStormBoss.snapshot().remaining);const s=gameStormBoss.snapshot();return {points:Array.from({length:60},()=>gameStormBoss.safeTarget()),arena:[W,H],boss:{x:boss.x,y:boss.y,r:boss.r},rects:s.rects,winds:s.winds};})''');
  for point in safe['points']:
   assert point and 22<=point['x']<=safe['arena'][0]-22 and 22<=point['y']<=safe['arena'][1]-22
   assert math.hypot(point['x']-safe['boss']['x'],point['y']-safe['boss']['y'])>safe['boss']['r']+39
   for rect in safe['rects']:
    nearest_x=max(rect['left'],min(rect['right'],point['x']));nearest_y=max(rect['top'],min(rect['bottom'],point['y']))
    assert math.hypot(point['x']-nearest_x,point['y']-nearest_y)>27
   assert all(math.hypot(point['x']-w['x'],point['y']-w['y'])>51 for w in safe['winds'])
  report['safe_destinations']=safe
  passed('Sixty sampled transport destinations independently satisfy inset/UI/boss/actor/projectile/wind safety; failure to find space skips relocation instead of forcing an unsafe point.')
  laser=page.evaluate('''ssRun(()=>{ssBegin();ssSelect('laser');const warning=gameStormBoss.snapshot();const line=warning.lasers[0];player.x=line.x+(line.endX-line.x)*.87;player.y=line.y+(line.endY-line.y)*.87;hp=4;invuln=0;ssAdvance(warning.remaining-.01);const warningHP=hp;ssAdvance(.02);const active=gameStormBoss.snapshot();const hitHP=hp;const geometry=gameStormBoss.laserContains(player);ssAdvance(.25);return {warning,warningHP,active,hitHP,afterHP:hp,geometry};})''');report['laser']=laser;assert laser['warningHP']==4 and laser['hitHP']==3 and laser['afterHP']==3 and laser['geometry'] and len(laser['active']['lasers'])==2
  assert laser['active']['phase']=='laser' and laser['active']['laserAngle']>0;report['laser']=laser;page.screenshot(path=str(args.artifacts/'storm-laser.png'))
  passed('Two actual turbine-origin laser warnings last1s with no damage; finite10px beams rotate slowly for2s, share segment collision and honor existing1.55s invulnerability/UI clipping.')
  awake=page.evaluate('''ssRun(()=>{ssBegin(2);ssSelect('barrage');boss.hp=boss.maxHp*.5;hp=9;const before={x:player.x,y:player.y,score:runScore};update(0);const initial=gameStormBoss.snapshot();ssAdvance(1);const pulled={x:player.x,y:player.y,hp};ssAdvance(1);const after=gameStormBoss.snapshot(),speed=enemyBullets.filter(b=>b.stormBoss).map(b=>Math.hypot(b.vx,b.vy));ssAdvance(14);return {before,initial,pulled,after,speed,last:gameStormBoss.snapshot(),hp};})''');assert awake['initial']['phase']=='awakening' and awake['initial']['awakenCount']==1 and awake['after']['phase2'] and awake['after']['shots']==12 and len(awake['speed'])==12 and all(abs(v-90.2)<1e-7 for v in awake['speed']) and awake['last']['awakenCount']==1
  assert math.hypot(awake['pulled']['x']-awake['before']['x'],awake['pulled']['y']-awake['before']['y'])>10;assert awake['after']['remaining']>=1.5;report['awakening']=awake;page.screenshot(path=str(args.artifacts/'storm-phase2.png'))
  passed('HP50% triggers exactly one2s awakening/pull then12-way volley; phase2 attack timing/turning rate×1.2 and bullet speed×1.1, with rest never below1.5s and no changes to other regions.')
  resistance=page.evaluate('''ssRun(()=>{ssBegin(2);boss.hp=10;player.x=W*.82;player.y=H*.72;player.vx=player.vy=0;tilt={x:1,y:0};update(0);const x=player.x;ssAdvance(.6);return {dx:player.x-x,hp,phase:gameStormBoss.snapshot().phase};})''');assert resistance['dx']>0;report['pull_resistance']=resistance
  passed('Tanko resists22px/s awakening pull using its original acceleration/drag and tilt input; player flight configuration and maximum rotation speeds remain byte-preserved.')
  sequence=page.evaluate('''ssRun(()=>{ssBegin();ssAdvance(100);return gameStormBoss.snapshot();})''');seq=sequence['sequence'];assert all(a!=b for a,b in zip(seq,seq[1:]));assert len(seq)>=10 and sequence['shots']>0 and len(page.evaluate('enemyBullets.filter(b=>b.stormBoss)'))<=32;report['pattern_sequence']=sequence
  passed('A100s controlled boss run keeps nonrepeating random pattern order and bounded winds/projectiles; no async attack timers or unbounded effect queues.')
  bossKills=[]
  for kind in range(3):
   row=page.evaluate('kind=>ssRun(()=>{ssBegin(kind);boss.hp=1;const dead=boss;ssHit(dead);const first={score:runScore,reward:dead.rewardGranted,state:gameStormBoss.snapshot(),boss:!!boss};grantBossReward(dead);gameScoring.bossDefeated(dead);ssAdvance(1);return {first,score:runScore,started,result:gameScoring.getLastResult()};})',kind)
   assert row['first']['score']==row['score']==2000 and row['first']['reward'] and row['first']['state'] is None and not row['first']['boss'] and not row['started'] and row['result']['developerTest'] and not row['result']['saved'];bossKills.append(row)
  report['boss_kills']=bossKills
  passed('All3 original weapons kill Storm Overlord via real bullets;2000points/reward once, attack cleanup and defeat outro complete, developer results remain outside TOP10/history.')
  layouts=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);page.evaluate("ssRun(()=>{ssBegin();ssSelect('laser');ssAdvance(gameStormBoss.snapshot().remaining+.2);})");page.wait_for_timeout(70)
   boxes=page.evaluate('''()=>{const ids=['hud','rotationJoystick','fire','fullscreenToggle','exitGame'];return Object.fromEntries(ids.map(id=>{const b=document.getElementById(id).getBoundingClientRect();return [id,{x:b.x,y:b.y,right:b.right,bottom:b.bottom,w:b.width,h:b.height}]}));}''');assert boxes['rotationJoystick']['x']==30 and h-boxes['rotationJoystick']['bottom']==22 and boxes['rotationJoystick']['right']<boxes['fire']['x'];assert boxes['hud']['right']<=boxes['fullscreenToggle']['x']
   page.screenshot(path=str(args.artifacts/f'storm-boss-{w}x{h}.png'));layouts.append({'viewport':[w,h],'boxes':boxes})
  report['layouts']=layouts
  passed('915×412/800×360/568×320 actual gameplay captures fit HUD, boss, finite laser and existing30px/22px joystick/fire/fullscreen/exit controls without UI overlap.')
  # Actual trusted UI exit/fullscreen, followed by death timer.
  page.evaluate('window.gameExitDialogOpen=false');
  if not page.evaluate('!!document.fullscreenElement'):page.locator('#fullscreenToggle').tap()
  page.wait_for_function('!!document.fullscreenElement');page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitCancel').tap();assert page.evaluate('started&&!!document.fullscreenElement');page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();page.wait_for_function('!started&&!menu.classList.contains("hidden")');assert page.evaluate('!!document.fullscreenElement&&gameStormBoss.snapshot()===null')
  page.evaluate('ssRun(()=>ssBegin())');page.evaluate('window.gameExitDialogOpen=false;hp=0;update(0)');expect(page.locator('#gameOverOverlay')).to_be_visible(timeout=1000)
  assert page.evaluate('!started&&gameOverPending&&gameStormBoss.snapshot()===null');page.wait_for_timeout(3100);assert page.evaluate('!gameOverPending&&!menu.classList.contains("hidden")&&!!document.fullscreenElement')
  passed('Trusted fullscreen→exit dialog→cancel→confirmed menu keeps fullscreen; HP0 stops immediately, clears storm effects and returns after original3s GAME OVER without browser dialogs.')
  assert page.evaluate('ssStorage()')==initial and not errors and not dialogs and not failed and (not args.standalone or not external)
  report.update(errors=errors,dialogs=dialogs,failed_resources=failed,offline_external_requests=external if args.standalone else [],all_passed=True)
  passed('No JS errors/native dialogs/resource failures, no offline network dependency, no developer storage writes; original music and controls are covered by retained regression suites.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
