"""Developer region entry matrix, zero persistence and retained normal/trial routes."""
import argparse,json,hashlib,re,shutil,subprocess,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright,expect
from snow_combat_preservation import COMBAT_ASSETS,assert_combat_asset
from developer_start_preservation import without_developer_start_source,without_developer_start_asset

ROOT=Path(__file__).resolve().parents[1];BASELINE='c5e8fa2a27a6c8d8f360c7680345a55589ae6a09'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASELINE,'standalone':args.standalone,'passed':[],'limits':[
 'Real Chromium/mobile pointer/fullscreen/media/storage with controlled combat fixtures; not physical Galaxy or Samsung Internet.',
 'The full entry matrix controls aim, spawn time and invulnerability; it does not measure manual play difficulty or physical sensors.',
 'Offline injects the exact standalone HTML at a blank local origin then disables networking; managed file policy is unchanged.',
 'The future-registry fixture modifies only one isolated browser response/document, not repository or distribution files.'
]}
def passed(text):report['passed'].append(text);print('PASS:',text,flush=True)
source=(ROOT/'index.html').read_text();assert without_developer_start_source(source)==subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT).decode()
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in COMBAT_ASSETS:assert_combat_asset(path);continue
 actual=without_developer_start_asset(path.read_text(),name).encode() if path.suffix in ['.js','.css'] else path.read_bytes()
 assert actual==subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Exact developer startup/UI/volatile-score hooks reverse to c5e8fa2; every image, atlas, manifest, sound, input and item asset is unchanged and all JavaScript parses.')

keys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1']
def record(id,region,score):return {'id':id,'score':score,'characterId':0,'characterName':'트리오','regionId':region,'phase':5,'order':1,'createdAt':'2026-11-02T01:00:00.000Z','outcome':'clear','normalKills':0,'itemKills':0,'bossKills':1,'clearedPhases':0,'playTimeSeconds':10,'finalUpgrade':0}
seed={key:json.dumps({'version':1,'records':[record('old-trial' if 'world2Trial' in key else 'old-normal',4 if 'world2Trial' in key else 0,35000 if 'world2Trial' in key else 28000)]}) for key in keys}
probe='''() => {
 window.devAudio=[];window.devPlay=[];const Native=Audio;window.Audio=new Proxy(Native,{construct(target,args){const a=new target(...args);devAudio.push(a);return a}});
 const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){if(this.loop)devPlay.push({index:devAudio.indexOf(this),id:this.id,t:performance.now()});return play.apply(this,args)};
}'''
helpers='''() => {
 window.devStorageKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];
 window.devStorageSnapshot=()=>Object.fromEntries(devStorageKeys.map(key=>[key,localStorage.getItem(key)]));
 window.devWrites=[];const write=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(devStorageKeys.includes(key))devWrites.push({key,value});return write.call(this,key,value)};
 window.devStartState=()=>({stage,phase,phaseKills,requiredKills,score:runScore,hp,maxHP:maxHP[player.type],upgrade:player.upgrade,type:player.type,angle:player.a,items:items.length,enemies:enemies.length,warnings:warnings.length,bullets:bullets.length,enemyBullets:enemyBullets.length,
  boss:boss&&{hp:boss.hp,maxHp:boss.maxHp,r:boss.r,shot:boss.shot},plan:itemMonsters.snapshot(),route:gameWorlds.snapshot(),developer:gameWorlds.developerSnapshot(),hud:hud.textContent});
 window.devHit=e=>{bullets=[];shoot();Object.assign(bullets[0],{x:e.x,y:e.y,vx:0,vy:0});update(0);};
 window.devExitFixture=()=>{gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();gameExitDialogOpen=false;clearGameOver();menu.classList.remove('hidden');gameControls.reset();gameSnowfield.reset();};
 window.devComplete=()=>{
  const waves=[];let safety=0;spawn=999;invuln=999;
  while(started&&safety++<7){const before={stage,phase};transition=0;spawn=999;
   if(!boss)for(let kill=phaseKills;kill<requiredKills;kill++){
    bullets=[];warnEnemy();for(let f=0;f<36;f++)update(.04);
    const e=enemies[0];if(!e)throw Error('No normal spawn');let shots=0;while(e.hp>0&&shots++<8)devHit(e);if(e.hp>0)throw Error('Normal survived');
   }
   let hpAtSpawn=null;
   if(before.phase===5){update(0);if(!boss)throw Error('No boss');transition=0;hpAtSpawn=boss.maxHp;let shots=0;while(boss&&shots++<250)devHit(boss);if(boss)throw Error('Boss survived');let outro=0;while((gameStormSky.snapshot().advancing||gameVolcano.snapshot().advancing)&&outro++<100)update(.04);if(gameStormSky.snapshot().advancing||gameVolcano.snapshot().advancing)throw Error('Art outro stalled');}
   waves.push({...before,hpAtSpawn});
   if(started&&stage===before.stage&&phase===before.phase)throw Error('No phase progress');
  }
  return {waves,stage,phase,score:runScore,started,result:gameScoring.getLastResult(),heading:menu.querySelector('h1').textContent};
 };
}'''
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/developer-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Test origin</title>');return
  super().do_GET()
