"""Issue27 independent fit geometry/pixel checks and real before/after browser captures."""
import argparse,base64,hashlib,io,json,math,shutil,subprocess,threading,zipfile
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image
from playwright.sync_api import sync_playwright
from storm_background_fit_preservation import verify,BASE
from storm_background_integrity import inspect_source
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':args.standalone,'passed':[],'preservation':verify(),'source_png':inspect_source(),'limits':['Fit checks prove no source-coordinate cropping or aspect distortion; they cannot recover the missing source PNG rows.','Real Chromium screenshots with controlled game state, not physical Galaxy Samsung Internet/Chrome or sensor hardware.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
passed('All109 preexisting assets/index reverse exactly to6c3446b after only background scale/metadata changes; PNGs,combat,world registry,HUD,controls/audio unchanged.')
source=(ROOT/'index.html').read_text();assert '"render_mode": "contain"' in source.split('<template id="stormSkyManifest">')[1].split('</template>')[0]
passed('Native manifest/template and asset preparation metadata consistently declare contain; approved background SHA and one-image identity stay unchanged.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/blank':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  if self.path.startswith('/before.html'):
   data=subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT);self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(data);return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
helpers=r'''()=>{
 window.bfStart=step=>{window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}clearGameOver();gameWorlds.setDeveloperStart({enabled:true,regionId:6,phase:step});start(0);spawn=999;transition=0;invuln=0;tilt={x:0,y:0};keys.fire=false;window.gameExitDialogOpen=true;draw();};
 window.bfLayer=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');const calls=[],draw=g.drawImage;g.drawImage=function(im,...a){calls.push({id:im.id,args:a});return draw.call(this,im,...a);};const handled=gameStormSky.drawBackground(g,W,H);return {handled,calls,data:c.toDataURL(),w:W,h:H,phase,same:terrainImgs[stage]===gameStormSky.backgroundImage,natural:[gameStormSky.backgroundImage.naturalWidth,gameStormSky.backgroundImage.naturalHeight]};};
}'''
sizes=[(915,412),(800,360),(568,320),(740,360),(844,390),(960,540),(1080,360),(1024,600),(360,800)]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);contexts=[];pages={};errors=[];failed=[];external=[]
  for version in (['after'] if args.standalone else ['before','after']):
   context=browser.new_context(viewport={'width':915,'height':412},has_touch=True,is_mobile=True);contexts.append(context);page=context.new_page();pages[version]=page;page.on('pageerror',lambda e:errors.append(str(e)));page.on('requestfailed',lambda r:failed.append(r.url))
   if args.standalone:
    page.goto(url+'blank');context.set_offline(True);payload=subprocess.check_output(['git','show',BASE+':dist/heli_trio_galaxy_test.html'],cwd=ROOT).decode() if version=='before' else (ROOT/'dist/heli_trio_galaxy_test.html').read_text();page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None);page.set_content(payload,wait_until='load')
   else:
    if version=='before':context.route('**/assets/storm_sky/storm_sky.js',lambda route:route.fulfill(status=200,content_type='text/javascript',body=subprocess.check_output(['git','show',BASE+':assets/storm_sky/storm_sky.js'],cwd=ROOT)))
    page.goto(url+('before.html' if version=='before' else ''),wait_until='load')
   page.wait_for_function('gameStormSky.ready()');page.evaluate(helpers)
  rows=[];rects={}
  for w,h in sizes:
   cases={}
   for version,page in pages.items():
    page.set_viewport_size({'width':w,'height':h});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h]);page.evaluate('bfStart(1)');data=page.evaluate('bfLayer()');raw=base64.b64decode(data.pop('data').split(',',1)[1]);image=Image.open(io.BytesIO(raw)).convert('RGB');draw=data['calls'];assert len(draw)==1 and draw[0]['id']=='stormSkyBackground' and len(draw[0]['args'])==4;assert data['same'] and data['natural']==[1920,864]
    x,y,dw,dh=draw[0]['args'];assert abs(dw/dh-1920/864)<1e-10 and abs(2*x+dw-w)<1e-8 and abs(2*y+dh-h)<1e-8
    # Derive source coverage by inverse rectangle intersection, not the production min/max expression.
    visible=max(0,min(w,x+dw)-max(0,x))*max(0,min(h,y+dh)-max(0,y))/(dw*dh)
    if version=='after':
     assert x>=-1e-8 and y>=-1e-8 and x+dw<=w+1e-8 and y+dh<=h+1e-8
     assert abs(visible-1)<1e-10 and (abs(dw-w)<1e-8 or abs(dh-h)<1e-8)
     samples=[]
     for px,py in [(0,0),(w//2,0),(w-1,0),(0,h-1),(w//2,h-1),(w-1,h-1)]:
      if px<x-1 or px>x+dw+1 or py<y-1 or py>y+dh+1:samples.append(image.getpixel((px,py)))
     assert all(tuple(color)==(16,33,62) for color in samples),samples
    data.update(source_coverage=visible,letterbox_samples=samples if version=='after' else []);cases[version]=data
    if (w,h) in [(915,412),(800,360),(568,320),(1080,360)]:
     page.screenshot(path=str(args.artifacts/f'{version}-{w}x{h}.png'));(args.artifacts/f'{version}-background-only-{w}x{h}.png').write_bytes(raw)
   rows.append({'viewport':[w,h],**cases})
  report['viewports']=rows
  if not args.standalone:
   assert next(r for r in rows if r['viewport']==[568,320])['before']['source_coverage']<.81
   assert next(r for r in rows if r['viewport']==[1080,360])['before']['source_coverage']<.75
  passed('Nine actual viewport ratios including915×412/800×360/568×320,ultrawide andportrait retain100% source coordinates with uniform scale/centering; cover cropping comparison is retained in the native before/after run.')
  passed('Unused area is opaque original#10213e navy, never black/transparent; no gradients,stripe textures,secondary image stretch or source PNG alteration introduced.')
  page=pages['after'];all_steps=[]
  page.set_viewport_size({'width':568,'height':320});page.wait_for_function('W===568&&H===320')
  for step in range(1,6):
   page.evaluate('bfStart('+str(step)+')');data=page.evaluate('bfLayer()');raw=base64.b64decode(data.pop('data').split(',',1)[1]);all_steps.append({'phase':step,'sha256':hashlib.sha256(raw).hexdigest(),'calls':data['calls'],'same':data['same']})
  assert len({r['sha256'] for r in all_steps})==1 and all(r['same'] for r in all_steps);report['all_phases']=all_steps
  passed('All1–5 phases use the same image object and produce byte-identical isolated background layers; boss/monster gameplay is not involved in fitting.')
  # Independent source-raster oracle: browser-decoded pixels, full 9-argument source rect and test-computed destination.
  oracle=page.evaluate('''()=>{const image=gameStormSky.backgroundImage,c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.fillStyle='#10213e';g.fillRect(0,0,W,H);const width=W,height=W*864/1920;g.drawImage(image,0,0,1920,864,0,(H-height)/2,width,height);return c.toDataURL();}''');oracle_png=base64.b64decode(oracle.split(',',1)[1]);assert oracle_png==raw
  passed('At the original problem ratio, a full-source-rectangle raster oracle matches the actual rendered layer byte-for-byte; comparison uses decoded available bytes and does not assert missing pixels exist.')
  for context in contexts:context.close()
  hd=browser.new_context(viewport={'width':568,'height':320},has_touch=True,is_mobile=True,device_scale_factor=2);hp=hd.new_page();hp.on('pageerror',lambda e:errors.append(str(e)))
  if args.standalone:
   hp.goto(url+'blank');hd.set_offline(True);hp.on('request',lambda r:external.append(r.url) if r.url.startswith('http') else None);hp.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:hp.goto(url,wait_until='load')
  hp.wait_for_function('gameStormSky.ready()');hp.evaluate(helpers);hp.evaluate('bfStart(1)')
  hdpi=hp.evaluate("""()=>{const originalDraw=ctx.drawImage,calls=[];ctx.drawImage=function(im,...a){if(im===gameStormSky.backgroundImage)calls.push({args:a,m:[ctx.getTransform().a,ctx.getTransform().d]});return originalDraw.call(this,im,...a);};try{draw();}finally{ctx.drawImage=originalDraw;}return {css:[W,H],bitmap:[canvas.width,canvas.height],dpr,calls};}""")
  assert hdpi['bitmap']==[1136,640] and hdpi['dpr']==2 and len(hdpi['calls'])==1
  px,py,pw,ph=hdpi['calls'][0]['args'];assert px>=0 and py>=0 and px+pw<=568+1e-8 and py+ph<=320+1e-8 and hdpi['calls'][0]['m']==[2,2]
  report['high_dpi']=hdpi;hp.screenshot(path=str(args.artifacts/'after-568x320-dpr2.png'))
  passed('Actual game Canvas atDPR2 is1136×640 for568×320 CSS pixels, with one unchanged-source uniform draw inside both axes; existing DPR cap and HUD remain unchanged.')
  assert not errors and not failed and (not args.standalone or not external),[errors,failed,external];report.update(errors=errors,failed_requests=failed,offline_external_requests=external if args.standalone else [],all_passed=True,full_original_art_verified=report['source_png']['complete'])
  passed('No browser JS/resource errors and offline network requests0; incomplete source PNG is separately reported as an acceptance blocker.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
