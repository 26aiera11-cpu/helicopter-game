"""Production Canvas screenshots; no game PNG or animation frame is edited."""
import ast,base64,json,shutil,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
node=ast.parse((ROOT/'tests/volcano_boss.py').read_text());helpers=next(ast.literal_eval(n.value) for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
def card(path,label):return '<figure><figcaption>'+label+'</figcaption><img src="data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()+'"></figure>'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':800,'height':360},is_mobile=True,has_touch=True);page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('gameVolcanoBoss.artSnapshot().status==="ready"&&gameVolcano.ready()');page.evaluate(helpers)
  frames=[];timing_cards=[];direction_cards=[]
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('([w,h])=>W===w&&H===h',arg=[width,height])
   for side in ['right','left']:
    page.evaluate('side=>vbRun(()=>{vbBegin(2);vbGo("breath_warning");const p=gameVolcanoBoss.snapshot().center;player.x=p.x+(side==="right"?150:-150);player.y=p.y;player.vx=player.vy=0;enemyBullets=[];})',side)
    previous=0
    for label,time in [('warning',.999),('flame-first',1),('flame-100ms',1.1),('flame-199ms',1.199),('turn-start',1.21),('quarter',2.15),('half',3.1),('three-quarter',4.05),('complete',5)]:
     page.evaluate('dt=>vbRun(()=>vbAdvance(dt))',time-previous);previous=time
     data=page.evaluate('({state:gameVolcanoBoss.snapshot(),geometry:gameVolcanoBoss.frameGeometry(boss),player:{x:player.x,y:player.y}})');path=OUT/f'{label}-{side}-{width}x{height}.png';page.screenshot(path=str(path));frames.append({'file':path.name,'viewport':[width,height],'side':side,'seconds_from_warning':time,'seconds_from_flame':round(time-1,3),**data})
     if width==800 and side=='right' and label in ['warning','flame-first','flame-100ms','flame-199ms','turn-start','quarter']:
      text={'warning':'직전 예고 · 불꽃 PNG 없음','flame-first':'분사 0.000초 · 아래로 먼저 표시','flame-100ms':'분사 0.100초 · 회전 없음','flame-199ms':'분사 0.199초 · 회전 없음','turn-start':'분사 0.210초 · 회전 시작 후','quarter':'분사 1.150초 · 반시계 90°'}[label];timing_cards.append(card(path,text))
     if label in ['flame-first','quarter','half','three-quarter','complete']:
      text=f'{width}×{height} · '+('오른쪽 → 반시계' if side=='right' else '왼쪽 → 시계')+' · '+{'flame-first':'분사 시작','quarter':'90°','half':'180°','three-quarter':'270°','complete':'360° / 분사 종료'}[label];direction_cards.append(card(path,text))
  viewer=browser.new_page(viewport={'width':1600,'height':950},device_scale_factor=1)
  for filename,title,cols,cards in [('flame-first-timeline.png','불꽃 PNG가 먼저, 0.2초 뒤 회전',2,timing_cards),('sweep-directions.png','아래에서 출발 → 선택한 방향으로 정확히 한 바퀴',5,direction_cards)]:
   viewer.set_content('<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:16px;background:#131c2b;color:#e8f4ff;font:15px sans-serif}h1{font-size:24px;margin:0 0 8px}p{margin:0 0 16px}main{display:grid;grid-template-columns:repeat('+str(cols)+',1fr);gap:10px}figure{margin:0}img{width:100%;display:block}figcaption{padding:7px;background:#25354c}</style><h1>'+title+'</h1><p>예고1초 / 아래 분사0.2초 / 360° 회전3.8초 · 원본 정지 PNG · 제어된 실제 Chromium 게임 화면</p><main>'+''.join(cards)+'</main>');viewer.locator('img').evaluate_all('(ims)=>Promise.all(ims.map(i=>i.decode()))');viewer.screenshot(path=str(OUT/filename),full_page=True)
  (OUT/'capture-metadata.json').write_text(json.dumps(frames,ensure_ascii=False,indent=2)+'\n');browser.close()
finally:server.shutdown()
