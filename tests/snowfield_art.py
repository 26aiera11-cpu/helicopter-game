"""Approved snowfield art: native events, original atlas geometry and World1 pixels."""
import argparse
import base64
import hashlib
import io
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from snowfield_preservation import SNOWFIELD_ASSETS,assert_snowfield_asset,without_snowfield_source,without_snowfield_asset

ROOT=Path(__file__).resolve().parents[1];BASELINE='0cbfe8205a761890a17b0cb9b77d161f2a283395'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASELINE,'standalone':args.standalone,'passed':[],'limits':[
 'Real Chromium canvas/pointer/fullscreen/media with controlled combat fixtures, not physical Galaxy/Samsung Internet or a manual difficulty playthrough.',
 'The supplied atlas animations are prototypes; original PNG/manifest bytes are preserved. Boss HP/motion and BGM retain the forest trial profile; Issue9 attacks are tested separately; Issue8 normal-enemy behavior is tested in snowfield_combat.py.',
 'Offline injects the exact one-file HTML into a blank origin with networking disabled; no managed file policy bypass.',
 'PNG screenshots are actual browser captures; game state/animation time is controlled for comparisons, without image editing.'
]}
def passed(message):report['passed'].append(message);print('PASS:',message,flush=True)
source=(ROOT/'index.html').read_text();manifest=json.loads((ROOT/'assets/snowfield/asset_manifest.json').read_text())
assert without_snowfield_source(source)==subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT).decode()
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name in SNOWFIELD_ASSETS:assert_snowfield_asset(path);continue
 actual=without_snowfield_asset(path.read_text(),name).encode() if path.suffix in ['.js','.css'] else path.read_bytes()
 assert actual==subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Exact art-only hooks reverse to0cbfe82; every earlier image/audio/input/score/item/combat asset is byte-identical and all JS syntax passes.')
assert hashlib.sha256((ROOT/'assets/snowfield'/manifest['background']['path']).read_bytes()).hexdigest()==manifest['background']['sha256']=='54e4463a5c9e44b30e8e736b6c9d980e5d2cf7f4f7f9a17d9c9578ac6cb32e0a'
alpha=[]
for spec in manifest['monsters']:
 atlas=Image.open(ROOT/'assets/snowfield'/spec['atlas']);assert atlas.mode=='RGBA' and atlas.size==(spec['cols']*spec['cell'][0],spec['rows']*spec['cell'][1])
 for name,anim in spec['animations'].items():
  assert len(anim['frames'])==anim['frame_count']
  for f in anim['frames']:
   x,y,w,h=f['rect_px'];assert [w,h]==spec['cell'] and 0<=x<x+w<=atlas.width and 0<=y<y+h<=atlas.height
   cell=atlas.crop((x,y,x+w,y+h));assert cell.getbbox() is not None and cell.getchannel('A').getextrema()[0]==0
 alpha.append({'id':spec['id'],'cell':spec['cell'],'atlas':atlas.size,'alpha':atlas.getchannel('A').getextrema(),'frames':sum(a['frame_count'] for a in spec['animations'].values())})
assert sum(s['frames'] for s in alpha)==115
report['source_atlases']=alpha
passed('Approved1920×864 background hash matches Issue6; all5 RGBA atlases have their distinct manifest cells, transparent padding and115 nonempty, in-bounds frames.')

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/offline-origin':
   self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline</title>');return
  super().do_GET()
def serve(directory):
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(directory)));threading.Thread(target=server.serve_forever,daemon=True).start();return server
class Touch:
 def __init__(self,c,p):self.cdp=c.new_cdp_session(p);self.page=p
 def tap(self,selector):
  expect(self.page.locator(selector)).to_be_visible();r=self.page.locator(selector).bounding_box();point={'id':50,'x':r['x']+r['width']/2,'y':r['y']+r['height']/2}
  self.cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});self.page.wait_for_timeout(60);self.cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[point]})
