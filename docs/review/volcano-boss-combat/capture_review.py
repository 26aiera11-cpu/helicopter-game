"""Review captures from actual game screenshots and unchanged manifest/atlas pixels."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,threading,shutil
from playwright.sync_api import sync_playwright
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
style='body{margin:0;padding:20px;background:#182335;color:#e8f2ff;font:16px system-ui}h1{font-size:25px}h2{font-size:18px}p{color:#bad2e6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.box{background:#26384c;border-radius:10px;padding:12px}.box img{width:100%;display:block}.rotation{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.frames{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}.frame{text-align:center;background:#2d4053;border-radius:8px;padding:7px}.frame canvas{width:145px;height:145px}.detail{height:340px;position:relative;overflow:hidden;background:#243449}.detail img{position:absolute;max-width:none;transform-origin:top left}'
html=f'<!doctype html><meta charset="utf-8"><title>Dragon combat review</title><style>{style}</style><h1>마그마 드래곤 · 실제 게임3패턴</h1><p>915×412 Chromium · 제어된 시간/위치의 실제 게임 렌더러 캡처 · 원본PNG/69프레임 유지</p><div class="grid">'
for file,label in [('fireball','화염구 · 3발 부채꼴 × 3연사'),('eruption-warning','용암 분출 · 경고 중 피해 없음'),('eruption-burst','용암 분출 · 한 번의 피해 판정'),('breath-000','회전 브레스 · 입에서 이어진 지속 화염')]:html+=f'<div class="box"><h2>{label}</h2><img src="boss-native/{file}-915x412.png"></div>'
html+='</div>';(HERE/'pattern-overview.html').write_text(html)
html=f'<!doctype html><meta charset="utf-8"><title>360deg breath review</title><style>{style}</style><h1>회전 브레스 · 시작 → 반바퀴 → 한 바퀴</h1><p>568×320 실제 게임 화면 · 1초 예고 후3.8초/360° · 몸·날개·머리·꼬리와 입 화염이 같은 중심/각도를 사용</p><div class="rotation">'
for file,label in [('breath-000','0° · 분사 시작'),('breath-180','180° · 같은 자리에서 반바퀴'),('breath-360','360° · 분사 종료/잔광')]:html+=f'<div class="box"><h2>{label}</h2><img src="boss-native/{file}-568x320.png"></div>'
html+='</div><p>브레스의 표시와 피해 판정에서 UI 영역을 함께 제외합니다. 이는 실기기 촬영본이 아닌 자동 브라우저 검사입니다.</p>';(HERE/'rotation-review.html').write_text(html)
data=json.loads((HERE/'boss-native/test-results.json').read_text());entry=next(r for r in data['entries'] if r['viewport']==[915,412] and r['kind']==0)
html=f'<!doctype html><meta charset="utf-8"><title>Mouth detail</title><style>{style}</style><h1>입과 화염 연결 · 실제 게임3배 확대</h1><p>원본 게임 캡처를 브라우저에서 확대 표시합니다. 이미지 파일을 재가공하지 않았습니다.</p><div class="grid">'
for phase,label,key in [('breath-000','0°','start'),('breath-180','180°','half')]:
 c=entry[key]['geo']['origin'];left=350-c['x']*3;top=170-c['y']*3
 html+=f'<div class="box"><h2>{label}</h2><div class="detail"><img src="boss-native/{phase}-915x412.png" style="left:{left}px;top:{top}px;width:2745px;height:1236px"></div></div>'
html+='</div>';(HERE/'mouth-detail.html').write_text(html)
frames=f'<!doctype html><meta charset="utf-8"><title>21 source mouth anchors</title><style>{style}</style><h1>승인된21프레임 · 입 기준점 검토</h1><p>원본 개별 프레임 좌표와 가상320셀을 사용합니다. 빨간 점은 화염 시작점이며 원본PNG에는 추가하지 않았습니다.</p><main class="frames"></main><script>window.ready=false;(async()=>{{const m=await(await fetch("../../../assets/volcano/asset_manifest.json")).json(),audit=await(await fetch("../../../tests/volcano_dragon_mouth_anchors.json")).json(),spec=m.monsters.find(s=>s.id==="magma_dragon"),im=new Image();im.src="../../../assets/volcano/"+spec.atlas;await im.decode();for(const row of audit.samples){{const f=spec.animations[row.state].frames.find(f=>f.index===row.index),[x,y,w,h]=f.rect_px,[dx,dy]=f.sprite_source_rect_px,box=document.createElement("div"),c=document.createElement("canvas"),crop=document.createElement("canvas");c.width=c.height=320;crop.width=w;crop.height=h;const cg=crop.getContext("2d");cg.drawImage(im,x,y,w,h,0,0,w,h);const pixels=cg.getImageData(0,0,w,h);for(let p=3;p<pixels.data.length;p+=4)if(pixels.data[p]<8)pixels.data.fill(0,p-3,p+1);cg.putImageData(pixels,0,0);const g=c.getContext("2d");g.drawImage(crop,dx,dy);g.fillStyle="#ff4848";g.beginPath();g.arc(dx+row.mouth_in_crop[0],dy+row.mouth_in_crop[1],3,0,Math.PI*2);g.fill();box.className="frame";box.append(c,document.createElement("br"),row.state+" "+(row.index+1));document.querySelector("main").append(box);}}window.ready=true;}})();</script>'
(HERE/'mouth-frames.html').write_text(frames)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':1600,'height':200});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  for name in ['pattern-overview','rotation-review','mouth-detail','mouth-frames']:
   page.goto(f'http://127.0.0.1:{server.server_port}/docs/review/volcano-boss-combat/{name}.html');page.wait_for_function('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
   if name=='mouth-frames':page.wait_for_function('window.ready===true')
   page.screenshot(path=str(HERE/(name+'.png')),full_page=True)
  assert not errors,errors;browser.close()
finally:server.shutdown()
print('Four game/rotation/mouth review captures created.')
