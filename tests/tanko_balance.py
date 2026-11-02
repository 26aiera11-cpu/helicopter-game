"""Actual before/after cadence: matched boss traces,12s accounting and normal-HP TTK."""
import argparse,json,shutil,subprocess,threading,hashlib
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
baseline='f622f3f9c8e82f390b40883abd1abd8f6b9e7f71';before=subprocess.check_output(['git','show',baseline+':index.html'],cwd=root).decode()
report={'baseline':baseline,'passed':[],'method':{'viewport':[915,412],'steps_hz':[120,60],'distance':160,'aim':'Stationary player, centre aim refreshed each tick, fixed random. Existing1.5s boss transition included; first trigger at first update with zero initial cooldown.','ttk':'Actual previous/current pages, normal spawn HP, invulnerable player for reproducible uninterrupted TTK; all3 characters/upgrades0..5/four regions.','defense':'12s for each boss at upgrades0/1/3/5. Test-only boss HP1e6 keeps it alive. Tanko starts with actual9HP and normal hurt/invulnerability; no invulnerability override during defense. Enemy timestamps/positions/velocities/radii/lifetimes must match exactly.','volleys':'One invocation of shoot(); generated projectiles also counted, since upgrades3/5 create two per volley.','reached':'An actual enemy-circle/player hit, counted even during native invulnerability; HP damage events recorded separately.','passed':'Neither intercepted nor player-reached, and removed by arena bounds/lifetime before12s. Still-flying at12s is separate. emitted=blocked+reached+passed+flying.'},'limits':['Controlled Chromium simulation, not physical Galaxy/Samsung Internet performance or human aim.','Finite-window counts reflect the unchanged frame scheduler and first-shot inclusion; exact ideal rate is80%.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ttk=[];defense=[];calibrations=[]
  for version in ['before','after']:
   page=browser.new_page(viewport={'width':915,'height':412});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   if version=='before':page.route('**/balance-baseline.html',lambda route:route.fulfill(status=200,content_type='text/html; charset=utf-8',body=before))
   page.goto(f'http://127.0.0.1:{server.server_port}/'+('balance-baseline.html' if version=='before' else ''),wait_until='load')
   data=page.evaluate('''version=>{
    const rows=[],shields=[],realFx=gameAudio.fx,realRandom=Math.random,realEmit=emitEnemyShot,realHurt=hurt,realShoot=shoot,realBlock=blockEnemyBullet;
    let emitted=[],blockedTargets,reachedTargets,volleys=0,projectiles=0,damageEvents=0,tick=0,trace=[],fireTrace=[];
    gameAudio.fx=()=>{};Math.random=()=>.75;
    shoot=()=>{const count=bullets.length;realShoot();volleys++;projectiles+=bullets.length-count;fireTrace.push(tick)};
    emitEnemyShot=(...args)=>{realEmit(...args);const b=enemyBullets[enemyBullets.length-1];emitted.push(b);trace.push([tick,b.x,b.y,b.vx,b.vy,b.r,b.life])};
    blockEnemyBullet=b=>{
     const live=bullets.filter(s=>s.kind===2&&s.life>0),ok=realBlock(b);
     if(ok){if(blockedTargets.has(b)||reachedTargets.has(b)||live.filter(s=>s.life<=0).length!==1)throw Error('Duplicate or incorrect mutual interception');blockedTargets.add(b)}
     return ok;
    };
    hurt=()=>{
     const candidates=emitted.filter(b=>b.life===0&&!blockedTargets.has(b)&&!reachedTargets.has(b)&&Math.hypot(b.x-player.x,b.y-player.y)<b.r+12);
     if(candidates.length!==1)throw Error('Expected one identifiable enemy-bullet/player contact');
     reachedTargets.add(candidates[0]);const previous=hp;realHurt();if(hp<previous)damageEvents++;
    };
    const setup=(type,level,region)=>{
     emitted=[];blockedTargets=new Set();reachedTargets=new Set();volleys=projectiles=damageEvents=tick=0;trace=[];fireTrace=[];
     start(type);stage=region;phase=5;phaseKills=requiredKills;spawn=999;invuln=999;fireCooldown=0;
     player.x=W*.5;player.y=H*.27+160;player.upgrade=level;update(0);keys.fire=true;return boss;
    };
    try{
     for(const hz of [120,60])for(let type=0;type<3;type++)for(let level=0;level<=5;level++)for(let region=0;region<4;region++){
      const target=setup(type,level,region);let frames=0;
      while(boss===target&&frames<hz*120){tick=frames+1;player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/hz);frames++;}
      rows.push({version,hz,type,level,stage:region,hp:target.maxHp,seconds:frames/hz,defeated:target.hp<=0,rewardGranted:!!target.rewardGranted,volleys,projectiles,blocked:blockedTargets.size,reached:reachedTargets.size});
     }
     for(const hz of [120,60])for(const level of [0,1,3,5])for(let region=0;region<4;region++){
      const target=setup(2,level,region);target.hp=target.maxHp=1e6;invuln=0;
      for(let frame=0;frame<hz*12;frame++){tick=frame+1;player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/hz)}
      const live=new Set(enemyBullets);let escaped=0;
      for(const b of emitted){
       if(!blockedTargets.has(b)&&!reachedTargets.has(b)&&!live.has(b)){
        if(!(b.life<=0||b.x<=-30||b.x>=W+30||b.y<=-30||b.y>=H+30))throw Error('Unclassified projectile disappearance');escaped++;
       }
      }
      shields.push({version,hz,level,stage:region,emitted:emitted.length,volleys,projectiles,blocked:blockedTargets.size,reached:reachedTargets.size,passed:escaped,flying:enemyBullets.length,hp_end:hp,damage_events:damageEvents,started,trace,fireTrace});
     }
     setup(2,0,0);keys.fire=false;invuln=0;boss.shot=99;
     emitEnemyShot({x:player.x,y:player.y+16});update(0);
     const calibration={version,emitted:emitted.length,reached:reachedTargets.size,damage_events:damageEvents,hp};
     keys.fire=false;return {rows,shields,calibration};
    }finally{gameAudio.fx=realFx;Math.random=realRandom;emitEnemyShot=realEmit;hurt=realHurt;shoot=realShoot;blockEnemyBullet=realBlock}
   }''',version)
   assert not errors,errors;ttk+=data['rows'];defense+=data['shields'];calibrations.append(data['calibration']);page.close()
  assert len(ttk)==288 and all(r['defeated'] and r['rewardGranted'] for r in ttk)
  for row in ttk:
   original=next(r for r in ttk if r['version']=='before' and all(r[k]==row[k] for k in ['hz','type','level','stage']))
   assert row['hp']==original['hp']
   if row['type']!=2:assert row==dict(original,version=row['version'])
  report['ttk']=ttk
  passed('288 actual old/new fights preserve boss HP/rewards; every fight ends, and Trio/Bingle entire fight statistics remain identical at all upgrades and120/60Hz.')
  assert len(defense)==64;patterns={}
  for row in defense:
   original=next(r for r in defense if r['version']=='before' and all(r[k]==row[k] for k in ['hz','level','stage']))
   assert row['trace']==original['trace'] and row['fireTrace'][0]==original['fireTrace'][0]
   assert row['projectiles']==row['volleys']*(1 if row['level']<2 else 2)
   if row['version']=='after':assert row['volleys']<original['volleys']
   row['attack_sha256']=hashlib.sha256(json.dumps(row['trace'],separators=(',',':')).encode()).hexdigest()
   key=f"{row['hz']}Hz-stage{row['stage']}"
   if key not in patterns:patterns[key]=row['trace']
   assert row['trace']==patterns[key]
  for row in defense:
   row['fire_times_seconds']=[v/row['hz'] for v in row.pop('fireTrace')];row.pop('trace')
  report['matched_attack_patterns']=patterns;report['sustained_defense']=defense
  passed('64 twelve-second cases cover four bosses×upgrades0/1/3/5×120/60Hz×old/new; enemy traces match exactly, first-shot timing matches, and Tanko volleys/projectiles decrease.')
  for row in defense:
   assert row['emitted']==row['blocked']+row['reached']+row['passed']+row['flying']
   assert row['hp_end']==9-row['damage_events'] and row['damage_events']<=row['reached'] and row['started']
  assert all(c['emitted']==c['reached']==c['damage_events']==1 and c['hp']==8 for c in calibrations)
  report['positive_contact_calibrations']=calibrations
  reached=[r for r in defense if r['version']=='after' and r['reached']>0]
  report['new_gap_cases']=reached;report['gap_cases_count']=len(reached)
  passed('Every emitted bullet is accounted for as blocked, player-reached, passed/expired, or still flying; native HP/invulnerability remains active, and a deliberately unblocked shot calibrates reached1/damage1/HP9→8 in each version.')
  # Long-window practical volley rates, with both endpoint effects and timestep exposed.
  rates=[]
  for hz in [120,60]:
   for level in [0,1,3,5]:
    a,b=[next(r for r in defense if r['version']==v and r['hz']==hz and r['level']==level and r['stage']==0) for v in ['before','after']]
    rates.append({'hz':hz,'level':level,'before_volleys':a['volleys'],'after_volleys':b['volleys'],'ratio':b['volleys']/a['volleys'],'before_projectiles':a['projectiles'],'after_projectiles':b['projectiles']})
  report['practical_12s_rates']=rates
  passed('Requested defense metrics and normal-HP TTK are recorded for both time steps; no extra balance adjustment is applied when frontal defense remains strong.')
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
lines=['# 탱코 연사20% 감소 전후 비교','','기준f622f3f 실제 HTML과 새 HTML을 Chromium에 각각 로드했다. 제품 변경은 탱코 발사 간격×1.25 한 곳이다. 거리160px, 정지, 매 틱 중앙 조준, 기존 등장 전환1.5초/최초 쿨다운0을 포함한다. 실제 갤럭시 성능이나 사람의 조준 시험이 아니다.','','발사 횟수는 shoot() 동작 수다. 0/1강은1발,3/5강은2발을 생성하므로 생성 탄환 수도 기록한다. 적 도달은 피격 무적 중이라도 실제 적 탄환/플레이어 충돌을 센다. 통과는 차단/도달 없이 화면 밖 또는 수명 종료로 제거된 탄이고12초 끝에 비행 중인 탄은 별도다. 적 발사=차단+도달+통과+비행 중이 모든 행에서 성립한다.','','12초 방어 검사에서만 보스 HP1,000,000을 사용했다. 플레이어는 실제9HP와 기본 피격 무적을 유지하고12초 생존했다. 처치 시간은 정상 보스 HP와 무적 플레이어로 별도 측정했다. 적 발사 시각/위치/속도/반경/수명 배열의 일치를 검사하고 해시를 보관했다.']
for hz in [120,60]:
 lines += ['',f'## {hz}Hz ·12초 방어 비교','','모든 셀의 화살표는 기존→새 버전이다. 적 발사는 두 버전이 같다.','','| 지역 | 강화 | 발사 동작 | 생성 탄환 | 적 발사 | 차단 | 도달 | 통과 | 비행 중 |','| --- | ---: | --- | --- | ---: | --- | --- | --- | --- |']
 for stage,name in enumerate(['숲','바위','바다','사막']):
  for level in [0,1,3,5]:
   a,b=[next(r for r in defense if r['version']==v and r['hz']==hz and r['stage']==stage and r['level']==level) for v in ['before','after']]
   arrow=lambda k:f'{a[k]}→{b[k]}'
   lines.append(f'| {name} | {level} | {arrow("volleys")} | {arrow("projectiles")} | {b["emitted"]} | {arrow("blocked")} | {arrow("reached")} | {arrow("passed")} | {arrow("flying")} |')
 lines += ['',f'### {hz}Hz ·정상 HP 보스 처치 시간','','| 지역 | 강화 | 보스 HP | 기존 | 새 버전 |','| --- | ---: | ---: | ---: | ---: |']
 for stage,name in enumerate(['숲','바위','바다','사막']):
  for level in range(6):
   a,b=[next(r for r in ttk if r['version']==v and r['hz']==hz and r['type']==2 and r['stage']==stage and r['level']==level) for v in ['before','after']]
   lines.append(f'| {name} | {level} | {b["hp"]:g} | {a["seconds"]:.3f}초 | {b["seconds"]:.3f}초 |')
lines += ['','## 발사 수와 남은 균형 결과','','| Hz | 강화 | 기존 발사 | 새 발사 | 기존 대비 |','| --- | ---: | ---: | ---: | ---: |']
for r in rates:lines.append(f'| {r["hz"]} | {r["level"]} | {r["before_volleys"]} | {r["after_volleys"]} | {r["ratio"]*100:.2f}% |')
lines += ['',f'새 버전의 플레이어 도달이 양수인 조건은32개 중 **{len(reached)}개**다. 각 조건의 실제 체력 감소/피격 수는 JSON에 있다. 도달이0인 조건의 정면 방어가 충분히 낮아졌다고 표현하지 않는다. 요청한20% 외의 연사·탄속·폭·관통/차단·보스 수치는 추가로 바꾸지 않았다.','']
(args.artifacts/'comparison.md').write_text('\n'.join(lines))
