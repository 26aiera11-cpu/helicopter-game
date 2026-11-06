"""Recreate enlarged review screenshots from original PNGs and actual render probes."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,shutil,subprocess,threading
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BASE='5fe31bbbde7f9aa46d25aba03d64731485c2c70b'
for name in ['lava_lizard','magma_dragon']:
    (HERE/f'before-{name}.png').write_bytes(subprocess.check_output(['git','show',f'{BASE}:assets/volcano/monsters/{name}.png'],cwd=ROOT))
style='''body{margin:0;padding:22px;background:#172237;color:#e7f3ff;font:16px system-ui}h1{font-size:24px;margin:0 0 10px}h2{font-size:19px}p{color:#c3d7e8}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}.box{border:1px solid #577083;border-radius:10px;padding:10px;text-align:center}.art{height:350px;max-width:95%;object-fit:contain}.check{background-color:#d5dce3;background-image:linear-gradient(45deg,#fff5 25%,transparent 25%,transparent 75%,#fff5 75%),linear-gradient(45deg,#fff5 25%,transparent 25%,transparent 75%,#fff5 75%);background-size:20px 20px;background-position:0 0,10px 10px}.frames{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}.frame{text-align:center;background:#263b50;border-radius:7px;padding:6px;font-size:12px}.frame canvas{width:130px;height:130px}.players{display:grid;grid-template-columns:repeat(8,1fr);gap:8px}.zoom{position:relative;width:128px;height:128px;overflow:hidden;margin:auto}.zoom img{position:absolute;width:915px;height:412px;max-width:none;left:50%;top:50%;transform:translate(-50%,-50%) scale(3)}.scenes img{width:100%}'''
html=f'<!doctype html><meta charset="utf-8"><title>Issue17 art review</title><style>{style}</style><h1>화산 외형 수정 전·후</h1><p>왼쪽: 기준 5fe31bb · 오른쪽: 수정본. 원본 비율 유지 / 확대 검토 화면</p>'
for name,label in [('lava_lizard','용암 도마뱀'),('magma_dragon','마그마 드래곤')]:
    html+=f'<h2>{label}</h2><div class="pair"><div class="box check"><img class="art" src="before-{name}.png"></div><div class="box check"><img class="art" src="../../../assets/volcano/monsters/{name}.png"></div></div>'
html+='<p>드래곤: 턱 아래 연결부·불꽃 제거 승인 반영. 위쪽 긴 꼬리는 유지.</p>'
(HERE/'art-review.html').write_text(html)
frames=f'<!doctype html><meta charset="utf-8"><title>33 frame review</title><style>{style}</style><h1>교체 2종 · 33프레임 확대 검토</h1><p>원본 PNG와 매니페스트의 개별 좌표 사용 · 렌더링 시 알파 8 미만만 정리 · PNG 원본 미가공</p><main></main><script>window.reviewReady=false;(async()=>{{const m=await(await fetch("../../../assets/volcano/asset_manifest.json")).json();for(const s of m.monsters.filter(s=>["lava_lizard","magma_dragon"].includes(s.id))){{const h=document.createElement("h2");h.textContent=s.name_ko;document.querySelector("main").append(h);const grid=document.createElement("div");grid.className="frames";document.querySelector("main").append(grid);const im=new Image();im.src="../../../assets/volcano/"+s.atlas;await im.decode();for(const [state,a]of Object.entries(s.animations))for(let i=0;i<a.frames.length;i++){{const f=a.frames[i],box=document.createElement("div"),c=document.createElement("canvas");box.className="frame";c.width=320;c.height=320;const [x,y,w,h]=f.rect_px,[dx,dy]=f.sprite_source_rect_px;const tmp=document.createElement("canvas");tmp.width=w;tmp.height=h;const g=tmp.getContext("2d");g.drawImage(im,x,y,w,h,0,0,w,h);const pixels=g.getImageData(0,0,w,h);for(let p=3;p<pixels.data.length;p+=4)if(pixels.data[p]<8)pixels.data.fill(0,p-3,p+1);g.putImageData(pixels,0,0);c.getContext("2d").drawImage(tmp,dx,dy);box.append(c,document.createElement("br"),state+" "+(i+1));grid.append(box);}}}}window.reviewReady=true;}})();</script>'
(HERE/'frames-review.html').write_text(frames)
players=f'<!doctype html><meta charset="utf-8"><title>player inspection</title><style>{style}</style><h1>플레이어 8방향 · 실제 게임 그리기 확대</h1><p>숲·설원·화산의 몸체/프로펠러 픽셀·비율·중심점이 방향별로 일치함. 3배 확대 / 실제 게임 크기는 유지.</p>'
for kind,label in enumerate(['뾰코','빙글','탱코']):
    players+=f'<h2>{label}</h2><div class="players">'
    for i in range(8):players+=f'<div class="box"><div class="zoom check"><img src="visual-native/rotation-{kind}-{i}.png"></div>{i*45}°</div>'
    players+='</div>'
(HERE/'player-review.html').write_text(players)
race=f'<!doctype html><meta charset="utf-8"><title>loader race comparison</title><style>{style}</style><h1>늦은 예전 이미지 로딩 · 수정 전 / 후</h1><p>로딩 순서를 의도적으로 늦춘 진단 조건. 사용자의 실제 갤럭시 화면을 재현했다고 단정하지 않음. 정상 로딩 시 외형은 유지됨.</p>'
for kind,label in enumerate(['뾰코','빙글','탱코']):
    race+=f'<h2>{label}</h2><div class="pair">'
    for variant,caption in [('before','이전: 예전 이미지가 덮어씀'),('after','수정: 최종 승인 이미지 유지')]:
        race+=f'<div class="box">{caption}<div class="zoom check"><img src="visual-native/{variant}-delayed-legacy-player-{kind}.png"></div></div>'
    race+='</div>'
(HERE/'loader-comparison.html').write_text(race)
scenes=f'<!doctype html><meta charset="utf-8"><title>Game before after</title><style>{style}</style><h1>실제 게임 화면 · 수정 전 / 후</h1><p>915×412 Chromium. 비교용 위치/시간 고정. 전투 수치와 UI는 동일함.</p>'
for step,label in [(2,'일반2단계 · 용암 도마뱀'),(5,'보스5단계 · 마그마 드래곤')]:
    scenes+=f'<h2>{label}</h2><div class="pair scenes"><div>수정 전<img src="visual-native/before-915x412-phase{step}.png"></div><div>수정 후<img src="visual-native/after-915x412-phase{step}.png"></div></div>'
(HERE/'game-comparison.html').write_text(scenes)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1400,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for file in ['art-review','frames-review','player-review','game-comparison','loader-comparison']:
        page.goto(f'http://127.0.0.1:{server.server_port}/docs/review/volcano-monster-player-visual-fix/{file}.html')
        page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
        if file=='frames-review':page.wait_for_function('window.reviewReady===true')
        page.screenshot(path=str(HERE/f'{file}.png'),full_page=True)
    assert not errors,errors
    browser.close()
finally:server.shutdown()
print('Five enlarged art/frame/player/game/loader review captures created.')
