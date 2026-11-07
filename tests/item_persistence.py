"""Ordinary item identity/lifetime through real phase and boss-kill transitions."""
import argparse,json,shutil,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'passed':[],'limits':['Controlled actual-code Chromium tests; physical Galaxy/Samsung Internet remains untested.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);page=browser.new_page(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}',wait_until='load')
  # Retain the explicit20-stage final-clear item/recovery contract.
  page.evaluate('gameWorlds.setTrialEnabled(false)')
  page.evaluate('''() => {
   window.itemReset=(type=0)=>{start(type);spawn=999;transition=0;invuln=999;fireCooldown=0};
   window.carried=(type='hp',life=7.25)=>({x:45,y:55,type,life,r:13,t:2,vx:11,vy:7,turn:5});
   window.itemKill=target=>{bullets=[];shoot();Object.assign(bullets[0],{x:target.x,y:target.y,vx:0,vy:0});update(.001)};
  }''')
  direct=page.evaluate('''() => {
   const result=[];
   for(let region=0;region<4;region++)for(let wave=1;wave<=5;wave++){
    itemReset();stage=region;phase=wave;const refs=[carried('hp'),carried('power',3.75)];items=refs.slice();
    const before=JSON.stringify(items);nextPhase();
    result.push({region,wave,unchanged:before===JSON.stringify(items),same:items.every((x,i)=>x===refs[i]),count:items.length});
   }return result;
  }''');assert all(r['unchanged'] and r['same'] and r['count']==2 for r in direct);report['direct_transitions']=direct
  passed('All 20 direct phase/region/final-clear transitions preserve ordinary item object identity, exact positions/types, movement fields and remaining lifetime without resetting them.')
  normal=page.evaluate('''() => {
   itemReset();phaseKills=requiredKills-1;const it=carried('power');items=[it];
   const enemy={x:player.x,y:player.y-70,hp:1,r:16,special:false,kind:0,life:999,t:0,turn:99,speed:0,shot:99,charge:99,vx:0,vy:0,mode:'chase'};enemies=[enemy];
   itemKill(enemy);return {phase,runScore,same:items[0]===it,life:it.life,x:it.x,y:it.y};
  }''');assert normal['phase']==2 and normal['runScore']==600 and normal['same'] and abs(normal['life']-7.249)<1e-9
  assert abs(normal['x']-45.011)<1e-9 and abs(normal['y']-55.007)<1e-9
  report['ordinary_kill_transition']=normal
  passed('The sixth ordinary monster dies through actual bullet collision and advances the phase while retaining its existing item with only the normal elapsed tick/movement deducted.')
  regional=page.evaluate('''() => {
   const rows=[],random=Math.random;Math.random=()=>.75;
   try{for(let region=0;region<4;region++){
    itemReset(2);stage=region;phase=5;phaseKills=requiredKills;hp=1;const it=carried();items=[it];update(0);boss.hp=1;const target=boss;
    itemKill(target);rows.push({region,stage,phase,hp,upgrade:player.upgrade,same:items[0]===it,life:it.life,reward:target.rewardGranted,started});
   }}finally{Math.random=random}return rows;
  }''')
  for r in regional:assert r['same'] and abs(r['life']-7.249)<1e-9 and r['reward'] and r['upgrade']==1 and r['hp']==(3 if r['region']<3 else 1) and r['started']==(r['region']<3)
  report['boss_region_transitions']=regional
  passed('All four actual boss-kill paths retain ordinary items; automatic boss rewards still occur once before existing next-region +2 healing (no region healing after final clear).')
  lifespan=page.evaluate('''() => {
   itemReset();const it=carried('power',.25);items=[it];nextPhase();const atTransition=it.life;
   update(.1);const afterTick=it.life;nextPhase();nextPhase();const afterMorePhases=it.life;
   update(.16);return {atTransition,afterTick,afterMorePhases,count:items.length,upgrade:player.upgrade};
  }''');assert lifespan['atTransition']==.25 and abs(lifespan['afterTick']-.15)<1e-9 and lifespan['afterTick']==lifespan['afterMorePhases'] and lifespan['count']==0 and lifespan['upgrade']==0
  passed('Transitions add no lifetime: a 0.25s item loses exactly 0.1s during update, keeps that remainder through two more phases and expires normally after another 0.16s.')
  pickups=page.evaluate('''() => {
   const values=[];
   for(const type of ['hp','power'])for(const atCap of [false,true]){
    itemReset();hp=atCap?4:1;player.upgrade=atCap?5:3;const it=carried(type);items=[it];nextPhase();
    Object.assign(it,{x:player.x,y:player.y,vx:0,vy:0});update(.001);const first={hp,upgrade:player.upgrade,count:items.length};update(.001);
    values.push({type,atCap,first,hp,upgrade:player.upgrade,count:items.length});
   }return values;
  }''')
  for r in pickups:assert r['count']==0 and r['first']=={'hp':r['hp'],'upgrade':r['upgrade'],'count':0} and r['hp']==(4 if r['atCap'] else 3 if r['type']=='hp' else 1) and r['upgrade']==(5 if r['atCap'] else 4 if r['type']=='power' else 3)
  passed('Carried health/power pickups apply the existing +2/+1 once, respect max HP/upgrade5, and disappear normally on contact.')
  drop=page.evaluate('''() => {itemReset();dropItem(45,55);const it=items[0],before=JSON.stringify(it);nextPhase();return {same:it===items[0],equal:before===JSON.stringify(it),life:it.life,r:it.r,count:items.length}}''')
  assert drop=={'same':True,'equal':True,'life':16,'r':13,'count':1}
  passed('The unchanged normal drop generator still creates one 16-second, 13px item and the new transition preserves it exactly.')
  page.evaluate('hp=0;update(0)');expect(page.locator('#gameOverOverlay')).to_be_visible();expect(page.locator('#menu')).to_be_visible(timeout=4000)
  page.locator('#startSelected').tap();assert page.evaluate('started&&items.length===0&&stage===0&&phase===1&&runScore===0&&player.upgrade===0')
  passed('After the actual three-second game-over return, a new user-started game resets items and the original stage/runScore/upgrade state.')
  assert not errors,errors
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
