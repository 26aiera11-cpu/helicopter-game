"""Real production spawn/Canvas captures; seeds select species, only positions arranged."""
import ast,base64,json,shutil,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
node=ast.parse((ROOT/'tests/volcano_mixed.py').read_text());helpers=next(ast.literal_eval(n.value) for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='helpers' for t in n.targets))
plans=json.loads((OUT/'mixed-final/volcano_mixed-native/test-results.json').read_text())['capture_plans']
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
def card(file,label):return '<figure><figcaption>'+label+'</figcaption><img src="data:image/png;base64,'+base64.b64encode(file.read_bytes()).decode()+'"></figure>'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page.goto(f'http://127.0.0.1:{server.server_port}/');page.wait_for_function('gameVolcano.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');page.evaluate(helpers)
  rows=[];stage_cards=[];character_cards=[]
  for step in range(1,6):
   row=page.evaluate('''({step,seed})=>vmRun(()=>{const counts=vmPopulate(0,step,seed);enemies.forEach((e,i)=>{e.x=W*(.11+i*.175);e.y=H*(.35+(i%2)*.19);});player.x=W*.5;player.y=H*.82;invuln=0;gameVolcano.observe(enemies,boss);return {...counts,actors:enemies.map(e=>({id:e.volcanoSpeciesId,hp:e.hp,x:e.x,y:e.y,pose:gameVolcano.pose(e),combat:gameVolcanoCombat.snapshot(e)}))};})''',{'step':step,'seed':plans[str(step)]['seed']})
   assert row['ids']==plans[str(step)]['ids'];file=OUT/f'phase-{step}-915x412.png';page.screenshot(path=str(file));rows.append({'phase':step,'seed':plans[str(step)]['seed'],'file':file.name,**row});stage_cards.append(card(file,f'화산 {step}단계 · 시드{plans[str(step)]["seed"]} · 원래 동시 수량 {row["cap"]} 유지'))
  for width,height in [(915,412),(800,360),(568,320)]:
   for kind,name in enumerate(['뾰코','빙글','탱코']):
    file=OUT/f'mixed-final/volcano_mixed-native/mixed-kind{kind}-{width}x{height}.png';assert file.exists();character_cards.append(card(file,f'{name} · {width}×{height} · 3단계 시드25 실제 혼합'))
  viewer=browser.new_page(viewport={'width':1600,'height':900})
  for filename,title,cards,cols in [('volcano-phase-overview.png','화산 1~5단계 · 개체별 가중 독립 추첨',stage_cards,2),('volcano-mixed-characters.png','세 캐릭터·세 가로 화면의 동시 혼합 등장',character_cards,3)]:
   viewer.set_content('<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:16px;background:#211b27;color:#fff2e6;font:16px sans-serif}h1{margin:0 0 8px;font-size:25px}p{margin:0 0 16px}main{display:grid;grid-template-columns:repeat('+str(cols)+',1fr);gap:12px}figure{margin:0}figcaption{padding:7px;background:#493346}img{width:100%;display:block}</style><h1>'+title+'</h1><p>기존 그래픽·AI·HP·생성 간격/상한 유지 · 재현용 시드와 위치/시간을 제어한 실제 Chromium 게임 화면</p><main>'+''.join(cards)+'</main>');viewer.locator('img').evaluate_all('(a)=>Promise.all(a.map(i=>i.decode()))');viewer.screenshot(path=str(OUT/filename),full_page=True)
  (OUT/'capture-metadata.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');browser.close()
finally:server.shutdown()
