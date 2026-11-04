from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import threading,shutil
from playwright.sync_api import sync_playwright
folder=Path(__file__).resolve().parent;root=folder.parents[2]
style='body{margin:0;background:#182335;color:#e8f3ff;padding:20px;font:17px system-ui}h1{font-size:25px}h2{font-size:19px;margin:4px 0 8px}p{color:#b9d0e6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.scene{background:#243349;border-radius:10px;padding:12px}.scene img{width:100%;display:block}.guards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.guards img{width:100%;display:block}'
html=f'<!doctype html><meta charset="utf-8"><title>Volcano combat review</title><style>{style}</style><h1>화산 일반 몬스터 전투 시험</h1><p>실제 Chromium 게임 화면 · 고정 위치/시간의 검토 캡처 · 기존 그래픽69프레임 유지</p><div class="grid">'
for step,label in [(1,'불씨콩 · HP1 / 빠른 추적·단발'),(2,'용암 도마뱀 · HP2 / 짧은 좌우 횡이동'),(3,'화산 박쥐 · HP2 / 지그재그·주황/보라 화염탄'),(4,'마그마 갑충 · HP4 / 짧은 1회 방어')]:
 html+=f'<div class="scene"><h2>{label}</h2><img src="combat-native/volcano-combat-{step}-915x412.png"></div>'
html+='</div>'
(folder/'combat-overview.html').write_text(html)
html=f'<!doctype html><meta charset="utf-8"><title>Beetle guard review</title><style>{style}</style><h1>마그마 갑충 · 방어 예고 → 방어 → 1회 차단</h1><p>예고0.25초 · 방어 최대0.7초 · 한 번 막으면 즉시 종료 · 재사용 대기4.5초</p><div class="guards">'
for name,label in [('beetle-windup.png','예고 · 점선 윤곽'),('volcano-combat-4-568x320.png','방어 · 실선 윤곽'),('beetle-blocked.png','1회 차단 · 즉시 방어 종료')]:
 html+=f'<div class="scene"><h2>{label}</h2><img src="combat-native/{name}"></div>'
html+='</div><p>캡처는 위치/시간이 제어된 실제 게임 렌더러이며 수동 갤럭시 플레이 촬영본이 아닙니다.</p>'
(folder/'guard-sequence.html').write_text(html)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':1600,'height':200})
  for name in ['combat-overview','guard-sequence']:
   page.goto(f'http://127.0.0.1:{server.server_port}/docs/review/volcano-normal-combat/{name}.html');page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)');page.screenshot(path=str(folder/(name+'.png')),full_page=True)
  browser.close()
finally:server.shutdown()
print('Two actual-game review contact sheets captured.')
