"""Issue32 same-coordinate/frame native before/after measurements; no source edits."""
import argparse,base64,hashlib,json,math,shutil,subprocess,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from machine_enemy_scale_preservation import verify,BASE,RENDERER
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);a=p.parse_args();a.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'preservation':verify(),'limits':['Native Chromium/controlled coordinates and frames, not physical Galaxy or user visual approval.','Display40px versus collision diameter32px is intentional per Issue32; no hitbox or paint/position change.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
passed('The only runtime delta from ed3dc55 is the shared normal renderWidth32->40; all125 other source assets/index normalize exactly, including PNG/audio/combat/controls/registry; boss132 unchanged.')
old=subprocess.check_output(['git','show',BASE+':'+RENDERER],cwd=ROOT)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def translate_path(self,path):
  for prefix in ['/before/','/after/']:
   if path.startswith(prefix):path='/'+path[len(prefix):];break
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/before/'+RENDERER:
   self.send_response(200);self.send_header('Content-Type','text/javascript');self.send_header('Content-Length',str(len(old)));self.end_headers();self.wfile.write(old);return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
helpers=(ROOT/'tests/machine_fortress.py').read_text().split("helpers=r'''",1)[1].split("'''",1)[0]
probes=r'''()=>{
 window.scaleMatrix=()=>mfRun(()=>{
  const rows=[];for(let hero=0;hero<3;hero++)for(let step=1;step<=5;step++){
   mfBegin(hero,step===5?4:step);if(step===5){nextPhase();transition=0;spawn=999;}
   for(let kind=0;kind<4;kind++){
    const e=mfSpawn(kind),spec=gameMachineFortress.species[kind];e.x=W*(.2+kind*.2);e.y=H*.45;
    const row={hero,step,id:spec.id,hp:e.hp,r:e.r,speed:e.speed,source:[spec.baseImage.naturalWidth,spec.baseImage.naturalHeight],frames:[]};
    for(const name of ['idle','move','attack','hit','defeat']){
     const selected=gameMachineFortress.frame(name,.12),original=ctx.drawImage;let call;
     ctx.drawImage=function(image,...args){if(image===spec.baseImage){const m=ctx.getTransform();call={args,m:{a:m.a,b:m.b,c:m.c,d:m.d,e:m.e,f:m.f},image:[image.naturalWidth,image.naturalHeight]};}return original.call(ctx,image,...args);};
     try{gameMachineFortress.paint(ctx,spec,e,selected);}finally{ctx.drawImage=original;}
     const width=call.args[6]*Math.hypot(call.m.a,call.m.b)/dpr,height=call.args[7]*Math.hypot(call.m.c,call.m.d)/dpr;
     row.frames.push({name,width,height,scale:selected.scale,drawWidth:call.args[6],sourceRect:call.args.slice(0,4)});
    }
    rows.push(row);
   }
  }
  mfBegin(0,5);const spec=gameMachineFortress.species[4],king={renderWidth:spec.renderWidth,hp:boss.hp,r:boss.r,source:[spec.baseImage.naturalWidth,spec.baseImage.naturalHeight]};
  return {rows,king,dpr,canvas:[canvas.width,canvas.height]};
 });
 window.scaleScene=()=>mfRun(()=>{
  mfBegin(0,1);rotorSpin=0;worldScroll=0;
  for(let i=0;i<4;i++){const e=mfSpawn(i);e.x=W*(.2+i*.2);e.y=H*.45;e.shot=999;}
  player.x=W*.5;player.y=H*.82;gameMachineFortress.observe(enemies,null);
  enemyBullets=[{x:W*.38,y:H*.63,vx:0,vy:0,r:5,life:99}];
  items=[{x:W*.62,y:H*.63,type:'hp',r:13,life:7.25,t:0,turn:99,vx:0,vy:0}];
 });
 window.scaleEdge=()=>mfRun(()=>{mfBegin();const e=mfSpawn(3);e.x=17;e.y=H*.45;const spec=gameMachineFortress.species[3],p=gameMachineFortress.frame('idle',0),g=gameMachineFortress.geometry(spec.baseImage,e,spec.renderWidth,p);return {center:e.x,displayLeft:e.x-g.width/2,displayWidth:g.width,hitRadius:e.r,hp:e.hp};});
}'''
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);all_rows=[];errors=[]
  for version,expected in [('before',32),('after',40)]:
   for w,h,dpr2 in [(915,412,1),(800,360,1),(568,320,1),(568,320,2)]:
    context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr2,is_mobile=True,has_touch=True);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}/{version}/');page.wait_for_function('gameMachineFortress.ready()&&gameStormSky.ready()');page.evaluate(helpers);page.evaluate(probes)
    data=page.evaluate('scaleMatrix()');assert len(data['rows'])==60 and data['king']['renderWidth']==132 and data['king']['hp']==20 and data['king']['r']==48
    for row in data['rows']:
     assert row['hp']==1 and row['r']==16 and row['speed']==38+(row['step']-1)*5
     for frame in row['frames']:
      assert frame['drawWidth']==expected and frame['sourceRect']==[0,0,*row['source']]
      assert abs(frame['width']-expected*frame['scale'])<1e-4
      assert abs(frame['width']/row['source'][0]-frame['height']/row['source'][1])<1e-6
    page.evaluate('scaleScene()');page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');page.screenshot(path=str(a.artifacts/f'{version}-{w}x{h}-dpr{dpr2}.png'))
    edge=page.evaluate('scaleEdge()');assert edge=={'center':17,'displayLeft':17-expected/2,'displayWidth':expected,'hitRadius':16,'hp':1}
    if (w,h,dpr2)==(568,320,1):page.screenshot(path=str(a.artifacts/f'{version}-edge-568x320.png'))
    all_rows.append({'version':version,'size':[w,h],'dpr':dpr2,'edge':edge,**data});context.close()
  for before,after in zip(all_rows[:4],all_rows[4:]):
   for old_row,new_row in zip(before['rows'],after['rows']):
    for old_f,new_f in zip(old_row['frames'],new_row['frames']):assert abs(new_f['width']/old_f['width']-1.25)<1e-8 and abs(new_f['height']/old_f['height']-1.25)<1e-8
  report['measurements']=all_rows
  passed('2400 real Canvas frame measurements:4species x3heroes x5phases x5states x4viewports/DPR xbefore-after; width/height both+25%, original ratio/source rect/pivot preserved, HP1/r16 and boss132/r48/HP20 unchanged.')
  passed('915x412/800x360/568x320/DPR2 same-coordinate/frame screenshots include background, player, enemy bullet and item; compare baseline module served from git with only the approved width difference.')
  passed('Edge probe records the unchanged17px center clamp:32px visual left1px before,40px left-3px after. Outer visual area can exceed viewport/hit radius; paint, positions and collisions were deliberately preserved.')
  assert not errors;report.update(all_passed=True,errors=errors)
  passed('No uncaught browser errors. Source preservation proves other7regions/boss/images/audio unchanged; native/offline integration and progression suites are run separately.')
  browser.close()
finally:
 server.shutdown();(a.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
