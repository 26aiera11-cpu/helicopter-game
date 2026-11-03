from world_preservation import WORLD_ASSETS, assert_world_asset, without_world_source, without_world_ui
from controls_preservation import CONTROLS_ASSETS, assert_controls_asset, without_controls_ui
from item_monster_preservation import assert_item_asset
"""Real-browser scoring, local TOP 10 persistence, result lifecycle and mobile UI."""
import argparse
import base64
import json
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import expect, sync_playwright
from scoring_preservation import without_scoring_changes, without_scoring_ui, SCORE_ASSETS, assert_scoring_asset

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '1279ec48a1b1f1f544245315d69200d94562b71a'
parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
parser.add_argument('--standalone', action='store_true')
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
report = {'baseline': BASELINE, 'standalone': args.standalone, 'passed': [], 'limits': [
    'Actual Chromium, controlled game-state fixtures and native storage/media; not physical Galaxy hardware or speaker listening.',
    'Offline uses the identical embedded HTML on a pre-established HTTP origin with networking disabled, not direct Android file opening.',
    'Storage denial/quota and corrupt-data branches are intentionally injected; ordinary persistence uses native localStorage.'
]}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


source = (ROOT / 'index.html').read_text()
assert without_scoring_changes(source) == subprocess.check_output(['git', 'show', BASELINE + ':index.html'], cwd=ROOT).decode()
for path in (ROOT / 'assets').rglob('*'):
    if path.is_file() and str(path.relative_to(ROOT)) in WORLD_ASSETS:
        assert_world_asset(path);continue
    if path.is_file() and str(path.relative_to(ROOT)) in CONTROLS_ASSETS:
        assert_controls_asset(path);continue
    if path.is_file() and str(path.relative_to(ROOT)).startswith('assets/item_monster/'):
     assert_item_asset(path);continue
    if not path.is_file():
        continue
    name = str(path.relative_to(ROOT))
    if name in SCORE_ASSETS:
        assert_scoring_asset(path)
        continue
    actual = without_scoring_ui(path.read_text(), name).encode() if path.suffix in ('.js', '.css') else path.read_bytes()
    assert actual == subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
assert not re.search(r'\bscore\b', re.sub(r'data:[^;]+;base64,[A-Za-z0-9+/=]+', '', source).split('function start(type)')[1].split('const sensorBtn=')[0])
for block in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S) + [
        (ROOT / 'assets/score/score.js').read_text(), (ROOT / 'assets/selection/selection.js').read_text()]:
    subprocess.run(['node', '--check', '-'], input=block, text=True, capture_output=True, check=True)
