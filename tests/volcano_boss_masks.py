"""Focused overlapping-UI clipping oracle, native and exact offline HTML."""
import argparse,ast,json,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
tree=ast.parse((ROOT/'tests/volcano_boss.py').read_text())
helpers=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/offline-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
report={'passed':[],'cases':[],'limits':['Two temporary visible boxes replace UI IDs only inside isolated fixtures and are restored before returning; no shipped UI changes.']}
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  for offline in [False,True]:
   context=browser.new_context(viewport={'width':568,'height':320});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   if offline:
    page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:page.goto(f'http://127.0.0.1:{server.server_port}/')
   page.wait_for_function('gameVolcanoBoss.artSnapshot().status==="ready"&&gameVolcano.ready()&&gameSnowfield.ready()');page.evaluate(helpers)
   result=page.evaluate('''()=>vbRun(()=>{vbBegin(0);vbGo('breath_warning');let p=gameVolcanoBoss.snapshot().center;player.x=p.x+180;player.y=p.y;player.vx=player.vy=0;vbAdvance(1.8);const geo=gameVolcanoBoss.frameGeometry(boss);let point=null;for(let y=70;y<H-50&&!point;y+=2)for(let x=40;x<W-40;x+=2)if(Math.hypot(x-geo.pivot.x,y-geo.pivot.y)>gameVolcanoBoss.bodyRadius+30&&gameVolcanoBoss.contains({x,y},geo)){point={x,y};break;}if(!point)throw Error('No safe visible flame sample');
    const sample=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');gameVolcanoBoss.draw(g);return g.getImageData(Math.floor(point.x),Math.floor(point.y),1,1).data[3];};const before=sample(),saved=[];
    try{for(const id of ['hud','sensor']){const original=document.getElementById(id);original.id=id+'-fixture-original';const el=document.createElement('div');el.id=id;el.style.cssText=`position:fixed!important;left:${point.x-8}px!important;top:${point.y-8}px!important;width:16px!important;height:16px!important;padding:0!important;margin:0!important;border:0!important;overflow:hidden!important;display:block!important;visibility:visible!important;`;document.body.append(el);saved.push([original,id,el]);}
      update(0);const after=sample(),rects=gameVolcanoBoss.blockedRects(),overlap=rects.filter(b=>point.x>=b.left&&point.x<=b.right&&point.y>=b.top&&point.y<=b.bottom).length;
      return {before,after,overlap,hit:gameVolcanoBoss.contains(point,geo),unmaskedHit:gameVolcanoBoss.contains(point,geo,[]),phase:gameVolcanoBoss.snapshot().phase};
    }finally{for(const [original,id,el]of saved){el.remove();original.id=id;}update(0);}
   })''')
   assert result['before']>128 and result['after']==0 and result['overlap']>=2 and not result['hit'] and result['unmaskedHit'] and result['phase']=='breath' and not errors,(result,errors)
   report['cases'].append({'offline':offline,**result,'errors':errors});report['passed'].append(('offline' if offline else 'native')+': two overlapping UI cutouts remove actual flame pixels and damage together; no even-odd cancellation hole')
   context.close()
  browser.close()
 report['all_passed']=True
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS:',len(report['passed']),'overlapping UI geometry groups')
