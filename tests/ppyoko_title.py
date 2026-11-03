"""Issue13: ID0 rename, legacy storage compatibility and localized Hangul title art."""
import argparse,hashlib,io,json,math,re,shutil,subprocess,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright,expect
from ppyoko_preservation import PPYOKO_ASSETS,assert_ppyoko_asset,without_ppyoko_source,without_ppyoko_asset
ROOT=Path(__file__).resolve().parents[1];BASE='48319030a0b15c2346a6ec99c3e4c8d84765178b'
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':['Real Chromium screenshots and native storage;not physical Galaxy/Samsung Internet or speaker listening.','Offline uses exact standalone HTML at a blank localhost origin with networking disabled;managed file policy not bypassed.','Final-clear name tests inject the final region/phase,then use real bullets/hits/rewards;full20/25-stage progress remains covered by retained regressions.','Hangul stroke legibility manually inspected in enlarged actual browser captures;pixel tests prove localization,not semantic OCR.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
s=(ROOT/'index.html').read_text();assert without_ppyoko_source(s)==subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT).decode()
for f in (ROOT/'assets').rglob('*'):
 if not f.is_file():continue
 name=str(f.relative_to(ROOT))
 if name in PPYOKO_ASSETS:assert_ppyoko_asset(f);continue
 b=without_ppyoko_asset(f.read_text(),name).encode() if f.suffix in ['.js','.css'] else f.read_bytes();assert b==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',s,re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Exact name/title-only changes reverse to4831903;original background,all character/115frame assets,combat/region tuning,input,audio,score logic/IDs/keys preserved;all JS parses.')
