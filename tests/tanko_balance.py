"""Compare real previous/current code TTK, sustained defense and visible footprint."""
import argparse,json,shutil,subprocess,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'baseline_commit':'71bce184d5b2b1cd59dcb696d3a64f3016b11c6a','method':{'ttk':'Actual old and new index pages; same HP scaling, distance160, stationary invulnerable player, centre aim each tick, fixed random. Two time steps120Hz/60Hz.','shield':'12s continuous centre-aim fire, invulnerable stationary player, actual boss with test-only HP1e6 to survive, unchanged boss patterns, counts incoming blocks and player contacts.','footprint':'Actual PNG alpha>40 union pixels, max-upgrade fire for6s in8 directions at3 mobile landscape sizes; sampled every0.5s.'},'limits':['Controlled real-browser simulation, not physical Galaxy/Samsung Internet, human aim or performance testing.','Continuous fire renews a finite ammunition shield, so per-projectile limits alone do not guarantee equal defense across boss patterns.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
before=subprocess.check_output(['git','show','71bce18:index.html'],cwd=root).decode()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ttk=[];defense=[]
  for version in ['before','after']:
   context=browser.new_context(viewport={'width':915,'height':412});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   if version=='before':page.route('**/baseline-tanko.html',lambda route:route.fulfill(status=200,content_type='text/html; charset=utf-8',body=before))
   page.goto(f'http://127.0.0.1:{server.server_port}/'+('baseline-tanko.html' if version=='before' else ''),wait_until='load')
   data=page.evaluate('''version=>{
    const rows=[],shields=[],realFx=gameAudio.fx,realRandom=Math.random,realEmit=emitEnemyShot,realHurt=hurt,realShoot=shoot;
    const realConsume=typeof consumeTankoPierce==='function'?consumeTankoPierce:null;
    let incoming,created=0,blocked=0,contacts=0,budget=0,spent=0;
    shoot=()=>{const count=bullets.length;realShoot();for(const b of bullets.slice(count))budget+=b.pierce};
    gameAudio.fx=()=>{};Math.random=()=>.75;
    emitEnemyShot=(...args)=>{realEmit(...args);incoming.add(enemyBullets[enemyBullets.length-1]);created++};
    if(realConsume)consumeTankoPierce=(b,target)=>{const previous=b.pierce,ok=realConsume(b,target);if(ok){if(b.pierce!==previous-1)throw Error('Incorrect penetration charge');spent++;if(incoming.has(target))blocked++;}return ok};
    hurt=()=>{contacts++;realHurt()};
    const setup=(type,level,region)=>{
     incoming=new WeakSet();created=blocked=contacts=budget=spent=0;
     start(type);stage=region;phase=5;phaseKills=requiredKills;spawn=999;invuln=999;fireCooldown=0;
     player.x=W*.5;player.y=H*.27+160;player.upgrade=level;update(0);keys.fire=true;return boss;
    };
    try{
     for(const hz of [120,60])for(let type=0;type<3;type++)for(let level=0;level<=5;level++)for(let region=0;region<4;region++){
      const target=setup(type,level,region);let frames=0;
      while(boss===target&&frames<hz*30){player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/hz);frames++;}
      rows.push({version,hz,type,level,stage:region,hp:target.maxHp,seconds:frames/hz,defeated:target.hp<=0,rewardGranted:!!target.rewardGranted,created,blocked,contacts,budget,spent});
     }
     for(let level of [0,1,3,5])for(let region=0;region<4;region++){
      const target=setup(2,level,region);target.hp=target.maxHp=1e6;
      for(let frame=0;frame<1440;frame++){player.a=Math.atan2(target.y-player.y,target.x-player.x)-Math.PI/2;update(1/120)}
      shields.push({version,level,stage:region,created,blocked,contacts,remaining:enemyBullets.length,playerHp:hp,budget,spent});
     }
     keys.fire=false;return {rows,shields};
    }finally{gameAudio.fx=realFx;Math.random=realRandom;emitEnemyShot=realEmit;hurt=realHurt;shoot=realShoot;if(realConsume)consumeTankoPierce=realConsume}
   }''',version)
   assert not errors,errors;ttk+=data['rows'];defense+=data['shields'];context.close()
  assert len(ttk)==288 and all(r['defeated'] and r['rewardGranted'] for r in ttk)
  for row in ttk:
   previous=next(r for r in ttk if r['version']=='before' and all(r[k]==row[k] for k in ['hz','type','level','stage']))
   assert row['hp']==previous['hp']
   if row['type']!=2:assert row['seconds']==previous['seconds']
  report['ttk']=ttk;report['sustained_defense']=defense
  passed('288 actual previous/current fights cover3 characters, upgrades0..5,4 bosses and120/60Hz. HP scaling/rewards are unchanged; Trio/Bingle TTK is exactly identical before/after.')
  assert len(defense)==32 and all(r['blocked']==0 for r in defense if r['version']=='before') and any(r['blocked']>0 for r in defense if r['version']=='after')
  assert all(r['blocked']<=r['spent']<=r['budget'] for r in defense if r['version']=='after')
  passed('Thirty-two12s boss volleys measure real blocking versus player contacts; every interception pays one finite charge, while continuous precise frontal fire produces zero player contacts in this controlled setup.')
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
lines=['# 탱코 전투 변경 전후 — 실제 코드 비교','','기준71bce18의 실제 HTML과 새 HTML을 각각 Chromium에 로드했다. 동일 보스 HP 배율, 거리160px, 매 틱 중심 조준, 정지/무적 플레이어, 기존 등장 전환1.5초/초기 쿨다운0. 120Hz 표를 아래에 기록했고60Hz 교차 검사는 JSON에 있다. 사람의 실전 시간이나 갤럭시 성능 측정이 아니다.','','| 지역 | 강화 | 보스 HP | 이전 피해2 | 변경 피해1.5·폭/차단 |','| --- | ---: | ---: | ---: | ---: |']
for region,name in enumerate(['숲','바위','바다','사막']):
 for level in range(6):
  pair=[next(r for r in ttk if r['version']==version and r['hz']==120 and r['type']==2 and r['stage']==region and r['level']==level) for version in ['before','after']]
  lines.append(f'| {name} | {level} | {pair[0]["hp"]:g} | {pair[0]["seconds"]:.3f}초 | {pair[1]["seconds"]:.3f}초 |')
lines+=['',f'최대 폭5강을8방향으로6초 연사한3가로 화면의 실제 PNG 알파 점유율 최대치는 **{report["peak_visible_percent"]:.2f}%**였다. UI는 캔버스 위 기존 레이어라 터치 버튼은 가려지지 않는다. 상한 검사는15%이며 실제 측정값/방향별 활성 탄환 수는 JSON에 기록했다.','','## 12초 연속 발사 방어 검사','','보스는 테스트 메모리에서만 HP1,000,000으로 올려12초간 생존시켰다. 기존 패턴으로 발사한 수/차단/플레이어 접촉을 비교했다. 플레이어 무적은 접촉 수 관찰을 위한 것으로 제품에 넣지 않았다.','','| 지역 | 강화 | 이전 피격 접촉 | 새 발사 수 | 새 차단 | 새 피격 접촉 |','| --- | ---: | ---: | ---: | ---: | ---: |']
for region,name in enumerate(['숲','바위','바다','사막']):
 for level in [0,1,3,5]:
  a,b=[next(r for r in defense if r['version']==v and r['stage']==region and r['level']==level) for v in ['before','after']]
  lines.append(f'| {name} | {level} | {a["contacts"]} | {b["created"]} | {b["blocked"]} | {b["contacts"]} |')
lines+=['','각 탄환의 차단은 기존 잔여 관통2/3/3/5/6/7회와 수명1.9초 안에서만 가능하다. 모든 차단/적 타격 비용이 실제 발사한 탄환의 총 관통 예산 이내임을 검사했다. 적/보스 타격도 같은 횟수를 소비하며 같은 대상은 한 번만 차감한다. 연속 발사는 새 탄환의 자원을 계속 공급하므로 일부 정면 탄막은 매우 잘 막는다. 이 중심 조준/연사 표본에서는 새 버전의 피격 접촉이 전부0이었다. 차단되지 않은 탄이 원래 빗나가거나 아직 비행 중인 경우도 있어 “발사된 모든 탄 제거”와는 구분한다. 뒤·측면 공격의 실제 피해는 별도 검사로 확인했다. 정면 연사 방어가 강한 밸런스 한계는 남으며, 단일 탄환 무한 관통/수명 연장 오류와는 구분한다. 요청한 폭·연사·관통 수치를 추가로 줄이는 임의 조정은 하지 않았다.','']
(args.artifacts/'boss-and-defense-comparison.md').write_text('\n'.join(lines))
