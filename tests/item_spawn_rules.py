from world_preservation import WORLD_ASSETS, assert_world_asset, without_world_source, without_world_ui
from controls_preservation import CONTROLS_ASSETS, assert_controls_asset, without_controls_ui
"""Native browser tests for regional kill-count reservations and 125% geometry."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from item_spawn_preservation import without_item_spawn_changes
from item_monster_preservation import assert_item_asset

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'dc9d5594650cfb700dd0a96f28dd10fc0fde5d87'
parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
parser.add_argument('--standalone', action='store_true')
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
report = {'baseline': BASELINE, 'standalone': args.standalone, 'passed': [], 'limits': [
    'Native Chromium with controlled game-state fixtures, not physical Galaxy hardware or a human balance playthrough.',
    'Offline uses the actual standalone HTML injected into an offline document; managed file navigation restrictions are unchanged.'
]}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


source = (ROOT / 'index.html').read_text()
assert without_item_spawn_changes(source) == subprocess.check_output(['git', 'show', BASELINE + ':index.html'], cwd=ROOT).decode()
for path in (ROOT / 'assets').rglob('*'):
    if path.is_file() and str(path.relative_to(ROOT)) in WORLD_ASSETS:
        assert_world_asset(path);continue
    if path.is_file() and str(path.relative_to(ROOT)) in CONTROLS_ASSETS:
        assert_controls_asset(path);continue
    if not path.is_file():
        continue
    relative = str(path.relative_to(ROOT))
    if relative in ['assets/item_monster/item_monster.js', 'assets/item_monster/README.md']:
        assert_item_asset(path)
    else:
        actual = without_controls_ui(path.read_text(), relative).encode() if path.suffix in ('.js','.css') else path.read_bytes()
        assert actual == subprocess.check_output(['git', 'show', BASELINE + ':' + relative], cwd=ROOT)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S) + [(ROOT / 'assets/item_monster/item_monster.js').read_text()]:
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
passed('Only two native integration hooks and the reviewed item manager change; every PNG/scoring/audio/UI/attack file remains unchanged and JS syntax passes.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *unused):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
helpers = '''() => {
 window.ruleReset=(type=0,count=3)=>{itemMonsters.configure({opportunitiesPerRegion:count});start(type);spawn=999;transition=0;invuln=999;fireCooldown=0;};
 window.ruleEnemy=()=>({x:100,y:100,hp:1,special:false,r:16,t:0,speed:0,shot:999,charge:999,kind:0,mode:'chase',vx:0,vy:0});
 window.ruleHit=target=>{bullets=[];shoot();Object.assign(bullets[0],{x:target.x,y:target.y,vx:0,vy:0});update(0);};
 window.ruleKill=()=>{const e=ruleEnemy();enemies=[e];ruleHit(e);};
 window.ruleSlot=()=>itemMonsters.snapshot().regions.find(p=>p.region===stage).phases[phase-1];
 window.ruleSelected=()=>itemMonsters.snapshot().regions.find(p=>p.region===stage).phases.filter(p=>p.selected);
}'''
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 915, 'height': 412}, is_mobile=True, has_touch=True, offline=args.standalone)
        page = context.new_page()
        errors, dialogs, failed, external = [], [], [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
        page.on('requestfailed', lambda request: failed.append(request.url))
        page.on('request', lambda request: external.append(request.url) if args.standalone and request.url.startswith('http') else None)
        if args.standalone:
            page.set_content((ROOT / 'dist/heli_trio_galaxy_test.html').read_text(), wait_until='load')
        else:
            page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.wait_for_function('window.itemMonsters?.ready()&&window.gameScoring&&sprites.every(i=>i.complete&&i.naturalWidth>0)')
        # This existing 4-region/30,400-point fixture explicitly exercises the retained20 option.
        page.evaluate('gameWorlds.setTrialEnabled(false)')
        page.evaluate(helpers)

        geometry = page.evaluate('''() => {
          ruleReset(0,0);const m=itemMonsters.spawn({x:W/2,y:H*.38}),native=ctx.drawImage,calls=[];
          ctx.drawImage=function(im,...v){if(im===itemMonsterAtlas)calls.push(v);return native.call(this,im,...v)};
          try{draw()}finally{ctx.drawImage=native}
          return {radius:m.r,draw:calls[0],snapshot:itemMonsters.snapshot()};
        }''')
        assert geometry['radius'] == 20 and geometry['draw'][6:] == [80, 64]
        assert geometry['draw'][4:6] == [-40, -31.75]
        assert geometry['snapshot']['bodyWidth'] / 64 == geometry['snapshot']['bodyHeight'] / 51.2 == 1.25
        report['geometry'] = {'old': [64, 51.2, 16], 'new': [80, 64, 20], 'draw': geometry['draw']}
        page.screenshot(path=str(args.artifacts / 'size-after-915.png'))
        passed('Actual drawImage geometry is80×64 with unchanged anchor/ratio; body and collision radius both scale exactly1.25 from64×51.2/r16.')

        collisions = page.evaluate('''() => {
          const rows=[];
          for(const kind of [0,1,2])for(const offset of [0,Math.PI/4,Math.PI/2,3*Math.PI/4]){
            const b={kind,x:100,y:100,vx:Math.cos(offset),vy:Math.sin(offset),upgrade:0};
            rows.push({kind,offset,inside:bulletHitsCircle(b,100,100,20),far:bulletHitsCircle(b,200,200,20)});
          }
          const b={kind:0,x:100,y:100,vx:0,vy:-1};return {rows,newEdge:bulletHitsCircle(b,124,100,20),oldEdge:bulletHitsCircle(b,124,100,16)};
        }''')
        assert all(row['inside'] and not row['far'] for row in collisions['rows'])
        assert collisions['newEdge'] and not collisions['oldEdge']
        report['collision_geometry'] = collisions
        passed('All3 bullet kinds use the enlarged collider through the existing circle/rotated-rectangle helper; the newly expanded edge hits while far targets do not.')

        samples = page.evaluate('''() => {
          ruleReset();const rows=[];
          for(let i=0;i<256;i++){itemMonsters.reset();const plan=itemMonsters.snapshot().regions[0];rows.push(plan.phases.filter(s=>s.selected).map(s=>({phase:s.phase,kills:s.requiredKills})));}
          return rows;
        }''')
        assert all(len(row) == 3 and len({slot['phase'] for slot in row}) == 3 and all(1 <= slot['phase'] <= 4 and 1 <= slot['kills'] <= 4 for slot in row) for row in samples)
        assert len({tuple(slot['phase'] for slot in row) for row in samples}) == 4
        assert {slot['kills'] for row in samples for slot in row} == {1, 2, 3, 4}
        report['native_random_plans'] = samples
        passed('256 new-run plans each choose3 distinct phases among1–4, exercise all4 possible omissions and kill thresholds1–4, and never select the boss phase.')

        stable = page.evaluate('''() => {
          ruleReset();const before=JSON.stringify(ruleSelected());for(let i=0;i<10;i++){itemMonsters.enterRegion(0);itemMonsters.update(0);}
          itemMonsters.configure({opportunitiesPerRegion:1});const same=before===JSON.stringify(ruleSelected());
          stage=1;phase=1;itemMonsters.enterRegion(1);const next=itemMonsters.snapshot().regions[1];return {same,next:next.opportunities};
        }''')
        assert stable == {'same': True, 'next': 1}
        passed('Plans/thresholds are fixed at region entry before combat; repeated context entry never rerolls, and quota configuration applies to the next region/run.')

        idle = page.evaluate('''() => {ruleReset();itemMonsters.update(100);itemMonsters.update(100);return {count:itemMonsters.targets().length,pending:itemMonsters.snapshot().entrances.length,normal:phaseKills};}''')
        assert idle == {'count': 0, 'pending': 0, 'normal': 0}
        passed('Elapsed time alone cannot create an item actor: the old interval/22% item generator is completely removed.')

        triggers = page.evaluate('''() => {
          ruleReset();const firstPlan=itemMonsters.snapshot().regions[0];const rows=[];
          for(let step=1;step<=4;step++){
            phase=step;phaseKills=0;itemMonsters.update(0);const slot=firstPlan.phases[step-1];
            for(let kill=1;kill<=4;kill++){
              ruleKill();const now=ruleSlot();rows.push({step,kill,selected:slot.selected,threshold:slot.requiredKills,status:now.status,reservations:itemMonsters.snapshot().entrances.filter(e=>e.region===0&&e.phase===step).length});
            }
          }return rows;
        }''')
        for row in triggers:
            due = row['selected'] and row['kill'] >= row['threshold']
            assert row['reservations'] == int(due)
            assert row['status'] == ('reserved' if due else 'waiting' if row['selected'] else 'not-selected')
        report['actual_kill_thresholds'] = triggers
        passed('Actual normal bullet kills reserve exactly at each chosen1–4 threshold; unselected phases never reserve and subsequent kills cannot duplicate a reservation.')

        fast = page.evaluate('''() => {
          ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;
          const targets=Array.from({length:6},()=>ruleEnemy());enemies=targets;
          bullets=targets.map(e=>({kind:0,x:100,y:100,vx:0,vy:0,life:1,damage:1,pierce:1,hit:[]}));
          update(0);const before=itemMonsters.snapshot();const pending=before.entrances.find(e=>e.phase===chosen.phase);
          itemMonsters.update(1.4);const m=itemMonsters.targets().find(m=>m.origin===pending.id);
          return {oldPhase:chosen.phase,phase,pending:before.entrances.length,origin:m.origin,life:m.life,spawned:itemMonsters.snapshot().regions[0].spawned};
        }''')
        assert fast['phase'] == fast['oldPhase'] + 1 and fast['pending'] == fast['spawned'] == 1 and fast['life'] == 10
        report['same_frame_phase_clear'] = fast
        passed('Six kills in one update trigger and clear a phase before the next tick; the reserved appearance still completes once with ten full seconds.')

        boss_carry = page.evaluate('''() => {
          ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;
          for(let i=0;i<chosen.requiredKills;i++)ruleKill();itemMonsters.update(1.4);const m=itemMonsters.targets()[0];
          m.life=6.75;phase=5;phaseKills=requiredKills;update(0);const before={same:itemMonsters.targets()[0]===m,life:m.life,hp:boss.hp};
          for(let i=0;i<5;i++)ruleHit(m);
          return {before,score:runScore,kills:phaseKills,drops:items.length,bossHP:boss.hp,remaining:itemMonsters.targets().length};
        }''')
        assert boss_carry['before']['same'] and boss_carry['before']['life'] == 6.75
        assert boss_carry['bossHP'] == boss_carry['before']['hp'] == 20 and boss_carry['kills'] == 6 and boss_carry['drops'] == 1 and boss_carry['remaining'] == 0
        passed('A genuinely scheduled live actor survives boss entry with the same object/remaining life and can be killed for its existing drop without damaging the boss or advancing normal kills.')

        pending_boss = page.evaluate('''() => {
          ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;for(let i=0;i<chosen.requiredKills;i++)ruleKill();
          itemMonsters.update(.4);const entry=itemMonsters.snapshot().entrances[0];phase=5;phaseKills=requiredKills;update(0);
          const preserved=itemMonsters.snapshot().entrances[0];itemMonsters.update(1.01);const m=itemMonsters.targets()[0];
          const after=itemMonsters.snapshot();const count=after.regions[0].spawned,lifeAtArrival=m.life;itemMonsters.update(20);
          return {entry,preserved,origin:m.origin,lifeAtArrival,spawned:count,afterExpiry:itemMonsters.targets().length,pending:itemMonsters.snapshot().entrances.length,score:runScore,kills:phaseKills};
        }''')
        assert pending_boss['entry'] == pending_boss['preserved'] and pending_boss['origin'] == pending_boss['entry']['id']
        assert pending_boss['spawned'] == 1 and pending_boss['afterExpiry'] == pending_boss['pending'] == 0
        report['pending_into_boss'] = pending_boss
        passed('An already-triggered warning finishes during the boss; expiration never refunds its opportunity or generates a replacement.')

        region_pending = page.evaluate('''() => {
          ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;for(let i=0;i<chosen.requiredKills;i++)ruleKill();
          const entry=itemMonsters.snapshot().entrances[0];const it={x:40,y:50,type:'hp',life:7.25,r:13,t:0,vx:0,vy:0,turn:999};items=[it];
          phase=5;phaseKills=requiredKills;update(0);while(boss)ruleHit(boss);
          const atTransition={stage,phase,same:items[0]===it,life:it.life,pending:itemMonsters.snapshot().entrances[0].id};
          itemMonsters.update(1.4);const snap=itemMonsters.snapshot();return {atTransition,origin:itemMonsters.targets()[0].origin,oldSpawned:snap.regions[0].spawned,newSpawned:snap.regions[1].spawned};
        }''')
        assert region_pending['atTransition']=={'stage':1,'phase':1,'same':True,'life':7.25,'pending':region_pending['origin']}
        assert region_pending['oldSpawned']==1 and region_pending['newSpawned']==0
        report['reservation_across_region']=region_pending
        passed('A reservation survives an instant boss kill/region change and is charged to its original region; an existing loose item retains identity and remaining lifetime.')

        waiting_art = page.evaluate('''() => {
          ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;for(let i=0;i<chosen.requiredKills;i++)ruleKill();
          Object.defineProperty(itemMonsterAtlas,'complete',{configurable:true,get:()=>false});
          try{phase=5;phaseKills=requiredKills;update(0);itemMonsters.update(2);}
          finally{delete itemMonsterAtlas.complete;}
          const pending=itemMonsters.snapshot().entrances.length;itemMonsters.update(0);
          return {pending,count:itemMonsters.targets().length,life:itemMonsters.targets()[0].life,spawned:itemMonsters.snapshot().regions[0].spawned};
        }''')
        assert waiting_art=={'pending':1,'count':1,'life':10,'spawned':1}
        passed('A separately simulated not-ready atlas cannot discard a triggered warning; readiness recovery in the boss materializes it once with full lifetime.')

        boss_only = page.evaluate('''() => {
          ruleReset();phase=5;phaseKills=requiredKills;update(0);const before=JSON.stringify(itemMonsters.snapshot().regions);
          for(let i=0;i<10;i++)itemMonsters.update(2);
          return {same:before===JSON.stringify(itemMonsters.snapshot().regions),count:itemMonsters.targets().length,pending:itemMonsters.snapshot().entrances.length};
        }''')
        assert boss_only == {'same': True, 'count': 0, 'pending': 0}
        passed('A fresh boss phase creates no new reservation or actor even after20 seconds; only earlier reservations can arrive.')

        missed = page.evaluate('''() => {
          ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;for(let i=0;i<chosen.requiredKills;i++)ruleKill();itemMonsters.update(1.4);
          const before=runScore;itemMonsters.update(10);for(let i=chosen.requiredKills;i<5;i++)ruleKill();itemMonsters.update(100);
          const plan=itemMonsters.snapshot().regions[0];return {before,score:runScore,spawned:plan.spawned,status:plan.phases[chosen.phase-1].status,count:itemMonsters.targets().length,pending:itemMonsters.snapshot().entrances.length,expected:500};
        }''')
        assert missed['spawned'] == 1 and missed['status'] == 'spawned' and missed['count'] == missed['pending'] == 0 and missed['score'] == missed['expected']
        passed('Missing or allowing an actor to expire still consumes that phase opportunity; extra ordinary kills/time never respawn it and expiry awards nothing.')

        no_item_progress = page.evaluate('''() => {
          ruleReset();const m=itemMonsters.spawn({x:150,y:130});for(let i=0;i<5;i++)ruleHit(m);
          return {score:runScore,normal:phaseKills,pending:itemMonsters.snapshot().entrances.length,counts:itemMonsters.snapshot().regions[0].phases.map(p=>p.normalKills)};
        }''')
        assert no_item_progress == {'score': 200, 'normal': 0, 'pending': 0, 'counts': [0, 0, 0, 0]}
        passed('Item kills keep200 points and neither advance phaseKills nor count toward any spawn threshold; boss kills use their separate existing path.')

        full = page.evaluate('''() => {
          ruleReset();const summary=[];
          for(let region=0;region<4;region++){
            const initial=itemMonsters.snapshot().regions.find(p=>p.region===region);
            for(let step=1;step<=5;step++){
              transition=0;for(let i=0;i<6;i++)ruleKill();
              itemMonsters.update(1.4);
              for(const m of itemMonsters.targets())while(m.hp>0)ruleHit(m);
              if(step===5){update(0);transition=0;while(boss)ruleHit(boss);}
            }
            const plan=itemMonsters.snapshot().regions.find(p=>p.region===region);summary.push({initial,after:plan});
          }
          return {summary,result:gameScoring.getLastResult().record,score:runScore,started};
        }''')
        assert not full['started'] and full['score'] == 30400
        record = full['result']
        assert record['normalKills'] == 120 and record['itemKills'] == 12 and record['bossKills'] == 4 and record['clearedPhases'] == 16 and record['score'] == 30400 and record['outcome'] == 'clear'
        assert all(row['after']['spawned'] == row['after']['opportunities'] == 3 and sum(slot['status'] == 'spawned' for slot in row['after']['phases']) == 3 for row in full['summary'])
        report['controlled_full_clear'] = full
        passed('All20 real combat phases and4 boss kills complete with exactly3 item actors per region/12 per run; existing scores total30,400 and match the saved clear/kill counters.')

        page.evaluate('ruleReset();itemMonsters.spawn({x:W*.35,y:H*.4});phase=5;phaseKills=requiredKills;update(0);transition=0;draw()')
        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_function('W===innerWidth&&H===innerHeight')
            page.evaluate('gameExitDialogOpen=true;draw()')
            page.screenshot(path=str(args.artifacts / f'boss-carry-{width}.png'))
            page.evaluate('gameExitDialogOpen=false')
        passed('Actual boss/item/HUD/touch layout screenshots are captured at915×412,800×360,568×320 with the enlarged sprite.')

        page.evaluate('ruleReset();const chosen=ruleSelected()[0];phase=chosen.phase;for(let i=0;i<chosen.requiredKills;i++)ruleKill()')
        page.locator('#exitGame').tap()
        frozen = page.evaluate('JSON.stringify(itemMonsters.snapshot())')
        page.wait_for_timeout(100)
        assert page.evaluate('JSON.stringify(itemMonsters.snapshot())') == frozen
        page.locator('#gameExitCancel').tap()
        page.evaluate('hp=0;update(0)')
        expect(page.locator('#gameOverOverlay')).to_be_visible()
        frozen = page.evaluate('JSON.stringify(itemMonsters.snapshot())')
        page.wait_for_timeout(100)
        assert page.evaluate('JSON.stringify(itemMonsters.snapshot())') == frozen
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        page.locator('#startSelected').tap()
        assert page.evaluate('itemMonsters.targets().length===0&&itemMonsters.snapshot().entrances.length===0&&itemMonsters.snapshot().regions.length===1&&itemMonsters.snapshot().regions[0].region===0')
        passed('Exit confirmation/game-over freeze actors and reservations; a new game clears every old reservation/quota and generates a fresh first-region plan.')

        assert not errors and not dialogs and not failed and not external, (errors, dialogs, failed, external)
        report['uncaught_errors'] = errors
        report['native_dialogs'] = dialogs
        report['failed_resources'] = failed
        report['external_requests'] = external
        passed('No uncaught errors, native dialogs, failed assets or standalone external requests; original art/resources remain embedded and playable.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()
(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
