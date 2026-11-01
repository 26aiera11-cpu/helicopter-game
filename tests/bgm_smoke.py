"""Observe real WAV playback clocks/pause states; do not mock audio playback."""
import argparse
import base64
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
from reward_preservation import without_boss_reward_changes, without_reward_notice
from final_trio_preservation import FINAL_TRIO_ASSET, assert_final_trio_asset, without_final_trio_changes
from tanko_preservation import TANKO_ASSET, assert_tanko_asset, without_tanko_restore

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
baseline = '7e5faf5cee3e38e17301fd8746f693b7010934cf'
before = subprocess.check_output(['git', 'show', baseline + ':index.html'], cwd=root).decode()
after = (root / 'index.html').read_text()
old = "if(hp<=0){started=false;menu.classList.remove('hidden');"
new = "if(hp<=0){started=false;window.gameAudioStarted=false;gameAudio.pause();menu.classList.remove('hidden');"
report = {'baseline_commit': baseline, 'passed': [], 'limits': [
    'Actual headless Chromium with user touch gestures and real HTMLAudioElement playback; no audio-playback/autoplay-policy mocks.',
    'No physical Galaxy/Samsung Internet/Chrome or audible speaker listening; volume, sound quality, latency and Android app/route changes require device tests.',
    'Health/stage/boss transitions are controlled game-state tests, not a manual full playthrough.'
]}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


