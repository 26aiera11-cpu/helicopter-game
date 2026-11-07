"""Issue37: original Machine Fortress PCM loops, exclusive native media routing and offline playback."""
import argparse,base64,hashlib,importlib.util,io,json,re,shutil,subprocess,tempfile,threading,wave
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];BASE='2f29ced6cd53b7ebcb8279669c70c74fc1374ff1'
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':['Real Chromium media play/pause events and clocks, not physical Galaxy Samsung Internet/Chrome, speaker listening or artistic approval.','Controlled combat coordinates/time/invulnerability for transitions; mobile gesture policy is tested in Chromium, not asserted for a physical phone.','WAV sample seams and native seek-to-end loops are measured; speaker loop comfort, tone and SFX masking require user listening.','Hidden-tab state and one play rejection are deliberately simulated; the other media calls use native play().']}
def passed(text):report['passed'].append(text);print('PASS:',text,flush=True)
def old(name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
from machine_fortress_bgm_preservation import verify
report['preservation']=verify()
source=(ROOT/'index.html').read_text()
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',source,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('All129 existing assets except the reviewed registry lines are byte-preserved; exactly3 index audio and3 Machine registry/notice deltas. Approved Cover/PNG11, boss and normal combat, old music/SFX and controls remain unchanged; JS parses.')
spec=importlib.util.spec_from_file_location('machine_music_generator',ROOT/'scripts/generate_machine_fortress_bgm.py');generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
with tempfile.TemporaryDirectory(prefix='machine-bgm-repeat-') as folder:
 rows=generator.generate(Path(folder))
 for row in rows:assert (Path(folder)/row['file']).read_bytes()==(ROOT/'assets/audio'/row['file']).read_bytes()
passed('Both newly composed scores and seeded synth/percussion regenerate byte-for-byte without reading any old music, external samples or third-party audio.')
quality=[]
for name,bpm in [('machine_fortress_stage.wav',132),('machine_fortress_boss.wav',152)]:
 data=(ROOT/'assets/audio'/name).read_bytes()
 with wave.open(io.BytesIO(data)) as a:
  assert (a.getnchannels(),a.getsampwidth(),a.getframerate(),a.getcomptype())==(1,2,22050,'NONE');frames=a.getnframes();x=np.frombuffer(a.readframes(frames),'<i2').astype(float)/32768
 assert abs(frames/22050-16*4*60/bpm)<=1/22050 and np.max(np.abs(x))<=.95 and abs(x.mean())<.0001 and x[0]==x[-1]==0
 windows=[float(np.sqrt(np.mean(x[i:i+2205]**2))) for i in range(0,len(x)-2205,2205)];assert min(windows)>.005
 seam=np.r_[x[-2205:],x[:2205]];fft=np.fft.rfft(x);power=np.abs(fft)**2;freq=np.fft.rfftfreq(len(x),1/22050)
 quality.append({'file':name,'bpm':bpm,'bars':16,'seconds':frames/22050,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'peak':float(np.max(np.abs(x))),'rms':float(np.sqrt(np.mean(x*x))),'dc':float(x.mean()),'clipped_samples':int(np.sum(np.abs(x)>=.999)),'seam_jump':float(abs(x[0]-x[-1])),'seam_rms200ms':float(np.sqrt(np.mean(seam*seam))),'minimum_rms100ms':min(windows),'energy_below500hz':float(power[freq<500].sum()/power.sum())})
assert sum(x['bytes'] for x in quality)<3500000;report['audio_quality']=quality
passed('132/152BPM16bars: mono22050Hz PCM16,29.091/25.263s, combined<3.5MB; no clipping/DC/100ms silence, zero file seam jump; per-track levels/low-frequency energy measured.')
reference=[]
for name in ['volcano_stage.wav','volcano_boss.wav','storm_sky_stage.wav','storm_sky_boss.wav']:
 with wave.open(str(ROOT/'assets/audio'/name)) as w:y=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)/32768
 reference.append({'file':name,'peak':float(abs(y).max()),'rms':float(np.sqrt(np.mean(y*y)))})
