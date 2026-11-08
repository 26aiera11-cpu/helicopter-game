"""Controlled real six-kill phase1 benchmarks; separate from natural40-stage routes."""
import json
from world_balance_harness import ROOT,browser_game
OUT=ROOT/'docs/review/world-balance-audit';rows=[]
with browser_game(pause=True) as (page,context,errors):
 page.evaluate((ROOT/'scripts/world_balance_probe.js').read_text());page.evaluate('balanceAudit.definitions()')
 for region in range(8):
  for hero in range(3):
   for upgrade in [1,3,5]:
    for low in [False,True]:
     for item in ['none','power','hp']:
      scenario={'region':region,'phase':1,'upgrade':upgrade,'lowHP':low,'item':item,'normal':True};r=page.evaluate('v=>balanceAudit.run(...v)',[hero,202611083,'collect',180,scenario]);rows.append({'hero':hero,'scenario':scenario,'seconds':r['seconds'],'cleared':r['normalPhaseCleared'],'deaths':r['deaths'],'damage_received':r['totals']['damage'],'shots':r['totals']['shots'],'blocked':r['totals']['blocked'],'result':r['result'],'phases':r['phases']})
  (OUT/'normal-encounters.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');print('Normal phase region',region,'cases',len(rows),flush=True)
 assert not errors,errors
