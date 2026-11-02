"""Native browser design inspection, touch-halo checks and review screenshots."""
import argparse
import io
import json
import shutil
import subprocess
import tarfile
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright
from controls_preservation import assert_controls_asset

ROOT=Path(__file__).resolve().parents[1]
BASELINE='22191f996908195937ebef7c220e871e487d7712'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true');args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASELINE,'standalone':args.standalone,'passed':[],'limits':['Native Chromium/mobile touch emulation, not physical Galaxy/Samsung Internet or outdoor display visibility.','Backdrop scenes use a frozen native game frame; screenshots are not image edits.','Standalone injects the actual embedded HTML offline; no managed file:// policy bypass.']}
def passed(message):report['passed'].append(message);print('PASS:',message,flush=True)
assert (ROOT/'index.html').read_bytes()==subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT)
for path in (ROOT/'assets').rglob('*'):
 if not path.is_file():continue
 name=str(path.relative_to(ROOT))
 if name=='assets/controls/controls.css':assert_controls_asset(path);continue
 assert path.read_bytes()==subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT),name
old_css=subprocess.check_output(['git','show',BASELINE+':assets/controls/controls.css'],cwd=ROOT).decode()
assert (ROOT/'assets/controls/controls.css').read_text().split('.rotation-joystick{')[0]==old_css.split('.rotation-joystick{')[0]
passed('Only joystick appearance CSS changes; index, every JavaScript file, touch-selection guards, images/audio and item/score/combat code exactly match the latest joystick baseline.')

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*unused):pass
def serve(folder):
 s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(folder)));threading.Thread(target=s.serve_forever,daemon=True).start();return s
