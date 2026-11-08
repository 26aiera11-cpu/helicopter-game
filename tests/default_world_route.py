"""Issue38 real default40 starts, three-hero routes, carry and legacy storage isolation."""
import argparse,base64,json,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from default_world_route_preservation import verify
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':args.standalone,'passed':[],'preservation':verify(),'limits':['Actual Chromium/native media/trusted taps with controlled combat, invulnerability and item-spawn quota0; not physical Galaxy or a human balance playthrough.','Offline exact HTML is injected into a network-disabled blank origin without bypassing file-navigation policy.','Original boss reward then region+2HP recovery are preserved; no HP reset.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
keys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1']
def old_record(trial):
 return {'id':'retained-trial' if trial else 'retained-normal','score':900000,'characterId':0,'characterName':'뾰코','regionId':4 if trial else 3,'regionName':'❄ 설원 (시험)' if trial else '🏜️ 사막 지역','worldId':int(trial),'worldName':'월드 2' if trial else '월드 1','regionKey':'world-2:snowfield' if trial else 'world-1:desert','localRegionIndex':0 if trial else 3,'trialMode':trial,'phase':5,'order':1,'createdAt':'2026-11-02T01:00:00.000Z','outcome':'clear','normalKills':0,'itemKills':0,'bossKills':1,'clearedPhases':0,'playTimeSeconds':10,'finalUpgrade':0}