s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=s.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{s.server_port}/'
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);context.add_init_script('('+probe+')()')
  page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  page.goto(url+'developer-origin');page.evaluate('seed=>{for(const [key,value] of Object.entries(seed))localStorage.setItem(key,value)}',seed);external.clear()
  def load():
   if args.standalone:
    context.set_offline(False);page.goto(url+'developer-origin');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:page.goto(url+'helicopter-game/',wait_until='load')
   page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()&&window.gameScoring');page.evaluate(helpers);page.evaluate('devAudio.push(volcanoStageBgm,volcanoBossBgm,stormSkyStageBgm,stormSkyBossBgm)')
  load();initial=page.evaluate('gameWorlds.developerSnapshot()');assert initial=={'enabled':False,'selected':{'regionId':0,'phase':1},'active':False,'start':{'regionId':0,'phase':1}}
  initial_storage=page.evaluate('devStorageSnapshot()');assert initial_storage==seed
  page.locator('#selectionHelp').tap();expect(page.locator('#developerStartToggle')).not_to_be_checked();expect(page.locator('#developerStartFields')).to_be_hidden()
  assert page.evaluate("[...developerStartWorld.options].map(o=>Number(o.value))")==[0,1]
  assert page.evaluate("[...developerStartRegion.options].map(o=>Number(o.value))")==[0,1,2,3]
  assert page.evaluate("[...developerStartPhase.options].map(o=>Number(o.value))")==[1,2,3,4,5]
  page.locator('#developerStartSettings').scroll_into_view_if_needed();page.screenshot(path=str(args.artifacts/'default-off-help.png'))
  passed('Fresh launch defaults to developerOFF/forest1 without changing any of the4 legacy storage values; Help lists only registered worlds/regions and phases1–5.')
  page.locator('#worldTrialToggle').check();assert page.evaluate('gameWorlds.isTrial()')
  page.locator('#developerStartToggle').check();expect(page.locator('#worldTrialToggle')).not_to_be_checked();expect(page.locator('#worldTrialToggle')).to_be_disabled()
  expect(page.locator('#developerStartPriority')).to_be_visible();page.locator('#developerStartWorld').select_option('1');assert page.evaluate('[...developerStartRegion.options].map(o=>Number(o.value))')==[4,5,6]
  page.locator('#developerStartRegion').select_option('4');page.locator('#developerStartPhase').select_option('5');page.screenshot(path=str(args.artifacts/'help-snow-boss-915x412.png'))
  page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap();page.wait_for_function('started&&boss!==null');state=page.evaluate('devStartState()')
  assert state['stage']==4 and state['phase']==5 and state['score']==0 and state['hp']==state['maxHP']==4 and state['upgrade']==0 and state['boss']['hp']==20
  assert state['items']==state['enemies']==state['warnings']==state['bullets']==state['enemyBullets']==0
  assert state['route']['route']==[4] and not state['route']['activeTrial'] and len(state['plan']['regions'])==1 and state['plan']['regions'][0]['region']==4
  assert state['plan']['monsters']==state['plan']['entrances']==[] and state['phaseKills']==state['requiredKills']==6
  assert page.evaluate('gameScoring.getLastResult()===null&&devWrites.length===0&&!!document.fullscreenElement')
  report['first_snow_boss_start']=state
  passed('Actual Help/select/start controls enter snow boss immediately at fullHP/upgrade0/score0 with no normal enemy, shot, item or old item-plan state; trial25 is excluded and fullscreen remains active.')
  locked=page.evaluate('''() => {const before=JSON.stringify(gameWorlds.developerSnapshot());const results=[gameWorlds.setDeveloperStart({regionId:0,phase:1}),gameWorlds.setDeveloperStart({enabled:false}),gameWorlds.setTrialEnabled(true)];
   const copy=gameWorlds.runStart();copy.regionId=99;return {results,same:before===JSON.stringify(gameWorlds.developerSnapshot()),start:gameWorlds.runStart()};}''')
  assert locked=={'results':[False,False,False],'same':True,'start':{'regionId':4,'phase':5}}
  passed('Run start is a fixed copy: live mode/region/phase changes and mutations of returned snapshots cannot change the active encounter.')

  #75 real spawn/shoot/collision paths, all regions/phases and all three characters.
  page.evaluate('devExitFixture()');matrix=[]
  for region in range(7):
   for step in range(1,6):
    for kind in range(3):
     assert page.evaluate('cfg=>gameWorlds.setDeveloperStart(cfg)',{'enabled':True,'regionId':region,'phase':step})
     row=page.evaluate('''type=>{itemMonsters.configure({opportunitiesPerRegion:0});devPlay=[];start(type);const first=devStartState();const firstTrack=devPlay.find(e=>e.index>=0)?.index;const finish=devComplete();return {first,firstTrack,finish};}''',kind)
     first=row['first'];finish=row['finish'];record=finish['result']['record'];waves=finish['waves']
     assert first['stage']==region and first['phase']==step and first['type']==kind and first['hp']==first['maxHP']==[4,6,9][kind] and first['upgrade']==first['score']==0
     assert first['route']['route']==[region] and first['developer']['start']=={'regionId':region,'phase':step}
     assert first['angle']==3.141592653589793 and first['items']==first['enemies']==first['warnings']==0
     assert (first['boss'] is not None)==(step==5)
     if step==5:assert first['boss']['maxHp']==[20,35,50,65,20,20,20][region] and first['phaseKills']==6
     else:assert first['phaseKills']==0
     assert row['firstTrack']==((13 if step==5 else 12) if region==5 else (15 if step==5 else 14) if region==6 else [0,1,2,3,0,4,5][region]+(4 if step==5 else 0)),row['firstTrack']
     assert [w['phase'] for w in waves]==list(range(step,6)) and all(w['stage']==region for w in waves) and len(waves)==6-step
     assert not finish['started'] and finish['stage']==region and finish['phase']==5 and '지역 테스트 완료' in finish['heading']
     assert finish['score']==[7000,5900,4800,3700,2000][step-1] and record['bossKills']==1 and record['clearedPhases']==5-step
     assert record['normalKills']==(0 if step==5 else (6-step)*6) and record['itemKills']==0 and record['regionId']==region and record['characterId']==kind
     assert finish['result']['developerTest'] and not finish['result']['saved'] and not finish['result']['isTop10'] and finish['result']['rank']==0 and record['order']==0
     page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending')
     expect(page.locator('#selectionResult')).to_contain_text('지역 테스트 완료')
     if region==4 and step==5 and kind==0:page.screenshot(path=str(args.artifacts/'developer-complete.png'))
     matrix.append({'region':region,'startPhase':step,'character':kind,**row})
  report['entry_completion_matrix']=matrix
  passed('All7 regions×5 starting phases×3 characters=105 actual encounter paths start at the exact target and finish at that region boss, with fullHP/upgrade0 and no traversal to other regions.')
  passed('Direct boss starts spawn20/35/50/65/20/20HP bosses with zero normal kills/cleared-phase bonuses; other starts credit only actual remaining phases, producing7000/5900/4800/3700/2000 points.')
  passed('Every matrix start selects the correct native stage/boss Audio target first, including forest-profile snow; no brief forest start is inserted for rock/sea/desert or direct bosses.')
  assert page.evaluate('devStorageSnapshot()')==initial_storage and page.evaluate('devWrites.length')==0
  assert page.evaluate('gameScoring.getTop().map(r=>r.id)')==['old-normal'] and page.evaluate('gameScoring.getHistory().map(r=>r.id)')==['old-normal']
  page.evaluate('gameWorlds.setTrialEnabled(true)');assert page.evaluate('!gameWorlds.developerSnapshot().enabled&&gameScoring.getTop().map(r=>r.id).join()==="old-trial"&&gameScoring.getHistory().map(r=>r.id).join()==="old-trial"')
  page.evaluate('gameWorlds.setDeveloperStart({enabled:true,regionId:4,phase:5})')
  assert page.evaluate('devStorageSnapshot()')==initial_storage and page.evaluate('devWrites.length')==0
  passed('After90 clears, all4 persistent record strings are byte-identical with0 storage writes; normal/trial TOP10 and memory/history caches contain only their original valid records.')

  # Native death, exit, forced restart and duplicate finish cannot leak analytics.
  page.locator('#startSelected').tap();page.evaluate('spawn=999;transition=0;hp=0;update(0)')
  expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#gameOverRank')).to_have_text('🧪 개발 테스트 · 기록 저장 안 함')
  gameover=page.evaluate('gameScoring.getLastResult()');assert gameover['developerTest'] and gameover['record']['outcome']=='game_over'
  page.screenshot(path=str(args.artifacts/'developer-game-over.png'))
  assert not page.evaluate('gameWorlds.setDeveloperStart({enabled:false})')
  expect(page.locator('#menu')).to_be_visible(timeout=4000);expect(page.locator('#selectionResult')).to_have_text('')
  for kind in [1,2]:
   page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();assert page.evaluate('player.type')==kind
   page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitCancel').tap();assert page.evaluate('started')
   page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible();result=page.evaluate('gameScoring.getLastResult()');assert result['developerTest'] and result['record']['outcome']=='abandoned'
  page.evaluate('start(0);spawn=999;start(1);spawn=999;devExitFixture();gameScoring.finish("clear");gameScoring.finish("game_over")')
  assert page.evaluate('devStorageSnapshot()')==initial_storage and page.evaluate('devWrites.length')==0
  passed('Actual3s game over clearly reports no recording, exits/cancels/restarts and duplicate finish save neither TOP10 nor analytics; all three characters retain their original selection/start/fullscreen flows.')

  # Item manager initializes directly for the chosen region and preserves its rules.
  item=page.evaluate('''() => {
   gameWorlds.setDeveloperStart({enabled:true,regionId:3,phase:3});itemMonsters.configure({opportunitiesPerRegion:3});start(0);spawn=999;transition=0;invuln=999;
   const initial=itemMonsters.snapshot();const selected=initial.regions[0].phases.find(s=>s.selected);phase=selected.phase;
   for(let n=0;n<selected.requiredKills;n++){enemies=[{x:100,y:100,r:16,hp:1,special:false,t:0,speed:0,shot:999,charge:999,kind:0,mode:'chase',vx:0,vy:0}];devHit(enemies[0]);}
   itemMonsters.update(1.4);const actor=itemMonsters.targets()[0],before=phaseKills,score=runScore;actor.x=100;actor.y=100;for(let i=0;i<5;i++)devHit(actor);
   return {initial,before,after:phaseKills,points:runScore-score,drops:items.length};
  }''')
  assert len(item['initial']['regions'])==1 and item['initial']['regions'][0]['region']==3 and item['initial']['regions'][0]['opportunities']==3
  assert sum(s['selected'] for s in item['initial']['regions'][0]['phases'])==3 and all(1<=s['requiredKills']<=4 for s in item['initial']['regions'][0]['phases'] if s['selected'])
  assert item['before']==item['after'] and item['points']==200 and item['drops']==1
  report['selected_region_item_manager']=item
  page.evaluate('devExitFixture()');assert page.evaluate('devStorageSnapshot()')==initial_storage
  passed('Selected-region item planning starts with one fresh3-opportunity/1–4-kill plan, no forest carryover; actual item spawn/HP5 kill still gives200+one drop without advancing normal kills or saving records.')

  # Verify real playback, not only requests, for all native scene choices.
  audio_rows=[]
  for region in range(7):
   for step in [1,5]:
    page.evaluate('cfg=>gameWorlds.setDeveloperStart(cfg)',{'enabled':True,'regionId':region,'phase':step});page.locator('#startSelected').tap();page.evaluate('spawn=999;invuln=999')
    index=(13 if step==5 else 12) if region==5 else (15 if step==5 else 14) if region==6 else [0,1,2,3,0,4,5][region]+(4 if step==5 else 0)
    page.wait_for_function('index=>!devAudio[index].paused&&devAudio[index].currentTime>.02&&selectionBgm.paused&&devAudio.filter(a=>a.loop&&!a.paused).length===1',arg=index)
    before=page.evaluate('index=>devAudio[index].currentTime',index);page.wait_for_timeout(120);after=page.evaluate('index=>devAudio[index].currentTime',index);assert after>before
    audio_rows.append({'region':region,'phase':step,'audio_index':index,'before':before,'after':after})
    page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
  report['native_entry_audio']=audio_rows
  passed('All7 regions normal/direct-boss starts play the expected native BGM with increasing currentTime, selection paused and exactly one looping track.')

  # Existing music setting remains authoritative for both encounter kinds.
  page.locator('#musicToggle').tap()
  for step in [1,5]:
   page.evaluate('step=>gameWorlds.setDeveloperStart({enabled:true,regionId:3,phase:step})',step);page.locator('#startSelected').tap();page.wait_for_timeout(120);assert page.evaluate('devAudio.filter(a=>a.loop&&!a.paused).length===0&&selectionBgm.paused')
   page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
  page.locator('#musicToggle').tap();page.wait_for_function('!selectionBgm.paused')
  passed('MusicOFF remains silent for developer normal/boss starts; exit/ON restores the same selection BGM with no new music control or audio resource.')

  layouts=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.locator('#selectionHelp').tap();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartPhase').select_option('5');page.locator('#developerStartFields').scroll_into_view_if_needed()
   boxes=page.evaluate('''() => {const r=id=>document.getElementById(id).getBoundingClientRect().toJSON();return {W:innerWidth,H:innerHeight,dialog:r('selectionHelpDialog'),fields:['developerStartWorld','developerStartRegion','developerStartPhase'].map(r),overflow:selectionHelpDialog.scrollHeight>selectionHelpDialog.clientHeight}}''')
   assert all(b['width']>=75 and b['height']>=44 and b['x']>=0 and b['right']<=w and b['y']>=0 and b['bottom']<=h for b in boxes['fields']),boxes
   assert 0<=boxes['dialog']['x'] and boxes['dialog']['right']<=w and 0<=boxes['dialog']['y'] and boxes['dialog']['bottom']<=h
   page.screenshot(path=str(args.artifacts/f'help-{w}x{h}.png'));page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap();page.evaluate('spawn=999;invuln=999;transition=0;gameScoring.updateHUD();gameExitDialogOpen=true;draw()')
   controls=page.evaluate('''() => {const r=id=>document.getElementById(id).getBoundingClientRect().toJSON();return {rotation:r('rotationJoystick'),fire:r('fire'),hud:r('hud'),full:r('fullscreenToggle'),stats:[hud.scrollWidth,hud.clientWidth]}}''')
   assert controls['rotation']['left']==30 and h-controls['rotation']['bottom']==22 and controls['rotation']['right']<controls['fire']['left']
   assert controls['hud']['right']<=controls['full']['left']
   page.screenshot(path=str(args.artifacts/f'direct-snow-boss-{w}x{h}.png'));page.evaluate('gameExitDialogOpen=false');page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
   layouts.append({'viewport':[w,h],'help':boxes,'controls':controls})
  report['landscape_layouts']=layouts
  passed('All3 landscape sizes fit the developer selectors with44px targets and scrollable Help; real close/start/exit work and gameplay retains30px/22px joystick and nonoverlapping HUD/fire/fullscreen.')

  invalid=page.evaluate('''() => {const before=JSON.stringify(gameWorlds.developerSnapshot());const values=[{regionId:99},{phase:0},{phase:6},{enabled:'yes'}].map(c=>gameWorlds.setDeveloperStart(c));return {values,same:before===JSON.stringify(gameWorlds.developerSnapshot())};}''')
  assert invalid=={'values':[False,False,False,False],'same':True}
  passed('Unknown regionIDs, phases outside1–5 and invalid switches are rejected without changing the chosen entry or any saved data.')
  assert page.evaluate('devStorageSnapshot()')==initial_storage and page.evaluate('devWrites.length')==0
  load();assert page.evaluate('!gameWorlds.developerSnapshot().enabled&&gameWorlds.developerSnapshot().selected.regionId===0&&gameWorlds.developerSnapshot().selected.phase===1&&!gameWorlds.isTrial()')
  assert page.evaluate('devStorageSnapshot()')==initial_storage
  passed('Reload forgets all developer settings and restores ordinary forest1/defaultOFF while preserving all original record bytes.')

  # Normal/trial paths are also covered by the retained complete-world regression.
  page.locator('#startSelected').tap();assert page.evaluate('stage===0&&phase===1&&gameWorlds.snapshot().route.join()==="0,1,2,3"&&!gameWorlds.isDeveloperRun()')
  page.evaluate('spawn=999;invuln=999;stage=3;phase=5;nextPhase()');normal=page.evaluate('gameScoring.getLastResult()');assert normal['saved'] and not normal.get('developerTest',False)
  page.wait_for_function('!menu.classList.contains("hidden")');page.evaluate('gameWorlds.setTrialEnabled(true)');page.locator('#startSelected').tap();assert page.evaluate('stage===0&&phase===1&&gameWorlds.snapshot().route.join()==="0,1,2,3,4,5,6"&&!gameWorlds.isDeveloperRun()')
  page.evaluate('spawn=999;invuln=999;stage=6;phase=5;nextPhase()');trial=page.evaluate('gameScoring.getLastResult()');assert trial['saved'] and trial['record']['trialMode'] and not trial.get('developerTest',False)
  assert page.evaluate('JSON.parse(localStorage.getItem("heliTrio.top10.v1")).records.some(r=>r.id==="old-normal")&&JSON.parse(localStorage.getItem("heliTrio.world2Trial.top10.v1")).records.some(r=>r.id==="old-trial")')
  assert page.evaluate('devStorageKeys.every(key=>JSON.parse(localStorage.getItem(key)).records.every(row=>!row.developerTest&&row.order>0))')
  passed('Turning developerOFF restores the unchanged20-phase normal and35-phase world2-trial routes; their legitimate results still save to their original distinct stores without losing prior records.')

  # Simulate a later registered world/region with a deliberately non-index ID.
  worlds_js=(ROOT/'assets/worlds/worlds.js').read_text();needle="    [4,'world-2:snowfield'";assert worlds_js.count(needle)==1
  virtual_js=worlds_js.replace(needle,"    [42,'fixture:registered',7,0,'등록 확장 검증 지역',0,'검증 보스'],\n"+needle,1)
  future_context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);future=future_context.new_page();future_errors=[];future.on('pageerror',lambda e:future_errors.append(str(e)))
  if args.standalone:
   future_context.set_offline(True);virtual_html=(ROOT/'dist/heli_trio_galaxy_test.html').read_text();assert virtual_html.count(worlds_js)==1;future.set_content(virtual_html.replace(worlds_js,virtual_js,1),wait_until='load')
  else:
   future.route('**/assets/worlds/worlds.js',lambda route:route.fulfill(status=200,content_type='text/javascript',body=virtual_js));future.goto(url,wait_until='load')
  future.wait_for_function('gameWorlds&&document.getElementById("developerStartToggle")');future.locator('#selectionHelp').tap();future.locator('#developerStartToggle').check();future.locator('#developerStartWorld').select_option('7');assert future.evaluate('[...developerStartRegion.options].map(o=>Number(o.value))')==[42]
  future.locator('#developerStartPhase').select_option('5');future.locator('#selectionHelpClose').tap();future.locator('#startSelected').tap();assert future.evaluate('stage===42&&phase===5&&boss.hp===20&&runScore===0&&gameWorlds.snapshot().route.join()==="42"')
  assert not future_errors,future_errors;future_context.close()
  passed('An isolated future registry fixture automatically adds worldID7/regionID42 to the selectors and starts its boss correctly; no option-name/index mapping or product region was hardcoded.')
  assert not errors and not dialogs and not failed and not external,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':external}
  passed('No uncaught JavaScript errors, native dialogs, failed assets or standalone external requests occur.')
  browser.close()
finally:s.shutdown();s.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
