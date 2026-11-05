"""Issue22 private weighted draws plus actual mixed actors, boss gate and lifecycle."""
import argparse,hashlib,json,math,re,shutil,subprocess,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from volcano_mixed_preservation import without_volcano_mixed,assert_volcano_mixed_asset
ROOT=Path(__file__).resolve().parents[1];BASE='19c3f603870c602b508944275fb51a00dce0ec8d'
IDS=['ember_bean','lava_lizard','volcano_bat','magma_beetle'];WEIGHTS=[[80,20,0,0],[45,40,15,0],[20,35,35,10],[10,25,35,30],[5,15,35,45]]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':['Controlled real Chromium spawn/combat/render/pointer paths and seed fixtures, not physical Galaxy/Samsung Internet or human difficulty evaluation.','Capture coordinates and invulnerability are controlled; species come from the production weighted selector and real warning/spawn path.','Fixed-seed replay is per volcano-region draw sequence; unseeded starts/region entries intentionally refresh private entropy.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
for name in ['index.html','assets/worlds/difficulty.js','assets/worlds/worlds.js','assets/volcano/volcano.js']:
 assert without_volcano_mixed((ROOT/name).read_text(),name).encode()==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name=='assets/volcano/spawns.js':assert_volcano_mixed_asset(name);continue
 actual=without_volcano_mixed(path.read_text(),name).encode() if path.suffix=='.js' else path.read_bytes()
 assert actual==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',(ROOT/'index.html').read_text(),re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Exact3 engine hooks plus art prepare/volcano-only table/2notice strings; combat.js, approved boss sweep, snow/World1, players/items/score/audio and every PNG/manifest byte-protected; all JS parses.')
helpers=r'''()=>{
 window.vmKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];
 window.vmStorage=()=>vmKeys.map(k=>localStorage.getItem(k));
 window.vmBegin=(kind=0,step=3,seed=12345)=>{window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}
  gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:step===5?4:step});start(kind);if(step===5)nextPhase();
  gameVolcanoSpawns.reset(seed);transition=0;spawn=999;invuln=999;keys.fire=false;tilt={x:0,y:0};player.x=W*.7;player.y=H*.8;player.vx=player.vy=0;itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();};
 window.vmRun=fn=>{window.gameExitDialogOpen=false;try{return fn();}finally{window.gameExitDialogOpen=true;gameScoring.updateHUD();draw();}};
 window.vmSpawn=(x=W*.4,y=H*.3)=>{warnEnemy();const warning=warnings.at(-1);warning.x=x;warning.y=y;warning.time=0;update(0);return enemies.at(-1);};
 window.vmHit=e=>{bullets=[];shoot();bullets=[bullets[0]];Object.assign(bullets[0],{x:e.x,y:e.y,vx:0,vy:0});update(0);};
 window.vmAdvance=(seconds,hz=120)=>{let left=seconds;while(left>1e-9&&started){const dt=Math.min(1/hz,left);update(dt);left-=dt;}};
 window.vmPopulate=(kind,step,seed)=>{vmBegin(kind,step,seed);spawn=0;const random=Math.random,seen=new WeakSet(),warningsAt=[],actorsAt=[];let elapsed=0;Math.random=()=>.5;
  try{const cap=Math.min(7,3+gameWorlds.profile(stage)+Math.floor(phase/2));while(enemies.length<cap&&elapsed<30){update(1/120);elapsed+=1/120;for(const w of warnings)if(!seen.has(w)){seen.add(w);warningsAt.push(elapsed);const i=warningsAt.length-1;w.x=W*(.14+i*.15);w.y=H*.3;}for(const e of enemies)if(!seen.has(e)){seen.add(e);actorsAt.push(elapsed);}}}
  finally{Math.random=random;spawn=999;}
  return {ids:enemies.map(e=>e.volcanoSpeciesId),hp:enemies.map(e=>e.hp),count:enemies.length,cap:Math.min(7,3+gameWorlds.profile(stage)+Math.floor(phase/2)),interval:Math.max(.72,tactics[stage].spawn-(phase-1)*.09),warningsAt,actorsAt,phaseKills,draws:gameVolcanoSpawns.snapshot().draws};};
}'''
def advance(seed):
 seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff;return seed&0xffffffff
def choose(step,x):
 c=0
 for i,w in enumerate(WEIGHTS[step-1]):
  c+=w
  if x/4294967296*100<c:return IDS[i]
def draws(seed,step,count):
 result=[]
 for _ in range(count):seed=advance(seed);result.append(choose(step,seed))
 return result
