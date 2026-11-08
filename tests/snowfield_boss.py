"""Issue9: native boss emissions/AOE/lifecycle, protected baseline, offline packaging."""
import argparse,hashlib,io,json,re,shutil,subprocess,tarfile,tempfile,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from snow_boss_preservation import BOSS_ASSETS,assert_boss_asset,without_snow_boss_source,without_snow_boss_asset
ROOT=Path(__file__).resolve().parents[1];BASE='c5daee93966ea926a17c1501c5b3a2d07f0c3600'
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(exist_ok=True,parents=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':[
 'Actual Chromium engine/input/media/fullscreen events with controlled aim, positions,dt and invulnerability; not physical Galaxy or manual difficulty completion.',
 '60/120Hz are deterministic simulation steps, not claimed hardware refresh rates.',
 'Offline runs the exact standalone HTML at a blank localhost origin with networking disabled, not a file policy bypass.',
 'Safe AOEs preserve the original target coordinate but choose the nearest unobstructed center only when screen/HUD/controls would make it unsafe; a resize can cancel an unsafe warning.'
]}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
s=(ROOT/'index.html').read_text();assert without_snow_boss_source(s)==subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT).decode()
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in BOSS_ASSETS:assert_boss_asset(path);continue
 data=without_snow_boss_asset(path.read_text(),name).encode() if path.suffix in ['.js','.css'] else path.read_bytes();assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',s,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Exact Issue9 hooks reverse toc5daee9; every earlier normal AI,art115frames,PNG/manifest,input/item/score/audio asset stays byte-identical apart from two reviewed notices; all JS parses.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/blank-boss-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Boss test origin</title>');return
  super().do_GET()
def serve(folder):
 s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(folder)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
