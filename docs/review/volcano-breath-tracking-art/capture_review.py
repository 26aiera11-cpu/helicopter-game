"""Capture production game frames; composite is a browser page, source art untouched."""
import ast,base64,json,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
node=ast.parse((ROOT/'tests/volcano_boss.py').read_text())
helpers=next(ast.literal_eval(n.value) for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('gameVolcanoBoss.artSnapshot().status==="ready"&&gameVolcano.ready()');page.evaluate(helpers)
  rows=[];cards=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   page.evaluate('vbRun(()=>{vbBegin(2);vbGo("breath_warning");const p=gameVolcanoBoss.snapshot().center;player.x=p.x+150;player.y=p.y;player.vx=player.vy=0;enemyBullets=[];vbAdvance(1.4);})')
   for name,label,step in [('right','오른쪽 추적',0),('turn','왼쪽 이동 후 선회 중',1.3),('left','왼쪽 추적',1.4)]:
    if name=='turn':page.evaluate('vbRun(()=>{const p=gameVolcanoBoss.snapshot().center;player.x=p.x-150;player.y=p.y;player.vx=player.vy=0;})')
    if step:page.evaluate('step=>vbRun(()=>vbAdvance(step))',step)
    state=page.evaluate('({state:gameVolcanoBoss.snapshot(),geometry:gameVolcanoBoss.frameGeometry(boss),player:{x:player.x,y:player.y}})');assert state['state']['phase']=='breath';filename=f'capture-{name}-{width}x{height}.png';payload=page.screenshot(path=str(OUT/filename));rows.append({'viewport':[width,height],'file':filename,**state});cards.append(f'<figure><figcaption>{width}×{height} · {label}</figcaption><img src="data:image/png;base64,{base64.b64encode(payload).decode()}"></figure>')
  viewer=browser.new_page(viewport={'width':1500,'height':900},device_scale_factor=1)
  viewer.set_content('<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:20px;background:#131c2b;color:#e8f4ff;font:16px sans-serif}h1{font-size:23px;margin:0 0 6px}p{margin:0 0 18px}main{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}figure{margin:0}img{width:100%;display:block}figcaption{padding:6px;background:#25354c}</style><h1>마그마 드래곤 · 플레이어 추적 브레스</h1><p>원본 정지 PNG · 최대70°/초 · 예고1초 / 분사3.8초 · 제어된 Chromium 게임 화면</p><main>'+''.join(cards)+'</main>');viewer.locator('img').evaluate_all('(ims)=>Promise.all(ims.map(i=>i.decode()))');viewer.screenshot(path=str(OUT/'tracking-comparison.png'),full_page=True)
  (OUT/'capture-metadata.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');browser.close()
finally:server.shutdown()
