"""Boss rewards through actual shot/collision paths plus ordinary item regression."""
import argparse
import json
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from reward_preservation import without_boss_reward_changes, without_reward_notice

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
baseline = '501b1a0a80e77e47068450bd263993a28eab1b3e'
source = (root / 'index.html').read_text()
assert without_boss_reward_changes(source).encode() == subprocess.check_output(['git', 'show', baseline + ':index.html'], cwd=root)
for path in (root / 'assets').rglob('*'):
    if path.is_file():
        name = str(path.relative_to(root))
        actual = without_reward_notice(path.read_text(), name).encode() if name.endswith(('.js', '.css')) else path.read_bytes()
        assert actual == subprocess.check_output(['git', 'show', baseline + ':' + name], cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S) + [(root / 'assets/selection/selection.js').read_text()]:
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
report = {'baseline_commit': baseline, 'passed': [], 'limits': [
    'Actual headless Chromium with mobile touch emulation; physical Galaxy/Samsung Internet/Chrome and speaker/sensor testing remain outstanding.',
    'Controlled health, boss and random samples; actual shoot/collision/update paths are exercised, not a manual difficulty playthrough.'
]}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


passed('Only the isolated automatic-reward function, boss payout call and appended notice differ; ordinary drop/pickup, region healing, all other logic/assets and audio are preserved; JS syntax passes.')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 915, 'height': 412}, is_mobile=True, has_touch=True)
        page = context.new_page()
        errors, native_dialogs = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (native_dialogs.append(dialog.type), dialog.dismiss()))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.locator('#startSelected').tap()
        page.wait_for_function('started&&!!document.fullscreenElement')
        page.evaluate('''() => {
            window.rewardEvents=[];
            document.addEventListener('bossreward',event=>rewardEvents.push({...event.detail,hp,upgrade:player.upgrade,stage,phase}));
            window.rewardReset=(kind=2)=>{
                start(kind);spawn=999;invuln=999;transition=0;
                keys.left=keys.right=keys.fire=false;tilt={x:0,y:0};rewardEvents.length=0;
            };
            window.defeatForReview=(index=0,roll=.25,health=1,upgrade=2)=>{
                stage=index;phase=5;phaseKills=requiredKills;hp=health;player.upgrade=upgrade;
                spawn=999;invuln=999;transition=0;enemies=[];enemyBullets=[];warnings=[];items=[];bullets=[];
                const defeated=boss={x:W/2,y:100,r:48,hp:1,maxHp:20+index*15,t:0,shot:999};
                const random=Math.random;let randomCalls=0;Math.random=()=>{randomCalls++;return roll};
                try {shoot();for(const b of bullets)Object.assign(b,{x:boss.x,y:boss.y,vx:0,vy:0});update(.001)}
                finally{Math.random=random}
                return {hp,upgrade:player.upgrade,stage,phase,started,score,items:items.length,
                    rewardGranted:defeated.rewardGranted,randomCalls,events:rewardEvents.slice()};
            };
        }''')

        probability = page.evaluate('''() => {
            const result=[],random=Math.random;
            try {for(const roll of [0,.499999999,.5,.999999999]) {
                rewardReset(2);hp=1;player.upgrade=1;let calls=0;Math.random=()=>{calls++;return roll};
                grantBossReward({hp:0});result.push({roll,calls,event:rewardEvents[0],hp,upgrade:player.upgrade});
            }}finally{Math.random=random}
            return result;
        }''')
        for value in probability:
            assert value['calls'] == 1 and value['event']['type'] == ('hp' if value['roll'] < .5 else 'power')
        report['probability_boundary_samples'] = probability
        passed('The original Math.random()<0.5 split is preserved at both boundaries: one 50/50 health/power draw per boss, with no extra no-reward branch.')

        matrix = page.evaluate('''() => {
            const result=[];
            for(let kind=0;kind<3;kind++)for(let index=0;index<4;index++)for(const roll of [.25,.75]) {
                rewardReset(kind);result.push({kind,defeatedStage:index,roll,...defeatForReview(index,roll)});
            }
            return result;
        }''')
        for value in matrix:
            index, kind = value['defeatedStage'], value['kind']
            is_health = value['roll'] < .5
            cap = [4, 6, 9][kind]
            reward_hp = min(cap, 3) if is_health else 1
            assert value['hp'] == min(cap, reward_hp + (2 if index < 3 else 0))
            assert value['upgrade'] == (2 if is_health else 3)
            assert value['stage'] == min(index + 1, 3) and value['phase'] == (1 if index < 3 else 5)
            assert value['started'] == (index < 3) and value['score'] == 10 and value['items'] == 0
            assert value['rewardGranted'] and value['randomCalls'] == 1 and len(value['events']) == 1
            event = value['events'][0]
            assert event['hp'] == reward_hp and event['upgrade'] == value['upgrade'] and event['stage'] == index
            assert event['amount'] == (2 if is_health else 1)
        report['all_character_stage_reward_cases'] = matrix
        passed('All 24 character×stage×reward cases defeat bosses through real bullets/collision: payout precedes original next-region +2 HP; desert final clear adds no region healing and no item is dropped.')

        caps = page.evaluate('''() => {
            const result=[],random=Math.random;
            try {for(let kind=0;kind<3;kind++)for(const full of [false,true])for(const roll of [.25,.75]) {
                rewardReset(kind);hp=maxHP[kind]-(full?0:1);player.upgrade=full?5:4;
                let calls=0;Math.random=()=>{calls++;return roll};grantBossReward({hp:0});
                result.push({kind,full,roll,calls,hp,upgrade:player.upgrade,event:rewardEvents[0]});
            }}finally{Math.random=random}
            return result;
        }''')
        for value in caps:
            is_health, cap = value['roll'] < .5, [4, 6, 9][value['kind']]
            assert value['hp'] == (cap if is_health or value['full'] else cap - 1)
            assert value['upgrade'] == (5 if not is_health or value['full'] else 4)
            assert value['calls'] == 1 and value['event']['amount'] == (0 if value['full'] else 1)
            assert value['event']['type'] == ('hp' if is_health else 'power')
        report['cap_cases'] = caps
        passed('Health 4/6/9 and upgrade 5 caps hold; partially useful health rewards report +1 and full caps report 0 without rerolling the reward type.')

        duplicates = page.evaluate('''() => {
            const result=[],random=Math.random;
            try {for(const roll of [.25,.75]) {
                rewardReset(2);hp=1;player.upgrade=0;let calls=0;Math.random=()=>{calls++;return roll};
                const target={hp:0};for(let i=0;i<10;i++)grantBossReward(target);
                const first={calls,hp,upgrade:player.upgrade,events:rewardEvents.length};
                grantBossReward({hp:1});started=false;grantBossReward({hp:0});
                result.push({roll,...first,afterInvalidCalls:calls,afterInvalidEvents:rewardEvents.length});
            }}finally{Math.random=random}
            return result;
        }''')
        for value in duplicates:
            assert value['calls'] == value['afterInvalidCalls'] == 1
            assert value['events'] == value['afterInvalidEvents'] == 1
            assert value['hp'] == (3 if value['roll'] < .5 else 1)
            assert value['upgrade'] == (0 if value['roll'] < .5 else 1)
        report['duplicate_guard_cases'] = duplicates
        passed('Ten attempts against the same defeated boss pay once; living bosses and ended games pay nothing; actual multi-bullet kills in the stage matrix also pay once.')

        ordinary = page.evaluate('''() => {
            const result=[],random=Math.random;
            try {for(const roll of [.25,.75]) {
                rewardReset(2);hp=1;player.upgrade=0;
                enemies=[{x:100,y:100,hp:1,special:true,r:16,life:999,turn:999,kind:0,speed:0,shot:999,t:0,mode:'chase',charge:999,vx:0,vy:0}];
                Math.random=()=>roll;shoot();Object.assign(bullets[0],{x:100,y:100,vx:0,vy:0});update(.001);
                const before={count:items.length,type:items[0]?.type,r:items[0]?.r,hp,upgrade:player.upgrade,events:rewardEvents.length};
                Object.assign(items[0],{x:player.x,y:player.y,vx:0,vy:0,turn:999});update(.001);
                const after={count:items.length,hp,upgrade:player.upgrade,events:rewardEvents.length};
                update(.001);result.push({roll,before,after,afterSecondUpdate:{hp,upgrade:player.upgrade}});
            }}finally{Math.random=random}
            return result;
        }''')
        for value in ordinary:
            is_health = value['roll'] < .5
            assert value['before'] == {'count': 1, 'type': 'hp' if is_health else 'power', 'r': 13, 'hp': 1, 'upgrade': 0, 'events': 0}
            expected = {'hp': 3 if is_health else 1, 'upgrade': 0 if is_health else 1}
            assert value['after'] == {'count': 0, 'events': 0, **expected} and value['afterSecondUpdate'] == expected
        report['ordinary_enemy_drop_and_pickup'] = ordinary
        passed('Ordinary special-enemy kills still drop one 13px health/power item; bonuses apply only on contact with the same effects and no boss notice or double pickup.')

        notice = page.locator('#bossRewardNotice')
        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.evaluate('rewardReset(2)')
            page.evaluate('defeatForReview(0,.25)')
            expect(notice).to_have_text('❤️ 체력 +2')
            expect(notice).to_be_visible()
            bounds = notice.bounding_box()
            assert bounds['x'] >= 0 and bounds['y'] >= 0 and bounds['x'] + bounds['width'] <= width
            assert bounds['height'] <= 30
            assert notice.evaluate('e=>getComputedStyle(e).pointerEvents') == 'none'
            for name in ['hud', 'fire', 'left', 'right', 'exitGame', 'fullscreenToggle']:
                control = page.locator('#' + name).bounding_box()
                assert not (bounds['x'] < control['x'] + control['width'] and bounds['x'] + bounds['width'] > control['x'] and bounds['y'] < control['y'] + control['height'] and bounds['y'] + bounds['height'] > control['y']), name
            if width == 915:
                page.screenshot(path=str(args.artifacts / 'health-reward.png'))
            if width == 568:
                page.screenshot(path=str(args.artifacts / 'compact-reward.png'))
        page.wait_for_timeout(850)
        page.evaluate('player.upgrade=0;const r=Math.random;Math.random=()=>.75;try{grantBossReward({hp:0})}finally{Math.random=r}')
        expect(notice).to_have_text('⚡ 무기 강화 +1')
        page.wait_for_timeout(1100)
        expect(notice).to_be_visible()
        expect(notice).to_be_hidden(timeout=1200)
        page.evaluate('hp=maxHP[player.type];const r=Math.random;Math.random=()=>.25;try{grantBossReward({hp:0})}finally{Math.random=r}')
        expect(notice).to_have_text('❤️ 체력 최대')
        page.evaluate('player.upgrade=5;const r=Math.random;Math.random=()=>.75;try{grantBossReward({hp:0})}finally{Math.random=r}')
        expect(notice).to_have_text('⚡ 무기 강화 최대')
        passed('The 1.8-second notice displays actual +2/+1/cap text, replaces earlier messages without stale timeouts, fits three landscape sizes and overlaps no HUD/touch/fullscreen/exit controls.')

        page.set_viewport_size({'width': 915, 'height': 412})
        page.evaluate('rewardReset(2)')
        page.evaluate('defeatForReview(3,.75,1,2)')
        expect(page.locator('#menu')).to_be_visible()
        expect(notice).to_have_text('⚡ 무기 강화 +1')
        expect(notice).to_be_visible()
        assert page.evaluate('!!document.fullscreenElement&&!started')
        page.screenshot(path=str(args.artifacts / 'final-clear-reward.png'))
        page.locator('#startSelected').tap()
        page.wait_for_function('started')
        expect(notice).to_be_hidden()
        page.evaluate('defeatForReview(0,.75,1,0)')
        assert page.evaluate('player.upgrade===1&&!!document.fullscreenElement')
        assert not errors and not native_dialogs, (errors, native_dialogs)
        passed('Final-clear rewards remain visible in fullscreen selection; a new game clears old text and its new boss can pay again; no native dialogs or uncaught JS errors occur.')
        browser.close()
finally:
    server.shutdown();server.server_close()

(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
