"""Native browser regression for opt-in world routing and snowfield prototype."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import expect, sync_playwright
from world_preservation import WORLD_ASSETS, assert_world_asset, without_world_source, without_world_ui

ROOT=Path(__file__).resolve().parents[1]
BASELINE='80aee3931b0425d314fafcb9b515f71ec5bac873'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true')
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASELINE,'standalone':args.standalone,'passed':[],'limits':[
 'Native Chromium controlled combat/input/media/fullscreen checks, not a human balance playthrough.',
 'Snowfield uses approved background/monster art with prototype atlas animation and Issue8 first-trial normal combat with the unchanged forest boss/audio profile; final balance is not approved.',
 'Physical Galaxy/Samsung Internet, actual sensors, audible output and file opening are not tested.',
 'Offline injects the exact standalone HTML into a blank local origin then disables networking; managed file policy is unchanged.'
]}
def passed(text):report['passed'].append(text);print('PASS:',text,flush=True)
source=(ROOT/'index.html').read_text()
assert without_world_source(source)==subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT).decode()
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in WORLD_ASSETS:assert_world_asset(path);continue
 value=without_world_ui(path.read_text(),name).encode() if path.suffix in ('.js','.css') else path.read_bytes()
 assert value==subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:
 subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Exact approved world hooks reverse to80aee39; all other gameplay, controls, PNG/audio bytes remain identical and every JS script parses.')

probe='''() => {
 window.worldAudio=[];const NativeAudio=Audio;window.Audio=new Proxy(NativeAudio,{construct(target,args){const a=new target(...args);worldAudio.push(a);return a}});
 window.worldActive=()=>[...worldAudio,document.getElementById('selectionBgm')].filter(a=>a&&a.loop&&!a.paused&&!a.ended);
 window.worldAudioOverlaps=[];const sample=()=>{const a=worldActive();if(a.length>1)worldAudioOverlaps.push(a.map(x=>worldAudio.indexOf(x)));requestAnimationFrame(sample)};
 document.addEventListener('DOMContentLoaded',sample,{once:true});
}'''
helpers='''() => {
 window.worldReset=(type=0,quota=0)=>{itemMonsters.configure({opportunitiesPerRegion:quota});start(type);spawn=999;transition=0;invuln=999;fireCooldown=0;};
 window.worldEnemy=()=>({x:100,y:100,hp:1,special:false,r:16,t:0,speed:0,shot:999,charge:999,kind:0,mode:'chase',vx:0,vy:0});
 window.worldHit=target=>{bullets=[];shoot();Object.assign(bullets[0],{x:target.x,y:target.y,vx:0,vy:0});update(0);};
 window.worldKill=()=>{const e=worldEnemy();enemies=[e];worldHit(e);};
 window.worldExit=()=>{gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();menu.classList.remove('hidden');clearGameOver();gameControls.reset();};
 window.worldSnow=()=>{stage=3;phase=5;boss=null;hp=maxHP[player.type];nextPhase();transition=0;spawn=999;gameScoring.updateHUD();};
 window.worldRoute=(type,quota=0)=>{
  worldReset(type,quota);const waves=[];let safety=0;
  while(started&&safety++<30){
   const before={stage,phase};transition=0;spawn=999;
   for(let kill=0;kill<6;kill++){
    bullets=[];warnEnemy();for(let i=0;i<36;i++)update(.04);
    const e=enemies[0];if(!e)throw Error('No normal enemy '+JSON.stringify({type,before,stage,phase,kill,started,warnings,enemies,boss,phaseKills,transition}));let shots=0;
    while(e.hp>0&&shots++<8)worldHit(e);if(e.hp>0)throw Error('Normal enemy survived');
    if(quota){itemMonsters.update(1.4);for(const actor of itemMonsters.targets()){
     actor.x=100;actor.y=100;let hits=0;while(actor.hp>0&&hits++<8)worldHit(actor);
     if(actor.hp>0)throw Error('Item actor survived');
    }}
   }
   let bossHP=null;
   if(before.phase===5){update(0);if(!boss)throw Error('No boss');transition=0;bossHP=boss.maxHp;
    let shots=0;while(boss&&shots++<250)worldHit(boss);if(boss)throw Error('Boss survived');
   }
   waves.push({...before,bossHP});if(started&&stage===before.stage&&phase===before.phase)throw Error('Route stalled');
  }
  return {waves,score:runScore,started,stage,phase,result:gameScoring.getLastResult(),title:menu.querySelector('h1').textContent};
 };
}'''
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-world-origin':
   self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline origin</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
class Touch:
 def __init__(self,context,page):self.cdp=context.new_cdp_session(page);self.points={}
 def down(self,id,x,y):self.points[id]={'id':id,'x':x,'y':y};self.cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':list(self.points.values())})
 def move(self,id,x,y):self.points[id].update(x=x,y=y);self.cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':list(self.points.values())})
 # Finish the last contact with an empty CDP touchEnd; partial release identifies the lifted contact.
 def up(self,id):point=self.points.pop(id);self.cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[point] if self.points else []})
 def tap(self,page,selector):
  expect(page.locator(selector)).to_be_visible();r=page.locator(selector).bounding_box()
  self.down(50,r['x']+r['width']/2,r['y']+r['height']/2);page.wait_for_timeout(60);self.up(50)
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
  context.add_init_script('('+probe+')()');page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
  page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  def load():
   if args.standalone:
    context.set_offline(False);page.goto(url+'offline-world-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:page.goto(url,wait_until='load')
   page.wait_for_function('gameWorlds&&gameSnowfield.ready()&&itemMonsters.ready()&&terrainImgs.every(i=>i.complete&&i.naturalWidth>0)');page.evaluate(helpers)
  load()
  registry=page.evaluate('({worlds:gameWorlds.worlds,regions:gameWorlds.regions,snapshot:gameWorlds.snapshot(),assets:terrainImgs.length,enemies:enemySprites.length,bosses:bossSprites.length})')
  assert [w['regionIds'] for w in registry['worlds']]==[[0,1,2,3],[4]]
  assert [r['id'] for r in registry['regions']]==list(range(5)) and len({r['key'] for r in registry['regions']})==5
  assert registry['snapshot']=={'trialEnabled':False,'activeTrial':False,'route':[0,1,2,3]}
  assert registry['assets']==registry['enemies']==registry['bosses']==5
  assert all(r['normalPhases']==4 and r['bossPhase']==5 for r in registry['regions'])
  report['registry']=registry;passed('Two worlds register only5 stable regions; World1 IDs0–3 remain unchanged, snow is4, and default route is exactly20 phases.')
  page.locator('#selectionHelp').tap();expect(page.locator('#worldTrialToggle')).not_to_be_checked()
  page.screenshot(path=str(args.artifacts/'trial-opt-in-help.png'))
  page.locator('#worldTrialToggle').check();page.locator('#selectionHelpClose').tap()
  page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement')
  page.locator('#startSelected').tap();page.wait_for_function('started')
  assert page.evaluate('gameWorlds.snapshot().route.join()==="0,1,2,3,4"&&!gameWorlds.setTrialEnabled(false)&&gameWorlds.isTrial()')
  passed('Existing Help offers an explicit default-OFF trial checkbox; a start snapshots the25-phase route and rejects mode changes during play.')

  carry=page.evaluate('''() => {
   worldReset(0,3);stage=3;phase=1;itemMonsters.enterRegion(3);
   const slot=itemMonsters.snapshot().regions.find(p=>p.region===3).phases.find(s=>s.selected);phase=slot.phase;
   for(let i=0;i<slot.requiredKills;i++)worldKill();itemMonsters.update(.4);
   const pending=itemMonsters.snapshot().entrances[0];const actor=itemMonsters.spawn({x:200,y:150});actor.life=6.75;
   const it={x:40,y:50,type:'hp',life:7.25,r:13,t:0,vx:0,vy:0,turn:999};items=[it];
   const samePlayer=player;hp=1;player.upgrade=3;phase=5;phaseKills=requiredKills;update(0);transition=0;
   const defeated=boss;boss.hp=1;const random=Math.random;Math.random=()=>.1;
   try{worldHit(boss)}finally{Math.random=random}
   const after={stage,phase,hp,upgrade:player.upgrade,samePlayer:player===samePlayer,sameItem:items[0]===it,item:{...items[0]},sameActor:itemMonsters.targets().includes(actor),actorLife:actor.life,pending:itemMonsters.snapshot().entrances.find(e=>e.id===pending.id),rewardGranted:defeated.rewardGranted,score:runScore};
   grantBossReward(defeated);gameScoring.bossDefeated(defeated);after.duplicateHP=hp;after.duplicateScore=runScore;
   itemMonsters.update(1.01);const arrived=itemMonsters.targets().find(m=>m.origin===pending.id);
   return {after,pending,arrival:{origin:arrived.origin,life:arrived.life},plans:itemMonsters.snapshot().regions};
  }''')
  after=carry['after'];assert after['stage']==4 and after['phase']==1 and after['hp']==after['duplicateHP']==4 and after['upgrade']==3
  assert after['samePlayer'] and after['sameItem'] and after['sameActor'] and after['actorLife']==6.75
  assert after['item']['x']==40 and after['item']['y']==50 and after['item']['life']==7.25
  assert after['pending']==carry['pending'] and after['rewardGranted'] and after['score']==after['duplicateScore']
  assert carry['arrival']['life']==10 and carry['arrival']['origin']==carry['pending']['id']
  assert page.evaluate('!!document.fullscreenElement&&gameWorlds.profile(4)===0&&gameWorlds.musicProfile(4)===0')
  report['desert_to_snow_carry']=carry
  passed('Real desert boss defeat rewards once, heals+2 then region+2 capped at4, enters snow1/5, preserves player/upgrade/items/actors/lifetimes/warning, and keeps fullscreen.')
  assert {p['regionKey'] for p in carry['plans']}=={'world-1:forest','world-1:desert','world-2:snowfield'}
  snowplan=next(p for p in carry['plans'] if p['region']==4)
  assert snowplan['worldId']==1 and snowplan['opportunities']==3 and sum(s['selected'] for s in snowplan['phases'])==3
  passed('Forest0, desert3 and snow4 have independent reservation keys; an old warning materializes against its original quota and snow gets3 distinct phases/kill thresholds.')

  reward_order=page.evaluate('''() => {
   const rows=[];
   for(const type of [0,1,2])for(const roll of [.1,.9]){worldReset(type);stage=3;phase=5;phaseKills=requiredKills;hp=1;player.upgrade=3;update(0);transition=0;boss.hp=1;
    const random=Math.random;Math.random=()=>roll;try{worldHit(boss)}finally{Math.random=random}
    rows.push({type,roll,hp,upgrade:player.upgrade,stage,score:runScore});}
   return rows;
  }''')
  assert all(r['stage']==4 and r['score']==2000 and r['hp']==(min([4,6,9][r['type']],5) if r['roll']<.5 else 3) and r['upgrade']==(3 if r['roll']<.5 else 4) for r in reward_order)
  report['reward_order']=reward_order;passed('Both unchanged50:50 boss rewards are checked for all3 characters: HP reward precedes region healing; power+1 precedes healing, no extra world/region points.')

  snow_combat=page.evaluate('''() => {
   worldReset();worldSnow();warnEnemy();for(let i=0;i<36;i++)update(.04);const e=enemies[0];const normal={hp:e.hp,speed:e.speed,special:e.special};worldHit(e);
   phase=5;phaseKills=requiredKills;player.upgrade=5;update(0);transition=0;const hpAtSpawn=boss.hp;player.upgrade=0;boss.shot=0;update(0);
   return {normal,profile:gameWorlds.profile(stage),tactics:tactics[4],sameSprites:enemySprites[4]===enemySprites[0]&&bossSprites[4]===bossSprites[0],hpAtSpawn,hpAfter:boss.hp,shots:enemyBullets.length,speed:Math.hypot(enemyBullets[0].vx,enemyBullets[0].vy),points:runScore};
  }''')
  assert snow_combat['normal']=={'hp':1,'speed':32.3,'special':False} and snow_combat['hpAtSpawn']==snow_combat['hpAfter']==44
  assert not snow_combat['sameSprites'] and snow_combat['shots']==1 and snow_combat['speed']==117 and snow_combat['points']==100
  report['snow_prototype_combat']=snow_combat;passed('Snow uses approved monster sprites with Issue8 slimeHP1/speed32.3 and the unchanged forest boss pattern and upgrade multipliers, snapshotted once; no fifth-region difficulty scaling.')

  routes=[]
  for trial in [False,True]:
   page.evaluate('worldExit()');page.evaluate('value=>gameWorlds.setTrialEnabled(value)',trial)
   for kind in range(3):
    route=page.evaluate('type=>worldRoute(type)',kind);page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending');waves=route['waves'];r=route['result']['record']
    assert len(waves)==(25 if trial else 20) and route['score']==(35000 if trial else 28000) and not route['started']
    assert sum(w['bossHP'] is not None for w in waves)==(5 if trial else 4)
    assert {w['stage'] for w in waves}==set(range(5 if trial else 4))
    assert r['characterId']==kind and r['bossKills']==(5 if trial else 4) and r['normalKills']==(150 if trial else 120) and r['clearedPhases']==(20 if trial else 16)
    assert r['regionId']==(4 if trial else 3) and r['worldId']==int(trial) and r['trialMode']==trial and r['outcome']=='clear'
    assert ('설원 시험 완료' if trial else '모든 지역 클리어') in route['title']
    assert page.evaluate('gameWorlds.nextRegion(stage)===null&&!!document.fullscreenElement')
    routes.append({'trial':trial,'character':kind,**route})
    if kind==0:
     expect(page.locator('#selectionResult')).to_contain_text('설원 시험 완료' if trial else '모든 지역 클리어')
     page.screenshot(path=str(args.artifacts/('snow-trial-clear.png' if trial else 'world1-default-clear.png')))
  report['controlled_full_routes']=routes
  passed('All3 helicopters complete default20 and opt-in25 phases through real warnings/spawns/shots/collisions:28,000 vs35,000,4 vs5 bosses; no undefined future region or duplicate clear credit.')
  expect(page.locator('#selectionResult')).to_contain_text('설원 시험 완료')
  passed('Snow boss ends at the existing safe clear/menu lifecycle with a clearly labeled trial result; default desert still uses the original World1 clear title.')

  storage=page.evaluate('''() => {
   const normal=localStorage.getItem('heliTrio.top10.v1'),normalHistory=localStorage.getItem('heliTrio.playHistory.v1');
   const trial=gameScoring.getTop(),trialHistory=gameScoring.getHistory();const r=gameScoring.finish('clear');gameScoring.finish('clear');
   const duplicate=gameScoring.getHistory().filter(x=>x.id===r.record.id).length;
   gameWorlds.setTrialEnabled(false);const base=gameScoring.getTop();gameWorlds.setTrialEnabled(true);
   return {normalUnchanged:normal===localStorage.getItem('heliTrio.top10.v1')&&normalHistory===localStorage.getItem('heliTrio.playHistory.v1'),trial,trialHistory,base,duplicate,keys:gameScoring.storageKeys};
  }''')
  assert storage['normalUnchanged'] and storage['duplicate']==1 and len(storage['trial'])==len(storage['base'])==3
  assert all(r['score']==35000 and r['regionKey']=='world-2:snowfield' and r['worldId']==1 for r in storage['trial'])
  assert all(r['score']==28000 and r['regionId']==3 and not r['trialMode'] for r in storage['base'])
  assert storage['keys']['top']=='heliTrio.world2Trial.top10.v1'
  report['storage_isolation']=storage;passed('Trial TOP10/analysis namespaces are separate, preserve normal storage bytes, retain all3 character results/tie order and store a repeated finish exactly once.')
  page.locator('#selectionSettings').tap();expect(page.locator('#leaderboardTitle')).to_have_text('🏆 설원 시험 TOP 10')
  expect(page.locator('#leaderboardRows')).to_contain_text('월드 2 · ❄ 설원 (시험)')
  page.screenshot(path=str(args.artifacts/'trial-leaderboard.png'));page.locator('#leaderboardClose').tap()
  load();assert page.evaluate('!gameWorlds.isTrial()&&gameScoring.getTop().length===3&&gameScoring.getTop().every(r=>!r.trialMode)')
  page.evaluate('gameWorlds.setTrialEnabled(true)');assert page.evaluate('gameScoring.getTop().length===3&&gameScoring.getTop().every(r=>r.regionId===4&&r.worldId===1)')
  passed('Trial leaderboard labels World2/snow and reload preserves fifth-region results; normal launch resets opt-in OFF and displays only original normal scores.')

  legacy=page.evaluate('''() => {gameWorlds.setTrialEnabled(false);const d=JSON.parse(localStorage.getItem(gameScoring.storageKeys.top));
   for(const r of d.records)for(const k of ['worldId','worldName','regionKey','localRegionIndex','trialMode'])delete r[k];
   const raw=JSON.stringify(d);localStorage.setItem(gameScoring.storageKeys.top,raw);return raw;}''')
  load();assert page.evaluate('gameScoring.getTop().every(r=>r.worldId===0&&r.regionKey==="world-1:desert")')
  assert page.evaluate('localStorage.getItem(gameScoring.storageKeys.top)')==legacy
  passed('Existing version1 records without world fields load as World1 without migrating, converting, discarding or rewriting the original stored record bytes.')
  # Test corruption and storage denial independently, retaining the old normal data.
  page.evaluate('localStorage.setItem("heliTrio.world2Trial.top10.v1","broken JSON");localStorage.removeItem("heliTrio.world2Trial.playHistory.v1")')
  load();page.evaluate('gameWorlds.setTrialEnabled(true)');assert page.evaluate('gameScoring.getTop().length===0')
  denied=page.evaluate('''() => {
   const get=Storage.prototype.getItem,set=Storage.prototype.setItem;
   Storage.prototype.getItem=()=>{throw Error('denied')};Storage.prototype.setItem=()=>{throw Error('denied')};
   try{worldReset();worldSnow();gameScoring.enemyDefeated({hp:0,special:false});const result=gameScoring.finish('game_over');worldExit();
    gameWorlds.setTrialEnabled(false);const base=gameScoring.getTop().length;gameWorlds.setTrialEnabled(true);
    return {saved:result.saved,score:gameScoring.getTop()[0].score,base,trial:gameScoring.getTop().length};
   }finally{Storage.prototype.getItem=get;Storage.prototype.setItem=set}
  }''')
  assert denied=={'saved':False,'score':100,'base':3,'trial':1}
  passed('Corrupt trial JSON and denied/quota-like storage errors cannot stop play; volatile trial results survive scope switches without contaminating the normal TOP10.')

  item_route=page.evaluate('worldRoute(0,3)');item_record=item_route['result']['record']
  assert len(item_route['waves'])==25 and item_record['score']==38000 and item_record['itemKills']==15 and item_record['normalKills']==150 and item_record['bossKills']==5
  assert page.evaluate('itemMonsters.snapshot().regions.every(p=>p.spawned===3&&p.phases.filter(s=>s.selected).length===3)&&itemMonsters.snapshot().regions.length===5')
  report['full_trial_with_item_monsters']=item_route
  passed('A further25-phase combat run exercises exactly3 item spawns per region/15 total:38,000 points,150 normal kills,15 item kills,5 bosses, with no item contribution to the6-kill phase goal.')

  # Realtime media routing and real three-second game over in the snow trial.
  page.locator('#startSelected').tap();page.evaluate('worldSnow()')
  page.wait_for_function('worldActive().length===1&&worldActive()[0]===worldAudio[0]&&worldAudio[0].currentTime>.05')
  t=page.evaluate('worldAudio[0].currentTime');page.wait_for_timeout(180);assert page.evaluate('worldAudio[0].currentTime')>t
  page.evaluate('phase=5;phaseKills=requiredKills;update(0)')
  page.wait_for_function('worldActive().length===1&&worldActive()[0]===worldAudio[4]&&worldAudio[4].currentTime>.02')
  page.evaluate('''() => {window.worldDeathAt=0;window.worldReturnAt=0;
   document.addEventListener('gameover',()=>{worldDeathAt=performance.now()},{once:true});
   new MutationObserver(()=>{if(worldDeathAt&&!menu.classList.contains('hidden'))worldReturnAt=performance.now()}).observe(menu,{attributes:true,attributeFilter:['class']});
   hp=0;update(0);}''');expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_hidden()
  assert page.evaluate('worldActive().length===0&&!gameWorlds.setTrialEnabled(false)&&!started&&gameOverPending')
  page.screenshot(path=str(args.artifacts/'snow-game-over.png'))
  page.wait_for_function('performance.now()-worldDeathAt>=2500');expect(page.locator('#gameOverOverlay')).to_be_visible()
  expect(page.locator('#menu')).to_be_visible(timeout=2000);expect(page.locator('#selectionResult')).to_have_text('')
  report['snow_game_over_delay_ms']=page.evaluate('worldReturnAt-worldDeathAt');assert 2990<=report['snow_game_over_delay_ms']<4000
  page.wait_for_function('worldActive().length===1&&worldActive()[0]===selectionBgm&&selectionBgm.currentTime>.02')
  passed('Snow normal/boss reuse forest media with increasing native playback times; death stops BGM immediately, keeps the3s overlay and resumes selection music on a clean menu.')
  page.locator('#musicToggle').tap();assert page.evaluate('worldActive().length===0')
  page.locator('#startSelected').tap();page.evaluate('worldSnow()');page.wait_for_timeout(100);assert page.evaluate('worldActive().length===0')
  page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap()
  assert page.evaluate('worldActive().length===0');page.locator('#musicToggle').tap()
  page.wait_for_function('worldActive().length===1&&worldActive()[0]===selectionBgm')
  passed('Existing music OFF/ON persists across trial start/exit and selection return; the original in-page exit confirmation stays intact.')

  # Actual mobile pointer owners and unchanged placement in each requested snow viewport.
  page.evaluate('''() => {window.worldPointerTrace=[];for(const name of ['pointerdown','pointerup','pointercancel','click'])window.addEventListener(name,e=>{const row={name,x:e.clientX,y:e.clientY,id:e.pointerId,primary:e.isPrimary,target:e.target.id||e.target.tagName,time:performance.now()};worldPointerTrace.push(row);if(worldPointerTrace.length>120)worldPointerTrace.shift();queueMicrotask(()=>row.prevented=e.defaultPrevented);},true);}''')
  layouts=[];touch=Touch(context,page)
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});touch.tap(page,'#startSelected');page.wait_for_function('started');page.evaluate('worldSnow();invuln=999;spawn=999;transition=0;player.x=W/2;player.y=H*.55;gameScoring.updateHUD();draw()')
   page.wait_for_function('!document.getElementById("worldPrototypeNotice").hidden')
   bounds=page.evaluate('''() => {const r=id=>{const b=document.getElementById(id).getBoundingClientRect();return {x:b.x,y:b.y,w:b.width,h:b.height,right:b.right,bottom:b.bottom}};return {joystick:r('rotationJoystick'),fire:r('fire'),hud:r('hud'),full:r('fullscreenToggle'),exit:r('exitGame'),notice:r('worldPrototypeNotice'),W,H}}''')
   j=bounds['joystick'];assert j['x']==30 and h-j['bottom']==22 and j['h']==58 and 135<=j['w']<=165
   for key in ['fire','joystick','notice']:
    b=bounds[key];assert b['x']>=0 and b['y']>=0 and b['right']<=w and b['bottom']<=h
   assert bounds['hud']['right']<=bounds['full']['x'] and j['right']<bounds['fire']['x'] and bounds['notice']['bottom']<j['y']
   page.screenshot(path=str(args.artifacts/f'snow-entry-{w}x{h}.png'))
   cx=j['x']+j['w']/2;cy=j['y']+j['h']/2
   travel=page.evaluate('''() => {const e=document.getElementById('rotationJoystick');return e.offsetWidth/2-parseFloat(getComputedStyle(e).getPropertyValue('--stick-inset'))}''')
   touch.down(1,cx,cy);assert page.evaluate('gameControls.rotation()')==0
   touch.move(1,cx+travel*.07,cy);assert page.evaluate('gameControls.rotation()')==0
   touch.move(1,cx+travel,cy);assert abs(page.evaluate('gameControls.rotation()')-1)<.001
   f=bounds['fire'];touch.down(2,f['x']+f['w']/2,f['y']+f['h']/2)
   touch.down(3,w*.55,h*.4);touch.move(3,w*.55+75,h*.4)
   page.wait_for_function('tilt.x>0&&keys.fire&&drag!==null&&Math.abs(gameControls.rotation()-1)<.001')
   state=page.evaluate('({fire:keys.fire,drag:drag!==null,tilt:tilt.x,rotation:gameControls.rotation(),owners:gameControls.snapshot()})')
   assert state['fire'] and state['drag'] and state['tilt']>0 and abs(state['rotation']-1)<.001,state
   touch.up(1);assert page.evaluate('gameControls.rotation()===0&&keys.fire&&drag!==null')
   touch.up(2);touch.up(3);assert page.evaluate('!keys.fire&&drag===null&&gameControls.rotation()===0')
   # Let the existing500ms gameplay-click suppression finish before a new UI tap.
   page.wait_for_timeout(550)
   assert page.evaluate('!document.getElementById("game").dispatchEvent(new Event("contextmenu",{cancelable:true,bubbles:true}))')
   page.evaluate('phase=5;phaseKills=requiredKills;update(0);transition=0;gameScoring.updateHUD();draw()')
   page.screenshot(path=str(args.artifacts/f'snow-boss-{w}x{h}.png'))
   touch.tap(page,'#exitGame')
   try:expect(page.locator('#gameExitDialog')).to_be_visible(timeout=3000)
   except AssertionError:
    diagnostic=page.evaluate('''() => {const e=document.getElementById('exitGame'),r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {viewport:[W,H],started,hp,dialog:gameExitDialogOpen,inert:e.inert,disabled:e.disabled,pointerEvents:getComputedStyle(e).pointerEvents,hit:hit?.id||hit?.tagName,rect:r.toJSON(),controls:gameControls.snapshot(),finale:gameSnowfield.snapshot().finale,trace:worldPointerTrace};}''')
    (args.artifacts/'exit-touch-failure.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')
    page.screenshot(path=str(args.artifacts/'exit-touch-failure.png'))
    raise
   state=page.evaluate('({started,stage,phase,hp,dialog:gameExitDialogOpen,open:document.getElementById("gameExitDialog").open,controls:gameControls.snapshot()})')
   assert state['dialog'] and state['open'],{'viewport':[w,h],**state}
   touch.tap(page,'#gameExitCancel');page.wait_for_function('started&&!gameExitDialogOpen')
   touch.tap(page,'#exitGame');touch.tap(page,'#gameExitConfirm');expect(page.locator('#menu')).to_be_visible()
   layouts.append(bounds)
  report['landscape_layouts']=layouts
  passed('915×412,800×360,568×320 snow entry/boss screenshots fit HUD/notice/controls; joystick remains30/22px,8% deadzone/max input and3-contact drag/rotate/fire/release/context-menu protection work.')
  assert page.evaluate('worldAudio.length===12&&worldAudioOverlaps.length===0')
  passed('Snow adds no media clones: exactly12 original Audio objects plus selection media, never more than one active looping BGM during all tested transitions.')
  if not args.standalone:
   page.goto(url+'?world2=1',wait_until='load');page.wait_for_function('gameWorlds&&document.getElementById("worldTrialToggle")');assert page.evaluate('gameWorlds.isTrial()&&worldTrialToggle.checked')
   page.goto(url,wait_until='load');page.wait_for_function('gameWorlds&&document.getElementById("worldTrialToggle")');assert page.evaluate('!gameWorlds.isTrial()&&!worldTrialToggle.checked')
   passed('Explicit?world2=1 opts into trial without persisting a default override; a normal URL always launches World1-only mode.')
  assert not errors and not dialogs and not failed and not external,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':external}
  passed('No uncaught JS errors, native dialogs, failed assets or offline external requests occur.')
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