helpers='''() => {
 window.artEnemy=(x=160,y=150)=>({x,y,r:16,hp:1,special:false,t:0,speed:38,shot:999,charge:999,kind:0,mode:'chase',vx:0,vy:0});
 window.artScene=(step=1,type=0)=>{
  gameExitDialogOpen=false;itemMonsters.configure({opportunitiesPerRegion:0});start(type);gameSnowfieldSpawns.reset(12345);stage=4;phase=step;transition=0;spawn=999;invuln=999;player.x=W*.55;player.y=H*.72;
  if(step<5)enemies=[gameSnowfieldCombat.prepare(artEnemy(W*.45,H*.42))];else{phaseKills=requiredKills;update(0);transition=0;boss.shot=999;}
  gameSnowfield.observe(enemies,boss);gameScoring.updateHUD();
 };
 window.artHit=target=>{bullets=[];shoot();Object.assign(bullets[0],{x:target.x,y:target.y,vx:0,vy:0});update(0);};
 window.artFreeze=()=>{worldScroll=0;invuln=0;rotorSpin=.35;gameExitDialogOpen=true;draw();};
 window.artHoldFinale=()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});draw();};
 window.artReleaseFinale=()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));};
 window.artExit=()=>{gameExitDialogOpen=false;gameScoring.finish('abandoned');started=false;gameAudioStarted=false;gameAudio.pause();menu.classList.remove('hidden');gameSnowfield.reset();};
}'''
probe='''() => {window.artAudio=[];const Native=Audio;window.Audio=new Proxy(Native,{construct(target,args){const a=new target(...args);artAudio.push(a);return a}})}'''
server=serve(ROOT);temp=tempfile.TemporaryDirectory(prefix='heli-snow-art-baseline-');reference=None
try:
 archive=subprocess.check_output(['git','archive',BASELINE,'index.html','assets'],cwd=ROOT)
 with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(temp.name,filter='data')
 reference=serve(temp.name)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);context.add_init_script('('+probe+')()')
  page=context.new_page();errors=[];dialogs=[];failed=[];requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url))
  page.on('request',lambda r:requests.append(r.url) if args.standalone and r.url.startswith('http') else None)
  url=f'http://127.0.0.1:{server.server_port}/'
  if args.standalone:
   page.goto(url+'offline-origin');requests.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url+'helicopter-game/',wait_until='load')
  page.wait_for_function('window.gameSnowfield?.ready()&&itemMonsters.ready()');page.evaluate(helpers)
  assert not page.evaluate('gameWorlds.isTrial()')
  assert page.evaluate("document.getElementById('snowfieldManifest').content.textContent")== (ROOT/'assets/snowfield/asset_manifest.json').read_text()
  page.locator('#selectionHelp').tap();expect(page.locator('#worldTrialToggle')).not_to_be_checked();page.locator('#worldTrialToggle').check();page.locator('#selectionHelpClose').tap()
  assert '설원→화산' in page.locator('#worldTrialSettings').inner_text() and '35단계' in page.locator('#worldTrialSettings').inner_text()
  assert '혼합 등장/전투 밸런스 시험 / BGM 숲 임시' in page.locator('#worldPrototypeNotice').inner_text()
  page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement');page.locator('#startSelected').tap()
  passed('Original manifest is embedded byte-for-byte; all approved resources load at project-prefix/native or offline paths, trial remains defaultOFF and its opt-in/temporary-combat notice is accurate.')

  mapping=[]
  for step in range(1,6):
   row=page.evaluate('''step=>{artScene(step);const entity=boss||enemies[0];return {step,pose:gameSnowfield.pose(entity,!!boss),hp:entity.hp,r:entity.r,speed:entity.speed,boss:!!boss,profile:gameWorlds.profile(stage),name:gameWorlds.region(stage).bossName}}''',step)
   assert row['pose']['id']==['snow_slime','penguin_raider','ice_yeti','frost_turtle','blizzard_king'][step-1]
   assert row['hp']==[1,2,2,3,20][step-1] and row['r']==(48 if step==5 else 16) and row['profile']==0
   if step<5:assert abs(row['speed']-[32.3*1.06,36.1*1.06,28.5*1.06,20.9*1.06][step-1])<1e-8
   else:assert row['name']=='❄ 눈보라 거인왕 (시험)'
   mapping.append(row)
  report['stage_mapping']=mapping
  passed('Snow phases1–4 use slime/penguin/yeti/turtle and boss5 uses blizzard king; Issue8 HP1/2/2/3 and trial speeds are linked to the preserved art, with r16 and original bossHP20/r48.')

  frames=page.evaluate('''() => {
   const rows=[];
   for(let i=0;i<5;i++)for(const name of ['idle','move','attack','hit','defeat']){
    artScene(i===4?5:i+1);gameSnowfield.reset();let entity=boss||enemies[0];entity.hp=10;gameSnowfield.observe(enemies,boss);
    if(name==='move'){entity.x+=1;gameSnowfield.observe(enemies,boss);}
    if(name==='attack')emitEnemyShot(entity);
    if(name==='hit'){artHit(entity);}
    if(name==='defeat'){entity.hp=0;gameSnowfield.hit(entity,!!boss);gameSnowfield.tick(.33);}
    const spec=gameSnowfield.species[i],anim=spec.animations[name];
    for(let n=0;n<anim.frame_count;n++){
     const calls=[],spy={drawImage:(image,...args)=>calls.push({image:image.id,args})};
     if(name==='defeat')gameSnowfield.drawDefeats(spy);else gameSnowfield.drawActor(spy,entity,!!boss);
     const selected=name==='defeat'?gameSnowfield.snapshot().ghosts[0].pose:gameSnowfield.pose(entity,!!boss);
     rows.push({id:spec.id,name,index:n,selected,call:calls[0],expected:anim.frames[n].rect_px});
     gameSnowfield.tick(anim.frame_duration_ms/1000);
    }
   }
   return rows;
  }''')
  assert len(frames)==115
  for row in frames:
   assert row['selected']['name']==row['name'] and row['selected']['index']==row['index'] and row['selected']['rect']==row['expected'],row
   values=row['call']['args'];assert values[:4]==row['expected'] and len(values)==8 and abs(values[6]/values[2]-values[7]/values[3])<1e-9,row
   assert values[4]>=0 and values[5]>=0 and values[4]+values[6]<=915 and values[5]+values[7]<=412
  report['actual_draw_frames']=frames
  passed('All115 supplied frames are selected through the runtime renderer with exact manifest source rectangles/counts/times and equal X/Y scaling; no adjacent-cell bleed, rotation or square distortion.')

  movement=page.evaluate('''() => {artScene(1);const e=enemies[0],before={x:e.x,y:e.y};update(.1);const moved=gameSnowfield.pose(e);update(.101);return {before,after:{x:e.x,y:e.y},moved,frame:gameSnowfield.pose(e),hp:e.hp,r:e.r,speed:e.speed};}''')
  assert movement['moved']['name']==movement['frame']['name']=='move' and movement['frame']['index']==1
  assert movement['hp']==1 and movement['r']==16 and abs(movement['speed']-32.3*1.06)<1e-8
  report['actual_movement']=movement;passed('Actual slime pursuit at34.238px/s changes idle to move and advances its frame; HP1 and the original collider remain exact.')
  attacks=page.evaluate('''() => {const rows=[];for(let step=1;step<=5;step++){artScene(step);const e=boss||enemies[0];e.shot=0;if(step===5){for(let n=0;n<180;n++)update(.01);}else update(0);const start=gameSnowfield.pose(e,!!boss);update(.121);rows.push({step,start,after:gameSnowfield.pose(e,!!boss),bullets:enemyBullets.length,speed:Math.hypot(enemyBullets[0].vx,enemyBullets[0].vy),interval:e.shot});}return rows;}''')
  assert all(r['start']['name']==r['after']['name']=='attack' and r['after']['index']==1 and r['bullets']==(3 if r['step']==5 else 1) and abs(r['speed']-[85,85,76.5,85,80][r['step']-1])<1e-8 for r in attacks),attacks
  report['actual_attacks']=attacks;passed('Real ordinary/boss bullet emission triggers attack once, advances the4-frame nonlooping row and uses Issue8 normal bullet speeds85/85/76.5/85 while using the Issue9 boss3-shot fan at80px/s after its1.8s delay.')

  hit=page.evaluate('''() => {artScene(5);const target=boss;artHit(target);const first=gameSnowfield.pose(target,true);update(.111);const middle=gameSnowfield.pose(target,true);update(.111);const last=gameSnowfield.pose(target,true);return {hp:target.hp,r:target.r,first,middle,last,score:runScore};}''')
  assert hit['hp']==19 and hit['r']==48 and hit['score']==0 and [hit[k]['index'] for k in ['first','middle','last']]==[0,1,2] and all(hit[k]['name']=='hit' for k in ['first','middle','last'])
  report['actual_nonlethal_hit']=hit;passed('A real nonlethal boss collision removes exactly1HP, awards no kill points and plays all3 hit frames; hit has priority over attack/movement.')
  fatal=page.evaluate('''() => {artScene(1);const e=enemies[0];phaseKills=5;artHit(e);const atDeath={phase,phaseKills,score:runScore,remaining:enemies.length,ghost:gameSnowfield.snapshot().ghosts[0]};
   gameSnowfield.hit(e);gameScoring.enemyDefeated(e);const count=gameSnowfield.snapshot().ghosts.length;
   update(.331);const defeat=gameSnowfield.snapshot().ghosts[0];update(.721);
   return {atDeath,count,defeat,ghosts:gameSnowfield.snapshot().ghosts.length,score:runScore,phase,phaseKills};}''')
  assert fatal['atDeath']['phase']==2 and fatal['atDeath']['phaseKills']==0 and fatal['atDeath']['remaining']==0 and fatal['atDeath']['score']==fatal['score']==600
  assert fatal['atDeath']['ghost']['pose']['name']=='hit' and fatal['defeat']['pose']['name']=='defeat' and fatal['defeat']['id']=='snow_slime' and fatal['count']==1 and fatal['ghosts']==0
  report['actual_fatal_hit']=fatal;passed('HP1 normal kill immediately removes collision/awards100+phase500, then a visual-only3-frame hit→6-frame defeat survives the phase change with the original species and cannot duplicate score or corpses.')

  edge=page.evaluate('''() => {const rows=[];for(let step=1;step<=5;step++){artScene(step);const e=boss||enemies[0];for(const [x,y] of [[17,18],[W-17,H-18]]){e.x=x;e.y=y;const before={x:e.x,y:e.y,r:e.r};const calls=[];gameSnowfield.drawActor({drawImage:(im,...v)=>calls.push(v)},e,!!boss);rows.push({step,before,after:{x:e.x,y:e.y,r:e.r},draw:calls[0]});}}return rows;}''')
  for row in edge:
   v=row['draw'];assert row['before']==row['after'] and v[4]>=0 and v[5]>=0 and v[4]+v[6]<=915 and v[5]+v[7]<=412
  report['viewport_edge_cells']=edge;passed('At both viewport corners every complete cell stays visible; visual offsets do not move or resize original enemy/boss colliders.')

  backgrounds=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('W===innerWidth&&H===innerHeight');page.evaluate('artScene(1)')
   bg=page.evaluate('''() => {const calls=[],spy={drawImage:(im,...args)=>calls.push({id:im.id,args})};gameSnowfield.drawBackground(spy,W,H);worldScroll=99999;gameSnowfield.drawBackground(spy,W,H);
    const native=ctx.drawImage;let actual=0;ctx.drawImage=function(im,...v){if(im===gameSnowfield.backgroundImage)actual++;return native.call(this,im,...v)};try{draw()}finally{ctx.drawImage=native}
    return {calls,actual,geometry:gameSnowfield.backgroundGeometry(W,H),size:[W,H],image:[gameSnowfield.backgroundImage.naturalWidth,gameSnowfield.backgroundImage.naturalHeight]};}''')
   assert bg['actual']==1 and bg['calls'][0]==bg['calls'][1] and bg['image']==[1920,864]
   box=bg['geometry'];assert box['scale']<=1 and box['w']>=w and box['h']>=h and abs(box['w']/box['h']-1920/864)<1e-9
   backgrounds.append(bg)
   for step in range(1,6):
    page.evaluate('step=>{artScene(step);artFreeze()}',step);page.screenshot(path=str(args.artifacts/f'snow-phase-{step}-{w}x{h}.png'))
  report['backgrounds']=backgrounds;passed('Three landscape sizes use exactly one static1920×864 cover draw, unchanged by scroll: no repeated seam, no nonuniform scale or excessive zoom; all5 phase screenshots are saved.')

  # Frozen baseline/new canvases must match exactly for every old region/boss.
  reference_context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);old=reference_context.new_page();old.goto(f'http://127.0.0.1:{reference.server_port}/',wait_until='load');old.wait_for_function('terrainImgs.every(i=>i.complete&&i.naturalWidth)&&enemySprites.flat().every(i=>i.complete&&i.naturalWidth)&&bossSprites.every(i=>i.complete&&i.naturalWidth)')
  fixture='''({area,king})=>{gameExitDialogOpen=false;itemMonsters.configure({opportunitiesPerRegion:0});start(0);spawn=999;stage=area;phase=king?5:2;phaseKills=0;transition=0;warnings=[];enemyBullets=[];bullets=[];worldScroll=37;rotorSpin=.35;invuln=0;player.x=W/2;player.y=H*.65;
   const e={x:W*.35,y:H*.45,r:16,hp:1,special:false,t:0,speed:38,shot:999,charge:999,kind:0,mode:'chase',vx:0,vy:0};enemies=king?[]:[e];boss=king?{x:W*.45,y:H*.3,r:48,hp:20,maxHp:20,t:0,shot:999}:null;gameScoring.updateHUD();gameExitDialogOpen=true;draw();return canvas.toDataURL();}'''
  matches=[];page.evaluate('artExit();gameWorlds.setTrialEnabled(false)');page.set_viewport_size({'width':915,'height':412})
  for area in range(4):
   for king in [False,True]:
    before=old.evaluate(fixture,{'area':area,'king':king});after=page.evaluate(fixture,{'area':area,'king':king});assert before==after,(area,king)
    matches.append({'region':area,'boss':king,'canvas_sha256':hashlib.sha256(after.encode()).hexdigest(),'pixel_equal':True})
  report['world1_exact_canvas_comparison']=matches;passed('All4 World1 normal scenes and4 boss scenes render byte-identical canvas PNGs to0cbfe82, proving old backgrounds/sprites/character drawing are unchanged.')

  for w,h in [(915,412),(800,360),(568,320)]:
   old.set_viewport_size({'width':w,'height':h});page.set_viewport_size({'width':w,'height':h});page.evaluate('artExit();gameWorlds.setTrialEnabled(true)');old.evaluate('started=false;menu.classList.remove("hidden");gameWorlds.setTrialEnabled(true)')
   for step in [1,5]:
    old.evaluate(fixture,{'area':4,'king':step==5});old.screenshot(path=str(args.artifacts/f'before-phase-{step}-{w}x{h}.png'))
    page.evaluate('step=>{artScene(step);artFreeze()}',step);page.screenshot(path=str(args.artifacts/f'after-phase-{step}-{w}x{h}.png'))
  reference_context.close();passed('Actual before/after snow normal/boss PNGs are captured at all3 landscape sizes from the baseline and new engine; no images are edited or composited.')

  # Real pause/menu/fullscreen and native animation-event captures.
  page.set_viewport_size({'width':915,'height':412});page.evaluate('artScene(5);gameExitDialogOpen=false;boss.shot=0;for(let n=0;n<180;n++)update(.01);artFreeze()');touch=Touch(context,page)
  page.screenshot(path=str(args.artifacts/'boss-attack.png'));page.evaluate('gameExitDialogOpen=false;artHit(boss);artFreeze()');page.screenshot(path=str(args.artifacts/'boss-hit.png'))
  page.evaluate('gameExitDialogOpen=false')
  touch.tap('#exitGame');expect(page.locator('#gameExitDialog')).to_be_visible();frozen=page.evaluate('gameSnowfield.snapshot()');page.wait_for_timeout(300);assert page.evaluate('gameSnowfield.snapshot()')==frozen
  assert page.evaluate('!!document.fullscreenElement');touch.tap('#gameExitCancel');page.wait_for_function('!gameExitDialogOpen')
  passed('Existing in-page exit modal freezes animation clock/frames exactly and preserves fullscreen; Continue resumes the same entities without resetting their poses.')
  page.evaluate('hp=0;update(0)');expect(page.locator('#gameOverOverlay')).to_be_visible();frozen=page.evaluate('gameSnowfield.snapshot()');page.wait_for_timeout(250);assert page.evaluate('gameSnowfield.snapshot()')==frozen
  expect(page.locator('#menu')).to_be_visible(timeout=4000);expect(page.locator('#selectionResult')).to_have_text('');assert page.evaluate('gameSnowfield.snapshot().clock===0&&gameSnowfield.snapshot().ghosts.length===0')
  passed('Game over still freezes immediately for3s, returns to clean selection and resets all art state; no animation continues behind the death overlay.')

  page.evaluate('gameWorlds.setDeveloperStart({enabled:true,regionId:4,phase:5});artScene(5);boss.hp=1;artHit(boss);gameSnowfield.tickFinale(0);artHoldFinale()');result=page.evaluate('gameScoring.getLastResult()');assert result['record']['outcome']=='clear' and result['record']['score']==2000
  page.wait_for_function('gameSnowfield.snapshot().finale.active');assert page.evaluate('!started&&boss===null&&getComputedStyle(menu).visibility==="hidden"&&!!document.fullscreenElement')
  page.screenshot(path=str(args.artifacts/'boss-fatal-hit.png'))
  page.evaluate('artReleaseFinale();gameSnowfield.tick(.331);artHoldFinale()')
  assert page.evaluate('gameSnowfield.snapshot().ghosts[0].pose.name')=='defeat';page.screenshot(path=str(args.artifacts/'boss-defeat.png'))
  page.evaluate('artReleaseFinale()')
  expect(page.locator('#menu')).to_be_visible(timeout=2500);expect(page.locator('#selectionResult')).to_contain_text('지역 테스트 완료')
  saved=page.evaluate('gameScoring.getLastResult()');assert saved==result and page.evaluate('!gameSnowfield.snapshot().finale.active&&gameSnowfield.snapshot().ghosts.length===0&&gameSnowfield.snapshot().clock===0')
  page.screenshot(path=str(args.artifacts/'snow-clear-after-defeat.png'))
  report['final_boss_result']=result
  passed('Real developer snow boss death awards a nonpersisted clear immediately once, removes combat, shows visual-only330ms hit+720ms defeat, then reveals the existing developer-clear selection with identical score/fullscreen.')
  page.evaluate('artScene(5);boss.hp=1;artHit(boss)');page.wait_for_function('gameSnowfield.snapshot().finale.active');page.evaluate('start(1);spawn=999;invuln=999');page.wait_for_timeout(1100)
  assert page.evaluate('started&&player.type===1&&stage===4&&menu.classList.contains("hidden")&&!gameSnowfield.snapshot().finale.active&&gameSnowfield.snapshot().ghosts.length===0')
  passed('A defensive restart during the art outro cancels it synchronously; no stale timer/class/corpse can cover or terminate the new game.')
  page.evaluate('artExit();gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true)')

  music=page.evaluate('''() => {artScene(1);gameAudio.tick(0);return {count:artAudio.length,media:document.getElementById('selectionBgm')!==null,profile:gameWorlds.musicProfile(stage)};}''')
  assert music=={'count':12,'media':True,'profile':0}
  page.wait_for_function('artAudio[0].currentTime>.02&&!artAudio[0].paused');old_time=page.evaluate('artAudio[0].currentTime');page.wait_for_timeout(120);assert page.evaluate('artAudio[0].currentTime')>old_time
  assert page.evaluate('artAudio.filter(a=>a.loop&&!a.paused).length===1')
  passed('Snow still uses the original forest BGM with increasing native playback time and one looping track; art adds no Audio objects, music files or control buttons.')
  assert not errors and not dialogs and not failed and not requests,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':requests}
  passed('No uncaught JS errors/native dialogs/failed resources/offline network requests occur across art, events, clear, pause, restart and reference comparisons.')
  browser.close()
finally:
 server.shutdown();server.server_close()
 if reference:reference.shutdown();reference.server_close()
 temp.cleanup()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
