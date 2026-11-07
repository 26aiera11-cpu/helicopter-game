from world_preservation import WORLD_ASSETS, assert_world_asset, without_world_source, without_world_ui
from controls_preservation import CONTROLS_ASSETS, assert_controls_asset, without_controls_ui
from item_monster_preservation import assert_item_asset
from scoring_preservation import SCORE_ASSETS,assert_scoring_asset,without_scoring_ui
"""Native19-track menu/game routing, trusted gesture, loop and retry checks."""
import argparse,base64,hashlib,json,re,shutil,subprocess,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright,expect
from selection_bgm_preservation import BGM_ASSET,BGM_SHA256,assert_selection_bgm_asset,without_selection_bgm_changes
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'standalone':args.standalone,'baseline':'dcd2fe20ced91447a5410e27f5929e421712f6c5','supplied_mp3_sha256':BGM_SHA256,'limits':['Native Chromium media playback clocks/states, not physical Galaxy Samsung Internet/Chrome or speaker listening.','Autoplay-rejection branch is separately simulated once; main playback/loop/transition tests use real native play().','Pages project-prefix routing is checked on HTTP locally; no GitHub Pages deployment is performed.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
source=(root/'index.html').read_text();assert without_selection_bgm_changes(source)==subprocess.check_output(['git','show','dcd2fe2:index.html'],cwd=root).decode()
data=assert_selection_bgm_asset()
for path in (root/'assets').rglob('*'):
 if path.is_file() and str(path.relative_to(root)) in WORLD_ASSETS:
     assert_world_asset(path);continue
 if path.is_file() and str(path.relative_to(root)) in CONTROLS_ASSETS:
     assert_controls_asset(path);continue
 if path.is_file() and str(path.relative_to(root)).startswith('assets/item_monster/'):
  assert_item_asset(path);continue
 if not path.is_file():continue
 name=str(path.relative_to(root))
 if name==BGM_ASSET:continue
 if name in SCORE_ASSETS:assert_scoring_asset(path);continue
 actual=without_scoring_ui(path.read_text(),name).encode() if name.endswith(('.js','.css')) else path.read_bytes()
 assert actual==subprocess.check_output(['git','show','dcd2fe2:'+name],cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S):subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('The supplied990740-byte MP3 matches its exact hash; only reviewed audio routing/hidden source differ from dcd2fe2, all earlier assets/gameplay and12WAV bytes remain unchanged, and syntax passes.')
probe='''(() => {
 const p=window.audioProbe={elements:[],events:[],overlaps:[],attempts:[],loops:[],maxActive:0,lastTime:0};
 const names=['stage_forest','stage_rock','stage_sea','stage_desert','boss_forest','boss_rock','boss_sea','boss_desert','warning','appear','hit','defeat'];
 p.active=()=>p.elements.filter(a=>a.loop&&!a.paused&&!a.ended);
 p.sample=reason=>{const active=p.active();p.maxActive=Math.max(p.maxActive,active.length);if(active.length>1)p.overlaps.push({reason,names:active.map(a=>a.probeName)})};
 p.register=(a,name)=>{if(p.elements.includes(a))return;a.probeName=name;p.elements.push(a);for(const type of ['play','playing','pause','waiting','stalled','ended','error'])a.addEventListener(type,()=>{p.events.push({name,type,time:a.currentTime,wall:performance.now()});p.sample(type)})};
 p.attach=()=>{for(const [id,name] of [['selectionBgm','selection'],['volcanoStageBgm','stage_volcano'],['volcanoBossBgm','boss_volcano'],['stormSkyStageBgm','stage_storm'],['stormSkyBossBgm','boss_storm'],['machineFortressStageBgm','stage_machine'],['machineFortressBossBgm','boss_machine']])p.register(document.getElementById(id),name)};
 const NativeAudio=window.Audio;window.Audio=new Proxy(NativeAudio,{construct(target,args){const a=new target(...args);p.register(a,names[p.elements.length]);return a}});
 const nativePlay=HTMLMediaElement.prototype.play;
 HTMLMediaElement.prototype.play=function(...args){p.attempts.push({name:this.probeName||this.id,wall:performance.now()});const result=nativePlay.apply(this,args);p.sample('play-call');return result;};
 const sample=()=>{p.sample('frame');const a=document.getElementById('selectionBgm');if(a){if(p.lastTime>a.duration-1&&a.currentTime<1&&!a.paused){const event={previous:p.lastTime,current:a.currentTime,wall:performance.now(),paused:a.paused,readyState:a.readyState};p.loops.push(event);p.loopRecovery=event;}
 if(p.loopRecovery&&a.readyState>=2&&a.currentTime>.03&&a.currentTime<1&&!a.paused){p.loopRecovery.recoveryMs=performance.now()-p.loopRecovery.wall;p.loopRecovery.resumedTime=a.currentTime;p.loopRecovery=null;}p.lastTime=a.currentTime;}requestAnimationFrame(sample)};requestAnimationFrame(sample);
})()'''
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path.split('?')[0].endswith('.mp3'):
   payload=Path(self.translate_path(self.path)).read_bytes();start=0;end=len(payload)-1
   requested=self.headers.get('Range');match=re.fullmatch(r'bytes=(\d+)-(\d*)',requested or '')
   if match:
    start=int(match[1]);end=min(end,int(match[2]) if match[2] else end)
   if start>end:
    self.send_response(416);self.end_headers();return
   self.send_response(206 if match else 200);self.send_header('Content-Type','audio/mpeg');self.send_header('Accept-Ranges','bytes');self.send_header('Content-Length',str(end-start+1))
   if match:self.send_header('Content-Range',f'bytes {start}-{end}/{len(payload)}')
   self.end_headers();self.wfile.write(payload[start:end+1]);return
  super().do_GET()
 def translate_path(self,path):
  if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
  return super().translate_path(path)
server=None
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True,offline=args.standalone)
  context.add_init_script(probe);errors=[];dialogs=[];responses=[];external=[]
  def observe(page):
   page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
   page.on('response',lambda r:responses.append({'url':r.url,'status':r.status}) if '.mp3' in r.url else None)
   page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  page=context.new_page();observe(page)
  html=(root/'dist/heli_trio_galaxy_test.html').read_text() if args.standalone else None
  if args.standalone:
   page.evaluate(probe);page.set_content(html,wait_until='load')
   embedded=re.search(r'<audio id="selectionBgm" src="data:audio/mpeg;base64,([A-Za-z0-9+/=]+)"',html);assert embedded and base64.b64decode(embedded[1])==data
  else:
   server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();page.goto(f'http://127.0.0.1:{server.server_port}/helicopter-game/',wait_until='load')
  page.evaluate('audioProbe.attach()');page.wait_for_function('audioProbe.elements.length===19&&audioProbe.elements.every(a=>!a.error&&a.readyState>=2&&a.duration>0)')
  page.wait_for_timeout(250);assert page.evaluate('audioProbe.active().length===0&&audioProbe.attempts.length===0&&selectionBgm.loop&&!selectionBgm.autoplay')
  report['native_duration']=page.evaluate('selectionBgm.duration')
  if not args.standalone:assert any(r['status'] in (200,206) and '/helicopter-game/assets/audio/' in r['url'] for r in responses)
  passed('No music/play attempts occur before user interaction;19 native media elements load, and the supplied MP3 resolves at the GitHub Pages project-prefix path (or byte-identical offline data URL).')
  def track(name):
   page.wait_for_function('name=>audioProbe.active().length===1&&audioProbe.active()[0].probeName===name&&audioProbe.active()[0].volume>0',arg=name)
   a=page.evaluate('audioProbe.active()[0].currentTime');page.wait_for_function('old=>audioProbe.active().length===1&&audioProbe.active()[0].currentTime>old+.07',arg=a)
  def start(kind=0):
   page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();page.wait_for_function('started');page.evaluate('invuln=999;spawn=999;transition=0')
  def exit_game():
   page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
  page.locator('.select-hit[data-heli="0"]').tap();track('selection');assert abs(page.evaluate('selectionBgm.volume')-.34)<1e-9
  before_time=page.evaluate('selectionBgm.currentTime');attempts=page.evaluate('audioProbe.attempts.filter(x=>x.name==="selection").length')
  for kind in [1,2,0,2,1]:page.locator(f'.select-hit[data-heli="{kind}"]').tap()
  assert page.evaluate('selectionBgm.currentTime')>=before_time and page.evaluate('audioProbe.attempts.filter(x=>x.name==="selection").length')==attempts
  passed('A trusted first touch starts native MP3 playback at volume0.34; changing characters preserves the same element/play request and advancing clock without rewinding.')
  # One complete natural loop in the online build; offline repeats at a real seek boundary.
  if not args.standalone:
   page.wait_for_function('audioProbe.loops.length>=1',timeout=40000)
   page.wait_for_function('audioProbe.loops.every(x=>x.recoveryMs!==undefined)',timeout=2000)
   track('selection')
  old_loops=page.evaluate('audioProbe.loops.length');page.evaluate('selectionBgm.currentTime=selectionBgm.duration-.25')
  page.wait_for_function('n=>audioProbe.loops.length>n',arg=old_loops,timeout=5000);track('selection')
  page.wait_for_function('audioProbe.loops.every(x=>x.recoveryMs!==undefined)',timeout=2000)
  report['loop_boundaries']=page.evaluate('audioProbe.loops')
  assert page.evaluate('audioProbe.loops.every(x=>!x.paused&&x.recoveryMs<1000)')
  passed('Native loop crosses the file end without a paused state and its playback clock recovers within1s (measured in the report); online includes one full natural30.9s pass, offline tests the real end boundary. Musical seam quality still needs listening.')
  page.locator('#selectionSettings').tap();expect(page.locator('#leaderboardDialog')).to_be_visible();page.locator('#leaderboardClose').tap();page.locator('#sfxToggle').tap();clock=page.evaluate('selectionBgm.currentTime');track('selection');assert page.evaluate('selectionBgm.currentTime')>clock
  page.locator('#sfxToggle').tap()
  page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement')
  start(0);track('stage_forest');assert page.evaluate('selectionBgm.paused&&selectionBgm.currentTime===0')
  assert page.evaluate('!!document.fullscreenElement')
  passed('SFX toggles leave selection music running; fullscreen/menu start stops and rewinds the MP3 before exactly one forest track starts, with native fullscreen retained.')
  page.evaluate('hp=0');page.wait_for_function('gameOverPending');expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_hidden();assert page.evaluate('audioProbe.active().length===0')
  page.wait_for_timeout(500);assert page.evaluate('audioProbe.active().length===0')
  expect(page.locator('#menu')).to_be_visible(timeout=4000);track('selection');expect(page.locator('#selectionResult')).to_have_text('')
  passed('Zero HP immediately silences all game BGM; the existing3s overlay stays silent, then selection music returns with clean selection UI and the original ON setting.')
  start(1);track('stage_forest');page.locator('#exitGame').tap();page.locator('#gameExitCancel').tap();track('stage_forest');assert page.evaluate('selectionBgm.paused&&!!document.fullscreenElement')
  exit_game();track('selection');assert page.evaluate('!!document.fullscreenElement')
  passed('The unchanged exit dialog cancels back to game music or confirms back to selection music, keeping fullscreen and avoiding browser dialogs.')
  page.locator('#musicToggle').tap();expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed','false');assert page.evaluate('audioProbe.active().length===0')
  start(2);page.wait_for_timeout(200);assert page.evaluate('audioProbe.active().length===0')
  page.evaluate('hp=0');page.wait_for_function('gameOverPending');expect(page.locator('#menu')).to_be_visible(timeout=4000);assert page.evaluate('audioProbe.active().length===0')
  expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed','false')
  page.locator('#musicToggle').tap();track('selection')
  passed('Music OFF immediately stops both scene types and persists through new-game/game-over return; ON resumes the current selection using the existing button, without altering SFX.')
  start(0);transitions=[]
  for region,name in enumerate(['forest','rock','sea','desert']):
   page.evaluate('region=>{stage=region;boss=null;phase=1}',region);track('stage_'+name)
   page.evaluate('phase=5;phaseKills=requiredKills;transition=0');page.wait_for_function('!!boss');track('boss_'+name);transitions.append(name)
   if region==0:
    page.evaluate('document.getElementById("musicToggle").click()');assert page.evaluate('audioProbe.active().length===0')
    page.evaluate('document.getElementById("musicToggle").click()');track('boss_forest')
  page.evaluate('boss=null;stage=3;phase=5;nextPhase()');expect(page.locator('#selectionResult')).to_contain_text('모든 지역 클리어');track('selection')
  assert page.evaluate('!gameAudioStarted&&!!document.fullscreenElement')
  report['stage_boss_switches']=transitions
  passed('All four stage/boss themes keep their switches, existing music toggle selects the current boss theme, and final-clear UI/effects path is retained; final return starts selection music after game music stops.')
  for index in range(12):
   start(index%3);track('stage_forest')
   if index%4==0:
    page.evaluate('hp=0');page.wait_for_function('gameOverPending');assert page.evaluate('audioProbe.active().length===0');expect(page.locator('#menu')).to_be_visible(timeout=4000)
   else:exit_game()
   track('selection')
  report['native_monitor']=page.evaluate('({elements:audioProbe.elements.length,maxActive:audioProbe.maxActive,overlaps:audioProbe.overlaps,attempts:audioProbe.attempts.length})')
  assert report['native_monitor']['elements']==19 and report['native_monitor']['maxActive']==1 and not report['native_monitor']['overlaps']
  passed('Twelve additional starts/returns across all characters reuse exactly19 media elements; synchronous play-call/event/frame monitoring detects no overlapping BGM or duplicate selection tracks.')
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('size=>W===size[0]&&H===size[1]',arg=[width,height]);track('selection');page.screenshot(path=str(args.artifacts/f'selection-music-{width}.png'))
  assert page.locator('#musicToggle').count()==1 and page.locator('#selectionBgm').count()==1
  passed('Three Galaxy landscape sizes retain the existing selection/fullscreen/touch layout and one music toggle; the hidden audio element adds no visible controls.')
  # Separate rejected-play branch: real browser playback resumes on the next real touch.
  retry=context.new_page();observe(retry)
  if args.standalone:retry.evaluate(probe);retry.set_content(html,wait_until='load')
  else:retry.goto(f'http://127.0.0.1:{server.server_port}/helicopter-game/',wait_until='load')
  retry.evaluate('''() => {audioProbe.attach();const native=HTMLMediaElement.prototype.play;window.blockSelectionPlay=true;window.rejectedCalls=0;HTMLMediaElement.prototype.play=function(...args){if(this.id==='selectionBgm'&&blockSelectionPlay){rejectedCalls++;return Promise.reject(new DOMException('Simulated policy denial','NotAllowedError'))}return native.apply(this,args)}}''')
  retry.locator('.select-hit[data-heli="0"]').tap();retry.wait_for_timeout(150)
  rejected=retry.evaluate('rejectedCalls');assert rejected>0 and retry.evaluate('selectionBgm.paused')
  retry.wait_for_timeout(250);assert retry.evaluate('rejectedCalls')==rejected
  retry.evaluate('blockSelectionPlay=false');retry.locator('.select-hit[data-heli="1"]').tap()
  retry.wait_for_function('!selectionBgm.paused&&selectionBgm.currentTime>.05')
  assert retry.evaluate('rejectedCalls')==rejected
  retry.evaluate('''() => {const native=HTMLMediaElement.prototype.play;window.blockStage=true;window.stageRejected=0;HTMLMediaElement.prototype.play=function(...args){if(this===audioProbe.elements[0]&&blockStage){stageRejected++;return Promise.reject(new DOMException('Simulated stage denial','NotAllowedError'))}return native.apply(this,args)}}''')
  retry.locator('#startSelected').tap();retry.wait_for_function('started');retry.evaluate('invuln=999;spawn=999');retry.wait_for_timeout(180)
  stageRejected=retry.evaluate('stageRejected');assert stageRejected>0 and retry.evaluate('audioProbe.active().length===0')
  retry.wait_for_timeout(250);assert retry.evaluate('stageRejected')==stageRejected
  retry.evaluate('blockStage=false');retry.locator('#fire').tap();retry.wait_for_function('audioProbe.active().length===1&&audioProbe.active()[0].probeName==="stage_forest"&&audioProbe.active()[0].currentTime>.05')
  passed('A separately denied stage play stays silent without per-frame retries; the next real gameplay touch resumes the native stage track without overlapping selection music.')
  retry.close()
  passed('A simulated rejected play promise is caught without unhandled errors, and a subsequent trusted click/touch retries native playback using the same audio element.')
  assert not errors and not dialogs and not external,(errors,dialogs,external)
  report['mp3_responses']=responses;report['external_requests']=external
  passed('No uncaught JavaScript errors, browser dialogs or external requests in standalone mode; online MP3 requests return200/206 under the project prefix.')
  browser.close()
finally:
 if server:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
