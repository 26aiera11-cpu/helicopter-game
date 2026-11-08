"""Focused app-asset/browser contract smoke; not a physical WebView/sensor test."""
import argparse,base64,hashlib,json,mimetypes,re,shutil,subprocess,time
from pathlib import Path
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'android-web';BASE='6547958555ce0b04597a113ec25ae4f1d83340c0'
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();a.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'limits':['Chromium touch/media/storage checks use an Android bridge mock, not a real WebView, physical sensor, Android system bars or hardware back button.','Random enemy spawns are disabled only in touch/audio/lifecycle QA so unrelated combat cannot end the run while media is loading. This is not combat/balance evidence.','No balance simulation or40-stage replay. Physical Galaxy approval remains required.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
start=time.monotonic()
receipt=json.loads((WEB/'build-receipt.json').read_text())
for name,expected in receipt['source_sha256'].items():
 data=(ROOT/name).read_bytes();assert hashlib.sha256(data).hexdigest()==expected
 assert data==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
page_text=(WEB/'index.html').read_text()
restored=page_text.replace('<script src="app-shell/capacitor-core.js"></script><script src="app-shell/bootstrap.js"></script>','',1).replace('<link rel="stylesheet" href="app-shell/android.css"><script src="app-shell/android.js"></script>','',1)
for name,info in receipt['embedded_files'].items():
 data=(WEB/name).read_bytes();assert hashlib.sha256(data).hexdigest()==info['sha256']
 restored=restored.replace(name,'data:'+info['mime']+';base64,'+base64.b64encode(data).decode())
assert restored==(ROOT/'index.html').read_text()
for name in receipt['source_sha256']:
 if name.startswith('assets/'):assert (WEB/name).read_bytes()==(ROOT/name).read_bytes()
for file in (ROOT/'app-shell').glob('*.js'):subprocess.run(['node','--check',str(file)],check=True,capture_output=True)
passed('Original index/131 game assets equal6547958;83 extracted media bytes reverse exactly to original HTML; app JavaScript parses; no game balance or graphics changes.')
mock=r'''window.nativeMock={events:{},starts:0,stops:0,exits:0,available:true};
for(const name of ['deviceorientation','devicemotion'])window.addEventListener(name,event=>{if(nativeMock.blockWebSensors)event.stopImmediatePropagation();},true);
window.testCreatedAudio=[];const RealAudio=Audio;
window.Audio=new Proxy(RealAudio,{construct(target,args){const audio=new target(...args);testCreatedAudio.push(audio);return audio;}});
window.testAudio=()=>[...new Set([...document.querySelectorAll('audio'),...testCreatedAudio])];
window.Capacitor={isNativePlatform:()=>true,getPlatform:()=>"android",registerPlugin:name=>({
 addListener:async(event,callback)=>{nativeMock.events[event]=callback;return {remove:async()=>{delete nativeMock.events[event]}};},
 start:async()=>{nativeMock.starts++;return {available:nativeMock.available}},stop:async()=>{nativeMock.stops++},exitApp:async()=>{nativeMock.exits++}
})};'''
external=[];missing=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
 context.set_offline(True)
 def route_handler(route):
  request=route.request;url=urlsplit(request.url)
  if url.hostname!='localhost':external.append(request.url);route.abort();return
  rel=unquote(url.path).lstrip('/') or 'index.html';path=(WEB/rel).resolve()
  if not path.is_relative_to(WEB.resolve()) or not path.is_file():missing.append(rel);route.fulfill(status=404,body='');return
  data=path.read_bytes()
  if rel=='app-shell/capacitor-core.js':data+=mock.encode()
  headers={'Content-Type':mimetypes.guess_type(path.name)[0] or 'application/octet-stream'}
  range_header=request.headers.get('range')
  if range_header:
   m=re.match(r'bytes=(\d+)-(\d*)',range_header);left=int(m[1]);right=int(m[2]) if m[2] else len(data)-1
   headers['Content-Range']=f'bytes {left}-{right}/{len(data)}';route.fulfill(status=206,body=data[left:right+1],headers=headers)
  else:route.fulfill(status=200,body=data,headers=headers)
 context.route('**/*',route_handler)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 try:
  page.goto('https://localhost/',wait_until='load');page.wait_for_function('gameMachineFortress.ready()&&gameVolcano.ready()&&gameSnowfield.ready()&&gameStormSky.ready()&&itemMonsters.ready()')
  page.wait_for_function("testAudio().length===19&&testAudio().every(a=>a.readyState>=2&&!a.error)")
  page.locator('#startSelected').tap();page.wait_for_function('started&&heliAndroidState.native')
  page.evaluate('spawn=999;warnings=[];enemies=[];enemyBullets=[]')
  page.wait_for_function('!!document.fullscreenElement');page.wait_for_timeout(100)
  playing="testAudio().filter(a=>a.loop&&!a.paused&&!a.ended).length"
  page.wait_for_function(playing+'===1');before=page.evaluate("testAudio().find(a=>a.loop&&!a.paused).currentTime");page.wait_for_timeout(200)
  assert page.evaluate("testAudio().find(a=>a.loop&&!a.paused).currentTime")>before
  assert page.evaluate('started&&!gameOverPending')
  passed('Exact app webDir runs with network disabled via local asset interception; actual native media decoder advances one stage BGM after trusted start.')
  # Trusted three-contact input; each control owns a separate pointer.
  cdp=context.new_cdp_session(page)
  page.evaluate('''()=>{window.androidTouchTrace=[];for(const name of ['pointerdown','pointermove','pointerup','pointercancel','blur','visibilitychange'])window.addEventListener(name,e=>androidTouchTrace.push({name,target:e.target.id||e.target.tagName,x:e.clientX,y:e.clientY,pointer:e.pointerId,started,hidden:document.hidden,controls:gameControls.snapshot()}),true);}''')
  def point(i,x,y):return {'id':i,'x':x,'y':y}
  def center(sel):r=page.locator(sel).bounding_box();return r['x']+r['width']/2,r['y']+r['height']/2
  jx,jy=center('#rotationJoystick');fx,fy=center('#fire');points=[point(11,jx,jy),point(12,600,200),point(13,fx,fy)]
  active=[]
  for value in points:
   active.append(value);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':active})
  points[0]['x']+=30;points[1]['x']+=15
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':points});page.wait_for_timeout(80)
  touch_state=page.evaluate('''points=>({fire:keys.fire,rotation:gameControls.rotation(),controls:gameControls.snapshot(),native:heliAndroidState,started,gameOverPending,menuHidden:menu.classList.contains('hidden'),hidden:document.hidden,viewport:{w:innerWidth,h:innerHeight,scale:visualViewport.scale},points,hits:points.map(p=>document.elementsFromPoint(p.x,p.y).slice(0,4).map(e=>e.id||e.tagName)),trace:androidTouchTrace,dialogs:[...document.querySelectorAll("dialog[open]")].map(x=>x.id)})''',points)
  report['touch_state']=touch_state
  if not (touch_state['fire'] and abs(touch_state['rotation'])>0):page.screenshot(path=str(a.artifacts/'touch-failure.png'))
  assert touch_state['fire'] and abs(touch_state['rotation'])>0,touch_state
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(40);assert page.evaluate('!keys.fire&&gameControls.rotation()===0')
  page.evaluate("nativeMock.events.backButton({})");expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitCancel').tap();assert page.evaluate('started&&!gameExitDialogOpen')
  passed('Trusted drag+joystick+fire multitouch releases cleanly; native-back callback opens the existing exit dialog and Cancel preserves the game.')
  page.locator('#sensor').tap();page.wait_for_function('nativeMock.starts>0||lastSensor>0',timeout=4000)
  sensor_state=page.evaluate('({sensorOn,lastSensor,sensorKind,status:sensorStatus.textContent,starts:nativeMock.starts,native:heliAndroidState})');report['initial_sensor_provider']=sensor_state
  assert sensor_state['sensorOn'],sensor_state
  if sensor_state['starts']==0:
   assert sensor_state['lastSensor']>0,sensor_state
   # Test the no-Web-signal case separately; production still prefers web events.
   page.evaluate('nativeMock.blockWebSensors=true');page.wait_for_timeout(1200);page.locator('#sensor').tap()
  page.wait_for_function('nativeMock.starts>0',timeout=4000)
  page.evaluate("nativeMock.events.gravity({x:0,y:0,z:9.81,rotation:90});nativeMock.events.gravity({x:1,y:2,z:9.81,rotation:90})")
  tilt_state=page.evaluate('({x:tilt.x,y:tilt.y})');assert abs(tilt_state['x']-6/17)<1e-8 and abs(tilt_state['y']+3/17)<1e-8,tilt_state
  report['gravity_coordinate_contract']=tilt_state
  combo=[point(41,jx,jy),point(42,fx,fy)];held=[]
  for value in combo:held.append(value);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':held})
  combo[0]['x']+=25;cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':combo})
  page.evaluate('nativeMock.events.gravity({x:1,y:2,z:9.81,rotation:90})')
  assert page.evaluate('keys.fire&&gameControls.rotation()>0&&Math.abs(tilt.x)>0')
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});report['gravity_rotation_fire_combined']=True
  passed('WebView-no-signal fallback requests native gravity only after user sensor enable; raw x/y uses unchanged x3 and /17 math plus native90-degree display rotation. Physical signs/sensitivity remain unverified.')
  # Original music controls belong to selection; use the real exit/start flow.
  def music_then_start():
   page.evaluate('nativeMock.events.backButton({})');expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
   page.locator('#musicToggle').tap();page.locator('#startSelected').tap();page.wait_for_function('started');page.evaluate('spawn=999;warnings=[];enemies=[];enemyBullets=[]')
  music_then_start();assert page.locator('#musicToggle').get_attribute('aria-pressed')=='false'
  page.evaluate('nativeMock.events.appStateChange({isActive:false})');page.wait_for_function('heliAndroidState.paused')
  snapshot="JSON.stringify({player,worldScroll,rotorSpin,hp,runScore,stage,phase})";frozen=page.evaluate(snapshot);page.wait_for_timeout(200);assert page.evaluate(snapshot)==frozen
  assert page.evaluate("testAudio().every(a=>a.paused)")
  page.evaluate('nativeMock.events.appStateChange({isActive:true})');expect(page.locator('#nativeResumeDialog')).to_be_visible();page.wait_for_timeout(100);assert page.evaluate(snapshot)==frozen
  page.locator('#nativeResumeDialog button').tap();assert page.evaluate('!heliAndroidState.paused&&!keys.fire&&gameControls.rotation()===0')
  assert page.locator('#musicToggle').get_attribute('aria-pressed')=='false' and page.evaluate(playing)==0
  music_then_start();page.wait_for_function(playing+'===1')
  passed('App inactive freezes the entire original frame and silences media; foreground waits for Continue; music OFF persists and ON resumes one BGM with cleared input.')
  page.evaluate('nativeMock.available=false;nativeMock.blockWebSensors=true');page.locator('#sensor').tap()
  page.wait_for_function('sensorStatus.textContent.includes("센서 사용 불가")')
  drag_points=[point(88,400,200)];cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':drag_points});drag_points[0]['x']+=30
  cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':drag_points});assert page.evaluate('drag!==null&&Math.abs(tilt.x)>0')
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  passed('Unavailable native sensor reports drag fallback; trusted canvas drag still moves input with the sensor enabled and no valid sensor signal.')
  # Three landscape sizes; do not replay stages or alter combat statistics.
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function(f'W==={width}&&H==={height}')
   for sel in ['#rotationJoystick','#fire','#exitGame']:
    r=page.locator(sel).bounding_box();assert r and r['x']>=0 and r['y']>=0 and r['x']+r['width']<=width and r['y']+r['height']<=height
  page.screenshot(path=str(a.artifacts/'android-shell-568x320.png'))
  page.evaluate('nativeMock.events.backButton({})');expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
  page.wait_for_function(playing+'===1')
  page.locator('#startSelected').tap();page.wait_for_function('started');page.evaluate('runScore=1234;hp=0;update(0)')
  expect(page.locator('#gameOverOverlay')).to_be_visible();page.evaluate('nativeMock.events.backButton({})');assert page.evaluate('gameOverPending&&!gameExitDialogOpen')
  page.wait_for_timeout(3100);expect(page.locator('#menu')).to_be_visible();assert page.locator('#selectionResult').inner_text()==''
  saved=page.evaluate("localStorage.getItem('heliTrio.world2Trial.top10.v1')");assert any(x['score']==1234 for x in json.loads(saved)['records'])
  page.reload(wait_until='load');assert page.evaluate("localStorage.getItem('heliTrio.world2Trial.top10.v1')")==saved
  passed('915x412/800x360/568x320 controls fit; confirmed exit returns selection; original3s GAME OVER blocks Back and one result survives same-origin reload.')
  page.wait_for_function('!!nativeMock.events.backButton');page.evaluate('nativeMock.events.backButton({})');expect(page.locator('#nativeExitDialog')).to_be_visible();page.evaluate("const b=[...document.querySelectorAll('#nativeExitDialog button')].at(-1);b.click();b.click()");assert page.evaluate('nativeMock.exits')==1
  assert not errors and not external and not missing,(errors,external,missing)
  report.update(errors=errors,external_requests=external,missing_paths=missing)
  passed('Selection Back uses an internal app-exit panel with duplicate-exit guard; no browser errors, missing assets or external network requests.')
 finally:
  report['elapsed_seconds']=round(time.monotonic()-start,2);(a.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');context.close();browser.close()
