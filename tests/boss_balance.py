"""Deterministic TTK via actual shoot/update/homing/collision/moving-boss code."""
import argparse,json,shutil,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'method':{'viewport':[915,412],'step_seconds':1/120,'simulation_timeout_seconds':60,'initial_distance_px':160,'aim':'Exact centre aim each simulation tick; actual boss movement, attacks, projectile spread/homing and hit tests; player stationary and invulnerable. Start with empty bullets, zero fire cooldown, existing 1.5s boss transition.','before':'Unscaled HP using current weapon rules (including current Tanko damage1.5); only initial hp/maxHp overridden. This is an HP-only comparison, not the previous Tanko combat version.','requested':'Initial proposed linear 1 + 0.2 * upgrade; only initial HP overridden in test memory.','after':'Actual product spawn HP, without test override.','limits':'Controlled reproducible simulation in a real browser, not human difficulty or physical-device frame-rate measurement. 120Hz fixed step; a second 60Hz matrix checks the conclusion.'},'limits':['Physical Galaxy/Samsung Internet and human aiming/latency/weapon balance are not tested. HP-only scaling cannot make every upgraded character equally fast without changing protected attacks.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':915,'height':412});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load')
  rows=page.evaluate('''() => {
   const rows=[],oldFx=gameAudio.fx,oldRandom=Math.random;
   gameAudio.fx=()=>{};Math.random=()=>.75;
   try{for(const hz of [120,60])for(const model of ['before','requested','after'])for(let type=0;type<3;type++)for(const level of [0,1,3,5])for(let region=0;region<4;region++){
    start(type);stage=region;phase=5;phaseKills=requiredKills;spawn=999;invuln=999;fireCooldown=0;
    player.x=W*.5;player.y=H*.27+160;player.upgrade=level;update(0);const target=boss;
    if(model!=='after')target.hp=target.maxHp=(20+15*region)*(model==='before'?1:1+.2*level);
    keys.fire=true;let frames=0,firstAttack=null,shots=0;const realShoot=shoot;
    shoot=()=>{shots++;realShoot()};
    try{while(boss===target&&frames<hz*60){
     player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/hz);frames++;
     if(firstAttack===null&&enemyBullets.length)firstAttack=frames/hz;
    }}finally{shoot=realShoot}
    rows.push({hz,model,type,level,stage:region,hp:target.maxHp,seconds:frames/hz,shots,firstAttack,defeated:target.hp<=0,rewardGranted:target.rewardGranted===true,score:runScore,regionAfter:stage,phaseAfter:phase});keys.fire=false;
   }return rows;}finally{gameAudio.fx=oldFx;Math.random=oldRandom}
  }''')
  assert len(rows)==288 and all(r['defeated'] and r['rewardGranted'] and r['score']==2000 for r in rows), {'count':len(rows),'failed':[r for r in rows if not (r['defeated'] and r['rewardGranted'] and r['score']==2000)]}
  report['timings']=rows
  passed('288 controlled actual-code fights cover all four bosses, three characters and upgrades 0/1/3/5 at 120Hz and 60Hz, comparing original, requested and final HP.')
  scale=[1,1.1,1.4,1.6,1.9,2.2];report['final_hp_scale']=scale
  exceptions=[]
  for r in rows:
   if r['model']=='after':
    assert abs(r['hp']-(20+15*r['stage'])*scale[r['level']])<1e-9
    base=next(a for a in rows if a['hz']==r['hz'] and a['model']=='before' and a['type']==r['type'] and a['stage']==r['stage'] and a['level']==0)
    if r['level']==0:assert r['seconds']==base['seconds'],(r,base)
    elif r['type']!=2:assert r['seconds']<base['seconds'],(r,base)
    elif r['seconds']>=base['seconds']:exceptions.append({'hz':r['hz'],'stage':r['stage'],'level':r['level'],'upgraded_seconds':r['seconds'],'unupgraded_seconds':base['seconds']})
  report['tanko_upgrade_ttk_balance_findings']=exceptions
  passed('Unupgraded HP/TTK and all HP multipliers remain unchanged; Trio/Bingle upgrades retain their advantage. Tanko TTK exceptions under the new mutual-interception rule are explicitly recorded as balance findings, not hidden by changing HP.')
  # All six spawn levels, then change the player's upgrade mid-fight.
  snapshots=page.evaluate('''() => {
   const rows=[];
   for(let type=0;type<3;type++)for(let level=0;level<=5;level++)for(let region=0;region<4;region++){
    start(type);stage=region;phase=5;phaseKills=requiredKills;spawn=999;invuln=999;player.upgrade=level;update(0);
    const before={hp:boss.hp,maxHp:boss.maxHp};player.upgrade=(level+1)%6;update(.01);
    rows.push({type,level,stage:region,before,after:{hp:boss.hp,maxHp:boss.maxHp}});
   }return rows;
  }''')
  for r in snapshots:assert r['before']==r['after'] and abs(r['before']['hp']-(20+15*r['stage'])*scale[r['level']])<1e-9
  report['spawn_snapshot_checks']=snapshots
  passed('All 72 character/region/level spawn combinations have correct hp/maxHp; changing upgrades mid-combat never changes existing boss HP.')
  page.evaluate('start(0);stage=3;phase=5;phaseKills=requiredKills;player.upgrade=5;invuln=999;spawn=999;update(0);boss.hp=boss.maxHp/2;transition=0;gameExitDialogOpen=true;draw()')
  page.screenshot(path=str(args.artifacts/'scaled-boss-half-health.png'))
  assert not errors,errors
  passed('The boss health bar renders against the snapshotted maxHp; existing collision/reward/progression paths finish every fight without JS errors.')
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
lines=['# 보스 체력·처치 시간 비교','','단위: 초. 실제 발사/탄환/보스 이동 코드를 고정 1/120초로 실행했다. 160px 거리, 매 틱 중심 조준, 무적·정지 플레이어 기준의 재현 가능한 비교이며 실제 사람의 처치 시간은 아니다. 60Hz 교차 검사도 JSON에 포함한다.','','최종 배율(강화 0~5): **1.0 / 1.1 / 1.4 / 1.6 / 1.9 / 2.2**. 기본 HP는 20/35/50/65다. 등장할 때만 적용한다.','','| 캐릭터 | 지역 | 강화 | 변경 전 | 제안식 0.2 | 최종 |','| --- | --- | ---: | ---: | ---: | ---: |']
for type,name in enumerate(['트리오','빙글','탱코']):
 for stage,region in enumerate(['숲','바위','바다','사막']):
  for level in [0,1,3,5]:
   values=[next(r['seconds'] for r in rows if r['hz']==120 and r['model']==model and r['type']==type and r['level']==level and r['stage']==stage) for model in ['before','requested','after']]
   lines.append(f'| {name} | {region} | {level} | '+ ' | '.join(f'{v:.3f}' for v in values)+' |')
lines+=['','이 표의 before/requested/after는 현재 무기 규칙을 공통으로 사용하고 보스 HP만 비교한다. 탱코 피해1.5 적용 전후의 실제 코드 비교는 tests/tanko_balance.py 및 docs/review/tanko-combat/balance/boss-and-defense-comparison.md를 따른다.','','HP 배율 결정 이력은 DEVELOPMENT_LOG.md 27절과 당시 docs/review/progression/boss-balance/에 보존되어 있다. 이 검사는 현재 무기에서 기존 체력 배율/등장 HP 고정을 확인하며 보정값을 자동으로 재설정하지 않는다. 상호 소멸 차단으로 생긴 탱코 강화 처치 시간 역전은 JSON의 tanko_upgrade_ttk_balance_findings에 남기고, 트리오/빙글의 강화 이점은 계속 엄격히 검사한다.','']
(args.artifacts/'boss-ttk-comparison.md').write_text('\n'.join(lines))
