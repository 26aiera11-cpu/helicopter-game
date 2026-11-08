"""Issue40 focused HP/lifecycle checks; reuse Issue39's bot for only24 fights."""
import argparse,csv,json,re,subprocess,sys,time
from pathlib import Path
from world2_boss_hp_preservation import ROOT,verify
sys.path.insert(0,str(ROOT/'scripts'))
from world_balance_harness import browser_game

p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');p.add_argument('--comparison-from',type=Path);a=p.parse_args();a.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':a.standalone,'passed':[],'preservation':verify(),'limits':['First HP trial, not final balance approval.','Issue39 fixed-seed perfect-information bot, actual60Hz update/health/attacks, no forced invulnerability/instant kills/revival in the24 comparison fights.','Separate lifecycle QA controls projectile contact and random reward rolls; it is not difficulty evidence.','No40-stage replay/full suite. Physical Galaxy and human reaction/speaker/sensor tests are not performed.']}
begin=time.monotonic()
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
passed('Exactly one index HP expression changes; all131 assets and reused Issue39 analysis are byte-identical to98676ed.')
bases=[20,35,50,65,72,80,90,100];scales={0:1,3:1.6,5:2.2}
try:
 if not a.standalone:
  for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',(ROOT/'index.html').read_text(),re.S):subprocess.run(['node','--check'],input=script,text=True,capture_output=True,check=True)
 with browser_game(standalone=a.standalone,pause=True) as (page,context,errors):
  page.evaluate((ROOT/'scripts/world_balance_probe.js').read_text())
  rows=[]
  for region in range(8):
   for hero in range(3):
    for up in [0,3,5]:
     row=page.evaluate('''v=>{balanceAudit.begin(v.hero);stage=v.region;phase=5;player.upgrade=v.up;spawnBossEncounter();const initial={hp:boss.hp,maxHp:boss.maxHp};player.upgrade=v.up===5?0:5;update(0);return {...v,...initial,afterUpgrade:boss.maxHp};}''',{'region':region,'hero':hero,'up':up})
     expected=bases[region]*scales[up];assert abs(row['hp']-expected)<1e-8 and row['hp']==row['maxHp']==row['afterUpgrade'],row;rows.append(row)
  report['HP_cases']=rows;page.evaluate('balanceAudit.clean()')
  passed('72 actual spawns:8regions x3heroes x0/3/5 levels; World1 stays20/35/50/65, World2 is72/80/90/100, original scales and spawn-time snapshot hold.')
  if not a.standalone and a.comparison_from:
   prior=json.loads(a.comparison_from.read_text());assert prior['preservation']==report['preservation'] and len(prior['comparison'])==24
   assert (ROOT/'scripts/world_balance_probe.js').read_bytes()==subprocess.check_output(['git','show',report['preservation']['baseline']+':scripts/world_balance_probe.js'],cwd=ROOT)
   report['comparison']=prior['comparison'];report['comparison_from']=str(a.comparison_from)
   assert all(abs(row['after_HP']-bases[row['region']]*scales[row['upgrade']])<1e-8 for row in report['comparison'])
   passed('Reused the24 successful fight measurements from this exact HP-only delta and unchanged Issue39 bot; only lifecycle assertions need a rerun.')
  elif not a.standalone:
   old=json.loads((ROOT/'docs/review/world-balance-audit/boss-encounters.json').read_text());comparison=[]
   for region in range(4,8):
    for hero in range(3):
     for up in [3,5]:
      scenario={'region':region,'upgrade':up,'lowHP':False,'item':'none'}
      prior=next(x for x in old if x['hero']==hero and x['encounter']==scenario)
      current=page.evaluate('v=>balanceAudit.run(...v)',[hero,202611083,'collect',120,scenario])
      assert not current['timeout'],current
      assert abs(current['bosses'][0]['startHP']-bases[region]*scales[up])<1e-8,current
      comparison.append({'region':region,'character':['뾰코','빙글','탱코'][hero],'upgrade':up,'before_HP':prior['bosses'][0]['startHP'],'after_HP':current['bosses'][0]['startHP'],'before_seconds':prior['seconds'],'after_seconds':current['seconds'],'before_defeated':prior['encounterDefeated'],'after_defeated':current['encounterDefeated'],'before_damage':prior['totals']['damage'],'after_damage':current['totals']['damage'],'deaths':current['deaths'],'shots':current['totals']['shots'],'blocked':current['totals']['blocked']})
   report['comparison']=comparison
   with (a.artifacts/'boss-comparison.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(comparison[0]));writer.writeheader();writer.writerows(comparison)
   passed('24 World2 fights only:3heroes x3/5 x4bosses, same Issue39 seed/policy/viewport and real HP damage; reused old results instead of rerunning old or40-stage analysis. Deaths are retained as measurements.')
  page.evaluate('''()=>{
   window.hp40Rewards=[];document.addEventListener('bossreward',e=>hp40Rewards.push({...e.detail,hp,upgrade:player.upgrade,region:stage}));
   window.hp40Storage=()=>JSON.stringify(Object.keys(localStorage).filter(k=>k.startsWith('heliTrio.')).sort().map(k=>[k,localStorage.getItem(k)]));
   window.hp40Lifecycle=(region,roll)=>{
    balanceAudit.begin(0,6000+region*2+(roll>.5));stage=region;phase=5;phaseKills=requiredKills;player.upgrade=3;hp=1;spawnBossEncounter();transition=0;spawn=999;hp40Rewards=[];
    const defeated=boss,initialHP=boss.maxHp;window.hp40Item={x:12,y:H-12,type:'hp',life:7.25,r:13,t:0,vx:0,vy:0,turn:99};items=[hp40Item];
    const before=hp40Storage(),random=Math.random;Math.random=()=>roll;let shots=0;
    try{while(boss&&shots++<500){bullets=[];shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(0);}}finally{Math.random=random;}
    const duplicateReward=grantBossReward(defeated);gameScoring.bossDefeated(defeated);
    for(let i=0;i<100&&started&&stage===region;i++)update(.04);
    const result=gameScoring.getLastResult(),after=hp40Storage(),recordCount=result?JSON.parse(localStorage.getItem('heliTrio.world2Trial.playHistory.v1')||'{"records":[]}').records.filter(r=>r.id===result.record.id).length:0;
    const savedBeforeRepeat=hp40Storage();if(region===7)gameScoring.finish('clear');
    return {region,roll,initialHP,dead:defeated.hp<=0,rewardGranted:defeated.rewardGranted,duplicateReward,events:hp40Rewards,score:runScore,stage,phase,hp,upgrade:player.upgrade,itemSame:items.includes(hp40Item),itemLife:hp40Item.life,started,result,storageUnchanged:before===after,recordCount,repeatStorageUnchanged:savedBeforeRepeat===hp40Storage()};
   };
  }''')
  lifecycle=[]
  for region in range(4,8):
   for roll in [.25,.75]:
    r=page.evaluate('v=>hp40Lifecycle(...v)',[region,roll]);assert r['dead'] and r['rewardGranted'] and r['duplicateReward'] is None and len(r['events'])==1 and r['score']==2000,r
    event=r['events'][0];assert event['region']==region and event['hp']==(3 if roll<.5 else 1) and event['upgrade']==(3 if roll<.5 else 4),r
    if region<7:assert r['started'] and r['stage']==region+1 and r['phase']==1 and r['hp']==(4 if roll<.5 else 3) and r['itemSame'] and 0<r['itemLife']<=7.25 and r['storageUnchanged'],r
    else:assert not r['started'] and r['result']['record']['score']==2000 and r['result']['record']['bossKills']==1 and r['recordCount']==1 and r['repeatStorageUnchanged'],r
    lifecycle.append(r)
  report['lifecycle']=lifecycle
  passed('8 controlled actual collision paths:4bosses xboth rewards;2000points/one reward, HP reward before existing region heal, items/life carried, next region and final clear/storage idempotency preserved.')
  page.evaluate('balanceAudit.clean();gameWorlds.setDeveloperStart({enabled:true,regionId:7,phase:5});')
  page.locator('#startSelected').tap();page.wait_for_function('started&&!!boss')
  assert page.evaluate('gameWorlds.isDeveloper()&&stage===7&&phase===5&&boss.hp===100&&enemies.length===0&&warnings.length===0&&player.upgrade===0')
  page.set_viewport_size({'width':568,'height':320});page.wait_for_function('W===568&&H===320&&canvas.width===568*dpr');page.evaluate('transition=0;draw()')
  if not a.standalone:page.screenshot(path=str(a.artifacts/'gigacore-100hp-568x320.png'))
  before=page.evaluate('hp40Storage()');page.evaluate('hp=0;update(0)');assert page.evaluate('gameOverPending&&!started&&!gameAudioStarted')
  page.wait_for_timeout(3100);assert page.evaluate('!menu.classList.contains("hidden")&&!gameOverPending&&document.getElementById("selectionResult").textContent===""')
  assert page.evaluate('hp40Storage()')==before
  passed('Trusted developer5 starts100HP GigaCore immediately;568x320 UI and original3s game-over/clean return hold; developer results do not enter TOP10/history.')
  assert not errors,errors
  assert not a.standalone or not page.audit_external,page.audit_external
  report['errors']=errors;report['external_requests']=page.audit_external
  passed('No uncaught browser errors; standalone executes the exact rebuilt HTML with network disabled and zero external requests.')
finally:
 report['elapsed_seconds']=round(time.monotonic()-begin,2)
 (a.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
