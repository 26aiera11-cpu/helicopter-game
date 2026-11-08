"""Issue39 real UI, unchanged raw records, original exit fallback and offline resources."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from world_balance_harness import browser_game
from world_balance_labels_preservation import verify
from playwright.sync_api import expect
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');a=p.parse_args();a.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':a.standalone,'preservation':verify(),'passed':[],'scenes':[],'limits':['UI state setup is not evidence of gameplay difficulty.','Physical Galaxy, actual sensors and audible speakers untested.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
with browser_game(a.standalone,True) as (page,context,errors):
 page.evaluate('''()=>{window.labelCanvasTexts=[];const original=ctx.fillText;ctx.fillText=function(t,...args){labelCanvasTexts.push(String(t));return original.call(this,t,...args)};window.labelKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];window.labelRead=()=>Object.fromEntries(labelKeys.map(k=>[k,localStorage.getItem(k)]));}''')
 seed=page.evaluate('''()=>{for(const key of labelKeys){const trial=key.includes('world2Trial'),ids=trial?[4,5,6,7]:[3],records=ids.map(id=>({id:'legacy-'+id,score:10000+id,characterId:0,characterName:'뾰코',regionId:id,regionName:gameWorlds.region(id).name+(trial?' (시험)':''),worldId:trial?1:0,worldName:trial?'월드 2':'월드 1',regionKey:gameWorlds.region(id).key,localRegionIndex:gameWorlds.region(id).localIndex,trialMode:trial,phase:5,order:id+1,createdAt:'2026-11-01T00:00:00.000Z',outcome:'clear',normalKills:120,itemKills:12,bossKills:4,clearedPhases:16,playTimeSeconds:100,finalUpgrade:5}));localStorage.setItem(key,JSON.stringify({version:1,records}));}return labelRead();}''')
 for mode in [True,False,True]:
  page.evaluate('v=>gameWorlds.setTrialEnabled(v)',mode);page.locator('#selectionSettings').tap();expect(page.locator('#leaderboardTitle')).to_have_text('🏆 40단계 TOP 10' if mode else '🏆 TOP 10');assert '(시험)' not in page.locator('dialog[open]').inner_text();page.screenshot(path=str(a.artifacts/f'legacy-leaderboard-{mode}.png'));page.locator('#leaderboardClose').tap();assert page.evaluate('labelRead()')==seed
 passed('Viewing20/40 leaderboards preserves all4 raw storage values; every legacy World2 row displays the clean name.')
 page.locator('#startSelected').tap();page.wait_for_function('started')
 for w,h in [(915,412),(800,360),(568,320)]:
  page.set_viewport_size({'width':w,'height':h})
  for region in range(4,8):
   for phase in [1,5]:
    page.evaluate('([r,p])=>{start((r-4)%3);stage=r;phase=p;if(p===5)spawnBossEncounter();transition=2;labelCanvasTexts=[];gameWorlds.syncUI();gameScoring.updateHUD();draw()}',[region,phase])
    state=page.evaluate('()=>({visible:document.body.innerText,canvas:labelCanvasTexts.join(" "),noticeHidden:worldPrototypeNotice.hidden})');assert state['noticeHidden'] and '(시험)' not in state['visible']+state['canvas'] and '월드 2 시험' not in state['visible']+state['canvas'],state;assert page.evaluate('gameWorlds.snapshot().route.length===8&&gameWorlds.isTrial()&&!gameWorlds.isDeveloperRun()');report['scenes'].append({'size':[w,h],'region':region,'phase':phase,**state});page.screenshot(path=str(a.artifacts/f'region-{region}-phase-{phase}-{w}x{h}.png'))
  page.evaluate('started=false;gameAudioStarted=false;menu.classList.remove("hidden")');page.locator('#selectionHelp').tap();assert '시험' not in page.locator('#worldTrialSettings').inner_text();expect(page.locator('#worldTrialSettings')).to_contain_text('숲 임시 BGM');page.screenshot(path=str(a.artifacts/f'help-{w}x{h}.png'));page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap()
 passed('All4 regions, phases1/5 and5/5, HUD/canvas/banner/boss labels are clean at915x412/800x360/568x320; normal notice hidden and40 route retained.')
 page.evaluate('stage=7;phase=5;runScore=999999;nextPhase()');expect(page.locator('#selectionResult')).to_contain_text('전체 40단계 클리어');assert '(시험)' not in page.locator('#selectionResult').inner_text()
 for width,height in [(915,412),(800,360),(568,320)]:
  page.set_viewport_size({'width':width,'height':height});page.screenshot(path=str(a.artifacts/f'full40-clear-{width}x{height}.png'));page.locator('#selectionSettings').tap();page.screenshot(path=str(a.artifacts/f'leaderboard-{width}x{height}.png'));page.locator('#leaderboardClose').tap()
 after=page.evaluate('labelRead()')
 for key,raw in seed.items():
  if 'world2Trial' not in key:assert after[key]==raw
  else:
   old=json.loads(raw)['records'];new=json.loads(after[key])['records']
   for record in old:assert record==next(r for r in new if r['id']==record['id'])
 passed('New40 clear title/result and new saved result preserve all fields of prior records, including original stored (시험) regionName.')
 for hero,region in [(0,4),(1,5),(2,7)]:
  page.evaluate('r=>gameWorlds.setDeveloperStart({enabled:true,regionId:r,phase:5})',region);page.locator(f'.select-hit[data-heli="{hero}"]').tap();page.locator('#startSelected').tap();assert page.evaluate('(h)=>started&&!!boss&&phase===5&&player.type===h&&player.upgrade===0&&gameWorlds.isDeveloperRun()',hero);expect(page.locator('#worldPrototypeNotice')).to_be_visible();assert '시험' not in page.locator('#worldPrototypeNotice').inner_text()
  if region==4:expect(page.locator('#worldPrototypeNotice')).to_contain_text('숲 임시 BGM')
  cdp=context.new_cdp_session(page);points={}
  for i,selector in [(1,'#rotationJoystick'),(2,'#fire'),(3,'#game')]:
   b=page.locator(selector).bounding_box();points[i]={'id':i,'x':b['x']+b['width']*.55,'y':b['y']+b['height']*.5};cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':list(points.values())})
  for i in [1,2,3]:
   q=points.pop(i);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[q] if points else []})
  page.evaluate('window.addEventListener("click",function omit(e){if(e.target.id==="exitGame"){e.stopImmediatePropagation();window.removeEventListener("click",omit,true)}},true)');page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitCancel').tap();page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
 passed('All3 developer heroes start at boss5 with upgrade0; correct notice, trusted3-touch input and missing-click exit fallback/cancel/reopen/confirm work.')
 assert not errors,errors;assert not page.audit_external,page.audit_external
 passed('No uncaught JS error; offline external HTTP requests0. Approved combat, images, audio and controls remain protected.')
(a.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