keys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1']
seed={key:json.dumps({'version':1,'records':[{'id':'kept-trial' if 'world2Trial' in key else 'kept-normal','score':35000 if 'world2Trial' in key else 28000,'characterId':0,'characterName':'트리오','regionId':4 if 'world2Trial' in key else 0,'phase':5,'order':1,'createdAt':'2026-11-02T01:00:00.000Z','outcome':'clear','normalKills':150,'itemKills':0,'bossKills':5,'clearedPhases':20,'playTimeSeconds':100,'finalUpgrade':5}]}) for key in keys}
probe='''() => {window.kingAudio=[];const Native=Audio;window.Audio=new Proxy(Native,{construct(t,a){const v=new t(...a);kingAudio.push(v);return v;}});}'''
helpers='''() => {
 window.kingWrites=[];const write=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.startsWith('heliTrio.'))kingWrites.push(k);return write.call(this,k,v);};
 window.kingStorage=()=>JSON.stringify(Object.keys(localStorage).sort().map(k=>[k,localStorage.getItem(k)]));
 window.kingExit=()=>{gameSnowfieldBoss.reset();gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();gameExitDialogOpen=false;clearGameOver();gameControls.reset();gameSnowfield.reset();menu.classList.remove('hidden');};
 window.kingScene=(kind=0)=>{kingExit();if(!gameWorlds.setDeveloperStart({enabled:true,regionId:4,phase:5}))throw Error('Cannot select boss');itemMonsters.configure({opportunitiesPerRegion:0});start(kind);transition=0;spawn=999;invuln=999;player.x=W*.5;player.y=H*.62;fireCooldown=0;return boss;};
 window.kingAdvance=(time,hz=120,fixed=false)=>{let elapsed=0;while(elapsed<time-1e-10&&started){const dt=Math.min(1/hz,time-elapsed);if(fixed&&boss){boss.x=W*.22;boss.y=H*.24;player.x=W*.78;player.y=H*.62;}update(dt);elapsed+=dt;}};
 window.kingWarning=(kind=0)=>{kingScene(kind);kingAdvance(7.8);enemyBullets=[];return gameSnowfieldBoss.snapshot();};
 window.kingKill=()=>{window.lastKing=boss;while(boss){bullets=[];shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(0);}return gameScoring.getLastResult();};
 window.kingFreeze=()=>{invuln=0;rotorSpin=.35;gameExitDialogOpen=true;draw();};
 window.kingDeathAt=null;window.kingReturnAt=null;document.addEventListener('gameover',()=>kingDeathAt=performance.now());new MutationObserver(()=>{if(kingDeathAt!==null&&!menu.classList.contains('hidden'))kingReturnAt=performance.now();}).observe(menu,{attributes:true,attributeFilter:['class']});
}'''
server=serve(ROOT);reference=None;temp=tempfile.TemporaryDirectory(prefix='heli-boss-before-')
try:
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE,'index.html','assets'],cwd=ROOT))) as t:t.extractall(temp.name,filter='data')
 reference=serve(temp.name)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);context.add_init_script('('+probe+')()');page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  url=f'http://127.0.0.1:{server.server_port}/';page.goto(url+'blank-boss-origin');page.evaluate('rows=>{for(const [key,value] of Object.entries(rows))localStorage.setItem(key,value)}',seed);external.clear()
  if args.standalone:context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url,wait_until='load')
  page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()&&window.gameSnowfieldBoss');page.evaluate(helpers);original_storage=page.evaluate('kingStorage()')
  # This historical20-stage regression selects the preserved option explicitly;
  # default40 and all three complete routes are checked by default_world_route.
  assert page.evaluate('gameWorlds.setTrialEnabled(false)')
  assert not page.evaluate('gameWorlds.isDeveloper()||gameWorlds.isTrial()')
  entries=[]
  for kind in range(3):
   if kind:page.evaluate('kingExit()')
   page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('4');page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap();page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap()
   r=page.evaluate('''()=>({type:player.type,hp,max:maxHP[player.type],upgrade:player.upgrade,score:runScore,stage,phase,normal:enemies.length,bossHP:boss.hp,r:boss.r,state:gameSnowfieldBoss.snapshot(),route:gameWorlds.snapshot().route,full:!!document.fullscreenElement})''')
   assert r['type']==kind and r['hp']==r['max']==[4,6,9][kind] and r['upgrade']==r['score']==r['normal']==0 and r['bossHP']==72 and r['r']==48 and r['route']==[4] and r['full'] and r['state']['next']=='fan';entries.append(r)
  report['actual_help_entries']=entries;passed('Actual Help→World2→snow→direct5 starts all3 selected characters at fullHP/upgrade0/score0 with one72HP/r48 boss,no normal quota and retained fullscreen.')

  sequences=[]
  for hz in [60,120]:
   r=page.evaluate('''hz=>{kingScene();const art=gameSnowfield,legacy=emitEnemyShot,hit=hurt,events=[],warnings=[],waves=[],seen=new WeakSet();let oldPhase='rest',max=0,legacyCalls=0,hurtCalls=0;
    window.gameSnowfield={...art,attack:(actor,isBoss)=>{art.attack(actor,isBoss);const state=gameSnowfieldBoss.snapshot();events.push({age:state.age,kind:state.phase==='burst'?'blast':state.next==='radial'?'fan':'radial',x:actor.x,y:actor.y,px:player.x,py:player.y,pose:art.pose(actor,true).name});}};
    emitEnemyShot=function(actor,...args){if(actor===boss)legacyCalls++;return legacy(actor,...args);};hurt=function(){hurtCalls++;return hit();};
    try{for(let n=0;n<35*hz;n++){boss.x=W*.22;boss.y=H*.24;player.x=W*.78;player.y=H*.62;update(1/hz);const state=gameSnowfieldBoss.snapshot();if(state.phase==='warning'&&oldPhase!=='warning')warnings.push({age:state.age,hazard:state.hazard});oldPhase=state.phase;const fresh=enemyBullets.filter(b=>b.snowBossPattern&&!seen.has(b));for(const b of fresh)seen.add(b);if(fresh.length)waves.push({age:events.at(-1).age,event:events.at(-1),shots:fresh.map(b=>({angle:Math.atan2(b.vy,b.vx),speed:Math.hypot(b.vx,b.vy),r:b.r,kind:b.snowBossPattern}))});max=Math.max(max,state.bullets);}return {hz,events,warnings,waves,max,legacyCalls,hurtCalls,hp,state:gameSnowfieldBoss.snapshot()};}
    finally{window.gameSnowfield=art;emitEnemyShot=legacy;hurt=hit;}}''',hz)
   expected=[1.8,4.8,9.2,12.45,15.45,19.85,23.1,26.1,30.5,33.75]
   assert len(r['events'])==len(expected) and all(abs(e['age']-t)<1e-7 for e,t in zip(r['events'],expected)),r['events']
   assert [e['kind'] for e in r['events']]==['fan','radial','blast']*3+['fan'] and all(e['pose']=='attack' for e in r['events'])
   assert r['max']==9 and r['legacyCalls']==0 and r['hurtCalls']==3 and r['hp']==4
   assert [round(w['age'],2) for w in r['warnings']]==[7.8,18.45,29.1]
   for wave in r['waves']:
    shots=wave['shots'];fan=wave['event']['kind']=='fan';assert len(shots)==(3 if fan else 6) and all(abs(s['speed']-(80 if fan else 65))<1e-8 and s['r']==5 for s in shots)
    if fan:
     aim=__import__('math').atan2(wave['event']['py']-wave['event']['y'],wave['event']['px']-wave['event']['x'])
     assert all(abs(__import__('math').atan2(__import__('math').sin(s['angle']-aim),__import__('math').cos(s['angle']-aim))-(i-1)*__import__('math').pi/10)<1e-8 for i,s in enumerate(shots))
    else:
     index=sum(w['event']['kind']=='radial' for w in r['waves'][:r['waves'].index(wave)])
     assert all(abs(__import__('math').atan2(__import__('math').sin(s['angle']-(index*__import__('math').pi/12+i*__import__('math').pi/3)),__import__('math').cos(s['angle']-(index*__import__('math').pi/12+i*__import__('math').pi/3))))<1e-8 for i,s in enumerate(shots))
   sequences.append(r)
  report['sequence_60_120']=sequences;passed('60/120Hz match35s fan→radial→blast sequence:1.8s initial delay,3.0s rest after completion,1.4s warning+.25s burst; old forest shot path is never called and active owned bullets cap at9.')
  passed('Actual fan is3 aimed shots at±18°/80px/s; radial is6 shots at60°/65px/s with0→15→30° starts,one attack art event per emitted burst/detonation and no warning-loop attack.')

  fixed=page.evaluate('''()=>{const before=kingWarning();const h=before.hazard;player.x=h.x+80;player.y=h.y;kingAdvance(.7);const middle=gameSnowfieldBoss.snapshot(),pose=gameSnowfield.pose(boss,true).name;kingAdvance(.7);return {before,middle,after:gameSnowfieldBoss.snapshot(),pose,hp,player:{x:player.x,y:player.y}};}''')
  assert fixed['before']['phase']==fixed['middle']['phase']=='warning' and fixed['before']['hazard']==fixed['middle']['hazard'] and fixed['pose']!='attack'
  assert fixed['after']['phase']=='burst' and fixed['hp']==4 and abs(fixed['middle']['remaining']-.7)<1e-8 and fixed['before']['hazard']['r']==74
  report['fixed_warning_and_dodge']=fixed;passed('Warning lasts1.4s at its original fixed coordinate/height-scaled56–74px; moving80px away does not drag the marker and avoids damage; warning alone does not trigger attack art.')

  damage=[]
  for kind in range(3):
   r=page.evaluate('''kind=>{const state=kingWarning(kind);player.x=state.hazard.x;player.y=state.hazard.y;invuln=0;const old=hurt;let calls=0;hurt=()=>{calls++;old();};try{kingAdvance(1.4);const first={hp,invuln,state:gameSnowfieldBoss.snapshot()};kingAdvance(.25);for(let i=0;i<20;i++)update(0);return {kind,first,after:hp,calls,state:gameSnowfieldBoss.snapshot()};}finally{hurt=old;}}''',kind)
   assert r['first']['hp']==r['after']==[4,6,9][kind]-1 and abs(r['first']['invuln']-1.55)<1e-8 and r['calls']==1 and r['first']['state']['phase']=='burst' and r['state']['phase']=='rest' and r['state']['hazard'] is None and abs(r['state']['remaining']-3.0)<1e-8;damage.append(r)
  report['blast_damage_all_characters']=damage;passed('All3 characters take exactly1HP at detonation through existing hurt()/1.55s invulnerability; .25s effect/repeated update(0) never deals another hit and next rest starts only after effect completion.')
  boundaries=[]
  for distance,invuln,expected in [(74,0,3),(74.1,0,4),(0,1.55,4)]:
   r=page.evaluate('''({distance,inv})=>{const s=kingWarning();player.x=s.hazard.x+distance;player.y=s.hazard.y;invuln=inv;kingAdvance(1.4);return {hp,invuln,state:gameSnowfieldBoss.snapshot()};}''',{'distance':distance,'inv':invuln});assert r['hp']==expected,r;boundaries.append({'distance':distance,'initialInvuln':invuln,**r})
  report['aoe_boundary_and_invulnerability']=boundaries;passed('Blast damages within the displayed74px center radius,not74.1px outside; an existing invulnerability window blocks damage without extra status effects.')

  projectiles=[]
  for pattern,age in [('fan',1.8),('radial',5)]:
   for kind in range(3):
    r=page.evaluate('''({age,kind,pattern})=>{kingScene(kind);kingAdvance(age,120,true);const b=enemyBullets.find(b=>b.snowBossPattern===pattern);const original={r:b.r,life:b.life,kind:b.snowBossPattern};b.x=W*.5;b.y=H*.55;bullets=[];shoot();const own=bullets[0];Object.assign(own,{x:b.x,y:b.y,vx:0,vy:0});update(0);return {original,enemyGone:!enemyBullets.includes(b),ownGone:own.life<=0};}''',{'age':age,'kind':kind,'pattern':pattern})
    assert r['original']['kind']==pattern and r['original']['r']==5 and r['enemyGone']==r['ownGone']==(kind==2);projectiles.append({'requested':pattern,'character':kind,**r})
  report['existing_projectile_interception']=projectiles;passed('Boss projectiles use the existing enemyBullets collision path: Tanko annihilates both projectiles,Trio/Bingle gain no block and original r5/life3.4 remains.')

  page.evaluate('kingWarning();enemyBullets=[]')
  page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();paused=page.evaluate('gameSnowfieldBoss.snapshot()');page.wait_for_timeout(200);page.evaluate('update(5)');assert page.evaluate('gameSnowfieldBoss.snapshot()')==paused
  page.locator('#gameExitCancel').tap();page.wait_for_function('!gameExitDialogOpen');assert page.evaluate('started&&gameSnowfieldBoss.snapshot().phase==="warning"&&!!document.fullscreenElement')
  page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible();assert page.evaluate('gameSnowfieldBoss.snapshot()===null&&enemyBullets.every(b=>!b.snowBossPattern)&&!!document.fullscreenElement')
  page.wait_for_timeout(1200);assert page.evaluate('gameSnowfieldBoss.snapshot()===null&&!started')
  passed('Actual in-game exit modal freezes warning/cooldown,Continue preserves the same pattern,and confirmed selection return clears hazard/projectiles with fullscreen retained and no later damage.')

  hidden=page.evaluate('''()=>{kingWarning();const before={state:gameSnowfieldBoss.snapshot(),x:boss.x,y:boss.y,bullets:enemyBullets.map(b=>({...b})),hp};Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));update(5);gameSnowfieldBoss.update(boss,5);const frozen={state:gameSnowfieldBoss.snapshot(),x:boss.x,y:boss.y,bullets:enemyBullets.map(b=>({...b})),hp};delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));update(0);return {before,frozen,resumed:gameSnowfieldBoss.snapshot()};}''')
  assert hidden['before']==hidden['frozen'] and hidden['before']['state']==hidden['resumed'];report['background_pause']=hidden
  passed('Scoped background pause freezes boss motion,all owned bullets,hazard and cooldown; visibility return validates geometry without advancing or restarting the1.4s timer.')

  restarted=page.evaluate('''()=>{kingWarning();const previous=boss;start(1);return {different:boss!==previous,state:gameSnowfieldBoss.snapshot(),type:player.type,hp,score:runScore,owned:enemyBullets.filter(b=>b.snowBossPattern).length};}''')
  assert restarted['different'] and restarted['type']==1 and restarted['hp']==6 and restarted['score']==restarted['owned']==0 and restarted['state']['phase']=='rest' and restarted['state']['hazard'] is None and abs(restarted['state']['remaining']-1.8)<1e-8
  report['defensive_restart']=restarted;passed('A defensive new game during a warning creates a new boss with fresh1.8s delay and clears every old danger/projectile without carrying score or damage.')

  page.evaluate('kingWarning();hp=1;invuln=0;kingAdvance(1.4)');expect(page.locator('#gameOverOverlay')).to_be_visible()
  dead=page.evaluate('''()=>({hp,started,state:gameSnowfieldBoss.snapshot(),owned:enemyBullets.filter(b=>b.snowBossPattern).length,result:gameScoring.getLastResult(),playing:kingAudio.filter(a=>a.loop&&!a.paused).length})''')
  assert dead['hp']==0 and not dead['started'] and dead['state'] is None and dead['owned']==dead['playing']==0 and dead['result']['developerTest'] and not dead['result']['saved']
  expect(page.locator('#menu')).to_be_visible(timeout=5000);delay=page.evaluate('kingReturnAt-kingDeathAt');assert 2990<=delay<4000,delay
  assert page.locator('#selectionResult').inner_text()=='';report['blast_game_over']={'atDeath':dead,'returnDelayMs':delay}
  passed('Fatal blast stops play/BGM immediately,clears hazard/projectiles,keeps the existing3s GAME OVER and clean selection return; developer result remains unsaved.')

  rewards=[]
  for kind in range(3):
   for roll in [.1,.9]:
    r=page.evaluate('''({kind,roll})=>{kingWarning(kind);hp=1;const random=Math.random;Math.random=()=>roll;try{const result=kingKill();grantBossReward(lastKing);gameScoring.finish('clear');return {kind,roll,hp,upgrade:player.upgrade,result,state:gameSnowfieldBoss.snapshot(),owned:enemyBullets.filter(b=>b.snowBossPattern).length,granted:lastKing.rewardGranted};}finally{Math.random=random;}}''',{'kind':kind,'roll':roll})
    assert r['hp']==(3 if roll<.5 else 1) and r['upgrade']==(0 if roll<.5 else 1) and r['granted'] and r['owned']==0 and r['state'] is None and r['result']['record']['score']==2000 and r['result']['record']['bossKills']==1 and not r['result']['saved']
    page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending');expect(page.locator('#selectionResult')).to_contain_text('지역 테스트 완료');rewards.append(r)
  report['real_kills_and_rewards']=rewards;passed('Real shots from each character kill the boss during a warning; both50:50 HP+2/power+1 rewards,2000points,one clear result and1.05s original hit/defeat outro occur once with no residual blast.')
  assert page.evaluate('kingStorage()')==original_storage and page.evaluate('kingWrites.length')==0
  passed('All developer pattern cycles,deaths,exits,restarts and6 reward clears preserve all4 valid preexisting TOP10/history strings with0 storage writes and no memory-record contamination.')

  hp_cases=page.evaluate('''()=>{const rows=[];for(let kind=0;kind<3;kind++)for(let upgrade=0;upgrade<=5;upgrade++){kingScene(kind);player.upgrade=upgrade;spawnBossEncounter();const initial=boss.hp;player.upgrade=5;update(.1);rows.push({kind,upgrade,hp:boss.hp,maxHp:boss.maxHp,initial,r:boss.r});}return rows;}''')
  assert all(abs(r['hp']-[72*m for m in [1,1.1,1.4,1.6,1.9,2.2]][r['upgrade']])<1e-8 and r['hp']==r['maxHp']==r['initial'] and r['r']==48 for r in hp_cases);report['protected_hp_scaling']=hp_cases
  passed('All3 characters×upgrade0–5 retain bossHP72/79.2/100.8/115.2/136.8/158.4,r48 and spawn-time-only scaling; new attacks add no rage,extra summons or upgrade-dependent pattern change.')

  layouts=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('W===innerWidth&&H===innerHeight')
   page.evaluate('kingScene()')
   page.wait_for_function('getComputedStyle(document.getElementById("rotationJoystick")).visibility==="visible"&&document.getElementById("fullscreenToggle").getBoundingClientRect().left>W*.5')
   safe=page.evaluate('''()=>{const rows=[],r=gameSnowfieldBoss.radiusForHeight();const ids=['rotationJoystick','fire','hud','fullscreenToggle','exitGame','sensor','sensorStatus','worldPrototypeNotice'];const rects=ids.map(id=>document.getElementById(id)).filter(e=>e&&!e.hidden&&e.getClientRects().length).map(e=>e.getBoundingClientRect());rects.push({left:W*.3,right:W*.7,top:31,bottom:66});
    const fire=document.getElementById('fire').getBoundingClientRect(),joy=document.getElementById('rotationJoystick').getBoundingClientRect();for(const target of [[12,12],[W-12,H-12],[fire.x+fire.width/2,fire.y+fire.height/2],[joy.x+joy.width/2,joy.y+joy.height/2],[W/2,H/2],[0,H/2]]){const p=gameSnowfieldBoss.safeTarget(...target);if(!p)throw Error('No safe target');const clear=rects.every(b=>Math.hypot(p.x-Math.max(b.left,Math.min(b.right,p.x)),p.y-Math.max(b.top,Math.min(b.bottom,p.y)))>r);rows.push({target,point:p,clear,bounds:p.x>=r+4&&p.x<=W-r-4&&p.y>=r+4&&p.y<=H-r-4});}return rows;}''')
   assert all(r['clear'] and r['bounds'] for r in safe),safe
   for name,age in [('entry',1.55),('fan',2.4),('radial',6.2),('warning',8.5),('burst',9.28)]:
    state=page.evaluate('''age=>{kingScene();kingAdvance(age);const state=gameSnowfieldBoss.snapshot();kingFreeze();return state;}''',age);assert state is not None
    if name in ['warning','burst']:assert state['phase']==name and abs(state['hazard']['r']-max(56,min(74,height*.18)))<1e-8
    page.screenshot(path=str(args.artifacts/f'{name}-{width}x{height}.png'))
   page.evaluate('kingScene();kingKill()');page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending');page.screenshot(path=str(args.artifacts/f'clear-{width}x{height}.png'));layouts.append({'viewport':[width,height],'safeTargets':safe})
  report['landscape_geometry']=layouts;passed('915×412,800×360,568×320 capture direct entry/all3 patterns/clear; height-scaled56–74px warnings remain fully on-canvas and disjoint from HUD/boss name/HP and actual joystick/fire/sensor/fullscreen/exit rectangles.')
  page.set_viewport_size({'width':915,'height':412});page.evaluate('kingWarning();gameExitDialogOpen=true');page.set_viewport_size({'width':568,'height':320});page.wait_for_function('W===568');resize=page.evaluate('''()=>{gameExitDialogOpen=false;update(0);return gameSnowfieldBoss.snapshot();}''');assert resize['hazard'] is None or resize['hazard']['r']+4<=resize['hazard']['x']<=568-resize['hazard']['r']-4;report['resize_safety']=resize
  passed('Resize/fullscreen/visibility validation cancels an unsafe warning rather than moving it to follow the player or allowing off-canvas damage.')

  # Separate native contexts compare World1 against the previous product; the tested offline page stays offline.
  page.evaluate('kingExit()');oldctx=browser.new_context(viewport={'width':915,'height':412});newctx=browser.new_context(viewport={'width':915,'height':412});old=oldctx.new_page();current=newctx.new_page();old.goto(f'http://127.0.0.1:{reference.server_port}/');current.goto(url);old.wait_for_function('gameSnowfield.ready()');current.wait_for_function('gameSnowfield.ready()')
  fixture='''area=>{if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}gameSnowfield.reset();gameWorlds.setDeveloperStart({enabled:false});start(0);stage=area;phase=5;phaseKills=6;transition=0;spawn=999;invuln=999;player.x=700;player.y=300;const random=Math.random;let seed=921;Math.random=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;};try{update(0);transition=0;boss.shot=0;const rows=[];for(let n=0;n<240;n++){update(1/60);if(n%15===0)rows.push({boss:{x:boss.x,y:boss.y,hp:boss.hp,maxHp:boss.maxHp,shot:boss.shot},bullets:enemyBullets.map(b=>({...b})),hp,phaseKills});}return rows;}finally{Math.random=random;}}'''
  comparisons=[]
  for area in range(4):
   old.bring_to_front();before=old.evaluate(fixture,area);current.bring_to_front();after=current.evaluate(fixture,area);assert before==after,area;comparisons.append({'area':area,'samples':len(after),'equal':True})
  report['world1_baseline_traces']=comparisons;oldctx.close();newctx.close();page.bring_to_front()
  passed('All4 World1 boss4s seeded traces remain byte-for-byte equal toc5daee9 for movement,HP,shot cadence,projectile vectors and counters; normal-monster AI is additionally byte-guarded and covered by retained16+16 regressions.')
  assert not errors and not dialogs and not failed and not external,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':external}
  passed('No uncaught JS errors,native dialogs,failed resources or offline external requests; no new audio objects/assets,online storage or unregistered region is introduced.')
  browser.close()
finally:
 server.shutdown();server.server_close()
 if reference:reference.shutdown();reference.server_close()
 temp.cleanup()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
