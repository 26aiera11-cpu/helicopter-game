"""Isolated Chromium profile for Issue39. No personal browser/storage is opened."""
import shutil,threading,subprocess
from pathlib import Path
from functools import partial
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='07c3d34331770f53817ca513241949ec19fe8dbe'
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/blank-origin':
   self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline origin</title>');return
  super().do_GET()
@contextmanager
def browser_game(standalone=False,pause=False,baseline=False):
 originals={n:subprocess.check_output(['git','show',BASE+':'+n],cwd=ROOT) for n in ['assets/worlds/worlds.js','assets/score/score.js','assets/selection/selection.js']} if baseline else {}
 class Handler(Quiet):
  def do_GET(self):
   key=self.path.split('?')[0].lstrip('/')
   if key in originals:
    self.send_response(200);self.send_header('Content-Type','application/javascript; charset=utf-8');self.end_headers();self.wfile.write(originals[key]);return
   super().do_GET()
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
  if pause:ctx.add_init_script("const auditRAF=requestAnimationFrame;window.requestAnimationFrame=fn=>fn.name==='frame'?0:auditRAF(fn)")
  page=ctx.new_page();errors=[];page.audit_external=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:page.audit_external.append(r.url) if standalone and r.url.startswith('http') and not r.url.endswith('/blank-origin') else None)
  try:
   if standalone:
    page.goto(f'http://127.0.0.1:{server.server_port}/blank-origin');ctx.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
   page.wait_for_function('gameMachineFortress.ready()&&gameSnowfield.ready()&&gameVolcano.ready()&&gameStormSky.ready()&&itemMonsters.ready()')
   yield page,ctx,errors
  finally:ctx.close();browser.close();server.shutdown();server.server_close()