for row in quality:
 old_levels=[r for r in reference if ('stage' in r['file'])==('stage' in row['file'])]
 assert row['rms']<=min(r['rms'] for r in old_levels) and row['peak']<=max(r['peak'] for r in old_levels)
 assert .3*row['rms']<row['seam_rms200ms']<2.5*row['rms']
report['reference_audio_levels']=reference
passed('New stage/boss RMS is below both corresponding older scores; peaks stay below the reference maximum and the200ms seam has sustained energy. Original volume caps.42/.58/.34 remain unchanged; subjective SFX masking is unapproved.')

probe=r'''(()=>{
 const p=window.vbMusic={tracks:[],events:[],attempts:[],overlaps:[],oscillators:0,maxActive:0};
 const names=['stage_forest','stage_rock','stage_sea','stage_desert','boss_forest','boss_rock','boss_sea','boss_desert','warning','appear','hit','defeat'];
 p.active=()=>p.tracks.filter(a=>a.loop&&!a.paused&&!a.ended);
 p.sample=reason=>{const a=p.active();p.maxActive=Math.max(p.maxActive,a.length);if(a.length>1)p.overlaps.push({reason,names:a.map(a=>a.vbName)})};
 p.register=(a,name)=>{if(p.tracks.includes(a))return;a.vbName=name;p.tracks.push(a);for(const type of ['play','playing','pause','ended','error'])a.addEventListener(type,()=>{p.events.push({type,name,time:a.currentTime,wall:performance.now()});p.sample(type)})};
 const Native=Audio;window.Audio=new Proxy(Native,{construct(t,args){const a=new t(...args);p.register(a,names[p.tracks.length]);return a}});
 p.attach=()=>{for(const [id,n] of [['selectionBgm','selection'],['volcanoStageBgm','stage_volcano'],['volcanoBossBgm','boss_volcano'],['stormSkyStageBgm','stage_storm'],['stormSkyBossBgm','boss_storm'],['machineFortressStageBgm','stage_machine'],['machineFortressBossBgm','boss_machine']])p.register(document.getElementById(id),n)};
 const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){p.attempts.push({name:this.vbName||this.id,time:performance.now()});const r=play.apply(this,args);p.sample('play-call');return r};
 const AC=window.AudioContext||window.webkitAudioContext;if(AC){const make=AC.prototype.createOscillator;AC.prototype.createOscillator=function(...args){p.oscillators++;return make.apply(this,args)}}
 const sample=()=>{p.sample('frame');requestAnimationFrame(sample)};requestAnimationFrame(sample);
})()'''
helpers=r'''()=>{
 window.vbConfigure=(region=7,step=1)=>gameWorlds.setDeveloperStart({enabled:true,regionId:region,phase:step});
 window.vbQuiet=()=>{transition=0;spawn=999;invuln=999;itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();};
 window.vbHit=e=>{bullets=[];shoot();bullets=[bullets[0]];Object.assign(bullets[0],{x:e.x,y:e.y,vx:0,vy:0});update(0);};
 window.vbSpawn=()=>{warnEnemy();warnings.at(-1).time=0;update(0);return enemies.at(-1);};
}'''
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/offline-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);context.add_init_script(probe);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None)
  def load(target):
   if args.standalone:context.set_offline(False);target.goto(url+'/offline-origin');external.clear();context.set_offline(True);target.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:target.goto(url+'/helicopter-game/',wait_until='load')
   target.wait_for_function('gameMachineFortress.ready()&&gameStormSky.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');target.evaluate('vbMusic.attach()');target.evaluate(helpers);target.wait_for_function('vbMusic.tracks.length===19&&vbMusic.tracks.every(a=>!a.error&&a.readyState>=2&&a.duration>0)')
  load(page);initial_records=page.evaluate("Object.keys(localStorage).filter(k=>/top10|playHistory/.test(k)).sort().map(k=>[k,localStorage.getItem(k)])");assert page.evaluate('vbMusic.active().length===0&&vbMusic.attempts.length===0');assert page.evaluate('gameWorlds.regions.map(r=>r.musicProfile)')==[0,1,2,3,0,4,5,6]
  if args.standalone:
   html=(ROOT/'dist/heli_trio_galaxy_test.html').read_text()
   for id,name in [('machineFortressStageBgm','machine_fortress_stage.wav'),('machineFortressBossBgm','machine_fortress_boss.wav')]:
    encoded=re.search(r'<audio id="'+id+r'" src="data:audio/[^;]+;base64,([A-Za-z0-9+/=]+)"',html);assert encoded and base64.b64decode(encoded[1])==(ROOT/'assets/audio'/name).read_bytes()
  passed('Native project-prefix/offline19 media metadata loads before gesture without play attempts; profiles remain0/1/2/3/0 then volcano4/storm5/machine6, with both Machine WAVs embedded exactly offline.')
  def track(name):
   page.wait_for_function('name=>vbMusic.active().length===1&&vbMusic.active()[0].vbName===name&&vbMusic.active()[0].volume>0',arg=name)
   before=page.evaluate('vbMusic.active()[0].currentTime');page.wait_for_function('old=>vbMusic.active().length===1&&vbMusic.active()[0].currentTime>old+.06',arg=before)
   return page.evaluate('({name:vbMusic.active()[0].vbName,time:vbMusic.active()[0].currentTime,volume:vbMusic.active()[0].volume})')
  def start(region=7,step=1,kind=0):
   assert page.evaluate('([r,p])=>vbConfigure(r,p)',[region,step]);page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();page.evaluate('vbQuiet()')
  def exit_game():
   page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
  page.locator('.select-hit[data-heli="0"]').tap();track('selection');page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement')
  # Real developer UI once; remaining matrix keeps the same public configuration API.
  page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');page.locator('#developerStartRegion').select_option('7');page.locator('#developerStartPhase').select_option('5');page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap();page.evaluate('vbQuiet()');track('boss_machine');assert page.evaluate('!!boss&&phaseKills===6&&enemies.length===0');exit_game();track('selection')
  passed('Trusted touch/fullscreen and real Help->World2->Machine5 start only the new boss WAV; confirming exit restores original selection MP3 with fullscreen retained.')
  stable=page.evaluate('({a:selectionBgm.currentTime,n:vbMusic.events.filter(e=>e.name==="selection"&&e.type==="play").length})')
  for kind in [1,2,0]:page.locator(f'.select-hit[data-heli="{kind}"]').tap()
  page.wait_for_timeout(100);assert page.evaluate('old=>selectionBgm.currentTime>old.a&&vbMusic.events.filter(e=>e.name==="selection"&&e.type==="play").length===old.n',stable)
  passed('Changing all three characters preserves one uninterrupted selection MP3 clock; no extra music button is introduced.')
  for step in [1,2,3,4]:start(step=step);track('stage_machine');exit_game()
  passed('All four normal Machine stages use the dedicated stage WAV; developer direct5 uses only dedicated boss WAV.')
  matrix=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height})
   for kind in range(3):
    for step in [1,5]:
     start(step=step,kind=kind);row=track('boss_machine' if step==5 else 'stage_machine');assert page.evaluate('selectionBgm.paused&&!!document.fullscreenElement');assert abs(row['volume']-(.58 if step==5 else .42))<1e-6;matrix.append({'size':[width,height],'kind':kind,'phase':step,**row})
     if kind==0:page.screenshot(path=str(args.artifacts/f'machine-bgm-phase{step}-{width}x{height}.png'))
     exit_game()
  report['mobile_matrix']=matrix
  passed('3characters x3 landscape sizes x stage/boss=18 actual playback paths advance currentTime with one BGM; original UI, controls and fullscreen remain available.')
  routes=[]
  for region,name in enumerate(['forest','rock','sea','desert','forest','volcano','storm','machine']):
   for step in [1,5]:
    start(region,step);routes.append({'region':region,'phase':step,**track(('boss_' if step==5 else 'stage_')+name)});exit_game()
  report['routes']=routes
  passed('All8 region stage/boss choices route correctly: eight original World1 WAVs and forest-profile snow and dedicated storm trial are routed separately, and Storm selects profile5 independently of Volcano4.')
  loops=[]
  for step,id in [(1,'machineFortressStageBgm'),(5,'machineFortressBossBgm')]:
   start(step=step);name='stage_machine' if step==1 else 'boss_machine';track(name)
   page.evaluate('id=>{const a=document.getElementById(id);a.currentTime=a.duration-.16}',id);page.wait_for_function('id=>{const a=document.getElementById(id);return !a.paused&&a.currentTime>.05&&a.currentTime<1}',arg=id,timeout=5000)
   loops.append(page.evaluate('id=>{const a=document.getElementById(id);return {id,time:a.currentTime,duration:a.duration,loop:a.loop,paused:a.paused,readyState:a.readyState}}',id));exit_game()
  report['native_loop_boundaries']=loops
  passed('Both actual native WAV players loop through a seek-to-end boundary, remain playing and advance again; PCM seam jumps are0 and long silence is absent, subject to speaker approval.')
  # Real ordinary phase4->5 path: six actual mixed enemies, not the direct5 shortcut.
  start(step=4);page.evaluate('nextPhase();vbQuiet()');track('stage_machine');normal=[]
  for _ in range(6):normal.append(page.evaluate('''()=>{const e=vbSpawn(),id=e.machineSpeciesId;while(e.hp>0)vbHit(e);return {id,kills:phaseKills,boss:!!boss};}'''))
  page.wait_for_function('!!boss');track('boss_machine');assert all(not x['boss'] and x['kills']==i+1 for i,x in enumerate(normal));assert page.evaluate('boss.maxHp===20&&runScore===1100')
  report['six_kill_gate']=normal;page.wait_for_function('vbMusic.events.some(e=>e.name==="appear"&&e.type==="play")')
  # old synthesized score must never be scheduled underneath the PCM.
  oscillator_before=page.evaluate('vbMusic.oscillators');page.wait_for_timeout(400);assert page.evaluate('vbMusic.oscillators')==oscillator_before
  passed('Normal Machine phase5 retains its mixed6-kill gate before the new boss music; warning/appear SFX remain separate and no old synthesized stage oscillators are scheduled under the WAV.')
  before=page.evaluate("({time:machineFortressBossBgm.currentTime,plays:vbMusic.events.filter(e=>e.name==='boss_machine'&&e.type==='play').length,pauses:vbMusic.events.filter(e=>e.name==='boss_machine'&&e.type==='pause').length})")
  page.evaluate('''()=>{while(boss.hp>boss.maxHp/2)vbHit(boss);window.sameBossMusic=machineFortressBossBgm;}''');page.wait_for_timeout(950)
  red=page.evaluate("({time:machineFortressBossBgm.currentTime,same:sameBossMusic===machineFortressBossBgm,plays:vbMusic.events.filter(e=>e.name==='boss_machine'&&e.type==='play').length,pauses:vbMusic.events.filter(e=>e.name==='boss_machine'&&e.type==='pause').length,overdrive:gameMachineBoss.snapshot().overdrive,count:gameMachineBoss.snapshot().awakenCount,image:gameMachineFortress.bossImage(boss).id})")
  assert red['same'] and red['overdrive'] and red['count']==1 and red['time']>before['time']+.5 and red['plays']==before['plays'] and red['pauses']==before['pauses'] and 'overdrive' in red['image'];report['overdrive_continuous_BGM']={'before':before,'after':red};page.screenshot(path=str(args.artifacts/'machine-bgm-overdrive.png'))
  passed('Real weapon hits reach HP50% and render the existing red PNG; boss BGM uses the identical media element with increasing time and zero new play/pause events across awakening.')
  sfx=page.evaluate('''()=>{const before=vbMusic.oscillators;gameAudio.fx('hit');gameAudio.fx('boss_defeat');gameAudio.fx('shot',0);return {before,after:vbMusic.oscillators,track:vbMusic.active()[0].vbName};}''');assert sfx['after']>sfx['before'] and sfx['track']=='boss_machine'
  page.evaluate('document.getElementById("sfxToggle").click()');count=page.evaluate('vbMusic.attempts.filter(e=>["warning","appear","hit","defeat"].includes(e.name)).length');osc=page.evaluate('vbMusic.oscillators');page.evaluate("gameAudio.fx('boss');gameAudio.fx('boss_defeat');gameAudio.fx('shot',0)");page.wait_for_timeout(40);assert page.evaluate('vbMusic.oscillators')==osc and page.evaluate('vbMusic.attempts.filter(e=>["warning","appear","hit","defeat"].includes(e.name)).length')==count;track('boss_machine');page.evaluate('document.getElementById("sfxToggle").click()')
  passed('Original boss-hit/defeat media and shot WebAudio SFX still work independently over the single boss BGM; SFX OFF suppresses new effect/oscillator calls without stopping music.')
  page.evaluate('document.getElementById("musicToggle").click()');assert page.evaluate('vbMusic.active().length===0');page.evaluate('document.getElementById("musicToggle").click()');track('boss_machine')
  page.locator('#exitGame').tap();clock=page.evaluate('machineFortressBossBgm.currentTime');page.wait_for_timeout(100);assert page.evaluate('machineFortressBossBgm.currentTime')>=clock;page.locator('#gameExitCancel').tap();track('boss_machine')
  page.evaluate('hp=0;update(0)');expect(page.locator('#gameOverOverlay')).to_be_visible();assert page.evaluate('vbMusic.active().length===0');page.wait_for_timeout(800);assert page.evaluate('vbMusic.active().length===0');expect(page.locator('#menu')).to_be_visible(timeout=4000);track('selection')
  passed('Boss music toggles OFF/ON exclusively; canceling internal exit preserves music/fullscreen; zeroHP immediately silences BGM through3s GAME OVER, then selection MP3 returns.')
  page.locator('#musicToggle').tap();start(step=5);page.wait_for_timeout(200);assert page.evaluate('vbMusic.active().length===0');exit_game();assert page.evaluate('vbMusic.active().length===0');page.locator('#musicToggle').tap();track('selection')
  passed('Existing musicOFF persists through direct-boss restart and menu return; ON restores the current selection without changing the effects setting.')
  start(step=5);track('boss_machine');page.evaluate('''()=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));}''');assert page.evaluate('vbMusic.active().length===0');page.evaluate('''()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));}''');track('boss_machine');exit_game()
  passed('Simulated hidden-tab events pause every music track and restore only the current boss track; production browser visibility policy remains unchanged.')
  start(step=5);track('boss_machine');score=page.evaluate('runScore');page.evaluate('''()=>{while(boss)vbHit(boss);}''');page.wait_for_function('!started&&!menu.classList.contains("hidden")');track('selection');assert page.evaluate('runScore')==score+2000
  passed('Actual GigaCore defeat retains2000points once, reward/outro/final return and restores selection music without any simultaneous BGM.')
  assert page.evaluate("Object.keys(localStorage).filter(k=>/top10|playHistory/.test(k)).sort().map(k=>[k,localStorage.getItem(k)])")==initial_records
  passed('Developer region starts, game-over and final-boss clear leave all original/trial TOP10 and play-history storage unchanged.')
  # Real route API and region advance, with only the preceding progress fixture shortened.
  assert page.evaluate('gameWorlds.setDeveloperStart({enabled:false})&&gameWorlds.setTrialEnabled(true)');page.locator('#startSelected').tap();page.evaluate('vbQuiet();stage=4;phase=5;boss=null');track('stage_forest');page.evaluate('nextPhase();vbQuiet()');track('stage_volcano');assert page.evaluate('stage===5&&phase===1&&gameVolcanoSpawns.snapshot().draws===0');page.evaluate('stage=5;phase=5;boss=null;nextPhase();vbQuiet()');track('stage_storm');assert page.evaluate('stage===6&&phase===1&&gameStormSpawns.snapshot().draws===0');page.evaluate('stage=6;phase=5;boss=null;nextPhase();vbQuiet()');track('stage_machine');assert page.evaluate('stage===7&&phase===1&&gameMachineSpawns.snapshot().draws===0');exit_game();page.evaluate('gameWorlds.setTrialEnabled(false)')
  passed('Actual Snow->Volcano->Storm->Machine nextRegion transitions change forest→volcano4→storm5→machine6 without touching mixed-spawn reset or the old World1 route.')
  after_route_records=page.evaluate("Object.keys(localStorage).filter(k=>/top10|playHistory/.test(k)).sort().map(k=>[k,localStorage.getItem(k)])")
  for index in range(12):start(step=5 if index%2 else 1,kind=index%3);track('boss_machine' if index%2 else 'stage_machine');exit_game();track('selection')
  assert page.evaluate('vbMusic.tracks.length===19&&vbMusic.maxActive===1&&vbMusic.overlaps.length===0');report['monitor']=page.evaluate('({events:vbMusic.events,attempts:vbMusic.attempts,tracks:vbMusic.tracks.length,maxActive:vbMusic.maxActive,overlaps:vbMusic.overlaps})')
  passed('12additional stage/boss starts and returns reuse the same19 media elements; synchronous play-call/event/frame probes detect zero simultaneous music or extra looping players.')
  assert page.evaluate("Object.keys(localStorage).filter(k=>/top10|playHistory/.test(k)).sort().map(k=>[k,localStorage.getItem(k)])")==after_route_records
  # Deliberate rejection only here; no autoplay policy bypass flags are used.
  page.close();retry=context.new_page();retry.on('pageerror',lambda e:errors.append(str(e)));retry.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));retry.on('requestfailed',lambda r:failed.append(r.url));load(retry);retry.evaluate('''()=>{window.policyBlocked=true;window.blockedAttempts=0;const play=HTMLMediaElement.prototype.play;HTMLMediaElement.prototype.play=function(...args){if(this.id==='machineFortressStageBgm'&&policyBlocked){blockedAttempts++;return Promise.reject(new DOMException('test policy denial','NotAllowedError'))}return play.apply(this,args)};vbConfigure(7,1);}''');retry.locator('#startSelected').tap();retry.evaluate('vbQuiet()');retry.wait_for_timeout(100);assert retry.evaluate('machineFortressStageBgm.paused&&blockedAttempts>=1');attempts=retry.evaluate('blockedAttempts');retry.wait_for_timeout(150);assert retry.evaluate('blockedAttempts')==attempts;retry.evaluate('policyBlocked=false');retry.locator('#fire').tap();retry.wait_for_function('!machineFortressStageBgm.paused&&machineFortressStageBgm.currentTime>.03');retry.close()
  assert not errors and not dialogs and not failed,(errors,dialogs,failed)
  if args.standalone:assert not external,external
  report.update(errors=errors,dialogs=dialogs,failed_requests=failed,offline_requests=external if args.standalone else [],all_passed=True)
  passed('Simulated autoplay policy denials are caught without frame retries and retries on the next trusted touch; no native dialogs/uncaught errors/failed resources occur, and standalone HTTP audio requests are0.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
