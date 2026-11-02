from scoring_preservation import SCORE_ASSETS,assert_scoring_asset,without_scoring_ui
from selection_bgm_preservation import BGM_ASSET,assert_selection_bgm_asset,without_selection_bgm_changes
"""Tanko real damage, monster penetration/mutual interception, 8-direction dimensions and finite defense."""
import argparse,json,shutil,subprocess,re,threading,math
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from tanko_combat_preservation import without_tanko_combat_changes,without_tanko_interception_changes,without_tanko_cadence_changes
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'standalone':args.standalone,'baseline_commit':'f622f3f9c8e82f390b40883abd1abd8f6b9e7f71','width_basis':'Existing upgrade-1 width 22.75 CSS px; 0 remains 17.5, upgrades1..5 use 200/225/250/275/300%; height29.','limits':['Chromium native fullscreen/touch emulation, not physical Galaxy/Samsung Internet or speaker/performance measurement.','Standalone mode injects identical built HTML into a fresh offline document; managed policy blocks file://, checked by galaxy_standalone.py.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
s=(root/'index.html').read_text();before=subprocess.check_output(['git','show','287629f:index.html'],cwd=root).decode()
assert without_tanko_cadence_changes(s)==subprocess.check_output(['git','show','f622f3f:index.html'],cwd=root).decode()
assert without_tanko_interception_changes(s)==before
assert without_tanko_combat_changes(s)==subprocess.check_output(['git','show','71bce18:index.html'],cwd=root).decode()
for path in (root/'assets').rglob('*'):
 if str(path.relative_to(root)) in SCORE_ASSETS:
  assert_scoring_asset(path);continue
 if str(path.relative_to(root))==BGM_ASSET:
  assert_selection_bgm_asset();continue
 if path.is_file():assert (without_scoring_ui(path.read_text(),str(path.relative_to(root))).encode() if path.suffix in ('.js','.css') else path.read_bytes())==subprocess.check_output(['git','show','287629f:'+str(path.relative_to(root))],cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',s,re.S):subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('After reversing reviewed selection-BGM changes, only the exact Tanko cooldown multiplier differs from f622f3f; reviewed penetration/mutual-interception deltas still match287629f; earlier authorized deltas still match71bce18; every asset, audio/UI, movement, other-character cooldowns, boss HP/reward and other-character source is preserved; JS syntax passes.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=None
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True,offline=args.standalone)
  page=context.new_page();errors=[];dialogs=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
  page.on('request',lambda r:external.append(r.url) if r.url.startswith('http') and '127.0.0.1' not in r.url else None)
  if args.standalone:page.set_content((root/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:
   server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load')
  page.wait_for_function('bulletSprites.every(i=>i.complete&&i.naturalWidth)&&sprites.every(i=>i.complete&&i.naturalWidth)')
  page.locator('.select-hit[data-heli="2"]').tap();page.locator('#startSelected').tap();page.wait_for_function('started&&player.type===2&&!!document.fullscreenElement')
  page.evaluate('''() => {
   window.resetCombat=(level=0,type=2)=>{start(type);player.upgrade=level;spawn=999;transition=0;invuln=999;fireCooldown=0;player.x=W/2;player.y=H*.7;};
   window.combatEnemy=(hp=10)=>({x:300,y:120,r:16,hp,special:false,life:99,t:0,shot:99,charge:99,kind:0,speed:0,vx:0,vy:0,mode:'chase'});
   window.combatShot=level=>{resetCombat(level);shoot();const b=bullets[0];bullets=[b];b.x=300;b.y=120;b.vx=0;b.vy=-410;return b;};
   window.hostile=()=>{emitEnemyShot({x:300,y:120});return enemyBullets[enemyBullets.length-1];};
  }''')
  matrix=page.evaluate('''() => {
   const rows=[];
   for(let level=0;level<=5;level++){resetCombat(level);shoot();rows.push({level,width:tankoBulletWidth(level),height:29,damage:bullets[0].damage,pierce:bullets[0].pierce,count:bullets.length,speed:bullets[0].speed,life:bullets[0].life});}
   return rows;
  }''');widths=[17.5,45.5,51.1875,56.875,62.5625,68.25]
  for r in matrix:
   u=r['level'];assert r=={'level':u,'width':widths[u],'height':29,'damage':1.5,'pierce':[2,3,3,4,4,5][u],'count':1 if u<2 else 2,'speed':410,'life':1.9}
  report['weapon_matrix']=matrix;passed('All six upgrades keep original speed410, lifetime1.9, counts; new monster penetration2/3/3/4/4/5; damage is1.5 and requested upgrade1..5 widths are exact with height29.')
  geometry=page.evaluate('''() => {
   const rows=[];gameExitDialogOpen=true;
   for(let level=0;level<=5;level++)for(let direction=0;direction<8;direction++){
    resetCombat(level);player.a=Math.PI+direction*Math.PI/4;shoot();bullets=[bullets[0]];const b=bullets[0];b.x=W/2;b.y=H/2;
    let call=null;const original=ctx.drawImage;ctx.drawImage=function(image,...values){if(image===bulletSprites[2]){const m=this.getTransform();call={values,m:[m.a,m.b,m.c,m.d,m.e,m.f]}}return original.call(this,image,...values)};
    try{draw()}finally{ctx.drawImage=original}
    const a=Math.atan2(b.vy,b.vx),nx=Math.cos(a),ny=Math.sin(a),w=tankoBulletWidth(level);
    const hit=(along,across)=>bulletHitsCircle(b,b.x+nx*along-ny*across,b.y+ny*along+nx*across,1);
    rows.push({level,direction,...call,dpr,vx:b.vx,vy:b.vy,boundaries:[hit(0,w/2+.99),hit(0,w/2+1.01),hit(14.5+.99,0),hit(14.5+1.01,0),hit(14.5+.6,w/2+.6),hit(14.5+.8,w/2+.8)]});
   }gameExitDialogOpen=false;window.combatGeometry=rows;return rows;
  }''')
  for r in geometry:
   w=widths[r['level']];assert r['values']==[-w/2,-14.5,w,29] and r['boundaries']==[True,False,True,False,True,False]
   a,b,c,d,*_=r['m'];assert abs(a*r['vx']+b*r['vy'])<1e-6 and abs(math.hypot(a,b)-r['dpr'])<1e-6 and abs(math.hypot(c,d)-r['dpr'])<1e-6
  report['geometry']=geometry;passed('48 actual draws across 0..5 upgrades and eight directions preserve a rectangular29px height with width perpendicular to travel; side/end/corner hit boundaries match the same oriented rectangle.')
  page.evaluate('''() => {
   const panel=document.createElement('div');panel.id='combatReview';panel.style.cssText='position:fixed;inset:0;z-index:1000;overflow:auto;background:#10283c;color:white;font:16px system-ui;text-align:center;padding:12px;box-sizing:border-box';
   panel.innerHTML='<h2>탱코 탄환 · 폭/PNG/색상 유지 · 적 탄환과 양쪽 소멸</h2><p>1강 기존 폭22.75px 기준 · 0강 유지 · 피해1.5 유지 · 높이29px 고정</p>';
   const canvas=document.createElement('canvas');canvas.width=1280;canvas.height=760;canvas.style.cssText='width:100%;height:auto';const t=canvas.getContext('2d');t.fillStyle='#10283c';t.fillRect(0,0,1280,760);t.fillStyle='white';t.textAlign='center';t.font='bold 18px system-ui';
   for(let level=0;level<=5;level++){
    const y=75+level*118;t.fillText(level+'강',60,y);t.fillText('기존 '+tankoBulletWidth(level).toFixed(4)+'px',230,y-53);t.fillText('변경 '+tankoBulletWidth(level).toFixed(4)+'px',460,y-53);
    for(const [x,w] of [[230,tankoBulletWidth(level)],[460,tankoBulletWidth(level)]])t.drawImage(bulletSprites[2],x-w*1.5,y-43.5,w*3,87);
    for(let i=0;i<8;i++){const x=650+i*80;t.save();t.translate(x,y);t.rotate(i*Math.PI/4);t.drawImage(bulletSprites[2],-tankoBulletWidth(level)/2,-14.5,tankoBulletWidth(level),29);t.restore();}
   }panel.append(canvas);document.body.append(panel);
  }''');page.set_viewport_size({'width':1400,'height':1040});page.screenshot(path=str(args.artifacts/'tanko-bullet-widths-eight-directions.png'));page.evaluate('document.getElementById("combatReview").remove()');page.set_viewport_size({'width':915,'height':412});page.wait_for_function('W===915&&H===412')
  damage=page.evaluate('''() => {
   const b=combatShot(1),e=combatEnemy(4);enemies=[e];update(0);const first={hp:e.hp,pierce:b.pierce,life:b.life};update(0);const again={hp:e.hp,pierce:b.pierce,life:b.life};
   const e2=combatEnemy(2),e3=combatEnemy(2);enemies.push(e2,e3);update(0);
   return {first,again,hp2:e2.hp,hp3:e3.hp,pierce:b.pierce,life:b.life};
  }''');assert damage['first']==damage['again']=={'hp':2.5,'pierce':2,'life':1.9} and damage['hp2']==.5 and damage['hp3']==.5 and damage['pierce']==0 and damage['life']==0
  passed('Actual ordinary-enemy HP falls by exactly1.5; same-target overlap across frames is ignored, and each distinct enemy consumes one shared penetration without resetting lifetime.')
  depleted=page.evaluate('''() => {
   const rows=[];for(let level=0;level<=5;level++){
    const b=combatShot(level),budget=b.pierce,targets=Array.from({length:budget+1},()=>combatEnemy(10));enemies=targets;
    update(0);const first=targets.map(e=>e.hp);update(0);
    rows.push({level,budget,hp:first,pierce:b.pierce,life:b.life,removed:!bullets.includes(b),noRepeat:targets.every((e,i)=>e.hp===first[i])});
   }return rows;
  }''');assert all(r['pierce']==0 and r['life']==0 and r['removed'] and r['noRepeat'] and r['hp']==[8.5]*r['budget']+[10] for r in depleted)
  report['monster_depletion']=depleted
  passed('All upgrades exhaust exactly2/3/3/4/4/5 distinct monster hits, apply1.5 each, remove the shot immediately and leave the next monster untouched without duplicate damage.')
  boss_damage=page.evaluate('''() => {
   const b=combatShot(0);stage=0;phase=5;phaseKills=requiredKills;update(0);boss.x=300;boss.y=120;boss.hp=boss.maxHp=10;boss.shot=99;const target=boss;
   update(0);const first={hp:boss.hp,pierce:b.pierce,life:b.life};update(0);const again={hp:boss.hp,pierce:b.pierce,life:b.life};
   const incoming=hostile();update(0);return {first,again,after:target.hp,pierce:b.pierce,life:b.life,blocked:incoming.life===0};
  }''');assert boss_damage['first']==boss_damage['again']=={'hp':8.5,'pierce':1,'life':1.9} and boss_damage['after']==8.5 and boss_damage['pierce']==1 and boss_damage['life']==0 and boss_damage['blocked']
  passed('Actual boss HP falls10→8.5 once per projectile; boss contact consumes one monster penetration; a later hostile collision destroys both bullets despite one charge left, without repeated boss damage.')
  intercepted=page.evaluate('''() => {
   const values=[];
   for(const source of ['ordinary','boss']){
    const b=combatShot(5);let incoming;
    if(source==='ordinary')incoming=hostile();
    else{stage=3;phase=5;phaseKills=requiredKills;update(0);boss.x=300;boss.y=120;boss.shot=0;transition=0;update(0);incoming=null;}
    if(source==='ordinary')update(0);
    values.push({source,left:enemyBullets.length,pierce:b.pierce,life:b.life,removed:!bullets.includes(b),hit:b.hit.length,bossHp:boss?.hp});
   }return values;
  }''');assert intercepted[0]['left']==0 and intercepted[0]['pierce']==5 and intercepted[0]['life']==0 and intercepted[0]['removed'] and intercepted[1]['left']==4 and intercepted[1]['pierce']==4 and intercepted[1]['life']==0 and intercepted[1]['removed'],intercepted
  report['interception']=intercepted;passed('Ordinary bullets and one projectile from the actual desert boss five-shot volley mutually annihilate the Tanko shot; the other four hostile bullets remain.')
  shared=page.evaluate('''() => {
   const b=combatShot(1),e=combatEnemy();enemies=[e];const one=hostile();update(0);const first={hp:e.hp,pierce:b.pierce,left:enemyBullets.length};
   const two=hostile();update(0);const third=hostile();update(0);
   return {first,hp:e.hp,pierce:b.pierce,life:b.life,one:one.life,two:two.life,third:third.life,left:enemyBullets.length,removed:!bullets.includes(b)};
  }''');assert shared['first']=={'hp':8.5,'pierce':2,'left':0} and shared['hp']==8.5 and shared['pierce']==2 and shared['life']==0 and shared['one']==0 and shared['two']>0 and shared['third']>0 and shared['left']==2 and shared['removed']
  passed('After one enemy hit leaves two charges, the first hostile contact destroys the Tanko shot that frame; subsequent hostile bullets are not intercepted.')
  duplicate=page.evaluate('''() => {
   const first=combatShot(0);const second={...first,hit:[]};bullets.push(second);const target=hostile();update(0);
   const again=blockEnemyBullet(target);return {first:first.pierce,second:second.pierce,firstLife:first.life,secondLife:second.life,again,left:enemyBullets.length,shots:bullets.length};
  }''');assert duplicate=={'first':2,'second':2,'firstLife':0,'secondLife':1.9,'again':False,'left':0,'shots':1}
  passed('One hostile bullet overlapping two Tanko shots destroys exactly one shot; the other survives, and retrying the removed hostile target has no effect.')
  limits=page.evaluate('''() => {
   const rows=[];
   for(let level=0;level<=5;level++){
    const b=combatShot(level),initial=b.pierce;for(let i=0;i<20;i++)hostile();update(0);
    const removed=!bullets.includes(b),remaining=enemyBullets.length;
    rows.push({level,initial,pierce:b.pierce,life:b.life,removed,remaining});
   }
   const b=combatShot(5);b.life=.01;update(.02);const expired=!bullets.includes(b);return {rows,expired};
  }''');assert all(r['pierce']==r['initial'] and r['life']==0 and r['removed'] and r['remaining']==19 for r in limits['rows']) and limits['expired']
  report['finite_limits']=limits;passed('At every upgrade, one Tanko projectile blocks exactly one of20 incoming bullets and vanishes despite2/3/3/4/4/5 charges; the other19 remain, and original lifetime expiry still works.')
  remaining=page.evaluate('''() => {
   const b=combatShot(0),incoming=hostile();update(0);
   const e=combatEnemy(2);enemies=[e];update(0);const afterBlock={hp:e.hp,pierce:b.pierce,removed:!bullets.includes(b)};
   const timed=combatShot(5);timed.vx=timed.vy=0;timed.life=.35;const e2=combatEnemy();enemies=[e2];update(.1);const afterHit={life:timed.life,pierce:timed.pierce,hp:e2.hp};
   update(.1);const afterOverlap={life:timed.life,pierce:timed.pierce,hp:e2.hp};
   const stopped=hostile();stopped.vx=stopped.vy=0;update(0);return {afterBlock,afterHit,afterOverlap,annihilated:timed.life===0&&stopped.life===0};
  }''');assert remaining['afterBlock']=={'hp':2,'pierce':2,'removed':True} and abs(remaining['afterHit']['life']-.25)<1e-9 and abs(remaining['afterOverlap']['life']-.15)<1e-9 and remaining['afterHit']['pierce']==remaining['afterOverlap']['pierce']==4 and remaining['afterHit']['hp']==remaining['afterOverlap']['hp']==8.5 and remaining['annihilated']
  passed('After interception a dead shot cannot damage a later monster; normal penetration still preserves remaining lifetime, skips repeat damage and later mutually annihilates with a hostile bullet.')
  bypass=page.evaluate('''() => {
   const rows=[];for(const side of ['rear','side']){
    const b=combatShot(5);b.x=player.x;b.y=player.y-70;invuln=0;
    emitEnemyShot({x:player.x+(side==='side'?16:0),y:player.y+(side==='rear'?16:0)});update(0);
    rows.push({side,hp,pierce:b.pierce});
   }return rows;
  }''');assert all(r['hp']==8 and r['pierce']==5 for r in bypass)
  passed('Actual rear/side hostile hits still reduce Tanko HP9→8 when they miss the shot rectangle; unused projectile charges do not create a global player shield.')
  others=page.evaluate('''() => {
   const rows=[];for(const type of [0,1])for(let level=0;level<=5;level++){
    resetCombat(level,type);shoot();const shots=bullets.map(b=>({kind:b.kind,damage:b.damage,pierce:b.pierce,homing:b.homing,speed:b.speed}));
    const incoming=hostile();for(const b of bullets){b.x=300;b.y=120;}update(0);rows.push({type,level,shots,unblocked:incoming.life>0});
   }return rows;
  }''')
  for r in others:
   t,u=r['type'],r['level'];assert r['unblocked'] and len(r['shots'])==([1,2,3,4,5,5][u] if t==0 else 1 if u<2 else 3)
   for b in r['shots']:assert b['damage']==1 and b['speed']==(535 if t==0 else 480) and b['pierce']==(2 if t==0 and u==5 else 1)
   assert sum(b['homing'] for b in r['shots'])==([0,0,0,1,2,3][u] if t==1 else 0)
  passed('Trio/Bingle upgrades0..5 retain damage1, original volley counts, speed535/480, piercing/homing and cannot intercept hostile bullets.')
  for width,height in [(915,412),(800,360),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_function('size=>W===size[0]&&H===size[1]',arg=[width,height]);page.evaluate('resetCombat(5);player.a=Math.PI;keys.fire=true')
   page.wait_for_timeout(600);page.evaluate('keys.fire=false;gameExitDialogOpen=true;draw()');page.screenshot(path=str(args.artifacts/f'tanko-combat-{width}.png'));page.evaluate('gameExitDialogOpen=false')
   for selector in ['#fire','#left','#right','#fullscreenToggle','#exitGame']:
    box=page.locator(selector).bounding_box();assert box and box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width+1 and box['y']+box['height']<=height+1
  page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible();assert page.evaluate('!!document.fullscreenElement')
  assert not errors and not dialogs and not external,(errors,dialogs,external)
  passed('915×412/800×360/568×320 real gameplay fits all touch/fullscreen/exit controls, exits via the original modal with fullscreen retained, and has no native dialogs, asset requests or JS errors.')
  browser.close()
finally:
 if server:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