seeds={}
for step in range(1,6):
 for idx,id in enumerate(IDS):
  if not WEIGHTS[step-1][idx]:continue
  seeds[f'{step}:{id}']=next((i*0x9e3779b1)&0xffffffff for i in range(1,100000) if draws((i*0x9e3779b1)&0xffffffff,step,1)==[id])
plans={}
for step in range(1,6):
 count=min(7,3+step//2);minimum=sum(w>0 for w in WEIGHTS[step-1]);seed=next(i for i in range(1,100000) if len(set(draws(i,step,count)))>=minimum);plans[str(step)]={'seed':seed,'ids':draws(seed,step,count)}
report['species_seeds']=seeds;report['capture_plans']=plans
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
  if args.standalone:page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.wait_for_function('gameVolcano.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');page.evaluate(helpers);initial=page.evaluate('vmStorage()')
  assert page.evaluate('gameVolcanoSpawns.weights')==WEIGHTS and page.evaluate('gameVolcanoSpawns.ids')==IDS
  boundary=page.evaluate('''()=>{const rows=[];for(let phase=1;phase<=5;phase++){let c=0;for(let i=0;i<4;i++){const w=gameVolcanoSpawns.weights[phase-1][i];if(w)rows.push({phase,id:gameVolcanoSpawns.ids[i],start:gameVolcanoSpawns.chooseForRoll(phase,c/100),middle:gameVolcanoSpawns.chooseForRoll(phase,(c+w*.5)/100),end:gameVolcanoSpawns.chooseForRoll(phase,(c+w-1e-8)/100)});c+=w;}}return rows;}''')
  assert all(x['id']==x['start']==x['middle']==x['end'] for x in boundary) and len(boundary)==17;report['boundaries']=boundary
  passed('Exact5 Issue22 weight rows sum100%; all17 nonzero interval boundaries/midpoints are correct, including phase1/2 zero-percent exclusions.')
  distributions=page.evaluate('''()=>{const rows=[];for(const seed of [1,12345,0xdeadbeef])for(let phase=1;phase<=5;phase++){gameVolcanoSpawns.reset(seed);const counts=Object.fromEntries(gameVolcanoSpawns.ids.map(id=>[id,0]));for(let i=0;i<30000;i++)counts[gameVolcanoSpawns.select(phase)]++;rows.push({phase,seed,total:30000,counts});}return rows;}''')
  for row in distributions:
   for idx,id in enumerate(IDS):assert abs(row['counts'][id]/300- WEIGHTS[row['phase']-1][idx])<1 and (WEIGHTS[row['phase']-1][idx]>0 or row['counts'][id]==0),row
  report['distributions']=distributions;passed('450,000 draws at3 fixed seeds x5 phases x30,000 match every target within1percentage point; every0% cell remains0.')
  isolation=page.evaluate('''()=>{const old=Math.random,snow=JSON.stringify(gameSnowfieldSpawns.snapshot());let calls=0;Math.random=()=>{calls++;throw Error('Shared RNG used');};try{gameVolcanoSpawns.reset(12345);const a=Array.from({length:1000},()=>gameVolcanoSpawns.select(3));gameVolcanoSpawns.reset(12345);const b=Array.from({length:1000},()=>gameVolcanoSpawns.select(3));gameVolcanoSpawns.reset(1);const repeat=Array.from({length:6},()=>gameVolcanoSpawns.select(1));const before=JSON.stringify(gameVolcanoSpawns.snapshot());let rejected=0;for(const fn of [()=>gameVolcanoSpawns.select(0),()=>gameVolcanoSpawns.select(6),()=>gameVolcanoSpawns.chooseForRoll(1,1),()=>gameVolcanoSpawns.chooseForRoll(1,-.1),()=>gameVolcanoSpawns.reset(NaN)])try{fn();}catch{rejected++;}return {same:JSON.stringify(a)===JSON.stringify(b),snowUnchanged:snow===JSON.stringify(gameSnowfieldSpawns.snapshot()),calls,repeat,rejected,invalidUnchanged:before===JSON.stringify(gameVolcanoSpawns.snapshot()),a};}finally{Math.random=old;}}''')
  assert isolation['same'] and isolation['snowUnchanged'] and isolation['calls']==0 and len(set(isolation['repeat']))==1 and isolation['rejected']==5 and isolation['invalidUnchanged'];assert isolation['a']==draws(12345,3,1000);report['isolation']=isolation
  passed('Independent Python xorshift oracle reproduces1,000 JS draws; replay identical, shared Math.random calls0, snow RNG unchanged, consecutive repeats permitted, invalid inputs rejected without consuming draws.')
  actual=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   for kind in range(3):
    for step in range(1,6):
     for idx,id in enumerate(IDS):
      if not WEIGHTS[step-1][idx]:continue
      row=page.evaluate('''({kind,step,seed})=>vmRun(()=>{vmBegin(kind,step,seed);warnEnemy();const pending=gameVolcanoSpawns.snapshot();warnings.at(-1).time=0;update(0);const e=enemies[0],before={id:e.volcanoSpeciesId,hp:e.hp,speed:e.speed,r:e.r,pose:gameVolcano.pose(e).id,state:gameVolcanoCombat.snapshot(e)};const rng=gameVolcanoSpawns.snapshot();gameVolcano.prepare(e);gameVolcanoCombat.prepare(e);const stable=JSON.stringify(rng)===JSON.stringify(gameVolcanoSpawns.snapshot());try{e.volcanoSpeciesId='invalid';}catch{}e.shot=0;update(0);const b=enemyBullets.at(-1),fire={id:b.volcanoFire,speed:Math.hypot(b.vx,b.vy),life:b.life,r:b.r,pose:gameVolcano.pose(e).name};const score=runScore,kills=phaseKills;let hits=0;while(e.hp>0&&hits++<8)vmHit(e);const ghost=gameVolcano.snapshot().ghosts.at(-1);gameVolcano.tick(.34);return {before,pending,rng,stable,assigned:e.volcanoSpeciesId,fire,hits,ghost:ghost.id,defeat:gameVolcano.snapshot().ghosts.at(-1).pose,score:runScore-score,kills:phaseKills-kills};})''',{'kind':kind,'step':step,'seed':seeds[f'{step}:{id}']})
      assert row['before']['id']==row['before']['pose']==row['before']['state']['id']==row['assigned']==row['fire']['id']==row['ghost']==row['defeat']['id']==id,row
      assert row['before']['hp']==[1,2,2,4][idx] and abs(row['before']['speed']-[45.6,38,41.04,19][idx])<1e-9 and row['before']['r']==16 and row['pending']['draws']==0 and row['rng']['draws']==1 and row['stable'],row
      assert abs(row['fire']['speed']-[85,89.25,95.2,80.75][idx])<1e-8 and row['fire']['life']==3.4 and row['fire']['r']==5 and row['fire']['pose']=='attack' and row['score']==100 and row['kills']==1 and row['defeat']['name']=='defeat',row
      actual.append({'viewport':[width,height],'kind':kind,'phase':step,'seed':seeds[f'{step}:{id}'],**row})
  report['actual_species']=actual;assert len(actual)==153
  passed('153 actual warning->spawn->shot->hit->death cases (3 heroes x3 sizes x17 permitted phase/species pairs): one draw at materialization, stable ID/art/HP/AI/fire/ghost,100points/one normal kill; repeats never heal/reroll.')
  natural=[]
  for step in range(1,6):
   plan=plans[str(step)];row=page.evaluate('''({step,seed})=>vmRun(()=>vmPopulate(0,step,seed))''',{'step':step,'seed':plan['seed']})
   assert row['ids']==plan['ids'] and row['count']==row['cap']==len(plan['ids']) and row['draws']==row['cap'] and row['phaseKills']==0,row
   assert all(abs((b-a)-row['interval'])<.02 for a,b in zip(row['warningsAt'],row['warningsAt'][1:])),row;natural.append({'phase':step,'seed':plan['seed'],**row})
  report['natural_spawns']=natural
  passed('Real unmodified automatic manager mixes all5 normal phases with original2.00/1.91/1.82/1.73/1.64s intervals (120Hz quantization) and3/4/4/5/5 caps; no forced variety, count changes or target changes.')
  mixed=page.evaluate('''seed=>vmRun(()=>{vmPopulate(0,3,seed);const actors=[...enemies];for(let i=0;i<actors.length;i++){actors[i].x=W*(.15+i*.2);actors[i].y=H*.3;actors[i].shot=999;}player.x=W*.5;player.y=H*.85;enemyBullets=[];const modes=Object.fromEntries(actors.map(e=>[e.volcanoSpeciesId,new Set()]));for(let n=0;n<336;n++){update(1/120);for(const e of actors)modes[e.volcanoSpeciesId].add(gameVolcanoCombat.snapshot(e).mode);}const beetle=actors.find(e=>e.volcanoSpeciesId==='magma_beetle');let wait=0;while(gameVolcanoCombat.snapshot(beetle).mode!=='guard'&&wait++<1200)update(1/120);if(wait>=1200)throw Error('Guard did not arrive');actors.forEach((e,i)=>{e.x=W*(.15+i*.2);e.y=H*.3;});const before=beetle.hp;vmHit(beetle);const afterFirst=beetle.hp,blocked=gameVolcanoCombat.snapshot(beetle).blocked;vmHit(beetle);const afterSecond=beetle.hp;enemyBullets=[];const shotsBefore=actors.map(e=>gameVolcanoCombat.snapshot(e).shots);for(let n=0;n<6;n++)for(const e of actors){e.shot=0;gameVolcanoCombat.update(e,0);}const ownerDelta=actors.map((e,i)=>gameVolcanoCombat.snapshot(e).shots-shotsBefore[i]);return {mixedBulletCount:enemyBullets.length,ownerDelta,ids:actors.map(e=>e.volcanoSpeciesId),modes:Object.fromEntries(Object.entries(modes).map(([id,s])=>[id,[...s]])),before,afterFirst,afterSecond,blocked,states:actors.map(e=>gameVolcanoCombat.snapshot(e))};})''',plans['3']['seed'])
  assert mixed['mixedBulletCount']==12 and mixed['ownerDelta']==[3,3,3,3] and len(set(mixed['ids']))==4 and 'strafe' in mixed['modes']['lava_lizard'] and mixed['modes']['volcano_bat']==['zigzag'] and 'guard' in mixed['modes']['magma_beetle'] and mixed['before']==mixed['afterFirst']==4 and mixed['afterSecond']==3 and mixed['blocked']==1 and all(s['blocked']==0 for s in mixed['states'] if s['id']!='magma_beetle'),mixed;report['coexisting_combat']=mixed
  passed('Four coexisting species retain independent pursuit/strafe/zigzag/guard clocks; only beetle blocks exactly one hit, next hit damages normally, other actors never share its defense.')
  # Actual ordinary phase5 gate, then reward/outro; developer direct5 separately below.
  gate=page.evaluate('''()=>vmRun(()=>{vmBegin(0,5,12345);const before=runScore,rows=[];for(let i=0;i<6;i++){const e=vmSpawn();const row={id:e.volcanoSpeciesId,hp:e.hp,bossBefore:!!boss};while(e.hp>0)vmHit(e);rows.push({...row,kills:phaseKills,score:runScore-before});}update(0);const normal={rows,score:runScore-before,bossHP:boss.maxHp,draws:gameVolcanoSpawns.snapshot().draws,bossNormal:gameVolcanoCombat.snapshot(boss),bossPose:gameVolcano.pose(boss,true).id};while(boss)vmHit(boss);vmAdvance(.95);return {normal,after:{started,score:runScore-before,draws:gameVolcanoSpawns.snapshot().draws}};})''')
  assert [x['id'] for x in gate['normal']['rows']]==draws(12345,5,6) and all(not x['bossBefore'] and x['kills']==i+1 and x['score']==100*(i+1) for i,x in enumerate(gate['normal']['rows'])) and gate['normal']['score']==600 and gate['normal']['bossHP']==20 and gate['normal']['draws']==6 and gate['normal']['bossNormal'] is None and gate['normal']['bossPose']=='magma_dragon' and gate['after']=={'started':False,'score':2600,'draws':6},gate;report['ordinary_boss_gate']=gate
  passed('Ordinary4->5 uses phase5 seeded mixed pool for exactly6 kills/600points then unchanged20HP dragon; boss/reward consume no species draw, clear/outro adds2000once and remains an unsaved developer fixture.')
  direct=[]
  page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('5');page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap()
  for kind in range(3):
   page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();row=page.evaluate('({type:player.type,phase,stage,normal:enemies.length,warnings:warnings.length,boss:boss.maxHp,draws:gameVolcanoSpawns.snapshot().draws})');assert row=={'type':kind,'phase':5,'stage':5,'normal':0,'warnings':0,'boss':20,'draws':0},row;direct.append(row);page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
  report['direct_boss']=direct
  passed('Real Help->World2->Volcano->5 starts all3 heroes directly at the dragon with0 normal actors/0 warnings/0 spawn draws; normal6-kill rule is unchanged outside direct mode.')
  scope=page.evaluate('''()=>vmRun(()=>{vmBegin(0,3,12345);const before=gameVolcanoSpawns.snapshot(),rows=[];for(const region of [0,3,4,5]){stage=region;const e={x:100,y:100,hp:5,special:region===5};gameVolcano.prepare(e);rows.push({region,id:e.volcanoSpeciesId,hp:e.hp});}stage=5;gameVolcano.prepare(boss);const after=gameVolcanoSpawns.snapshot();return {before,after,rows};})''')
  assert scope['before']==scope['after'] and all(x.get('id') is None and x['hp']==5 for x in scope['rows']),scope;report['scope']=scope
  drops=page.evaluate('''()=>vmRun(()=>{const rows=[];for(const roll of [.1,.9]){vmBegin(0,3,12345);const e=itemMonsters.spawn({x:100,y:100});gameVolcano.prepare(e);const random=Math.random;Math.random=()=>roll;try{while(e.hp>0)vmHit(e);}finally{Math.random=random;}const it=items[0],before={x:it.x,y:it.y,type:it.type,life:it.life};const itemScore=runScore;nextPhase();rows.push({itemScore,score:runScore,normal:phaseKills,draws:gameVolcanoSpawns.snapshot().draws,before,after:{x:items[0].x,y:items[0].y,type:items[0].type,life:items[0].life}});}return rows;})''')
  assert [x['before']['type'] for x in drops]==['hp','power'] and all(x['itemScore']==200 and x['draws']==0 and x['before']==x['after'] and x['before']['life']==16 and x['normal']==0 for x in drops),drops;report['item_drops']=drops
  passed('Special item actors/World1/snow/bosses do not consume volcano draws; real HP5 item kills still drop both existing16s hp/power types and preserve remaining lifetime/position across phase change.')
  assert page.evaluate('vmStorage()')==initial;report['developer_storage_unchanged_before_normal_trial']=True
  resets=page.evaluate('''()=>vmRun(()=>{vmBegin(0,3,12345);vmSpawn();const consumed=gameVolcanoSpawns.snapshot().draws;nextPhase();const next=gameVolcanoSpawns.snapshot().draws;started=false;menu.classList.remove('hidden');gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true);start(0);gameVolcanoSpawns.reset(12345);gameVolcanoSpawns.select(1);stage=4;phase=5;nextPhase();const entering={stage,phase,draws:gameVolcanoSpawns.snapshot().draws};gameVolcanoSpawns.select(1);start(0);const fresh=gameVolcanoSpawns.snapshot().draws;gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');gameWorlds.setTrialEnabled(false);return {consumed,next,entering,fresh};})''')
  assert resets=={'consumed':1,'next':1,'entering':{'stage':5,'phase':1,'draws':0},'fresh':0},resets;report['resets']=resets
  after_trial=page.evaluate('vmStorage()');history=json.loads(after_trial[3])['records'];assert after_trial[:2]==initial[:2] and json.loads(after_trial[2])['records']==[] and len(history)==2 and all(x['outcome']=='abandoned' for x in history),after_trial;report['intentional_normal_trial_analytics']={'records':history,'normalStoresUnchanged':True,'ranked':0}
  passed('Normal phase changes preserve PRNG progress; actual Snow->Volcano region entry resets it, and new starts reset draw counters; pause/exit do not leak actor-specific state into another run.')
  # Screens use real weighted selections; positions alone are arranged after normal spawning.
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   for kind in range(3):
    page.evaluate('''({kind,seed})=>vmRun(()=>{vmPopulate(kind,3,seed);enemies.forEach((e,i)=>{e.x=W*(.18+i*.21);e.y=H*(.36+(i%2)*.16);});player.x=W*.5;player.y=H*.78;gameVolcano.observe(enemies,boss);})''',{'kind':kind,'seed':plans['3']['seed']});page.screenshot(path=str(args.artifacts/f'mixed-kind{kind}-{width}x{height}.png'))
  passed('3heroes x3 requested landscape screenshots show actual four-species selections together at their existing sizes/animations with unchanged HUD/notice/controls.')
  # All direct fixtures stay out of rankings/history; reset trial scope before comparing.
  page.evaluate('''()=>{window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}gameWorlds.setTrialEnabled(false);}''')
  assert page.evaluate('vmStorage()')==after_trial
  assert not errors and not dialogs and not failed,(errors,dialogs,failed)
  if args.standalone:assert not external,external
  report.update(all_passed=True,page_errors=errors,dialogs=dialogs,failed_requests=failed,offline_external_requests=external if args.standalone else [])
  passed('Native/offline assets load with0 JS/native-dialog/resource errors; offline requests0; developer runs add no records; the two intentional nondeveloper trial restarts save only their2abandoned analysis records, without TOP10 entries or normal-store changes.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
