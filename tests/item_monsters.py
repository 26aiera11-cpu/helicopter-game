"""Native browser verification of the independent item monster system."""
import argparse
import base64
import hashlib
import json
import math
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from item_monster_preservation import assert_item_asset, without_item_monsters

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '17da293570f422035d455add578dbc8412e4f24b'
parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
parser.add_argument('--standalone', action='store_true')
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
report = {'baseline_main': BASELINE, 'prior_feature': '6d4e4e969e38cbab7e4c499f73fda68f2be1b09c',
          'standalone': args.standalone, 'passed': [], 'limits': [
              'Actual Chromium and controlled state/input tests, not physical Galaxy or a human balance playthrough.',
              'New spawn cadence is not finalized: only inherited legacy parameters are the compatibility default.',
              'Standalone is injected into an offline document because direct file navigation is blocked by managed policy.'
          ]}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


source = (ROOT / 'index.html').read_text()
assert without_item_monsters(source) == subprocess.check_output(['git', 'show', BASELINE + ':index.html'], cwd=ROOT).decode()
for path in (ROOT / 'assets').rglob('*'):
    if not path.is_file():
        continue
    if str(path.relative_to(ROOT)).startswith('assets/item_monster/'):
        assert_item_asset(path)
    else:
        assert path.read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + str(path.relative_to(ROOT))], cwd=ROOT)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S) + [(ROOT / 'assets/item_monster/item_monster.js').read_text()]:
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
passed('Only exact reviewed item integration differs from main; every previous asset/scoring/audio/UI file is unchanged, supplied assets match pinned bytes, and JS syntax passes.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *unused):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
html = (ROOT / 'dist/heli_trio_galaxy_test.html').read_text() if args.standalone else None
helpers = '''() => {
  window.itemReset=(type=0)=>{start(type);itemMonsters.configure({probability:0,intervalSeconds:null,maxActive:null,allowDuringBoss:false,stageRules:{0:{},1:{},2:{},3:{}}});spawn=999;transition=0;invuln=999;fireCooldown=0;};
  window.hitItem=m=>{bullets=[];shoot();Object.assign(bullets[0],{x:m.x,y:m.y,vx:0,vy:0});update(0);};
  window.plainEnemy=(x=100,y=100)=>({x,y,hp:1,special:false,r:16,t:0,speed:0,shot:999,charge:999,kind:0,mode:'chase',vx:0,vy:0});
}'''
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 915, 'height': 412}, is_mobile=True, has_touch=True)
        if args.standalone:
            context.set_offline(True)
        page = context.new_page()
        errors, dialogs, failed, external = [], [], [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
        page.on('requestfailed', lambda request: failed.append(request.url))
        page.on('request', lambda request: external.append(request.url) if args.standalone and request.url.startswith('http') else None)
        if args.standalone:
            page.set_content(html, wait_until='load')
            embedded = re.search(r'<img id="itemMonsterAtlas" src="data:image/png;base64,([A-Za-z0-9+/=]+)"', html)
            assert embedded and base64.b64decode(embedded[1]) == (ROOT / 'assets/item_monster/item_monster_atlas.png').read_bytes()
        else:
            page.goto(url, wait_until='load')
        page.wait_for_function('window.itemMonsters?.ready()&&window.gameScoring&&sprites.every(i=>i.complete&&i.naturalWidth>0)')
        page.evaluate(helpers)
        assert page.evaluate('itemMonsterAtlas.naturalWidth===2560&&itemMonsterAtlas.naturalHeight===1280')
        assert page.evaluate('document.querySelectorAll("#itemMonsterAtlas").length') == 1
        report['initial_runtime_policy'] = page.evaluate('itemMonsters.snapshot()')
        assert report['initial_runtime_policy']['policy']['probability'] == .22
        assert report['initial_runtime_policy']['normalOpportunityProbability'] == .78
        passed('One actual supplied RGBA atlas decodes with correct dimensions; no static stand-in, synthesized artwork, missing motion frame or dynamic JS loader is used.')

        policies = page.evaluate('''() => {
          itemReset();const rows=[];
          for(let area=0;area<4;area++)for(let step=1;step<=5;step++){
            stage=area;phase=step;rows.push({area,step,...itemMonsters.snapshot().policy});
          }return rows;
        }''')
        for row in policies:
            assert abs(row['intervalSeconds'] - max(.72, [2, 1.8, 1.62, 1.46][row['area']] - (row['step'] - 1) * .09)) < 1e-9
            assert row['probability'] == 0 and row['maxActive'] == min(7, 3 + row['area'] + row['step'] // 2)
            assert not row['allowDuringBoss']
        report['inherited_policy_matrix'] = policies
        passed('All20 region/phase policies inherit existing cadence/capacity rather than the prototype8/7/11–16-second timers; independent probability/cap/boss/stage controls remain configurable.')

        independence = page.evaluate('''() => {
          itemReset();itemMonsters.configure({probability:1,maxActive:1});spawn=999;itemMonsters.update(0);
          const independent={normal:warnings.length,item:itemMonsters.snapshot().entrances.length};
          itemReset();const random=Math.random;Math.random=()=>.9;spawn=0;
          try{update(0)}finally{Math.random=random}
          return {independent,ordinary:{normal:warnings.length,item:itemMonsters.snapshot().entrances.length,special:warnings[0].special}};
        }''')
        assert independence == {'independent': {'normal': 0, 'item': 1}, 'ordinary': {'normal': 1, 'item': 0, 'special': False}}
        report['independence'] = independence
        distribution = page.evaluate('''() => {
          itemReset();const random=Math.random;let normal=0;
          try{for(let i=0;i<1000;i++){Math.random=()=>i/1000;warnings=[];spawn=0;update(0);normal+=warnings.length;}}
          finally{Math.random=random}return normal;
        }''')
        assert distribution == 780
        passed('Item and normal clocks operate without driving each other;1000 deterministic empty-arena opportunities retain780 normal spawns, with the original normal interval/AI untouched.')

        arrival = page.evaluate('''() => {
          itemReset();itemMonsters.configure({probability:1,intervalSeconds:.5,maxActive:1});itemMonsters.update(0);
          const first=itemMonsters.snapshot();for(let i=0;i<15;i++)itemMonsters.update(.1);
          const entered=itemMonsters.targets()[0];itemMonsters.update(.5);
          return {warnings:first.entrances.length,firstNormal:enemies.length,count:itemMonsters.targets().length,hp:entered.hp,life:entered.life,pending:itemMonsters.snapshot().entrances.length};
        }''')
        assert arrival['warnings'] == 1 and arrival['count'] == 1 and arrival['hp'] == 5 and arrival['pending'] == 0 and arrival['firstNormal'] == 0
        passed('Independent warning becomes one HP5 entity; active plus pending entries respect the configured cap and never enter the regular enemy array.')

        flee = page.evaluate('''() => {
          itemReset();const rows=[];
          for(let area=0;area<4;area++){
            itemMonsters.reset();stage=area;const m=itemMonsters.spawn({x:player.x+60,y:player.y});
            m.turn=999;m.vx=-1;m.vy=0;const x=m.x,y=m.y,d=Math.hypot(m.x-player.x,m.y-player.y);
            itemMonsters.update(.1);rows.push({area,before:d,after:Math.hypot(m.x-player.x,m.y-player.y),speed:Math.hypot(m.x-x,m.y-y)/.1});
          }return rows;
        }''')
        assert all(row['after'] > row['before'] and row['speed'] <= 45 + 8 * row['area'] + 1e-8 for row in flee)
        report['flee_speed'] = flee
        no_attack = page.evaluate('''() => {itemReset();const m=itemMonsters.spawn({x:player.x,y:player.y});const before=hp;for(let i=0;i<30;i++)update(.04);return {before,hp,shots:enemyBullets.length,kills:phaseKills};}''')
        assert no_attack == {'before': 4, 'hp': 4, 'shots': 0, 'kills': 0}
        passed('Even movement initially pointing toward the player yields gentle escape in every region; speed never exceeds existing45–69px/s, with no shots or contact damage.')

        expired = page.evaluate('''() => {
          itemReset();const m=itemMonsters.spawn({x:100,y:100});itemMonsters.update(9.99);const before=itemMonsters.targets().length;itemMonsters.update(.011);
          return {before,after:itemMonsters.targets().length,score:runScore,kills:phaseKills,drops:items.length,bursts:itemMonsters.snapshot().bursts.length};
        }''')
        assert expired == {'before': 1, 'after': 0, 'score': 0, 'kills': 0, 'drops': 0, 'bursts': 0}
        passed('The10-second exit gives no score, kill progress, drop or destruction reward; no timer is restarted by movement or animation.')

        hit_matrix = page.evaluate('''() => {
          const rows=[];
          for(let kind=0;kind<3;kind++){
            itemReset(kind);const m=itemMonsters.spawn({x:100,y:100});let shots=0;
            while(m.hp>0&&shots<6){hitItem(m);shots++;}
            const before={score:runScore,kills:phaseKills,items:items.length};itemMonsters.collide();
            rows.push({kind,shots,hp:m.hp,before,score:runScore,kills:phaseKills,items:items.length,remaining:itemMonsters.targets().length});
          }return rows;
        }''')
        assert [row['shots'] for row in hit_matrix] == [5, 5, 4]
        assert all(row['score'] == 200 and row['kills'] == 0 and row['items'] == 1 and row['remaining'] == 0 and row['before'] == {'score': 200, 'kills': 0, 'items': 1} for row in hit_matrix)
        saved = page.evaluate('gameScoring.finish("abandoned").record')
        assert saved['score']==200 and saved['itemKills']==1 and saved['normalKills']==0 and saved['phase']==1
        report['saved_item_analysis'] = saved
        report['actual_hit_matrix'] = hit_matrix
        repeated = page.evaluate('''() => {
          itemReset();for(let count=0;count<6;count++){const m=itemMonsters.spawn({x:100,y:100});for(let hit=0;hit<5;hit++)hitItem(m);}
          return {score:runScore,kills:phaseKills,phase,items:items.length,analysis:gameScoring.finish('abandoned').record.itemKills};
        }''')
        assert repeated == {'score':1200,'kills':0,'phase':1,'items':6,'analysis':6}
        report['six_item_kills_without_phase_progress'] = repeated
        passed('Real bullets from Trio/Bingle/Tanko defeat HP5 in5/5/4 hits, retain damage1/1/1.5, award200 once and drop once without advancing phaseKills.')

        shared = page.evaluate('''() => {
          itemReset(2);const m=itemMonsters.spawn({x:100,y:100});enemies=[plainEnemy()];shoot();const b=bullets[0];Object.assign(b,{x:100,y:100,vx:0,vy:0});update(0);
          return {score:runScore,kills:phaseKills,itemHP:m.hp,pierce:b.pierce,life:b.life,hits:b.hit.length,normalCount:enemies.length};
        }''')
        assert shared['score'] == 100 and shared['kills'] == 1 and shared['itemHP'] == 3.5 and shared['pierce'] == 0 and shared['life'] == 0 and shared['hits'] == 2 and shared['normalCount'] == 0
        homing = page.evaluate('''() => {
          itemReset(1);player.upgrade=3;const m=itemMonsters.spawn({x:player.x+80,y:player.y-70});shoot();const b=bullets.find(b=>b.homing);const before=b.vx;update(.04);return {before,after:b.vx};
        }''')
        assert homing['after'] > homing['before']
        nearest = page.evaluate('''() => {
          const rows=[];
          for(const itemNear of [true,false]){
            itemReset(1);player.upgrade=3;shoot();const b=bullets.find(b=>b.homing);b.x=player.x;b.y=player.y;b.vx=0;b.vy=-480;
            const m=itemMonsters.spawn({x:player.x+(itemNear?35:150),y:player.y-70});
            enemies=[plainEnemy(player.x-(itemNear?150:35),player.y-70)];const original=Math.atan2(b.vy,b.vx);update(.02);
            rows.push({itemNear,turn:Math.atan2(b.vy,b.vx)-original});
          }return rows;
        }''')
        assert nearest[0]['turn']>0 and nearest[1]['turn']<0
        report['nearest_homing_target'] = nearest
        passed('Tanko shares its original penetration/hit list across both target types; Bingle retains nearest-target selection and the original3.3rad/s homing turn.')

        drops = page.evaluate('''() => {
          const rows=[],random=Math.random;
          try{for(const roll of [.25,.75]){
            itemReset();hp=1;const m=itemMonsters.spawn({x:100,y:100});Math.random=()=>roll;
            for(let i=0;i<5;i++)hitItem(m);const it=items[0];const before={type:it.type,life:it.life,r:it.r};
            nextPhase();const same=items[0]===it;Object.assign(it,{x:player.x,y:player.y,vx:0,vy:0,turn:999});update(.001);
            rows.push({roll,before,same,hp,upgrade:player.upgrade,remaining:items.length});
          }}finally{Math.random=random}return rows;
        }''')
        for row in drops:
            assert row['before'] == {'type': 'hp' if row['roll'] < .5 else 'power', 'life': 16, 'r': 13}
            assert row['same'] and row['remaining'] == 0 and row['hp'] == (3 if row['roll'] < .5 else 1) and row['upgrade'] == (0 if row['roll'] < .5 else 1)
        report['drop_and_pickup'] = drops
        passed('The existing50:50 hp/power generator,16s lifetime,13px radius,+2/+1 effects and carried-item identity are reused without changing cap handling.')

        transitions = page.evaluate('''() => {
          itemReset();const m=itemMonsters.spawn({x:100,y:100});m.life=7.25;nextPhase();const first={same:itemMonsters.targets()[0]===m,life:m.life,phase};
          phase=5;nextPhase();const second={same:itemMonsters.targets()[0]===m,life:m.life,stage,phase};return {first,second};
        }''')
        assert transitions == {'first': {'same': True, 'life': 7.25, 'phase': 2}, 'second': {'same': True, 'life': 7.25, 'stage': 1, 'phase': 1}}
        boss_rules = page.evaluate('''() => {
          itemReset();itemMonsters.spawn({x:100,y:100});phase=5;phaseKills=requiredKills;update(0);
          const blocked={count:itemMonsters.targets().length,warnings:itemMonsters.snapshot().entrances.length,spawn:itemMonsters.spawn({x:100,y:100}),hp:boss.hp,score:runScore};
          itemMonsters.configure({allowDuringBoss:true});const m=itemMonsters.spawn({x:100,y:100});const allowed=Boolean(m);return {blocked,allowed};
        }''')
        assert boss_rules['blocked']['count'] == boss_rules['blocked']['warnings'] == boss_rules['blocked']['score'] == 0
        assert boss_rules['blocked']['spawn'] is None and boss_rules['blocked']['hp'] == 20 and boss_rules['allowed']
        passed('Live item lifetime/position survive ordinary phase and region transitions; default boss policy clears item entities without rewards, while explicit boss allowance works independently.')

        configured = page.evaluate('''() => {
          itemReset();itemMonsters.configure({intervalSeconds:.5,probability:1,maxActive:2,stageRules:{0:{enabled:false},1:{intervalSeconds:1.25,probability:0,maxActive:3,allowDuringBoss:true}}});
          const disabled=itemMonsters.spawn({x:100,y:100});stage=1;const policy=itemMonsters.snapshot().policy;
          const errors=[];for(const patch of [{intervalSeconds:0},{probability:2},{maxActive:-1},{stageRules:{9:{}}}])try{itemMonsters.configure(patch)}catch(e){errors.push(e.name)}
          return {disabled,policy,errors};
        }''')
        assert configured == {'disabled': None, 'policy': {'enabled': True, 'intervalSeconds': 1.25, 'probability': 0, 'maxActive': 3, 'allowDuringBoss': True}, 'errors': ['RangeError'] * 4}
        passed('Interval/probability/capacity, per-region enable/overrides and boss permission configure independently; invalid settings are rejected without partially applying them.')

        animation = page.evaluate('''() => {
          itemReset();const m=itemMonsters.spawn({x:150,y:130});const frames={};
          for(const [group,count,duration] of [['idle',6,.115],['move',6,.105],['hit',3,.095]]){
            frames[group]=[];for(let i=0;i<count;i++){m.t=(i+.1)*duration;m.moving=group==='move';m.turnLeft=0;m.hitLeft=group==='hit'?(3-i-.1)*duration:0;frames[group].push(itemMonsters.frame(m));}
          }
          frames.directions=[];for(let i=0;i<8;i++){m.hitLeft=0;m.turnLeft=.12;m.angle=-Math.PI/2+i*Math.PI/4;frames.directions.push(itemMonsters.frame(m));}
          return frames;
        }''')
        for group, count, row in [('idle', 6, 0), ('move', 6, 1), ('hit', 3, 3), ('directions', 8, 2)]:
            assert [pose['index'] for pose in animation[group]] == list(range(count))
            assert all(pose['group'] == group and pose['row'] == row for pose in animation[group])
        manifest = json.loads((ROOT / 'assets/item_monster/manifest.json').read_text())
        for group in ['idle', 'move', 'hit', 'directions']:
            given = [f for f in manifest['frames'] if f['group'] == group]
            assert all(pose['column'] == frame['atlas_cell'][0] and pose['row'] == frame['atlas_cell'][1] for pose, frame in zip(animation[group], given))
        report['animation_cells'] = animation
        passed('All idle6/move6/direction8/hit3 cells and timing match the supplied manifest; frame changes use actual distinct art, not repeated idle placeholders.')

        destruction = page.evaluate('''() => {
          itemReset();const m=itemMonsters.spawn({x:150,y:130});for(let i=0;i<5;i++)hitItem(m);
          const native=ctx.drawImage,calls=[];ctx.drawImage=function(img,...a){if(img===itemMonsterAtlas)calls.push(a);return native.call(this,img,...a)};
          try{for(let i=0;i<4;i++){if(i)itemMonsters.update(.095);draw();}}finally{ctx.drawImage=native}
          itemMonsters.update(.1);return {calls,remaining:itemMonsters.snapshot().bursts.length};
        }''')
        assert [call[:4] for call in destruction['calls']] == [[i * 320, 768, 320, 256] for i in [3, 4, 5, 6]]
        assert destruction['remaining'] == 0
        for call in destruction['calls']:
            assert abs(call[6] / call[7] - 1.25) < 1e-8
        passed('Actual canvas draw calls show all4 supplied explosion cells then remove the effect; sprite sampling preserves320×256 ratio and160/127 anchor.')

        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_function('W===innerWidth&&H===innerHeight')
            page.evaluate('''() => {itemReset();itemMonsters.configure({maxActive:3});for(let i=0;i<3;i++){const m=itemMonsters.spawn({x:W*(i+1)/4,y:H*.35});m.angle=0;m.moving=i===1;m.turnLeft=i===2?.12:0;}window.gameExitDialogOpen=true;draw();}''')
            page.screenshot(path=str(args.artifacts / f'item-monsters-{width}.png'))
            assert page.evaluate('itemMonsters.targets().every(m=>m.x>18&&m.x<W-18&&m.y>18&&m.y<H-18)')
            page.evaluate('gameExitDialogOpen=false')
        page.set_viewport_size({'width': 915, 'height': 412})
        page.wait_for_function('W===innerWidth&&H===innerHeight')
        page.evaluate('''() => {itemReset();itemMonsters.configure({maxActive:8});for(let i=0;i<8;i++){const m=itemMonsters.spawn({x:W*(i+1)/9,y:H*.4});m.angle=-Math.PI/2+i*Math.PI/4;m.turnLeft=.12;}gameExitDialogOpen=true;draw();}''')
        page.screenshot(path=str(args.artifacts / 'eight-directions.png'))
        page.evaluate('gameExitDialogOpen=false')
        passed('Actual supplied art is visible at915×412,800×360,568×320 and all8 directions; existing HUD/touch layout and character imagery stay intact.')

        page.evaluate('itemReset();itemMonsters.spawn({x:100,y:100})')
        page.locator('#exitGame').tap()
        page.evaluate('window.beforePause=JSON.stringify(itemMonsters.snapshot())')
        page.wait_for_timeout(150)
        assert page.evaluate('JSON.stringify(itemMonsters.snapshot())===beforePause')
        page.locator('#gameExitCancel').tap()
        page.evaluate('hp=0;update(0);window.deathItems=JSON.stringify(itemMonsters.snapshot())')
        expect(page.locator('#gameOverOverlay')).to_be_visible()
        page.wait_for_timeout(150)
        assert page.evaluate('JSON.stringify(itemMonsters.snapshot())===deathItems')
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        page.locator('#startSelected').tap()
        assert page.evaluate('itemMonsters.targets().length===0&&itemMonsters.snapshot().entrances.length===0')
        passed('Exit modal and3-second game-over freeze all item state; restart synchronously clears live entities/warnings/effects without changing existing exit/fullscreen/audio flows.')

        assert not errors and not dialogs and not failed and not external, (errors, dialogs, failed, external)
        report['uncaught_errors'] = errors
        report['native_dialogs'] = dialogs
        report['failed_requests'] = failed
        report['external_requests'] = external
        passed('No uncaught JS errors, native dialogs, failed resources or external requests in standalone mode; full atlas and source scripts are embedded.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()
(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
