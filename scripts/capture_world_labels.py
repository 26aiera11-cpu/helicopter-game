"""Controlled before/after visual scenes; original baseline JS served without editing game files."""
import argparse,json
from pathlib import Path
from world_balance_harness import browser_game
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);rows=[]
with browser_game(pause=True,baseline=a.baseline) as (page,context,errors):
 page.locator('#startSelected').tap();page.wait_for_function('started')
 for w,h in [(915,412),(800,360),(568,320)]:
  page.set_viewport_size({'width':w,'height':h})
  for region in range(4,8):
   for phase in [1,5]:
    page.evaluate('([r,p])=>{start(0);stage=r;phase=p;if(p===5)spawnBossEncounter();transition=2;gameWorlds.syncUI();gameScoring.updateHUD();draw()}',[region,phase]);page.screenshot(path=str(a.output/f'region-{region}-phase-{phase}-{w}x{h}.png'));rows.append(page.evaluate('()=>({stage,phase,hud:hud.innerText,noticeHidden:worldPrototypeNotice.hidden})'))
  page.evaluate('started=false;gameAudioStarted=false;menu.classList.remove("hidden")');page.locator('#selectionHelp').tap();page.screenshot(path=str(a.output/f'help-{w}x{h}.png'));page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap();page.evaluate('stage=7;phase=5;runScore=12345;nextPhase()');page.wait_for_timeout(40);page.screenshot(path=str(a.output/f'full40-clear-{w}x{h}.png'));page.locator('#selectionSettings').tap();page.screenshot(path=str(a.output/f'leaderboard-{w}x{h}.png'));page.locator('#leaderboardClose').tap();page.locator('#startSelected').tap()
 assert not errors,errors
(a.output/'labels.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('Captured24 region/boss scenes +9 help/result/leaderboard views')