seed={k:json.dumps({'version':1,'records':[old_record('world2Trial' in k)]},ensure_ascii=False) for k in keys}
probe=r'''()=>{
 window.routeMedia=[];window.routeMaxMusic=0;window.routeOverlaps=[];const Native=Audio;
 window.Audio=new Proxy(Native,{construct(t,args){const a=new t(...args);routeMedia.push(a);return a}});
 window.routeAttach=()=>{for(const a of document.querySelectorAll('audio'))if(!routeMedia.includes(a))routeMedia.push(a)};
 window.routeActive=()=>routeMedia.filter(a=>a.loop&&!a.paused&&!a.ended);
 const sample=()=>{const a=routeActive();routeMaxMusic=Math.max(routeMaxMusic,a.length);if(a.length>1)routeOverlaps.push(a.map(a=>a.id||routeMedia.indexOf(a)));requestAnimationFrame(sample)};requestAnimationFrame(sample);
}'''
common=(ROOT/'tests/worlds.py').read_text().split("helpers='''",1)[1].split("'''",1)[0]
helpers=r'''()=>{
 window.routeKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];
 window.routeStorage=()=>Object.fromEntries(routeKeys.map(k=>[k,localStorage.getItem(k)]));
 window.routeWrites=[];const write=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(routeKeys.includes(k))routeWrites.push({key:k,value:v});return write.call(this,k,v)};
 window.routeQuiet=()=>{spawn=999;transition=0;invuln=999;itemMonsters.configure({opportunitiesPerRegion:0});};
 window.routeNormal=()=>{
  const before={region:stage,phase,type:player.type,score:runScore};routeQuiet();
  if(stage===3&&phase===5){hp=1;player.upgrade=3;}
  for(let n=0;n<6;n++){bullets=[];warnEnemy();for(let j=0;j<36;j++)update(.04);const e=enemies[0];if(!e)throw Error('No enemy '+JSON.stringify({before,kill:n,stage,phase,phaseKills,score:runScore,warnings: warnings.length,bullets:bullets.length}));let hits=0;while(e.hp>0&&hits++<10)worldHit(e);if(e.hp>0)throw Error('Enemy survived');}
  if(before.phase===5){update(0);transition=0;if(!boss)throw Error('No boss');}
  return {before,stage,phase,score:runScore,hp,bossHP:boss?.maxHp,bossReady:!!boss,menu:!menu.classList.contains('hidden'),started};
 };
 window.routeFinishBoss=()=>{
  const before={region:stage,phase,type:player.type,score:runScore,hp,upgrade:player.upgrade,bossHP:boss.hp};const actor=player,king=boss,events=[];const on=e=>events.push(e.detail);document.addEventListener('bossreward',on);
  let marker;if(stage===3&&!gameWorlds.isDeveloperRun()){marker={x:W-40,y:H-40,type:'power',life:7.25,r:13,t:0,vx:0,vy:0,turn:999};items=[marker];}
  const random=Math.random;try{if(marker)Math.random=()=>.1;let hits=0;while(boss&&hits++<300)worldHit(boss);if(boss)throw Error('Boss survived');}finally{Math.random=random;document.removeEventListener('bossreward',on);}
  let n=0;while((gameMachineFortress.snapshot().advancing||gameStormSky.snapshot().advancing||gameVolcano.snapshot().advancing)&&n++<100)update(.04);
  const immediate={stage,phase,type:player.type,hp,upgrade:player.upgrade,score:runScore,started,menu:!menu.classList.contains('hidden'),samePlayer:player===actor,sameItem:marker?items.includes(marker):null,item:marker&&{...marker},rewardGranted:king.rewardGranted,events};
  if(marker){transition=0;for(let i=0;i<5;i++)update(.04);immediate.afterTickLife=marker.life;immediate.sameItemAfterTick=items.includes(marker);}
  return {before,after:immediate,result:gameScoring.getLastResult()};
 };
}'''
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
  return super().translate_path(path)
 def do_GET(self):
  if self.path.split('?')[0]=='/route-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline route</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);ctx.add_init_script('('+probe+')()');ctx.add_init_script('const seed='+json.dumps(seed)+';for(const [k,v] of Object.entries(seed))if(localStorage.getItem(k)===null)localStorage.setItem(k,v);');page=ctx.new_page();errors=[];dialogs=[];failed=[];external=[]
  def observe(target):
   target.on('pageerror',lambda e:errors.append(str(e)));target.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));target.on('requestfailed',lambda r:failed.append(r.url));target.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  observe(page)
  def ready():
   page.wait_for_function('gameMachineFortress.ready()&&gameStormSky.ready()&&gameSnowfield.ready()&&gameVolcano.ready()&&itemMonsters.ready()');page.evaluate('routeAttach()');page.wait_for_function('routeMedia.length===19&&routeMedia.every(a=>!a.error&&a.readyState>=2&&a.duration>0)');page.evaluate(common);page.evaluate(helpers)
  def load(query=''):
   global page
   if args.standalone:
    # Retain real context storage, but release each previous 80 MB document.
    page.close();page=ctx.new_page();observe(page);
   if args.standalone:ctx.set_offline(False);page.goto(url+'/route-origin'+query);external.clear();ctx.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:page.goto(url+'/helicopter-game/'+query)
   ready()
  def music(region,boss=False):
   profile=[0,1,2,3,0,4,5,6][region];ids=['volcano','stormSky','machineFortress'];target=(ids[profile-4]+('BossBgm' if boss else 'StageBgm')) if profile>=4 else str(profile+(4 if boss else 0))
   page.wait_for_function('t=>routeActive().length===1&&routeActive()[0]===(Number.isInteger(+t)?routeMedia[+t]:document.getElementById(t))&&routeActive()[0].currentTime>.03',arg=target)
   return page.evaluate('({id:routeActive()[0].id,index:routeMedia.indexOf(routeActive()[0]),time:routeActive()[0].currentTime})')
  def start(kind):
   page.evaluate('itemMonsters.configure({opportunitiesPerRegion:0})');page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();page.evaluate('routeQuiet()');page.wait_for_function('started')
  load();assert page.evaluate('gameWorlds.isTrial()&&!gameWorlds.isDeveloper()&&gameWorlds.snapshot().route.length===8');assert page.evaluate('routeStorage()')==seed;assert page.evaluate('routeActive().length===0');page.locator('#selectionHelp').tap();expect(page.locator('#worldTrialToggle')).to_be_checked();expect(page.locator('#worldTrialSettings')).to_contain_text('기본 ON');expect(page.locator('#worldTrialSettings')).to_contain_text('20단계');page.screenshot(path=str(args.artifacts/'default-on-help.png'));page.locator('#selectionHelpClose').tap()
  passed('Fresh URL defaults40 ON/regions0..7; Help explains20 OFF, developer defaultsOFF, no autoplay and all4 seeded legacy storage values remain byte-identical.')
  page.locator('#selectionSettings').tap();expect(page.locator('#leaderboardTitle')).to_contain_text('40단계');expect(page.locator('#leaderboardRows')).to_contain_text('900,000');page.locator('#leaderboardClose').tap();assert page.evaluate('routeStorage()')==seed;passed('Default leaderboard reads existing trial records without writing or migrating either score/history store.')
  routes=[];boundaries=[]
  for hero,(w,h) in enumerate([(915,412),(800,360),(568,320)]):
   if hero:load()
   page.set_viewport_size({'width':w,'height':h});start(hero);assert page.evaluate('gameWorlds.snapshot().route.join()==="0,1,2,3,4,5,6,7"&&gameWorlds.snapshot().activeTrial&&!gameWorlds.isDeveloperRun()');assert page.evaluate('!gameWorlds.setTrialEnabled(false)&&!gameWorlds.setDeveloperStart({enabled:true,regionId:3,phase:5})')
   waves=[];normalBefore=page.evaluate('routeStorage()');writesBefore=page.evaluate('routeWrites.length')
   for region in range(8):
    stageMusic=music(region)
    for phase in range(1,6):
     row=page.evaluate('routeNormal()');assert row['before']['region']==region and row['before']['phase']==phase and row['before']['type']==hero
     if phase==5:
      row['music']=music(region,True);row['boss']=page.evaluate('routeFinishBoss()');after=row['boss']['after'];assert len(after['events'])==1 and after['rewardGranted']
      if region<7:assert after['started'] and not after['menu'] and after['stage']==region+1 and after['phase']==1 and after['samePlayer']
      if region==3:
       assert after['type']==hero and after['upgrade']==3 and after['hp']==min([4,6,9][hero],5) and after['score']==28000 and after['sameItem'] and after['item']['life']==7.25 and after['sameItemAfterTick'] and abs(after['afterTickLife']-7.05)<1e-6
       assert page.evaluate('routeWrites.length')==writesBefore;music(4);page.screenshot(path=str(args.artifacts/f'desert-to-snow-{hero}-{w}x{h}.png'));boundaries.append(row['boss'])
     waves.append(row)
   page.wait_for_function('!started&&!menu.classList.contains("hidden")');result=page.evaluate('gameScoring.getLastResult()');r=result['record'];assert r['score']==56000 and r['normalKills']==240 and r['bossKills']==8 and r['clearedPhases']==32 and r['regionId']==7 and r['worldId']==1 and r['phase']==5 and r['characterId']==hero and r['trialMode'] and result['saved'];assert page.evaluate('routeWrites.length')==writesBefore+2
   stored=page.evaluate('routeStorage()');assert all(stored[k]==normalBefore[k] for k in keys[:2]);assert all(old_record(True)==next(z for z in json.loads(stored[k])['records'] if z['id']=='retained-trial') for k in keys[2:]);n=page.evaluate('routeWrites.length');page.evaluate('gameScoring.finish("clear");gameScoring.finish("clear")');assert page.evaluate('routeWrites.length')==n;assert page.evaluate('id=>gameScoring.getHistory().filter(r=>r.id===id).length',r['id'])==1
   page.screenshot(path=str(args.artifacts/f'full40-clear-{hero}.png'));routes.append({'hero':hero,'size':[w,h],'waves':waves,'result':result});report['full40_routes_in_progress']=routes
  report['default_full40_three_heroes']=routes;report['desert_boundary_three_heroes']=boundaries;passed('All3 trusted default starts complete40 actual phases/240normal kills/8bosses/32bonuses for56000points; only final GigaCore ends play and writes one trial TOP10/history result. Every region stage/boss BGM resolves correctly.')
  passed('Actual desert HP0/reward enters snow1 with hidden menu/startedtrue and same player/item objects, upgrade3,28000points, original reward+2 then region+2HP cap. Item7.25s stays7.25 at transition and ages to7.05 after.2s; no intermediate score write/reset.')
  passed('World1 storage bytes remain unchanged through default40; seeded old trial records retain every field and repeated finish calls write nothing.')
  page.locator('#selectionHelp').tap();page.locator('#worldTrialToggle').uncheck();page.locator('#selectionHelpClose').tap();start(0);assert page.evaluate('gameWorlds.snapshot().route.join()==="0,1,2,3"&&!gameWorlds.snapshot().activeTrial');before20=page.evaluate('routeStorage()');rows=[]
  for region in range(4):
   for phase in range(1,6):
    row=page.evaluate('routeNormal()');assert row['before']['region']==region and row['before']['phase']==phase
    if phase==5:row['boss']=page.evaluate('routeFinishBoss()')
    rows.append(row)
  page.wait_for_function('!started');result20=page.evaluate('gameScoring.getLastResult()');assert result20['record']['score']==28000 and result20['record']['regionId']==3 and not result20['record']['trialMode'];stored20=page.evaluate('routeStorage()');assert all(stored20[k]==before20[k] for k in keys[2:]);assert all(any(r['id']=='retained-normal' and r['score']==900000 for r in json.loads(stored20[k])['records']) for k in keys[:2]);report['explicit20']={'waves':rows,'result':result20};passed('HelpOFF retains20phase/4boss/28000point desert clear in original World1 stores; old normal records and all trial storage bytes are preserved.')
  raw=page.evaluate('routeStorage()')
  for query,on in [('',True),('?world2=1',True),('?world2=0',False),('?world2=unknown',True)]:
   load(query);assert page.evaluate('gameWorlds.isTrial()')==on;assert page.evaluate('routeStorage()')==raw
  page.locator('#selectionHelp').tap();page.locator('#worldTrialToggle').uncheck();page.locator('#selectionHelpClose').tap()
  if not args.standalone:page.reload();ready()
  else:load()
  assert page.evaluate('gameWorlds.isTrial()') and page.evaluate('routeStorage()')==raw
  passed('Ordinary/unknown URL and?world2=1 initializeON;?world2=0 initializesOFF. ManualOFF is per-document and fresh reload returns defaultON, with no stored preference/migration/deletion.')
  dev=[]
  for region in [3,4,7]:
   page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('0' if region==3 else '1');page.locator('#developerStartRegion').select_option(str(region));page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap();start(0);assert page.evaluate('r=>gameWorlds.snapshot().route.join()===String(r)&&gameWorlds.isDeveloperRun()&&!gameWorlds.isTrial()&&!!boss&&phaseKills===6',region);music(region,True);row=page.evaluate('routeFinishBoss()');page.wait_for_function('!started');r=page.evaluate('gameScoring.getLastResult()');assert r['developerTest'] and not r['saved'] and r['record']['regionId']==region and page.evaluate('routeStorage()')==raw;dev.append({'region':region,'boss':row,'result':r})
  report['developer_single_region']=dev;passed('Real developer UI desert/snow/GigaCore direct5 remains single-region only and returns after that boss, without changing TOP10/history bytes.')
  page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').uncheck();page.locator('#worldTrialToggle').check();page.locator('#selectionHelpClose').tap();start(0);assert page.evaluate('!gameWorlds.isDeveloperRun()&&gameWorlds.snapshot().route.length===8')
  if not page.evaluate('!!document.fullscreenElement'):page.locator('#fullscreenToggle').tap()
  page.wait_for_function('!!document.fullscreenElement');page.locator('#exitGame').tap();page.locator('#gameExitCancel').tap();page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();assert page.evaluate('!started&&!!document.fullscreenElement');passed('Explicit ON after developerOFF restores full40; trusted fullscreen/internal exit cancel/confirm remain intact without native dialogs.')
  if args.standalone:
   payload=(ROOT/'dist/heli_trio_galaxy_test.html').read_bytes()
   for f in [*list((ROOT/'assets/machine_fortress').rglob('*.png')),*list((ROOT/'assets/audio').glob('*'))]:assert base64.b64encode(f.read_bytes()) in payload
   assert not external
  assert not errors and not dialogs and not failed,(errors,dialogs,failed);assert page.evaluate('routeMaxMusic===1&&routeOverlaps.length===0');report.update(all_passed=True,errors=errors,dialogs=dialogs,failed_requests=failed,offline_requests=external if args.standalone else []);passed('No uncaught errors/native dialogs/missing assets or overlapping BGM; standalone embeds PNG11/audio7 bytes and performs0external HTTP requests.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
