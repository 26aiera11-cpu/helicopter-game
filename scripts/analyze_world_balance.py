"""Issue39 isolated original-engine measurements; never changes shipped balance."""
import argparse,hashlib,json
from pathlib import Path
from world_balance_harness import ROOT,BASE,browser_game
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'docs/review/world-balance-audit');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
source=(ROOT/'index.html').read_text();update=source[source.index('function update(dt)'):]
move=update[update.index(' for(let b of bullets){'):update.index(' for(let e of enemies){')]
fire=update[update.index(' fireCooldown-=dt;'):update.index(' spawn-=dt;')]
with browser_game(pause=True) as (page,ctx,errors):
 page.evaluate('window.auditAdvanceBullets=dt=>{'+move+'}');page.evaluate('window.auditFireTick=dt=>{'+fire+'}');page.evaluate((ROOT/'scripts/world_balance_probe.js').read_text())
 definitions=page.evaluate('balanceAudit.definitions()');(a.output/'definitions.json').write_text(json.dumps(definitions,ensure_ascii=False,indent=2)+'\n')
 assays=[]
 for hero in range(3):
  for up in [0,1,3,5]:
   for distance in [80,160,240]:
    for radius in [16,48]:
     for rate in [60,120]:assays.append(page.evaluate('v=>balanceAudit.assay(...v)',[hero,up,distance,radius,1e9,12,rate]))
 (a.output/'weapon-assays.json').write_text(json.dumps(assays,indent=2)+'\n');print('Weapon assays',len(assays),flush=True)
 runs=[]
 for seed,policy in [(202611081,'ignore'),(202611082,'opportunistic'),(202611083,'collect')]:
  for hero in range(3):
   row=page.evaluate('v=>balanceAudit.run(...v)',[hero,seed,policy,1800]);runs.append(row);(a.output/'route-samples.json').write_text(json.dumps(runs,ensure_ascii=False,indent=2)+'\n');print('Route',hero,seed,policy,'region',row['stage'],'phase',row['phase'],'up',row['upgrade'],'deaths',row['deaths'],'seconds',round(row['seconds'],2),flush=True)
 again=page.evaluate('v=>balanceAudit.run(...v)',[0,202611081,'ignore',1800]);fields=['seconds','stage','phase','totals','phases','boundaries','bosses'];equality={k:again[k]==runs[0][k] for k in fields};(a.output/'seed-replay.json').write_text(json.dumps(equality,indent=2)+'\n');assert all(equality.values()),equality
 encounters=[]
 for region in range(8):
  for hero in range(3):
   for up in [0,1,3,5]:
    for low in [False,True]:
     for item in (['none'] if up==0 else ['none','power','hp']):
      scenario={'region':region,'upgrade':up,'lowHP':low,'item':item};row=page.evaluate('v=>balanceAudit.run(...v)',[hero,202611083,'collect',120,scenario]);encounters.append({k:row[k] for k in ['hero','encounter','encounterDefeated','seconds','deaths','firstDeath','totals','bosses','hp','upgrade']})
  (a.output/'boss-encounters.json').write_text(json.dumps(encounters,ensure_ascii=False,indent=2)+'\n');print('Boss region',region,'cases',len(encounters),flush=True)
 assert not errors,errors
 (a.output/'measurement-provenance.json').write_text(json.dumps({'baseline':BASE,'index_sha256':hashlib.sha256(source.encode()).hexdigest(),'original_projectile_loop_sha256':hashlib.sha256(move.encode()).hexdigest(),'original_fire_loop_sha256':hashlib.sha256(fire.encode()).hexdigest(),'browser':ctx.browser.version,'routes':len(runs),'weapon_assays':len(assays),'boss_encounters':len(encounters),'forced_invulnerability':False,'instant_kills':False,'revival':False,'frame_step_hz':60,'fresh_profile':True,'human_playtest':False},indent=2)+'\n')
