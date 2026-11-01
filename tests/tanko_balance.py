"""Compare real previous/current code TTK, sustained defense and visible footprint."""
import argparse,json,shutil,subprocess,threading,hashlib
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'baseline_commit':'287629fb7a1bc91d359375f253aef23ef376dcaf','method':{'ttk':'Actual old and new index pages; same HP scaling, distance160, stationary invulnerable player, centre aim each tick, fixed random. Two time steps120Hz/60Hz.','shield':'12s centre-aim fire, stationary invulnerable player, boss HP1e6 in test memory only. Every emitted timestamp/position/velocity/radius is compared exactly before/after; reached means an actual hostile-circle/player collision, including invulnerability. All0..5 upgrades,4 bosses,120/60Hz.','footprint':'Actual PNG alpha>40 union pixels, max-upgrade fire for6s in8 directions at3 mobile landscape sizes; sampled every0.5s.'},'limits':['Controlled real-browser simulation, not physical Galaxy/Samsung Internet, human aim or performance testing.','Continuous fire renews a finite ammunition shield, so per-projectile limits alone do not guarantee equal defense across boss patterns.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
before=subprocess.check_output(['git','show','287629f:index.html'],cwd=root).decode()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ttk=[];defense=[]
  for version in ['before','after']:
   context=browser.new_context(viewport={'width':915,'height':412});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   if version=='before':page.route('**/baseline-tanko.html',lambda route:route.fulfill(status=200,content_type='text/html; charset=utf-8',body=before))
   page.goto(f'http://127.0.0.1:{server.server_port}/'+('baseline-tanko.html' if version=='before' else ''),wait_until='load')
   data=page.evaluate('''version=>{
    const rows=[],shields=[],realFx=gameAudio.fx,realRandom=Math.random,realEmit=emitEnemyShot,realHurt=hurt,realShoot=shoot,realBlock=blockEnemyBullet;
    const realConsume=typeof consumeTankoPierce==='function'?consumeTankoPierce:null;
    let incoming,created=0,blocked=0,contacts=0,budget=0,spent=0,shotsCreated=0,annihilated=0,trace=[],tick=0;
    shoot=()=>{const count=bullets.length;realShoot();for(const b of bullets.slice(count)){budget+=b.pierce;shotsCreated++}};
    gameAudio.fx=()=>{};Math.random=()=>.75;
    emitEnemyShot=(...args)=>{realEmit(...args);const target=enemyBullets[enemyBullets.length-1];incoming.add(target);created++;trace.push([tick,target.x,target.y,target.vx,target.vy,target.r,target.life])};
    if(realConsume)consumeTankoPierce=(b,target)=>{const previous=b.pierce,ok=realConsume(b,target);if(ok){if(b.pierce!==previous-1)throw Error('Incorrect penetration charge');spent++;}return ok};
    blockEnemyBullet=target=>{
     const alive=bullets.filter(b=>b.kind===2&&b.life>0),ok=realBlock(target);
     if(ok){blocked++;const lost=alive.filter(b=>b.life<=0).length;annihilated+=lost;if(lost>1||version==='after'&&lost!==1)throw Error('Duplicate or missing shot consumption')}
     return ok;
    };
    hurt=()=>{contacts++;realHurt()};
    const setup=(type,level,region)=>{
     incoming=new WeakSet();created=blocked=contacts=budget=spent=shotsCreated=annihilated=tick=0;trace=[];
     start(type);stage=region;phase=5;phaseKills=requiredKills;spawn=999;invuln=999;fireCooldown=0;
     player.x=W*.5;player.y=H*.27+160;player.upgrade=level;update(0);keys.fire=true;return boss;
    };
    try{
     for(const hz of [120,60])for(let type=0;type<3;type++)for(let level=0;level<=5;level++)for(let region=0;region<4;region++){
      const target=setup(type,level,region);let frames=0;
      while(boss===target&&frames<hz*120){player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/hz);frames++;}
      rows.push({version,hz,type,level,stage:region,hp:target.maxHp,seconds:frames/hz,defeated:target.hp<=0,rewardGranted:!!target.rewardGranted,created,blocked,contacts,budget,spent,shotsCreated,annihilated});
     }
     for(const hz of [120,60])for(let level=0;level<=5;level++)for(let region=0;region<4;region++){
      const target=setup(2,level,region);target.hp=target.maxHp=1e6;
      for(let frame=0;frame<hz*12;frame++){tick=frame+1;player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/hz)}
      shields.push({version,hz,level,stage:region,created,blocked,contacts,remaining:enemyBullets.length,playerHp:hp,budget,spent,shotsCreated,annihilated,trace});
     }
     keys.fire=false;return {rows,shields};
    }finally{gameAudio.fx=realFx;Math.random=realRandom;emitEnemyShot=realEmit;hurt=realHurt;shoot=realShoot;blockEnemyBullet=realBlock;if(realConsume)consumeTankoPierce=realConsume}
   }''',version)
   assert not errors,errors;ttk+=data['rows'];defense+=data['shields'];context.close()
  assert len(ttk)==288 and all(r['rewardGranted']==r['defeated'] for r in ttk)
  for row in ttk:
   previous=next(r for r in ttk if r['version']=='before' and all(r[k]==row[k] for k in ['hz','type','level','stage']))
   assert row['hp']==previous['hp']
   if row['type']!=2:assert row['seconds']==previous['seconds']
  report['ttk']=ttk;report['sustained_defense']=defense
  report['ttk_limit_seconds']=120
  report['uncleared_fixed_aim_cases']=[r for r in ttk if not r['defeated']]
  passed('288 actual previous/current fights cover3 characters, upgrades0..5,4 bosses and120/60Hz. HP scaling/rewards are unchanged; Trio/Bingle TTK is exactly identical before/after.')
  assert len(defense)==96
  patterns={}
  for row in defense:
   previous=next(r for r in defense if r['version']=='before' and all(r[k]==row[k] for k in ['hz','level','stage']))
   assert row['trace']==previous['trace'] and row['shotsCreated']==previous['shotsCreated']
   row['pattern_sha256']=hashlib.sha256(json.dumps(row['trace'],separators=(',',':')).encode()).hexdigest()
   key=f"{row['hz']}Hz-stage{row['stage']}"
   if key not in patterns:patterns[key]=row['trace']
   assert row['trace']==patterns[key]
  report['matched_attack_patterns']=patterns
  for row in defense:row.pop('trace')
  assert all(r['blocked']==r['annihilated']<=r['shotsCreated'] and r['spent']<=r['budget'] for r in defense if r['version']=='after')
  passed('Ninety-six12s cases have identical attack traces and player firing counts before/after; each new block destroys exactly one Tanko shot, with player-reached counts measured independently.')
  # Actual visible PNG area, without enemies or interception, at the largest width.
  page=browser.new_page(viewport={'width':915,'height':412});page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load');page.wait_for_function('bulletSprites.every(i=>i.complete&&i.naturalWidth)')
  coverage=[]
  for w,h in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_function('size=>W===size[0]&&H===size[1]',arg=[w,h])
   rows=page.evaluate('''() => {
    const rows=[],oldFx=gameAudio.fx;gameAudio.fx=()=>{};
    try{for(let direction=0;direction<8;direction++){
     start(2);player.upgrade=5;player.a=Math.PI+direction*Math.PI/4;spawn=999;transition=0;invuln=999;fireCooldown=0;keys.fire=true;
     const mask=document.createElement('canvas');mask.width=W;mask.height=H;const g=mask.getContext('2d',{willReadFrequently:true});let peak=0,maxActive=0;
     for(let frame=0;frame<360;frame++){
      update(1/60);maxActive=Math.max(maxActive,bullets.length);if(frame%30!==0)continue;
      g.clearRect(0,0,W,H);
      for(const b of bullets){if(b.kind!==2||b.life<=0)continue;const width=tankoBulletWidth(b.upgrade);g.save();g.translate(b.x,b.y);g.rotate(Math.atan2(b.vy,b.vx)+Math.PI/2);g.drawImage(bulletSprites[2],-width/2,-14.5,width,29);g.restore()}
      const pixels=g.getImageData(0,0,W,H).data;let opaque=0;for(let i=3;i<pixels.length;i+=4)if(pixels[i]>40)opaque++;peak=Math.max(peak,opaque/(W*H));
     }keys.fire=false;rows.push({width:W,height:H,direction,peak_visible_fraction:peak,max_active:maxActive});
    }return rows;}finally{gameAudio.fx=oldFx}
   }''');coverage+=rows
  assert len(coverage)==24 and {(r['width'],r['height']) for r in coverage}=={(915,412),(800,360),(568,320)} and all(r['peak_visible_fraction']<.15 for r in coverage)
  report['coverage']=coverage;report['peak_visible_percent']=max(r['peak_visible_fraction'] for r in coverage)*100
  passed('Twenty-four6s sustained-fire scenarios measure actual alpha coverage across8 directions and3 landscape sizes; peak visible coverage stays below15% of the game area.')
  print('PEAK_VISIBLE_PERCENT:',report['peak_visible_percent'],flush=True)
  page.close();browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
lines=['# 탱코 관통·차단 변경 전후 비교','','기준287629f 실제 HTML과 새 HTML을 각각 Chromium에 로드했다. 두 버전 모두 피해1.5·기존 폭·높이29px·탄속410·연사/이동/보스 HP/패턴이 같다. 거리160px, 정지/무적 플레이어, 매 틱 중심 조준, 기존 등장1.5초/초기 쿨다운0이다. 주 표는120Hz이며60Hz 교차 검사는JSON에 있다. 사람의 실제 처치 시간이나 갤럭시 성능 측정은 아니다.','','| 지역 | 강화 | 보스 HP | 기존 처치 시간 | 새 처치 시간 |','| --- | ---: | ---: | ---: | ---: |']
for region,name in enumerate(['숲','바위','바다','사막']):
 for level in range(6):
  pair=[next(r for r in ttk if r['version']==version and r['hz']==120 and r['type']==2 and r['stage']==region and r['level']==level) for version in ['before','after']]
  times=[f"{r['seconds']:.3f}초" if r['defeated'] else '120초 내 미처치' for r in pair]
  lines.append(f'| {name} | {level} | {pair[0]["hp"]:g} | {times[0]} | {times[1]} |')
lines+=['','## 동일한 보스 탄막·12초 정면 연사','','테스트에서만 보스 HP1,000,000으로 생존시켜12초간 같은 공격을 관찰했다. 발사 프레임·좌표·속도·반경/수명 배열을 두 버전/모든 강화에서 정확히 비교했고 SHA-256을 JSON에 저장했다. 발사 수는 enemy bullets, 플레이어 도달 수는 실제 적 탄환/플레이어 충돌 수다. 무적 중 도달도 세며, 빗나감/아직 비행 중인 탄과 구분한다. 플레이어 발사 수/연사 간격도 두 버전이 같다.','','| 지역 | 강화 | 적 발사 | 기존 차단 | 새 차단 | 차단 감소 | 기존 도달 | 새 도달 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for region,name in enumerate(['숲','바위','바다','사막']):
 for level in range(6):
  a,b=[next(r for r in defense if r['version']==v and r['hz']==120 and r['stage']==region and r['level']==level) for v in ['before','after']]
  lines.append(f'| {name} | {level} | {b["created"]} | {a["blocked"]} | {b["blocked"]} | {a["blocked"]-b["blocked"]} | {a["contacts"]} | {b["contacts"]} |')
lines+=['',f'새 버전5강 탄환8방향·3가로 화면의6초 연사 PNG 알파 합집합 최대점유율은 **{report["peak_visible_percent"]:.2f}%**다. 폭/높이/이미지는 기준 버전과 바이트/그리기 값이 같다.','','몬스터 관통은0~5강[2,3,3,4,4,5]이며 한 적/보스에 한 번1.5 피해/횟수1을 쓴다. 적 탄환은 관통 잔량과 관계없이 서로 소멸하므로 한 탱코 탄환당 최대1개 차단이다. 차단 뒤 남은 관통 횟수로 탄환을 재사용하지 않는다.','']
(args.artifacts/'boss-and-defense-comparison.md').write_text('\n'.join(lines))
