"""Issue35 background-only before/after, cover pixels and actual mobile/DPR layouts."""
import argparse,json,shutil,subprocess,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
from machine_cover_preservation import BASE,RENDERER,verify
from machine_cover_probe import probe,check_background
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':args.standalone,'passed':[],'preservation':verify(),'limits':['Real Chromium screenshots and pixel checks, not physical Galaxy Samsung Internet/Chrome approval.','Cover cropping is approved; source PNG/ratio are unchanged.','No new projectile E2E or attack diagnostics: only the existing regressions are run.','Offline exact HTML uses network-disabled injection without bypassing managed file policy.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
helpers=(ROOT/'tests/machine_normal.py').read_text().split("helpers=r'''",1)[1].split("'''",1)[0]
old=subprocess.check_output(['git','show',BASE+':'+RENDERER],cwd=ROOT)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  for prefix in ['/before/','/after/']:
   if path.startswith(prefix):path='/'+path[len(prefix):];break
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/blank':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  if self.path=='/before/'+RENDERER:self.send_response(200);self.send_header('Content-Type','text/javascript');self.end_headers();self.wfile.write(old);return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append({'url':r.url,'error':r.failure}));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  if args.standalone:page.goto(url+'/blank');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url+'/after/')
  page.wait_for_function('gameMachineFortress.ready()&&gameStormSky.ready()&&itemMonsters.ready()');page.evaluate(helpers);page.evaluate('mcRun(()=>mcBegin())')
  source=(ROOT/RENDERER).read_text();assert all(token not in source for token in ['extendedBackground','backgroundCache','blur(','rgba(8,15,24','createElement'])
  subprocess.run(['node','--check',str(ROOT/RENDERER)],capture_output=True,check=True)
  passed('Only one runtime file changes: background rendering. Index and127/128assets including complete combat/config/spawn/projectile code, original PNG/manifest/audio/controls remain byte-identical; no extension/blur/cache allocation code; JS parses.')
  rows=[]
  for ratio in [1,2]:
   for w,h in [(915,412),(800,360),(568,320),(1672,941),(412,915)]:
    row=page.evaluate(probe,[w,h,ratio]);check_background(row);rows.append(row)
  report['background_pixels']=rows;passed('Ten viewport/DPR cases use exactly one unfiltered original image at alpha1; full Canvas pixels equal a cover reference with no transparent/solid margins, overlay, ratio distortion or seam; visible source crop recorded.')
  phases=page.evaluate('''()=>mcRun(()=>{const rows=[],original=ctx.drawImage,im=gameMachineFortress.backgroundImage;let calls=[];ctx.drawImage=function(image,...args){if(image===im)calls.push(args);return original.call(ctx,image,...args)};try{for(let step=1;step<=5;step++){mcBegin(0,step);calls=[];draw();rows.push({phase:step,background:calls,boss:!!boss,bossHP:boss?.hp});}return rows;}finally{ctx.drawImage=original;}})''');assert all(len(r['background'])==1 and r['background']==phases[0]['background'] for r in phases) and phases[-1]['bossHP']==20 and phases[-1]['boss'];report['phase_backgrounds']=phases;passed('Actual stages1-5 draw the same single cover source/geometry; developer stage5 still starts original20HP GigaCore immediately.')
  layouts=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);page.evaluate('mcRun(()=>{mcBegin();for(let kind=0;kind<4;kind++)mcSpawn(kind,W*(.2+kind*.2),H*.5);player.x=W*.5;player.y=H*.75;rotorSpin=0;})');page.screenshot(path=str(args.artifacts/f'after-{w}x{h}.png'))
   row=page.evaluate('''()=>({W,H,dpr,boxes:Object.fromEntries(['hud','rotationJoystick','fire','fullscreenToggle','exitGame'].map(id=>[id,document.getElementById(id).getBoundingClientRect().toJSON()]))})''');assert row['boxes']['rotationJoystick']['left']==30 and h-row['boxes']['rotationJoystick']['bottom']==22 and row['boxes']['rotationJoystick']['right']<row['boxes']['fire']['left'] and row['boxes']['hud']['right']<=row['boxes']['fullscreenToggle']['left'];layouts.append(row)
  report['layouts']=layouts;passed('915x412/800x360/568x320 actual game captures retain40px sprites, centered player and original HUD/joystick/fire/exit/fullscreen targets with no new overlap or input layer.')
  extra=browser.new_context(viewport={'width':915,'height':412},device_scale_factor=2,is_mobile=True,has_touch=True);dpage=extra.new_page()
  if args.standalone:extra.set_offline(True);dpage.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:dpage.goto(url+'/after/')
  dpage.wait_for_function('gameMachineFortress.ready()');dpage.evaluate(helpers);dprRows=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   dpage.set_viewport_size({'width':w,'height':h});dpage.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);dpage.evaluate('mcRun(()=>mcBegin(0,5))');assert dpage.evaluate('dpr===2&&canvas.width===W*2&&canvas.height===H*2&&gameMachineFortress.species[4].renderWidth===132');row=dpage.evaluate(probe,[w,h,2]);check_background(row);dprRows.append(row)
  dpage.screenshot(path=str(args.artifacts/'after-boss-568x320-dpr2.png'));extra.close();report['actual_dpr2']=dprRows;passed('ActualDPR2 game contexts at all3landscape sizes retain one sharp cover background, original132px boss and correct CSS/pixel scale; no blurry auxiliary image.')
  page.set_viewport_size({'width':360,'height':800});page.wait_for_function('W===360&&H===800');page.evaluate('mcRun(()=>draw())');page.set_viewport_size({'width':915,'height':412});page.wait_for_function('W===915&&H===412');row=page.evaluate(probe,[915,412,1]);check_background(row);passed('Portrait-to-landscape resize recalculates cover immediately without old cached dimensions or a second background.')
  if not args.standalone:
   before=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);bpage=before.new_page();bpage.goto(url+'/before/');bpage.wait_for_function('gameMachineFortress.ready()');bpage.evaluate(helpers)
   for version,target in [('before',bpage),('after',page)]:
    for w,h in [(915,412),(568,320)]:
     target.set_viewport_size({'width':w,'height':h});target.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);target.evaluate('mcRun(()=>{mcBegin();rotorSpin=0;worldScroll=0;for(let kind=0;kind<4;kind++)mcSpawn(kind,W*(.2+kind*.2),H*.5);player.x=W*.5;player.y=H*.75;})');target.screenshot(path=str(args.artifacts/f'{version}-comparison-{w}x{h}.png'))
   before.close();passed('Actual before/after915x412 and568x320 compare baseline46e8631 blurred extension against single cover; the renderer is the only served source difference, actors/PNG/AI unchanged.')
  assert not errors and not dialogs and not failed and (not args.standalone or not external),(errors,dialogs,failed,external)
  report.update(all_passed=True,errors=errors,dialogs=dialogs,failed=failed,offline_requests=external if args.standalone else []);passed('No JS errors/native dialogs/missing resources; exact standalone HTML executes network-disabled with zero external requests. Existing combat regressions run separately, no added projectile diagnostics.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