assert before.count(old) == 1 and without_boss_reward_changes(without_final_trio_changes(without_tanko_restore(after))) == before.replace(old, new, 1)
audio_pattern = r'data:audio/[^;]+;base64,[A-Za-z0-9+/=]+'
old_audio, new_audio = re.findall(audio_pattern, before), re.findall(audio_pattern, after)
assert old_audio == new_audio and len(new_audio) == 12
report['unchanged_wav_sha256'] = [hashlib.sha256(base64.b64decode(url.split(',')[1])).hexdigest() for url in new_audio]
for path in (root / 'assets').rglob('*'):
    if path.is_file():
        name = str(path.relative_to(root))
        if name == TANKO_ASSET:
            assert_tanko_asset()
            continue
        if name == FINAL_TRIO_ASSET:
            assert_final_trio_asset()
            continue
        actual = without_reward_notice(path.read_text(), name).encode() if name.endswith(('.js', '.css')) else path.read_bytes()
        assert actual == subprocess.check_output(['git', 'show', baseline + ':' + name], cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', after, re.S):
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
passed('Only authorized audio/boss-reward/Trio/Tanko PNG changes differ; original audio, other character assets and game/UI code are preserved, and JavaScript syntax checks pass.')


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


probe = '''(() => {
    const names=['stage_forest','stage_rock','stage_sea','stage_desert',
        'boss_forest','boss_rock','boss_sea','boss_desert','warning','appear','hit','defeat'];
    const probe=window.__bgmProbe={elements:[],events:[],overlaps:[],maxActive:0};
    probe.active=()=>probe.elements.filter(a=>a.loop&&!a.paused&&!a.ended);
    probe.sample=reason=>{
        const active=probe.active();probe.maxActive=Math.max(probe.maxActive,active.length);
        if(active.length>1)probe.overlaps.push({reason,names:active.map(a=>a.__probeName)});
    };
    const NativeAudio=window.Audio;
    window.Audio=new Proxy(NativeAudio,{construct(target,args){
        const a=new target(...args);a.__probeName=names[probe.elements.length];probe.elements.push(a);
        for(const type of ['play','playing','pause','ended'])a.addEventListener(type,()=>{
            probe.events.push({type,name:a.__probeName,time:a.currentTime});probe.sample(type);
        });
        return a;
    }});
    const sample=()=>{probe.sample('frame');requestAnimationFrame(sample)};requestAnimationFrame(sample);
})()'''
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 915, 'height': 412}, is_mobile=True, has_touch=True)
        context.add_init_script(probe)
        page = context.new_page()
        errors, native_dialogs = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (native_dialogs.append(dialog.type), dialog.dismiss()))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        page.wait_for_function('__bgmProbe.elements.length===12 && __bgmProbe.elements.every(a=>!a.error&&a.readyState>=1&&a.duration>0)')
        assert page.evaluate('__bgmProbe.elements.filter(a=>a.loop).length===8 && __bgmProbe.active().length===0')
        passed('All 12 original WAV files load native playable metadata; eight BGM elements are initially paused on the selection screen.')

        def start(kind):
            page.locator(f'.select-hit[data-heli="{kind}"]').tap()
            page.locator('#startSelected').tap()
            page.wait_for_function('(kind)=>started&&player.type===kind', arg=kind)
            page.evaluate('invuln=999;spawn=999;transition=0')

        def expect_track(name):
            page.wait_for_function('name=>__bgmProbe.active().length===1&&__bgmProbe.active()[0].__probeName===name&&__bgmProbe.active()[0].volume>0', arg=name)
            previous = page.evaluate('__bgmProbe.active()[0].currentTime')
            page.wait_for_function('old=>__bgmProbe.active().length===1&&__bgmProbe.active()[0].currentTime>old+.08', arg=previous)

        def lose():
            page.evaluate('hp=0')
            page.wait_for_function('!started')
            expect(page.locator('#menu')).to_be_visible()
            expect(page.locator('#selectionResult')).to_contain_text('게임 오버')
            assert page.evaluate('!window.gameAudioStarted&&__bgmProbe.elements.filter(a=>a.loop).every(a=>a.paused)')

        start(0)
        expect_track('stage_forest')
        report['forest_start'] = page.evaluate('({active:__bgmProbe.active().map(a=>a.__probeName),time:__bgmProbe.elements[0].currentTime,volume:__bgmProbe.elements[0].volume})')
        passed('A real touch start plays the forest BGM at nonzero volume and its native playback clock advances.')

        lose()
        page.wait_for_timeout(80)
        paused_times = page.evaluate('__bgmProbe.elements.filter(a=>a.loop).map(a=>a.currentTime)')
        page.wait_for_timeout(350)
        assert page.evaluate('__bgmProbe.elements.filter(a=>a.loop).map(a=>a.currentTime)') == paused_times
        report['game_over'] = {'game_audio_started': False, 'active_bgm': 0, 'playback_clocks_frozen': True}
        passed('Zero health immediately pauses every BGM, resets gameAudioStarted and freezes the playback clocks after game over.')

        page.evaluate('document.dispatchEvent(new Event("visibilitychange"))')
        page.wait_for_timeout(150)
        assert page.evaluate('!started&&!window.gameAudioStarted&&__bgmProbe.active().length===0')
        expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed', 'true')
        page.screenshot(path=str(args.artifacts / 'game-over-music-stopped.png'))
        passed('Selection stays silent after game over and a visible-page notification; the music ON preference remains unchanged.')

        start(1)
        expect_track('stage_forest')
        assert page.evaluate('player.type===1&&hp===6&&__bgmProbe.active().length===1')
        lose()
        passed('Restarting with Bingle starts exactly one forest BGM again, with the original character and music settings.')

        page.locator('#musicToggle').tap()
        expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed', 'false')
        for kind in [2, 0]:
            start(kind)
            page.wait_for_timeout(250)
            assert page.evaluate('__bgmProbe.active().length===0')
            lose()
            expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed', 'false')
        page.locator('#musicToggle').tap()
        expect(page.locator('#musicToggle')).to_have_attribute('aria-pressed', 'true')
        assert page.evaluate('__bgmProbe.active().length===0')
        passed('Music OFF survives game over and two different-character restarts; turning it ON in selection does not start old gameplay music.')

        start(0)
        transitions = []
        names = ['forest', 'rock', 'sea', 'desert']
        for index, name in enumerate(names):
            expect_track('stage_' + name)
            page.evaluate('phase=5;phaseKills=requiredKills;boss=null;transition=0')
            page.wait_for_function('!!boss')
            expect_track('boss_' + name)
            if index == 0:
                page.wait_for_function('__bgmProbe.events.some(e=>e.name==="appear"&&e.type==="play")')
            transitions.append({'stage': name, 'boss_track': 'boss_' + name, 'active_bgm': 1})
            page.evaluate('boss=null;nextPhase()')
            if index < 3:
                page.wait_for_function('(index)=>stage===index+1&&phase===1', arg=index)
            else:
                page.wait_for_function('!started')
                assert page.evaluate('!window.gameAudioStarted&&__bgmProbe.active().length===0')
        report['stage_and_boss_transitions'] = transitions
        passed('All four stage/boss themes retain their original switches, boss appearance effect and next-stage progression; final clear still stops BGM.')

        cycles = []
        for index in range(12):
            kind = index % 3
            start(kind)
            expect_track('stage_forest')
            lose()
            cycles.append({'cycle': index + 1, 'character': kind, 'after_game_over_active_bgm': 0})
        report['restart_cycles'] = cycles
        report['audio_monitor'] = page.evaluate('({max_simultaneous_bgm:__bgmProbe.maxActive,overlap_events:__bgmProbe.overlaps,base_audio_elements:__bgmProbe.elements.length,play_events:__bgmProbe.events.filter(e=>e.type==="play").length})')
        assert report['audio_monitor']['max_simultaneous_bgm'] == 1
        assert not report['audio_monitor']['overlap_events']
        assert report['audio_monitor']['base_audio_elements'] == 12
        assert not errors and not native_dialogs, (errors, native_dialogs)
        passed('Twelve additional game-over/restart cycles across all characters reuse the same audio elements; event/frame monitoring finds no overlapping BGM, native dialogs or uncaught JS errors.')
        browser.close()
finally:
    server.shutdown();server.server_close()

(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