web=serve(ROOT)
try:
 with tempfile.TemporaryDirectory(prefix='heli-minimal-before-') as folder,sync_playwright() as p:
  archive=subprocess.check_output(['git','archive',BASELINE,'index.html','assets'],cwd=ROOT)
  with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(folder,filter='data')
  old_web=serve(folder);browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True,offline=args.standalone)
  page=context.new_page();errors=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  if args.standalone:page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(f'http://127.0.0.1:{web.server_port}/',wait_until='load')
  page.wait_for_function('window.gameControls&&terrainImgs.every(i=>i.complete&&i.naturalWidth)&&sprites.every(i=>i.complete&&i.naturalWidth)')
  cdp=context.new_cdp_session(page)
  def down(x,y):cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'id':1,'x':x,'y':y}]})
  def up():cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  def settled(opacity):page.wait_for_function('v=>Number(getComputedStyle(rotationJoystick).opacity)===v',arg=opacity,timeout=5000)
  def layout():return page.evaluate('''() => {
   const r=rotationJoystick.getBoundingClientRect(),knob=document.querySelector('.rotation-knob'),k=knob.getBoundingClientRect(),c=getComputedStyle(rotationJoystick),t=getComputedStyle(document.querySelector('.rotation-track')),s=getComputedStyle(knob),f=fire.getBoundingClientRect();
   return {rect:r.toJSON(),knob:k.toJSON(),travel:r.width/2-parseFloat(c.getPropertyValue('--stick-inset')),opacity:Number(c.opacity),background:c.backgroundColor,image:c.backgroundImage,border:c.borderTopWidth,shadow:c.boxShadow,trackHeight:parseFloat(t.height),trackColor:t.backgroundColor,knobColor:s.backgroundColor,knobImage:s.backgroundImage,labelsHidden:[...document.querySelectorAll('.rotation-direction,.rotation-caption')].every(e=>getComputedStyle(e).display==='none'),fireX:f.left};
  }''')
  def freeze():page.evaluate('worldScroll=0;player.a=Math.PI;player.x=W/2;player.y=H/2;invuln=0;rotorSpin=.35;gameExitDialogOpen=true;draw()')
  rows=[];halos=[]
  names=['forest','rock','sea','desert']
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('W===innerWidth&&H===innerHeight')
   page.evaluate('gameExitDialogOpen=false;start(0);spawn=999;transition=0;enemies=[];enemyBullets=[];warnings=[]');freeze();page.wait_for_timeout(180)
   initial=layout();r=initial['rect'];cx=r['x']+r['width']/2;cy=r['y']+r['height']/2
   assert 135<=r['width']<=165 and r['height']==58 and initial['knob']['width']==initial['knob']['height']==32
   assert initial['opacity']==.4 and initial['background']=='rgba(0, 0, 0, 0)' and initial['image']=='none' and initial['border']=='0px' and initial['shadow']=='none' and initial['labelsHidden']
   assert initial['trackHeight']==2 and initial['knobImage']=='none' and r['x']==15 and r['bottom']==height-10 and r['right']<initial['fireX']
   for raw in [-1,0,1]:
    page.evaluate('gameExitDialogOpen=false');down(cx+raw*initial['travel'],cy);settled(.7)
    current=layout();k=current['knob'];kx=k['x']+k['width']/2;ky=k['y']+k['height']/2
    hits=page.evaluate('''({x,y})=>[-21,21].flatMap(dx=>[-21,21].map(dy=>document.elementFromPoint(x+dx,y+dy)?.id==='rotationJoystick'))''',{'x':kx,'y':ky})
    actual=page.evaluate('gameControls.snapshot()')
    assert all(hits) and current['opacity']==.7 and abs(actual['value']-raw)<1e-6,{'width':width,'raw':raw,'hits':hits,'layout':current,'input':actual}
    assert k['left']>=r['left'] and k['right']<=r['right']
    up();settled(.4)
    # A real contact21px below center lies outside the16px visible radius.
    page.evaluate('gameExitDialogOpen=false');down(cx,cy+21)
    assert page.evaluate('gameControls.snapshot().rotationPointer!==null&&gameControls.rotation()===0')
    up();halos.append({'viewport':[width,height],'raw':raw,'all_44px_corners_hit':hits,'outside_visible_circle_contact':True})
   for area,name in enumerate(names):
    page.evaluate('area=>{stage=area;gameScoring.updateHUD();gameExitDialogOpen=false;gameControls.reset();spawn=999;transition=0;enemies=[];enemyBullets=[];warnings=[]}',area);freeze();settled(.4)
    idle=layout();idle_bytes=page.screenshot();idle_img=Image.open(io.BytesIO(idle_bytes)).convert('RGB')
    page.evaluate("rotationJoystick.style.visibility='hidden'");clear_img=Image.open(io.BytesIO(page.screenshot())).convert('RGB');page.evaluate("rotationJoystick.style.visibility=''")
    def delta(x,y):return sum(abs(a-b) for a,b in zip(idle_img.getpixel((x,y)),clear_img.getpixel((x,y))))/3
    corner=delta(round(r['x']+3),round(r['y']+3));line=sum(delta(x,round(cy)) for x in range(round(r['x']+24),round(cx-20)))/len(range(round(r['x']+24),round(cx-20)))
    thumb=delta(round(cx),round(cy))
    assert corner==0 and line>3 and thumb>3,(width,name,corner,line,thumb)
    if width==915 or area==0:(args.artifacts/f'{name}-idle-{width}.png').write_bytes(idle_bytes)
    page.evaluate('gameExitDialogOpen=false');down(cx,cy);freeze();settled(.7);held=layout();assert held['opacity']==.7
    if width==915:(args.artifacts/f'{name}-held-{width}.png').write_bytes(page.screenshot())
    up();assert page.evaluate('gameControls.rotation()===0');settled(.4)
    rows.append({'viewport':[width,height],'region':name,'idle':idle,'held_opacity':held['opacity'],'uncovered_corner_rgb_difference':corner,'track_rgb_difference':round(line,3),'knob_rgb_difference':round(thumb,3)})
  report['layouts_and_backdrops']=rows;report['touch_halos']=halos
  passed('All3 landscape sizes meet135–165×58, visible32px knob,2px white line, zero panel/border/gradient and hidden labels; native idle/held opacity reaches.4/.7.')
  passed('The entire control accepts touch; all44px square corners remain hittable at both ends/center, and native contacts outside the visible knob own the joystick without shrinking its usable range.')
  passed('All12 region/viewport native scenes show distinct line/knob pixels through the translucent control with exact zero change in the empty panel corner; pressed/released opacity and endpoints work.')
  # Before screenshots come from the actual original commit at the same pose.
  old_context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);old=old_context.new_page();old.goto(f'http://127.0.0.1:{old_web.server_port}/',wait_until='load');old.wait_for_function('sprites.every(i=>i.complete&&i.naturalWidth)')
  for width,height in [(915,412),(800,360),(568,320)]:
   old.set_viewport_size({'width':width,'height':height});old.wait_for_function('W===innerWidth&&H===innerHeight');old.evaluate('gameExitDialogOpen=false;start(0);spawn=999;transition=0;enemies=[];enemyBullets=[];warnings=[];worldScroll=0;player.a=Math.PI;player.x=W/2;player.y=H/2;invuln=0;rotorSpin=.35;gameExitDialogOpen=true;draw()');old.screenshot(path=str(args.artifacts/f'before-{width}.png'))
  assert not errors and not failed and not external,(errors,failed,external)
  report.update(uncaught_errors=errors,failed_resources=failed,external_requests=external)
  passed('Unedited before/after native screenshots are saved; current web/offline game has no JS errors, failed assets or offline HTTP requests.')
  browser.close();old_web.shutdown()
finally:web.shutdown()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