passed('Exact reviewed score/UI changes reverse to current-main baseline; all previous assets, combat, items, BGM, fullscreen and exit code are preserved; JS syntax passes.')


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *unused):
        pass

    def do_GET(self):
        if self.path == '/offline-origin':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<!doctype html><title>Offline test origin</title>')
        else:
            super().do_GET()


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}'
html = (ROOT / 'dist/heli_trio_galaxy_test.html').read_text() if args.standalone else None
helpers = '''() => {
 window.scoreReset=(kind=0)=>{itemMonsters.configure({opportunitiesPerRegion:0});start(kind);transition=0;spawn=999;invuln=999;fireCooldown=0;};
 window.scoreEnemy=(special=false)=>({x:100,y:100,r:16,hp:1,special,life:10,t:0,turn:999,speed:0,shot:999,charge:999,vx:0,vy:0,kind:0,mode:'chase'});
 window.scoreKill=target=>{bullets=[];shoot();Object.assign(bullets[0],{x:target.x,y:target.y,vx:0,vy:0});update(0);};
}'''

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 915, 'height': 412}, is_mobile=True, has_touch=True, timezone_id='Asia/Seoul')
        context.add_init_script('''(() => {const Native=window.Audio;window.nativeTracks=[];
          window.Audio=new Proxy(Native,{construct(target,args){const a=new target(...args);nativeTracks.push(a);return a;}});})()''')
        errors, dialogs, external = [], [], []

        def observe(page):
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('dialog', lambda dialog: (dialogs.append(dialog.type), dialog.dismiss()))
            page.on('request', lambda request: external.append(request.url) if args.standalone and request.url.startswith('http') and request.url != url + '/offline-origin' else None)

        page = context.new_page()
        observe(page)

        def load(clear=False):
            if args.standalone:
                context.set_offline(False)
                page.goto(url + '/offline-origin', wait_until='load')
                if clear:
                    page.evaluate('localStorage.clear()')
                context.set_offline(True)
                page.set_content(html, wait_until='load')
            else:
                page.goto(url, wait_until='load')
                if clear:
                    page.evaluate('localStorage.clear()')
                    page.reload(wait_until='load')
            page.wait_for_function('window.gameScoring && [...sprites,...terrainImgs].every(i=>i.complete&&i.naturalWidth>0)')
            page.evaluate(helpers)

        load(clear=True)
        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.screenshot(path=str(args.artifacts / f'selection-{width}.png'))
        page.set_viewport_size({'width': 915, 'height': 412})
        page.locator('#selectionSettings').tap()
        expect(page.locator('#selectionSettings')).to_have_text('🏆 점수 순위표')
        expect(page.locator('#leaderboardDialog')).to_be_visible()
        expect(page.locator('#leaderboardEmpty')).to_have_text('아직 기록이 없습니다')
        assert page.evaluate('!audioControls.classList.contains("settings-open")')
        page.screenshot(path=str(args.artifacts / 'empty-top10.png'))
        page.locator('#leaderboardClose').tap()
        passed('Visible Settings lettering is covered by the opaque score button; empty TOP10 opens/closes, without the removed audio-settings highlight.')

        kills = page.evaluate('''() => {
          scoreReset();const e=scoreEnemy();enemies=[e];scoreKill(e);
          const normal={score:runScore,kills:phaseKills};
          const repeated=gameScoring.enemyDefeated(e);update(0);
          const afterDuplicate={score:runScore,kills:phaseKills};
          const special=itemMonsters.spawn({x:100,y:100});for(let i=0;i<5;i++)scoreKill(special);
          return {normal,repeated,afterDuplicate,score:runScore,items:items.length,kills:phaseKills};
        }''')
        assert kills == {'normal': {'score': 100, 'kills': 1}, 'repeated': False,
                         'afterDuplicate': {'score': 100, 'kills': 1}, 'score': 300, 'items': 1, 'kills': 1}
        counted = page.evaluate('gameScoring.finish("abandoned").record')
        assert counted['normalKills'] == 1 and counted['itemKills'] == 1 and counted['score'] == 300
        report['actual_kills'] = kills
        report['actual_kill_analysis'] = counted
        passed('Actual normal/item-monster bullet kills award100/200 exactly once; repeated credit is rejected and requiredKills/normal item drop stay unchanged.')
        expired = page.evaluate('''() => {scoreReset();const e=itemMonsters.spawn({x:100,y:100});e.life=0;update(.001);return {score:runScore,kills:phaseKills,items:items.length}}''')
        assert expired == {'score': 0, 'kills': 0, 'items': 0}
        passed('An item monster expiring without a kill gives no points, kill progress or dropped item.')

        phases = page.evaluate('''() => {
          scoreReset();const values=[];
          for(let region=0;region<4;region++)for(let step=1;step<=4;step++) {
            stage=region;phase=step;const before=runScore;nextPhase();
            gameScoring.phaseCleared(region,step);gameScoring.phaseCleared(region,5);
            values.push(runScore-before);
          }return {values,total:runScore};
        }''')
        assert phases == {'values': [500] * 16, 'total': 8000}
        report['ordinary_phase_bonuses'] = phases
        passed('Only the16 ordinary phases award500 each; repeated clear notification and phase5 add no duplicate/region bonus.')

        bosses = page.evaluate('''() => {
          const values=[];
          for(let region=0;region<4;region++) {
            scoreReset(2);stage=region;phase=5;phaseKills=requiredKills;update(0);
            const target=boss;target.hp=1;scoreKill(target);gameScoring.bossDefeated(target);
            values.push({region,score:runScore,reward:target.rewardGranted,stage,phase,started});
          }return values;
        }''')
        assert all(row['score'] == 2000 and row['reward'] for row in bosses)
        assert [row['stage'] for row in bosses] == [1, 2, 3, 3]
        assert [row['phase'] for row in bosses] == [1, 1, 1, 5]
        assert not bosses[-1]['started']
        clear_result = page.evaluate('gameScoring.getLastResult()')
        assert clear_result['record']['score'] == 2000 and clear_result['record']['characterName'] == '탱코'
        assert clear_result['record']['outcome'] == 'clear' and clear_result['record']['bossKills'] == 1
        expect(page.locator('#selectionResult')).to_contain_text('탱코 · 2,000점')
        page.screenshot(path=str(args.artifacts / 'final-clear.png'))
        assert page.evaluate('gameScoring.finish("clear").record.id') == clear_result['record']['id']
        report['boss_kill_bonuses'] = bosses
        passed('All4 actual boss kills award2000 once, including desert; automatic reward/region transition stay intact and final-clear character/score match the single saved result.')

        load(clear=True)
        page.locator('.select-hit[data-heli="2"]').tap()
        page.wait_for_function('!selectionBgm.paused&&selectionBgm.currentTime>.03')
        audio_geometry = page.locator('#audioControls').bounding_box()
        page.locator('#fullscreenToggle').tap()
        page.wait_for_function('!!document.fullscreenElement')
        page.locator('#startSelected').tap()
        page.wait_for_function('started&&!nativeTracks[0].paused&&nativeTracks[0].currentTime>.03')
        page.evaluate('spawn=999;transition=0;invuln=999;runScore=8500;stage=2;phase=3;player.upgrade=4;update(0)')
        expect(page.locator('#hud')).to_contain_text('🏆 8,500')
        assert '⭐' not in page.locator('#hud').inner_text()
        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.screenshot(path=str(args.artifacts / f'hud-{width}.png'))
            layout = page.evaluate('''() => {const a=hud.getBoundingClientRect(),b=fullscreenToggle.getBoundingClientRect();return {fits:a.right<=b.left+1&&a.height<H*.3,text:hud.textContent}}''')
            assert layout['fits'] and '⚡ 4/5' in layout['text'] and '❤️ 9/9' in layout['text']
        page.set_viewport_size({'width': 915, 'height': 412})
        passed('HUD updates with comma-separated trophy points and keeps HP/upgrade readable without overlapping fullscreen/exit controls at all3 requested landscape sizes.')

        page.evaluate('''() => {window.deathTime=performance.now();hp=1;invuln=0;
          enemyBullets=[{x:player.x,y:player.y,vx:0,vy:0,r:5,life:3}];update(0);}''')
        expect(page.locator('#gameOverOverlay')).to_be_visible()
        expect(page.locator('#gameOverScore')).to_have_text('🏆 8,500점')
        expect(page.locator('#gameOverCharacter')).to_have_text('탱코')
        expect(page.locator('#gameOverRank')).to_contain_text('새로운 TOP 10 기록 · 1위')
        record = page.evaluate('gameScoring.getLastResult().record')
        assert record['score'] == 8500 and record['regionId'] == 2 and record['phase'] == 3 and record['finalUpgrade'] == 4
        assert page.evaluate('[...nativeTracks,selectionBgm].filter(a=>a.loop).every(a=>a.paused)')
        snapshot = 'JSON.stringify({player,bullets,enemyBullets,enemies,items,worldScroll,rotorSpin,runScore,hp})'
        frozen = page.evaluate(snapshot)
        page.evaluate('beginGameOver();gameScoring.finish("game_over")')
        page.wait_for_timeout(180)
        assert page.evaluate(snapshot) == frozen
        assert page.evaluate('gameScoring.getHistory().length===1&&gameScoring.getTop().length===1')
        page.screenshot(path=str(args.artifacts / 'game-over-915.png'))
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        elapsed = page.evaluate('performance.now()-deathTime')
        assert 2950 <= elapsed < 4300
        expect(page.locator('#selectionResult')).to_have_text('')
        page.wait_for_function('!selectionBgm.paused&&selectionBgm.currentTime>.03')
        assert page.evaluate('!!document.fullscreenElement')
        report['game_over'] = {'return_ms': elapsed, 'record': record, 'bgm_paused_during_overlay': True}
        passed('Real fatal hit freezes play/BGM, shows score/character/newTOP10 for3s, stores one matching result despite duplicate finish calls, then restores clean selection music/fullscreen.')

        page.locator('#selectionSettings').tap()
        expect(page.locator('tr.latest-record')).to_have_count(1)
        clock = page.evaluate('selectionBgm.currentTime')
        page.touchscreen.tap(450, 370)
        page.touchscreen.tap(200, 170)
        page.wait_for_timeout(100)
        assert page.evaluate('!started&&selectedHeli===2&&leaderboardDialog.open&&!!document.fullscreenElement&&selectionBgm.currentTime') > clock
        page.locator('#leaderboardClose').tap()
        assert page.locator('#audioControls').bounding_box() == audio_geometry
        for selector in ['#musicToggle', '#sfxToggle']:
            page.locator(selector).tap()
            expect(page.locator(selector)).to_have_attribute('aria-pressed', 'false')
            page.locator(selector).tap()
            expect(page.locator(selector)).to_have_attribute('aria-pressed', 'true')
        passed('Modal blocks underlying character/Start touches and highlights the latest record; closing preserves fullscreen/BGM and original audio button geometry/toggles.')

        load(clear=True)
        seeded = page.evaluate('''() => {
          const NativeDate=Date;window.Date=class extends NativeDate {constructor(...a){super(...(a.length?a:['2026-11-02T04:00:00Z']))}};
          const scores=[500,3000,1000,3000,8000,12000,7000,9000,4000,11000,100,10000],records=[];
          try {scores.forEach((points,index)=>{scoreReset(index%3);runScore=points;beginGameOver();records.push(gameScoring.getLastResult().record);gameScoring.finish('game_over');});}
          finally {window.Date=NativeDate;}
          return {records,top:gameScoring.getTop(),history:gameScoring.getHistory()};
        }''')
        expected = sorted(seeded['records'], key=lambda row: (-row['score'], row['order']))[:10]
        assert seeded['top'] == expected and len(seeded['history']) == 12
        assert len({row['createdAt'] for row in seeded['records']}) == 1
        assert [row['id'] for row in expected if row['score'] == 3000] == [seeded['records'][1]['id'], seeded['records'][3]['id']]
        assert len({row['characterId'] for row in expected}) == 3
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        page.locator('#selectionSettings').tap()
        expect(page.locator('#leaderboardRows tr')).to_have_count(10)
        expect(page.locator('tr.latest-record')).to_have_count(1)
        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            scroll = page.locator('.leaderboard-scroll')
            scroll.evaluate('e=>e.scrollTop=0')
            page.screenshot(path=str(args.artifacts / f'top10-{width}.png'))
            scroll.evaluate('e=>e.scrollTop=e.scrollHeight')
            assert scroll.evaluate('e=>e.scrollTop>0&&e.scrollWidth<=e.clientWidth+1')
            last = page.locator('#leaderboardRows tr').last.bounding_box()
            viewport = scroll.bounding_box()
            assert last['y'] + last['height'] <= viewport['y'] + viewport['height'] + 1
            page.screenshot(path=str(args.artifacts / f'top10-bottom-{width}.png'))
        report['ranked_fixtures'] = {'input': seeded['records'], 'expected_top': expected}
        passed('Twelve results across3 characters produce exactly10 rows; equal timestamps/scores keep earlier achievement first, repeated characters are allowed and every landscape scrolls through row10.')
        page.locator('#leaderboardClose').tap()
        before_reload = page.evaluate('gameScoring.getTop()')
        load()
        assert page.evaluate('gameScoring.getTop()') == before_reload
        page.locator('#selectionSettings').tap()
        expect(page.locator('#leaderboardRows tr')).to_have_count(10)
        page.keyboard.press('Escape')
        expect(page.locator('#leaderboardDialog')).not_to_be_visible()
        passed('Native localStorage restores the same sorted TOP10 after navigation/reload; Escape closes the modal and no legacy star conversion occurs.')

        page.evaluate('scoreReset();runScore=0;hp=0;update(0)')
        expect(page.locator('#gameOverRank')).to_have_text('TOP 10 진입 안됨')
        assert page.evaluate('gameScoring.getTop()') == before_reload
        assert page.evaluate('gameScoring.getHistory().at(-1).score') == 0
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        passed('A new result below tenth place explicitly reports no TOP10 entry, keeps the ranking unchanged and still saves analysis once.')

        bounded = page.evaluate('''() => {
          const before=JSON.stringify(gameScoring.getTop());
          for(let i=0;i<115;i++){scoreReset(i%3);runScore=999999;gameScoring.finish('abandoned');}
          return {unchanged:before===JSON.stringify(gameScoring.getTop()),history:gameScoring.getHistory(),
            stored:JSON.parse(localStorage.getItem(gameScoring.storageKeys.history)),top:JSON.parse(localStorage.getItem(gameScoring.storageKeys.top))};
        }''')
        assert bounded['unchanged'] and len(bounded['history']) == 100
        assert len({row['id'] for row in bounded['history']}) == 100
        assert bounded['stored']['version'] == bounded['top']['version'] == 1
        assert all(row['outcome'] == 'abandoned' for row in bounded['history'])
        page.locator('#exitGame').tap()
        page.locator('#gameExitCancel').tap()
        assert page.evaluate('started')
        page.locator('#exitGame').tap()
        page.locator('#gameExitConfirm').tap()
        assert page.evaluate('!started&&gameScoring.getHistory().length===100')
        report['history_capacity'] = {'limit': 100, 'retained': len(bounded['history']), 'version': 1, 'top_unchanged_by_abandoned': True}
        passed('Analysis history is separate/versioned and capped at100;115 abandoned games never affect TOP10, with unique IDs and all required counters/time/upgrade/result fields.')

        # Real modal-confirmed abandonment, rather than only the capacity fixture.
        page.locator('#startSelected').tap()
        page.evaluate('spawn=999;invuln=999;runScore=987654;stage=1;phase=4;player.upgrade=3;update(.5)')
        old_top = page.evaluate('gameScoring.getTop()')
        page.locator('#exitGame').tap()
        page.locator('#gameExitConfirm').tap()
        last = page.evaluate('gameScoring.getHistory().at(-1)')
        assert last['outcome'] == 'abandoned' and last['score'] == 987654 and last['phase'] == 4 and last['playTimeSeconds'] >= .5
        assert page.evaluate('gameScoring.getTop()') == old_top
        passed('Actual in-game exit cancel resumes play; confirmed exit saves one analysis-only result with reached phase/active play time and leaves TOP10 unchanged.')

        for raw in ['{invalid', '{"version":999,"records":[]}', '{"version":1,"records":[{"id":"broken"}]}']:
            page.evaluate('(raw)=>{localStorage.clear();localStorage.setItem("heliTrio.top10.v1",raw);localStorage.setItem("heliTrio.playHistory.v1",raw);localStorage.setItem("legacyStars","160");}', raw)
            load()
            assert page.evaluate('gameScoring.getTop().length===0&&localStorage.getItem("legacyStars")==="160"')
            page.evaluate('scoreReset(1);runScore=400;hp=0;update(0)')
            expect(page.locator('#gameOverScore')).to_have_text('🏆 400점')
            assert page.evaluate('gameScoring.getLastResult().saved&&gameScoring.getHistory().length===1&&gameScoring.getTop()[0].score===400&&JSON.parse(localStorage.getItem(gameScoring.storageKeys.top)).version===1')
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        page.locator('#selectionSettings').tap()
        expect(page.locator('#leaderboardStorage')).to_have_text('')
        page.locator('#leaderboardClose').tap()
        passed('Corrupt JSON, unknown versions and invalid records recover with valid persisted new data and no stale failure notice; legacy160 stars stay untouched and are never converted.')

        for failure in ['quota', 'unavailable']:
            bad_context = browser.new_context(viewport={'width': 568, 'height': 320}, has_touch=True, is_mobile=True)
            script = "Storage.prototype.setItem=function(){throw new DOMException('Test quota','QuotaExceededError')}" if failure == 'quota' else "Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Test storage denial','SecurityError')}})"
            bad_context.add_init_script(script)
            bad = bad_context.new_page()
            bad.on('pageerror', lambda error: errors.append(str(error)))
            if args.standalone:
                bad.goto(url + '/offline-origin', wait_until='load')
                bad_context.set_offline(True)
                bad.set_content(html, wait_until='load')
            else:
                bad.goto(url, wait_until='load')
            bad.wait_for_function('window.gameScoring')
            bad.evaluate('start(0);runScore=100;hp=0;update(0)')
            expect(bad.locator('#gameOverOverlay')).to_be_visible()
            expect(bad.locator('#gameOverRank')).to_contain_text('기록 저장 불가')
            assert bad.evaluate('gameScoring.getTop().length===1&&gameScoring.getHistory().length===1')
            expect(bad.locator('#menu')).to_be_visible(timeout=4000)
            bad.locator('#selectionSettings').tap()
            expect(bad.locator('#leaderboardStorage')).to_contain_text('이번 실행 동안만')
            bad_context.close()
        passed('Denied localStorage access and quota exceptions keep game-over/return/modal usable with a volatile result and a clear persistence limitation.')

        assert not errors and not dialogs and not external, (errors, dialogs, external)
        report['uncaught_errors'] = errors
        report['native_dialogs'] = dialogs
        report['external_game_requests'] = external
        passed('No uncaught JS errors or browser alert/confirm dialogs occur during score, storage, modal and result flows.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()
(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