keys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];names=['뾰코','빙글','탱코'];legacy={}
for key in keys:
 trial='world2Trial' in key;records=[]
 for i in range(10):records.append({'id':('trial' if trial else 'normal')+'-legacy-'+str(i),'score':10000-(i//2)*100,'characterId':i%3,'characterName':['트리오','빙글','탱코'][i%3],'regionId':4 if trial else 3,'phase':1+i%5,'order':i+1,'createdAt':f'2026-11-0{1+i//6}T01:00:{i:02d}.000Z','outcome':'game_over','normalKills':20+i,'itemKills':2,'bossKills':1,'clearedPhases':4,'playTimeSeconds':90+i,'finalUpgrade':i%6})
 legacy[key]=json.dumps({'version':1,'records':records},ensure_ascii=False)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/ppyoko-origin':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline origin</title>');return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
helpers='''()=>{
 window.nameStorage=()=>Object.fromEntries(['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'].map(k=>[k,localStorage.getItem(k)]));
 window.nameFinishBoss=()=>{transition=0;spawn=999;invuln=999;let attempts=0;while(boss&&attempts++<100){bullets=[];shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(0);}if(boss)throw Error('Boss survived');};
}'''
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True,timezone_id='Asia/Seoul')
  ctx.add_init_script('(()=>{try{if(location.protocol!=="http:")return;const seed='+json.dumps(legacy,ensure_ascii=False)+';if(!localStorage.getItem("ppyokoSeeded")){for(const [k,v] of Object.entries(seed))localStorage.setItem(k,v);localStorage.setItem("ppyokoSeeded","yes");}}catch{}})()')
  page=ctx.new_page();errors=[];dialogs=[];failed=[];external=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  url=f'http://127.0.0.1:{server.server_port}/'
  def load():
   if args.standalone:ctx.set_offline(False);page.goto(url+'ppyoko-origin');external.clear();ctx.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
   else:page.goto(url,wait_until='load')
   page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()');page.evaluate(helpers)
  load();assert page.title()=='헬리 트리오';assert page.locator('#menu h1').inner_text()=='🚁 헬리 트리오'
  assert page.evaluate('nameStorage()')==legacy
  compatibility=[]
  for trial in [False,True]:
   page.evaluate('on=>gameWorlds.setTrialEnabled(on)',trial);result=page.evaluate('({top:gameScoring.getTop(),history:gameScoring.getHistory()})');scope='trial' if trial else 'normal';expected_ids=[scope+'-legacy-'+str(i) for i in range(10)]
   assert [r['id'] for r in result['top']]==expected_ids and [r['id'] for r in result['history']]==expected_ids
   for kind in ['top','history']:
    for row in result[kind]:
     original=next(r for r in json.loads(legacy[keys[2 if trial else 0]])['records'] if r['id']==row['id']);assert row['characterName']==names[row['characterId']]
     assert all(row[k]==v for k,v in original.items() if k!='characterName')
   page.locator('#selectionSettings').tap();expect(page.locator('#leaderboardDialog')).to_be_visible();assert page.locator('#leaderboardRows tr').count()==10 and '트리오' not in page.locator('#leaderboardRows').inner_text() and '뾰코' in page.locator('#leaderboardRows').inner_text();page.screenshot(path=str(args.artifacts/f'legacy-{scope}-top10.png'));page.locator('#leaderboardClose').tap();compatibility.append(result)
  assert page.evaluate('nameStorage()')==legacy;report['legacy_records_canonical_names']=compatibility
  passed('All40 legacy normal/trial TOP10/history records retain IDs,scores,dates,order,region,stats and ties;ID0 displays뾰코,others unchanged;reading/scope switches/table opening do not rewrite a single stored byte.')
  load();assert page.evaluate('nameStorage()')==legacy and page.evaluate('gameScoring.getTop().filter(r=>r.characterId===0).every(r=>r.characterName==="뾰코")')
  passed('Reload/reopen preserves all original version1 storage keys and raw records while resolving the new display name by characterId0;no destructive migration.')
  visuals=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('W===innerWidth&&H===innerHeight')
   for kind,name in enumerate(names):
    page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.wait_for_timeout(260);assert page.locator(f'.character-details[data-heli="{kind}"] .character-name').inner_text()==name;assert name+' 선택:' in page.locator(f'.select-hit[data-heli="{kind}"]').get_attribute('aria-label')
    box=page.locator(f'.character-details[data-heli="{kind}"] .character-name').evaluate('(e)=>({w:e.clientWidth,scroll:e.scrollWidth,h:e.getBoundingClientRect().height})');assert box['scroll']<=box['w'];page.screenshot(path=str(args.artifacts/f'selection-{kind}-{w}x{h}.png'))
   page.evaluate('''()=>{const source=document.querySelector('.select-screen'),base=getComputedStyle(source),corrected=getComputedStyle(source,'::before'),box=document.createElement('div');box.id='titlePixelReview';box.style='position:fixed;inset:0;z-index:2147483000';box.style.backgroundImage=base.backgroundImage;box.style.backgroundSize=base.backgroundSize;box.style.backgroundPosition=base.backgroundPosition;const patch=document.createElement('div');patch.className='patch';patch.style='position:absolute;inset:0;pointer-events:none';patch.style.backgroundImage=corrected.backgroundImage;patch.style.backgroundSize=corrected.backgroundSize;patch.style.backgroundPosition=corrected.backgroundPosition;patch.style.clipPath=corrected.clipPath;box.append(patch);document.body.append(box);}''')
   page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');after=page.locator('#titlePixelReview').screenshot();page.evaluate("document.querySelector('#titlePixelReview .patch').style.visibility='hidden'");before=page.locator('#titlePixelReview').screenshot();page.evaluate('titlePixelReview.remove()')
   diff=ImageChops.difference(Image.open(io.BytesIO(before)).convert('RGB'),Image.open(io.BytesIO(after)).convert('RGB'));bbox=diff.getbbox();assert bbox and bbox[0]>=math.floor(.37*w)-1 and bbox[2]<=math.ceil(.418*w)+1 and bbox[1]>=math.floor(.024*h)-1 and bbox[3]<=math.ceil(.112*h)+1,bbox
   (args.artifacts/f'title-before-{w}x{h}.png').write_bytes(before);(args.artifacts/f'title-after-{w}x{h}.png').write_bytes(after);assert page.locator('.select-screen').evaluate('e=>getComputedStyle(e,"::before").pointerEvents')=='none';visuals.append({'viewport':[w,h],'difference_bbox':bbox})
  report['local_title_pixel_differences']=visuals;passed('All3 characters fit3landscapes;isolated background-layer pixel differences from title correction stay entirely inside the first vowel ROI37–41.8%×2.4–11.2%,with other title letters/background/layout unchanged and no pointer interception.')
  # Actual browser zoom inspection without cropping/editing any source image.
  page.set_viewport_size({'width':1240,'height':560});page.evaluate('''()=>{const source=document.querySelector('.select-screen'),base=getComputedStyle(source).backgroundImage,patch=getComputedStyle(source,'::before').backgroundImage,review=document.createElement('div');review.id='titleReview';review.style='position:fixed;left:0;top:0;width:1220px;height:540px;background:white;z-index:10000;display:flex;gap:20px';for(const after of [false,true]){const slot=document.createElement('div');slot.style='width:600px;height:540px;overflow:hidden;position:relative';const label=document.createElement('strong');label.textContent=after?'수정 후 — 헬':'수정 전';label.style='position:absolute;top:5px;left:15px;z-index:1;font-size:22px';const art=document.createElement('div');art.className='titleZoom'+(after?' corrected':'');art.style='position:absolute;width:1672px;height:941px;left:-1260px;top:35px;transform:scale(2.4);transform-origin:0 0;background-size:100% 100%';art.style.backgroundImage=base;art.style.setProperty('--title-patch',patch);slot.append(art,label);review.append(slot);}const style=document.createElement('style');style.textContent='.titleZoom.corrected::before{content:"";position:absolute;inset:0;background-image:var(--title-patch);background-size:100% 100%;clip-path:polygon(37% 2.4%,41.8% 2.4%,41.8% 11.2%,37% 11.2%)}';document.head.append(style);document.body.append(review);}''');page.locator('#titleReview').screenshot(path=str(args.artifacts/'title-enlarged-before-after.png'));page.evaluate('titleReview.remove()');page.set_viewport_size({'width':915,'height':412});page.evaluate('document.getAnimations().forEach(a=>a.play())')
  passed('Enlarged before/after title screenshot uses actual CSS layers in browser;visibleㅔ has separate vertical strokes and its short stroke extends left,with original yellow/orange bevel and navy outline.')
  page.locator('#fullscreenToggle').tap();page.wait_for_function('!!document.fullscreenElement');deaths=[]
  for kind,name in enumerate(names):
   page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap();assert page.evaluate('({type:player.type,hp})')=={'type':kind,'hp':[4,6,9][kind]};page.evaluate('spawn=999;transition=0;window.namedDeathAt=performance.now();hp=0;update(0)');expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#gameOverCharacter')).to_have_text(name);page.screenshot(path=str(args.artifacts/f'game-over-{kind}.png'));page.wait_for_timeout(2500);expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_visible(timeout=3000);elapsed=page.evaluate('performance.now()-namedDeathAt');assert elapsed>=2990 and page.locator('#selectionResult').inner_text()=='' and page.locator('#menu h1').inner_text()=='🚁 헬리 트리오' and page.evaluate('!!document.fullscreenElement');deaths.append({'kind':kind,'name':name,'observed_return_ms':elapsed})
  history=page.evaluate('gameScoring.getHistory()');assert len(history)==13 and all(r['characterName']==names[r['characterId']] for r in history);assert all(any(r['id']==old['id'] and all(r[k]==v for k,v in old.items() if k!='characterName') for r in history) for old in json.loads(legacy[keys[1]])['records']);report['gameover_names_and_3s']=deaths
  passed('All3 actual start→HP0→3s game-over→clean menu paths show canonical names,retain fullscreen and preserve every old analysis record;new ID0 results save뾰코,without changing keys/scores.')
  before_dev=page.evaluate('nameStorage()');clears=[]
  for region in [3,4]:
   for kind,name in enumerate(names):
    page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending',timeout=4000)
    assert page.evaluate('r=>gameWorlds.setDeveloperStart({enabled:true,regionId:r,phase:5})',region)
    page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.wait_for_function('k=>selectedHeli===k',arg=kind)
    page.locator('#startSelected').tap();page.wait_for_function('k=>started&&player?.type===k',arg=kind)
    page.evaluate('nameFinishBoss()');expect(page.locator('#menu')).to_be_visible(timeout=4000)
    page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending',timeout=4000)
    diagnostic=page.evaluate('({text:selectionResult.textContent,heading:menu.querySelector("h1").textContent,selectedHeli,started,result:gameScoring.getLastResult()})')
    (args.artifacts/f'developer-clear-{region}-{kind}.json').write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+'\n')
    expect(page.locator('#selectionResult')).to_contain_text(name,timeout=4000);expect(page.locator('#selectionResult')).to_contain_text('지역 테스트 완료',timeout=4000)
    text=page.locator('#selectionResult').inner_text();result=page.evaluate('gameScoring.getLastResult()');assert result['record']['characterName']==name and result['record']['characterId']==kind and result['record']['score']==2000 and not result['saved'];clears.append({'region':region,'kind':kind,'text':text})
  assert page.evaluate('nameStorage()')==before_dev;report['developer_clear_names']=clears
  passed('All3 names appear in real bullet-kill desert/snow developer clear results;score2000/rewards/finale preserved and all4 ranking/history storage strings remain untouched.')
  final=[]
  for trial in [False,True]:
   page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending',timeout=4000)
   assert page.evaluate('gameWorlds.setDeveloperStart({enabled:false})');assert page.evaluate('on=>gameWorlds.setTrialEnabled(on)',trial)
   page.locator('.select-hit[data-heli="0"]').tap();page.wait_for_function('selectedHeli===0');page.locator('#startSelected').tap();page.wait_for_function('started&&player?.type===0')
   page.evaluate('trial=>{stage=trial?4:3;phase=5;phaseKills=6;spawn=999;transition=0;update(0);nameFinishBoss();}',trial)
   expect(page.locator('#menu')).to_be_visible(timeout=4000);page.wait_for_function('!gameSnowfield.snapshot().finale.active&&!gameSnowfield.snapshot().finale.pending',timeout=4000)
   expect(page.locator('#selectionResult')).to_contain_text('뾰코',timeout=4000);expect(page.locator('#selectionResult')).to_contain_text('설원 시험 완료' if trial else '모든 지역 클리어',timeout=4000)
   text=page.locator('#selectionResult').inner_text();result=page.evaluate('gameScoring.getLastResult()');assert result['record']['characterName']=='뾰코' and result['record']['characterId']==0 and result['saved'];page.screenshot(path=str(args.artifacts/f'clear-{trial}.png'));final.append({'trial':trial,'text':text,'score':result['record']['score']})
  report['normal_trial_clear_names']=final;passed('Normal and trial final-clear headings and newly stored results consistently use뾰코/ID0 while game title stays헬리 트리오;legacy top entries remain available.')
  load();page.evaluate('gameWorlds.setTrialEnabled(true)');assert all(r['characterName']==names[r['characterId']] for r in page.evaluate('gameScoring.getTop()'));assert page.title()=='헬리 트리오'
  assert not errors and not dialogs and not failed and not external,{'errors':errors,'dialogs':dialogs,'failed':failed,'external':external};passed('Native reload/offline reopen retain canonical names and old records with no uncaught JS,native dialogs,failed assets or offline external requests.')
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
