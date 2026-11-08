"""Conservative rectangular UI occlusion inside Gigacore's unchanged25% safe bands."""
import json
from world_balance_harness import ROOT,browser_game
OUT=ROOT/'docs/review/world-balance-audit'
def union_area(rects):
 xs=sorted({x for l,t,r,b in rects for x in (l,r)});area=0
 for left,right in zip(xs,xs[1:]):
  ys=sorted((t,b) for l,t,r,b in rects if l<right and r>left);bottom=-1e9;covered=0
  for t,b in ys:
   if b>bottom:covered+=b-max(t,bottom);bottom=b
  area+=(right-left)*covered
 return area
rows=[]
with browser_game(pause=True) as (page,context,errors):
 page.locator('#startSelected').tap();page.wait_for_function('started')
 for w,h in [(915,412),(800,360),(568,320)]:
  page.set_viewport_size({'width':w,'height':h});page.evaluate('start(2);stage=7;phase=5;spawnBossEncounter();gameWorlds.syncUI();gameScoring.updateHUD();draw()')
  rects=page.evaluate('''()=>['hud','rotationJoystick','fire','fullscreenToggle','exitGame','sensor','sensorStatus','worldPrototypeNotice'].flatMap(id=>{const e=document.getElementById(id);if(!e||e.hidden||!e.getClientRects().length)return [];const r=e.getBoundingClientRect();return [{id,x:r.x,y:r.y,w:r.width,h:r.height}]})''');rects.append({'id':'canvasBossNameHP','x':w*.3,'y':30,'w':w*.4,'h':38})
  for band in ['top','bottom']:
   l,r=12,w-12;t,b=(12,h*.25-12) if band=='top' else(h*.75+12,h-12);clips=[]
   for box in rects:
    x0=max(l,box['x']-12);x1=min(r,box['x']+box['w']+12);y0=max(t,box['y']-12);y1=min(b,box['y']+box['h']+12)
    if x1>x0 and y1>y0:clips.append((x0,y0,x1,y1))
   area=(r-l)*(b-t);occluded=union_area(clips);rows.append({'viewport':[w,h],'band':band,'player_center_band_height':b-t,'area':area,'conservative_occluded_area':occluded,'conservative_occlusion_ratio':occluded/area,'ui_rectangles':rects})
 assert not errors,errors
(OUT/'safe-band-occlusion.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print([(r['viewport'],r['band'],round(r['conservative_occlusion_ratio']*100,1)) for r in rows])
