from volcano_spawn_fixtures import FIXED_VOLCANO_SPECIES
"""Issue18: actual spawn/combat/guard/projectile/lifecycle tests, native and offline."""
import argparse,hashlib,json,re,shutil,subprocess,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from volcano_combat_preservation import COMBAT_ASSETS,assert_volcano_combat_asset,without_volcano_combat

ROOT=Path(__file__).resolve().parents[1];BASE='4418d500e1dbcb087fa6cea44e706e21dbff2b7b'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true')
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':[
 'Chromium mobile/touch emulation, not physical Galaxy/Samsung Internet/sensor hardware or audible speaker listening.',
 'Actual production spawn/shoot/collision/draw paths; controlled time, positions, invulnerability and pause flags isolate assertions.',
 'Motion/frame-rate comparisons and forced capacity tests are separate controlled fixtures, not manual-play difficulty ratings.'
]}
def passed(value):report['passed'].append(value);print('PASS:',value,flush=True)
def baseline(name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
source=(ROOT/'index.html').read_text()
assert without_volcano_combat(source,'index.html').encode()==baseline('index.html')
asset_hashes={}
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in COMBAT_ASSETS:assert_volcano_combat_asset(name)
 else:assert (without_volcano_combat(path.read_text(),name).encode() if path.suffix=='.js' else path.read_bytes())==baseline(name),name
 asset_hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:
 subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
report['asset_hashes']=asset_hashes
passed('Exact scoped normal-combat hooks only; every existing PNG/atlas/manifest/audio and protected module preserved; all JavaScript parses.')

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-origin':
   self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()

helpers=r'''()=>{
 window.vcKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];
 window.vcStorage=()=>vcKeys.map(k=>localStorage.getItem(k));
 window.vcBegin=(kind=0,step=1)=>{
   window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}
   gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:step});start(kind);
   transition=0;spawn=999;invuln=999;keys.fire=false;tilt={x:0,y:0};enemies=[];warnings=[];bullets=[];enemyBullets=[];particles=[];
   itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();
   player.x=W*.5;player.y=H*.8;player.vx=player.vy=0;
 };
 window.vcSpawn=()=>{vmFixedPhase();warnEnemy();warnings.forEach(w=>w.time=0);update(0);const e=enemies[enemies.length-1];e.x=W*.5;e.y=H*.25;return e;};
 window.vcHit=(e,all=false)=>{bullets=[];shoot();if(!all)bullets=[bullets[0]];for(const b of bullets)Object.assign(b,{x:e.x,y:e.y,vx:0,vy:0});const shots=[...bullets];update(0);return shots;};
 window.vcAdvance=(seconds,step=1/120)=>{let left=seconds;while(left>1e-9){const dt=Math.min(step,left);update(dt);left-=dt;}};
 window.vcArm=e=>{e.shot=999;vcAdvance(2.8);if(gameVolcanoCombat.snapshot(e).mode!=='guard')throw Error('Guard did not arm');};
 window.vcPause=()=>{window.gameExitDialogOpen=true;draw();};
}'''
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
  page=context.new_page();page.add_init_script(FIXED_VOLCANO_SPECIES);errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
  page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
  if args.standalone:
   page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');external.clear();context.set_offline(True)
   page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.wait_for_function('gameVolcano.ready()&&gameSnowfield.ready()&&sprites.length===3&&sprites.every(i=>i.complete&&i.naturalWidth>0)');page.evaluate(helpers)
  initial=page.evaluate('vcStorage()')
  # First use actual Help selectors and direct phase4 entry.
  page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('5');page.locator('#developerStartPhase').select_option('4');page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap()
  assert page.evaluate('stage===5&&phase===4&&!boss&&gameVolcanoCombat.enabled()')
  passed('Real developer Help -> World2 -> Volcano -> phase4 starts the new normal combat without changing route/default trial settings.')
  matrix=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height})
   for kind in range(3):
    for step in range(1,5):
     row=page.evaluate('''({kind,step})=>{vcBegin(kind,step);const e=vcSpawn(),spawnHP=e.hp,id=e.volcanoSpeciesId;
       const before={x:e.x,y:e.y};update(.04);const moved=Math.hypot(e.x-before.x,e.y-before.y);e.shot=0;update(0);
       const bullet=enemyBullets.at(-1),fire={tag:bullet.volcanoFire,speed:Math.hypot(bullet.vx,bullet.vy),life:bullet.life,r:bullet.r},attack=gameVolcano.pose(e).name;
       let hits=0;while(e.hp>0&&hits++<8)vcHit(e);if(e.hp>0)throw Error('Kill stalled');
       const result={kind,step,id,hp:spawnHP,speed:e.speed,fire,moved,attack,score:runScore,phaseKills,dead:e.hp<=0,ghost:gameVolcano.snapshot().ghosts[0].pose.name};vcPause();return result;
      }''',{'kind':kind,'step':step})
     assert row['hp']==[1,2,2,4][step-1] and row['score']==100 and row['phaseKills']==1 and row['dead'] and row['ghost']=='hit',row
     assert row['moved']>0 and row['attack']=='attack' and row['fire']['tag']==row['id'] and row['fire']['life']==3.4 and row['fire']['r']==5,row
     assert abs(row['speed']-[45.6,38,41.04,19][step-1])<1e-9
     assert abs(row['fire']['speed']-[85,89.25,95.2,80.75][step-1])<1e-9
     matrix.append({'viewport':[width,height],**row})
  report['entries']=matrix
  passed('36 real spawns/kills:3 helicopters x3 viewports x4 species, HP1/2/2/4, configured speed/aimed shot, hit/death art,100points and single phase credit.')
  # Time-based motion, smoothness and boundaries, independently of firing.
  motion=page.evaluate('''()=>{const rows=[];for(let step=1;step<=4;step++)for(const fps of [30,60,120]){
    vcBegin(0,step);const random=Math.random;Math.random=()=>.25;const e=vcSpawn();Math.random=random;e.x=W*.2;e.y=H*.2;e.t=0;e.shot=999;player.x=W*.8;player.y=H*.8;
    let maxStep=0,minLateral=0,maxLateral=0;const modes=new Set();
    for(let n=0;n<fps*4;n++){const x=e.x,y=e.y,dx=player.x-x,dy=player.y-y,d=Math.hypot(dx,dy);gameVolcanoCombat.update(e,1/fps);
      const distance=Math.hypot(e.x-x,e.y-y);maxStep=Math.max(maxStep,distance);const side=(-(dy/d)*(e.x-x)+(dx/d)*(e.y-y))*fps;minLateral=Math.min(minLateral,side);maxLateral=Math.max(maxLateral,side);modes.add(gameVolcanoCombat.snapshot(e).mode);
      if(e.x<17||e.x>W-17||e.y<18||e.y>H-18||distance>e.speed/fps+1e-7)throw Error('Boundary/speed jump');}
    rows.push({step,fps,x:e.x,y:e.y,maxStep,minLateral,maxLateral,modes:[...modes]});
    for(const [x,y]of [[17,18],[W-17,18],[17,H-18],[W-17,H-18]]){e.x=x;e.y=y;for(let n=0;n<60;n++)gameVolcanoCombat.update(e,1/60);if(e.x<17||e.x>W-17||e.y<18||e.y>H-18)throw Error('Edge escaped');}
   }vcPause();return rows;}''')
  for step in range(1,5):
   rows=[r for r in motion if r['step']==step]
   assert max(r['x'] for r in rows)-min(r['x'] for r in rows)<.08 and max(r['y'] for r in rows)-min(r['y'] for r in rows)<.08,rows
   if step in [2,3]:assert all(r['minLateral']<-10 and r['maxLateral']>10 for r in rows),rows
  report['motion']=motion
  passed('30/60/120Hz trajectories agree within.08px over4s; both strafe directions/irregular smooth zigzag observed; no teleport, speed overshoot or boundary escape.')
  guards=page.evaluate('''()=>{const rows=[];for(const kind of [0,1,2])for(const up of [0,2,3,5]){
    vcBegin(kind,4);player.upgrade=up;const e=vcSpawn();vcArm(e);const first=vcHit(e)[0],blockedHP=e.hp,firstPierce=first.pierce,blocked=gameVolcanoCombat.snapshot(e);
    bullets=first.life>0?[first]:[];update(0);const repeatedHP=e.hp;vcHit(e);const damagedHP=e.hp;
    rows.push({kind,up,blockedHP,repeatedHP,damagedHP,blocked:blocked.blocked,mode:blocked.mode,firstPierce,score:runScore});
    if(blockedHP!==4||repeatedHP!==4||damagedHP!==4-(kind===2?1.5:1)||blocked.blocked!==1||blocked.mode!=='pursue'||runScore!==0)throw Error('Guard/damage mismatch');
   }
   // A simultaneous volley loses one contact only, never the whole attack.
   for(const kind of [0,1,2]){vcBegin(kind,4);player.upgrade=5;const e=vcSpawn();vcArm(e);const shots=vcHit(e,true);const expected=4-(shots.length-1)*(kind===2?1.5:1);
     rows.push({kind,volley:shots.length,hp:e.hp,expected,blocks:gameVolcanoCombat.snapshot(e).blocked});if(e.hp!==expected||gameVolcanoCombat.snapshot(e).blocked!==1)throw Error('Volley overblocked');if(e.hp<=0&&(runScore!==100||phaseKills!==1))throw Error('Duplicate volley credit');}
   vcPause();return rows;}''')
  report['guards']=guards
  passed('Guard blocks exactly one contact then ends:3 characters at upgrades0/2/3/5, homing/multishot and Tanko1.5 damage; repeat bullet cannot re-hit, volley remainder applies normal damage.')
  guard_rules=page.evaluate('''()=>{
    vcBegin(2,4);const e=vcSpawn();e.shot=999;vcAdvance(2.5);const windup=gameVolcanoCombat.snapshot(e);vcAdvance(.25);const active=gameVolcanoCombat.snapshot(e);vcAdvance(.7);const expired=gameVolcanoCombat.snapshot(e);
    vcAdvance(4.5);const windupAgain=gameVolcanoCombat.snapshot(e);vcAdvance(.25);const rearmed=gameVolcanoCombat.snapshot(e);const first=vcHit(e)[0];const firstHit=[e.hp,first.pierce];
    const second=gameVolcanoCombat.prepare({x:e.x+60,y:e.y,hp:1,r:16,t:0,shot:999,volcanoSpeciesId:'magma_beetle'});enemies=[second];Object.assign(first,{x:second.x,y:second.y,vx:0,vy:0});bullets=[first];update(0);
    const shared={hp:second.hp,pierce:first.pierce,life:first.life,removed:!bullets.includes(first)};
    e.hp=0;const before=gameVolcanoCombat.snapshot(e);gameVolcanoCombat.update(e,1);const noRevive=JSON.stringify(before)===JSON.stringify(gameVolcanoCombat.snapshot(e))&&!gameVolcanoCombat.blockHit(e);
    vcPause();return {windup,active,expired,windupAgain,rearmed,firstHit,shared,noRevive};
   }''')
  assert [guard_rules[k]['mode'] for k in ['windup','active','expired','windupAgain','rearmed']]==['windup','guard','pursue','windup','guard'],guard_rules
  assert guard_rules['firstHit']==[4,1] and guard_rules['shared']=={'hp':2.5,'pierce':0,'life':0,'removed':True} and guard_rules['noRevive'],guard_rules
  report['guard_rules']=guard_rules
  passed('Guard .25s warning/.7s maximum/4.5s cooldown expires and rearms; Tanko spends shared pierce on block then damages next enemy and vanishes; dead actors cannot fire/rearm/block.')
  fire=page.evaluate('''()=>{const rows=[];for(let step=1;step<=4;step++){
    vcBegin(0,step);const e=vcSpawn();e.shot=0;const shots=[];let seen=0;
    for(let n=0;n<12*120;n++){update(1/120);e.x=W*.2;e.y=H*.2;player.x=W*.8;player.y=H*.8;const s=gameVolcanoCombat.snapshot(e);if(s.shots!==seen){shots.push(s.age);seen=s.shots;}}
    rows.push({step,shots,interval:gameVolcanoCombat.snapshot(e).interval,live:enemyBullets.length});
   }
   vcBegin(0,1);const actors=Array.from({length:14},(_,i)=>gameVolcanoCombat.prepare({x:40+i*10,y:40,hp:1,r:16,t:0,shot:0,volcanoSpeciesId:'ember_bean'}));
   for(let n=0;n<6;n++){actors[0].shot=0;gameVolcanoCombat.update(actors[0],0);}for(let n=0;n<6;n++)for(const e of actors){e.shot=0;gameVolcanoCombat.update(e,0);}
   const cap=enemyBullets.length;const perActor=actors.map(e=>gameVolcanoCombat.snapshot(e).shots);enemyBullets.forEach(b=>b.life=0);actors[0].shot=0;gameVolcanoCombat.update(actors[0],0);const afterExpiry=gameVolcanoCombat.snapshot(actors[0]).shots;
   vcPause();return {rows,cap,perActor,afterExpiry};}''')
  assert fire['cap']==28 and max(fire['perActor'])<=3 and fire['afterExpiry']>fire['perActor'][0],fire
  assert [len(r['shots']) for r in fire['rows']]==[4,3,3,2],fire
  report['fire']=fire
  passed('12s normal-engine firing gives4/3/3/2 single shots, finite3.4s life and separated cooldowns; forced load caps at28 total/3 per owner and permits shots after expiry.')
  # Actual flame collision reuses hurt/invulnerability and ordinary Tanko cancellation.
  damage=page.evaluate('''()=>{vcBegin(2,1);const e=vcSpawn();e.shot=0;update(0);const shot=enemyBullets[0];enemies=[];invuln=0;shot.x=player.x;shot.y=player.y;shot.vx=shot.vy=0;const before=hp;update(0);const after=hp;enemyBullets=[{...shot,life:3.4}];update(0);const invulnerableHP=hp;
    enemyBullets=[];bullets=[];shoot();const b=bullets[0];const block={...shot,x:b.x,y:b.y,life:3.4};enemyBullets=[block];update(0);vcPause();return {before,after,invulnerableHP,enemyLife:block.life,tankoLife:b.life};}''')
  assert damage['after']==damage['before']-1 and damage['invulnerableHP']==damage['after'] and damage['enemyLife']==damage['tankoLife']==0,damage
  report['damage']=damage
  passed('Flame hit uses existing1HP hurt/invulnerability; Tanko and flame cancel each other immediately with unchanged projectile rules.')
  contact=page.evaluate('''()=>{vcBegin(0,1);const e=vcSpawn();e.x=player.x;e.y=player.y;invuln=0;const before=hp;update(0);const after=hp;update(0);const protectedHP=hp;
    e.x=player.x+29.01;invuln=0;update(0);const outsideHP=hp;e.x=player.x+28.99;update(0);const insideHP=hp;vcPause();return {before,after,protectedHP,outsideHP,insideHP};}''')
  assert contact['after']==contact['before']-1 and contact['protectedHP']==contact['outsideHP']==contact['after'] and contact['insideHP']==contact['after']-1,contact
  report['contact']=contact
  # Guard screenshots and mobile readibility are actual game renderer captures.
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height})
   for step in range(1,5):
    page.evaluate('''step=>{vcBegin(0,step);const e=vcSpawn();e.shot=0;update(0);const b=enemyBullets[0];b.x=W*.5;b.y=H*.52;
      if(step===4){e.shot=999;vcAdvance(2.8);e.x=W*.5;e.y=H*.35;}vcPause();}''',step)
    page.screenshot(path=str(args.artifacts/f'volcano-combat-{step}-{width}x{height}.png'))
  page.evaluate('vcBegin(0,4);window.vcBeetle=vcSpawn();vcBeetle.shot=999;vcAdvance(2.6);vcPause()');page.screenshot(path=str(args.artifacts/'beetle-windup.png'))
  page.evaluate('window.gameExitDialogOpen=false;vcAdvance(.2);vcHit(vcBeetle);vcPause()');page.screenshot(path=str(args.artifacts/'beetle-blocked.png'))
  passed('Actual4-species flame/guard screenshots fit915x412,800x360,568x320; warmup/guard/blocked states use original69-frame art and bounded decorative overlays.')
  prelude=page.evaluate('''()=>{vcBegin(0,4);nextPhase();transition=0;spawn=999;const initial=runScore;const entries=[];
    for(let i=0;i<6;i++){const e=vcSpawn();entries.push({id:e.volcanoSpeciesId,hp:e.hp});while(e.hp>0)vcHit(e);}update(0);
    const result={entries,scoreDelta:runScore-initial,phaseKills,bossHP:boss.maxHp,bossCombat:gameVolcanoCombat.snapshot(boss),bossGuard:gameVolcanoCombat.blockHit(boss)};vcPause();return result;}''')
  assert prelude['entries']==[{'id':'magma_beetle','hp':4}]*6 and prelude['scoreDelta']==600 and prelude['phaseKills']==6 and prelude['bossHP']==80 and prelude['bossCombat'] is None and not prelude['bossGuard'],prelude
  report['prelude']=prelude
  passed('Seeded normal phase5 audit requires6 beetles withHP4 and600kill points; developer5 remains direct dragon; dragon receives no normal-combat state/guard.')
  scoped=page.evaluate('''()=>{const rows=[];for(const region of [0,3,4,5]){vcBegin(0,1);stage=region;const e={x:100,y:100,hp:7,r:16,t:0,shot:999,special:region===5,volcanoSpeciesId:'magma_beetle'};gameVolcanoCombat.prepare(e);rows.push({region,hp:e.hp,state:gameVolcanoCombat.snapshot(e),blocked:gameVolcanoCombat.blockHit(e)});}vcBegin(0,4);const e=vcSpawn();vcArm(e);gameVolcanoCombat.cleanup();const cleared=gameVolcanoCombat.snapshot(e)===null;vcPause();return {rows,cleared};}''')
  assert scoped['cleared'] and all(x['hp']==7 and x['state'] is None and not x['blocked'] for x in scoped['rows']),scoped
  report['scope']=scoped
  passed('World1/snow/item actors never opt in; explicit cleanup drops normal combat state without touching art or item systems.')
  # Real exit overlay preserves normal state while paused; confirming clears it.
  page.evaluate('window.gameExitDialogOpen=false;vcBegin(0,4);window.vcExitActor=vcSpawn();vcExitActor.shot=999;')
  page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();state=page.evaluate('gameVolcanoCombat.snapshot(vcExitActor)');page.wait_for_timeout(150);assert page.evaluate('gameVolcanoCombat.snapshot(vcExitActor)')==state
  page.locator('#gameExitCancel').tap();page.wait_for_timeout(70);assert page.evaluate('gameVolcanoCombat.snapshot(vcExitActor).age')>state['age']
  page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();assert page.evaluate('gameVolcanoCombat.snapshot(vcExitActor)===null')
  assert page.evaluate('vcStorage()')==initial
  passed('In-page exit pauses/resumes combat timers; confirmed exit clears state and developer runs leave all4 ranking/history keys unchanged.')
  lifecycle=page.evaluate('''()=>{vcBegin(0,2);const old=vcSpawn();old.shot=0;update(0);nextPhase();const phaseClean=gameVolcanoCombat.snapshot(old)===null&&enemyBullets.length===0;
    vcBegin(0,4);const dead=vcSpawn();vcArm(dead);hp=0;update(0);return {phaseClean,deathClean:gameVolcanoCombat.snapshot(dead)===null,stopped:!started,overlay:gameOverPending};}''')
  assert lifecycle=={'phaseClean':True,'deathClean':True,'stopped':True,'overlay':True},lifecycle
  expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_visible(timeout=5000)
  assert page.evaluate('vcStorage()')==initial and page.locator('#selectionResult').inner_text()==''
  report['lifecycle']=lifecycle
  passed('Actual nextPhase clears prior normal state/bullets;HP0 clears guard state, freezes play and returns a clean unsaved developer menu after3s.')
  assert not errors and not dialogs and not failed,(errors,dialogs,failed)
  if args.standalone:assert not external,external
  report.update(page_errors=errors,native_dialogs=dialogs,failed_requests=failed,offline_external_requests=external if args.standalone else [],all_passed=True)
  passed('Native/embedded module loads with no JS/dialog/resource errors; offline external requests0.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
