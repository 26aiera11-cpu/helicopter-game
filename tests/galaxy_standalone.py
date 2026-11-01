"""Validate the one-file Galaxy build offline, including real touch input.

python tests/galaxy_standalone.py --artifacts /absolute/path/to/review
"""
import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

from playwright.sync_api import Error, expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
artifact = root / 'dist/heli_trio_galaxy_test.html'
html = artifact.read_text()
source = (root / 'index.html').read_text()
report = {'artifact': str(artifact.relative_to(root)), 'bytes': artifact.stat().st_size,
          'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(), 'passed': [],
          'limits': ['Physical Galaxy/Samsung Internet, hardware sensors, audible speaker output and device fullscreen/orientation permissions were not tested.']}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key in ['src', 'href', 'xlink:href'] and value:
                assert value.startswith(('data:', '#')), f'External dependency: {tag} {key}={value}'
                self.values.append(value)


resources = Resources()
resources.feed(html)
assert not re.search(r'@import\s', html, re.I)
for url in re.findall(r'url\(([^)]+)\)', html):
    assert url.strip('\"\' ').startswith(('data:', '#'))
passed('All HTML and CSS resource references are embedded data URLs; no external stylesheet, script, font or image dependency.')
old_scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', source, re.S)
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
assert scripts == old_scripts + [(root / 'assets/selection/selection.js').read_text()]
for script in scripts:
    subprocess.run(['node', '--check', '-'], input=script, text=True, capture_output=True, check=True)
passed('The current source game/audio scripts and selection JavaScript are embedded exactly and pass syntax checks.')
embedded_pngs = {base64.b64decode(value.split(',', 1)[1]) for value in resources.values if value.startswith('data:image/png;base64,')}
for path in (root / 'assets/selection').glob('*.png'):
    if path.name == 'background-clean.png':
        value = re.search(r'<style id="galaxy-selection-css">(.*?)</style>', html, re.S)[1]
        data = re.search(r'url\("(data:image/png;base64,[^"]+)"\)', value)[1]
        assert base64.b64decode(data.split(',', 1)[1]) == path.read_bytes()
    else:
        assert path.read_bytes() in embedded_pngs
passed('All five selection PNGs are embedded without changing their bytes, alpha, colors or geometry.')

# The isolated directory intentionally contains only the generated HTML file.
isolated = args.artifacts / 'isolated-file'
isolated.mkdir(exist_ok=True)
isolated_html = isolated / artifact.name
shutil.copyfile(artifact, isolated_html)
assert [path.name for path in isolated.iterdir()] == [artifact.name]
file_url = isolated_html.resolve().as_uri()
audio_probe = '''() => {
    if (window.__galaxyAudio) return;
    window.__galaxyAudio = [];
    const NativeAudio = window.Audio;
    window.Audio = new Proxy(NativeAudio, {construct(target,args) {
        const audio = new target(...args);window.__galaxyAudio.push(audio);return audio;
    }});
}'''

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':915,'height':412}, is_mobile=True, has_touch=True, offline=True)
    context.add_init_script('(' + audio_probe + ')()')
    page = context.new_page()
    errors, failed_assets, external_requests = [], [], []

    def observe(current_page):
        current_page.on('pageerror', lambda error: errors.append(str(error)))
        current_page.on('requestfailed', lambda request: failed_assets.append(request.url) if request.url != file_url else None)
        current_page.on('request', lambda request: external_requests.append(request.url) if request.url.startswith(('http:', 'https:')) else None)
        current_page.on('dialog', lambda dialog: (errors.append('Unexpected native dialog: '+dialog.type),dialog.dismiss()))

    observe(page)
    try:
        page.goto(file_url, wait_until='load', timeout=15000)
        report['local_file_navigation'] = 'passed'
        report['execution_mode'] = 'file:// in an isolated directory, browser offline'
    except Error as error:
        if 'ERR_BLOCKED_BY_ADMINISTRATOR' not in str(error):
            raise
        report['local_file_navigation'] = 'blocked_by_browser_administrator_policy'
        report['execution_mode'] = 'identical HTML injected into about:blank with browser offline'
        report['limits'].append('Direct file:// navigation is blocked by this environment browser policy. The same HTML was tested offline without a server; actual Galaxy local-file opening still requires device validation.')
        print('LIMIT: file:// blocked by browser policy; testing identical standalone HTML offline without a server.', flush=True)
        # A fresh blank page avoids racing the administrator error-page navigation.
        page.close()
        page = context.new_page()
        observe(page)
        page.evaluate(audio_probe)
        page.set_content(html, wait_until='load', timeout=30000)

    page.wait_for_function('''() => [...terrainImgs,...sprites,...bossSprites,
        ...enemySprites.flat(),...rotorImages,...bulletSprites,...document.images]
        .every(image=>image.complete&&image.naturalWidth>0)''')
    dimensions = page.evaluate('''async () => {
        const dimensions = await Promise.all([...document.querySelectorAll('.heli-stage image')].map(async element=>{
            const image=new Image();image.src=element.getAttribute('href');await image.decode();
            return [image.naturalWidth,image.naturalHeight];
        }));
        const background = getComputedStyle(document.querySelector('.select-screen')).backgroundImage;
        const image=new Image();image.src=background.slice(5,-2);await image.decode();
        return {layers:dimensions,background:[image.naturalWidth,image.naturalHeight]};
    }''')
    assert len(dimensions['layers']) == 6 and dimensions['background'] == [1672,941]
    report['decoded_selection_images'] = dimensions
    passed('Offline isolated HTML decodes all character/rotor/background images and all original terrain/enemy/boss/projectile images.')
    page.wait_for_function('''() => window.__galaxyAudio.length===12 &&
        window.__galaxyAudio.every(audio=>!audio.error&&audio.readyState>=1&&audio.duration>0)''')
    report['audio_durations'] = page.evaluate('window.__galaxyAudio.map(audio=>audio.duration)')
    passed('All 12 embedded original WAV tracks/effects load playable metadata while offline.')

    fullscreen = page.locator('#fullscreenToggle')
    expect(fullscreen).to_be_visible()
    fullscreen.tap()
    page.wait_for_function('document.fullscreenElement===document.documentElement')
    report['standalone_selection_fullscreen'] = True

    for kind in range(3):
        page.locator(f'.select-hit[data-heli="{kind}"]').tap()
        assert page.evaluate('selectedHeli') == kind
        hit = page.locator(f'.select-hit[data-heli="{kind}"]')
        assert hit.evaluate('e=>getComputedStyle(e).outlineStyle==="none"&&getComputedStyle(e).boxShadow==="none"')
        assert hit.evaluate('e=>getComputedStyle(e).webkitTapHighlightColor') == 'rgba(0, 0, 0, 0)'
        assert page.locator('.podium-light.is-selected').count() == 1
        assert page.locator('.character-details.is-selected').count() == 1
        page.wait_for_function('(kind)=>document.querySelector(`#heliStage${kind}`).classList.contains("is-hovering")', arg=kind)
        assert page.locator(f'#heliStage{kind} .heli-rotor').evaluate('e=>getComputedStyle(e).animationName') == 'selection-rotor'
    assert page.locator('#heliStage0 .heli-rotor').evaluate('e=>getComputedStyle(e).animationName') == 'none'
    passed('All three touch selections retain no yellow rectangle, colored circular lighting, panel accents, floating and front-view rotor/stop behavior.')
    page.locator('.select-hit[data-heli="0"]').tap()
    page.wait_for_function('getComputedStyle(document.querySelector(".podium-light[data-heli=\\"0\\"]")).opacity==="1"')
    page.screenshot(path=str(args.artifacts / 'galaxy-selection.png'))

    for selector in ['#musicToggle','#sfxToggle']:
        button=page.locator(selector)
        button.tap();expect(button).to_have_attribute('aria-pressed','false')
        button.tap();expect(button).to_have_attribute('aria-pressed','true')
    passed('Original music and SFX toggles work with touch input.')

    cdp = context.new_cdp_session(page)

    def touch_start(x,y):
        cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})

    def touch_end():
        cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})

    for kind,health in enumerate([4,6,9]):
        page.locator(f'.select-hit[data-heli="{kind}"]').tap()
        page.locator('#startSelected').tap()
        page.wait_for_function('(kind)=>started&&player.type===kind',arg=kind)
        assert page.evaluate('hp') == health
        if kind == 0:
            final_draw=page.evaluate('''() => {
                let args;const original=ctx.drawImage;
                ctx.drawImage=function(image,...values){if(image===sprites[0])args=values;return original.call(this,image,...values)};
                try{draw()}finally{ctx.drawImage=original}
                return {width:sprites[0].naturalWidth,height:sprites[0].naturalHeight,args};
            }''')
            assert [final_draw['width'],final_draw['height']]==[1402,1122]
            assert len(final_draw['args'])==4
            assert abs(final_draw['args'][2]/1402-final_draw['args'][3]/1122)<1e-12
            report['final_trio_draw']=final_draw
            passed('The final 1402×1122 Trio PNG loads offline and its actual draw uses equal X/Y scale without square distortion or cropping.')
        expect(page.locator('#menu')).to_be_hidden()
        page.wait_for_function('worldScroll>1')
        angle=page.evaluate('player.a')
        box=page.locator('#right').bounding_box()
        touch_start(box['x']+box['width']/2,box['y']+box['height']/2)
        page.wait_for_function('(angle)=>player.a>angle+.12',arg=angle)
        touch_end()
        x,y=page.evaluate('[W/2,H/2]');old_x=page.evaluate('player.x')
        touch_start(x,y)
        cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+75,'y':y,'id':1}]})
        page.wait_for_function('(old)=>player.x>old+5',arg=old_x)
        touch_end()
        box=page.locator('#fire').bounding_box()
        touch_start(box['x']+box['width']/2,box['y']+box['height']/2)
        page.wait_for_function('bullets.length>0')
        assert page.evaluate('bullets.every(b=>b.kind===player.type)')
        touch_end()
        if kind == 0:
            page.screenshot(path=str(args.artifacts/'galaxy-gameplay.png'))
            page.wait_for_function('enemies.length>0',timeout=15000)
            page.wait_for_function('window.__galaxyAudio.some(audio=>audio.loop&&!audio.paused&&audio.currentTime>0)')
        page.locator('#exitGame').tap()
        expect(page.locator('#gameExitDialog')).to_be_visible()
        assert page.evaluate('gameExitDialogOpen && !!document.fullscreenElement')
        if kind == 0:
            paused = page.evaluate('worldScroll')
            page.wait_for_timeout(200)
            assert page.evaluate('worldScroll') == paused
            page.screenshot(path=str(args.artifacts/'galaxy-exit-confirm.png'))
            page.locator('#gameExitCancel').tap()
            page.wait_for_function('(old)=>started&&worldScroll>old',arg=paused)
            assert page.evaluate('!gameExitDialogOpen&&!!document.fullscreenElement')
            page.locator('#exitGame').tap()
        page.locator('#gameExitConfirm').tap()
        expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!started&&player===null')
        assert page.evaluate('!!document.fullscreenElement')
    passed('Each helicopter starts via touch with HP 4/6/9; real touch-hold rotation, drag movement, firing, return and enemy spawning work offline.')
    passed('The rebuilt offline HTML includes the in-page exit modal, gameplay pause/resume and fullscreen-preserving selection return without native dialogs.')
    passed('The original embedded background track starts after a user gesture; audible speaker output remains a device test.')
    fullscreen.tap();page.wait_for_function('!document.fullscreenElement')
    passed('The rebuilt standalone file enters fullscreen from selection, retains it through all three game/return flows and exits through the shared control.')

    page.locator('#startSelected').tap()
    page.wait_for_function('window.__galaxyAudio[0]&&!window.__galaxyAudio[0].paused&&window.__galaxyAudio[0].currentTime>0')
    page.evaluate('hp=0')
    page.wait_for_function('!started')
    expect(page.locator('#selectionResult')).to_contain_text('게임 오버')
    assert page.evaluate('!window.gameAudioStarted&&window.__galaxyAudio.filter(a=>a.loop).every(a=>a.paused)')
    page.wait_for_timeout(80)
    stopped=page.evaluate('window.__galaxyAudio[0].currentTime')
    page.wait_for_timeout(200)
    assert page.evaluate('window.__galaxyAudio[0].currentTime')==stopped
    page.locator('.select-hit[data-heli="1"]').tap()
    page.locator('#startSelected').tap()
    page.wait_for_function('started&&player.type===1&&window.__galaxyAudio.filter(a=>a.loop&&!a.paused).length===1')
    page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
    passed('The latest standalone HTML pauses all BGM on game over, freezes its playback clock and restarts one track with another character offline.')

    for roll in [.25,.75]:
        page.locator('#startSelected').tap()
        page.wait_for_function('started&&player.type===1')
        reward=page.evaluate('''roll=>{
            stage=0;phase=5;phaseKills=requiredKills;hp=1;player.upgrade=0;
            spawn=999;transition=0;invuln=999;enemies=[];warnings=[];enemyBullets=[];bullets=[];
            boss={x:W/2,y:100,r:48,hp:1,maxHp:20,t:0,shot:999};
            const target=boss,random=Math.random;Math.random=()=>roll;
            try{shoot();Object.assign(bullets[0],{x:boss.x,y:boss.y,vx:0,vy:0});update(.001)}finally{Math.random=random}
            return {hp,upgrade:player.upgrade,stage,phase,items:items.length,rewardGranted:target.rewardGranted};
        }''',roll)
        assert reward=={'hp':5 if roll<.5 else 3,'upgrade':0 if roll<.5 else 1,'stage':1,'phase':1,'items':0,'rewardGranted':True}
        expect(page.locator('#bossRewardNotice')).to_have_text('❤️ 체력 +2' if roll<.5 else '⚡ 무기 강화 +1')
        expect(page.locator('#bossRewardNotice')).to_be_visible()
        if roll>.5:page.screenshot(path=str(args.artifacts/'galaxy-boss-reward.png'))
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
    passed('The rebuilt offline HTML applies both boss rewards before existing region HP healing, drops no boss item and displays the compact reward notice.')

    page.locator('#startSelected').tap()
    for stage in range(4):
        state=page.evaluate('''index=>{stage=index;phase=4;nextPhase();
            phaseKills=requiredKills;transition=0;boss=null;update(.01);
            return {stage,phase,hp:boss.hp,enemies:enemySprites[stage].length};}''',stage)
        assert state['stage']==stage and state['phase']==5 and state['hp']==20+stage*15
    page.evaluate('stage=3;phase=5;nextPhase()')
    expect(page.locator('#selectionResult')).to_contain_text('모든 지역 클리어')
    passed('All four original stage/boss configurations and final-clear return pass controlled-state regression checks.')

    # Reopen a clean offline document so the compact screenshot is not a victory screen.
    page.close()
    page = context.new_page()
    observe(page)
    if report['local_file_navigation'] == 'passed':
        page.goto(file_url,wait_until='load')
    else:
        page.evaluate(audio_probe)
        page.set_content(html,wait_until='load')
    page.wait_for_function('terrainImgs.every(image=>image.complete&&image.naturalWidth>0)')
    page.set_viewport_size({'width':800,'height':360})
    page.locator('.select-hit[data-heli="0"]').tap()
    page.wait_for_function('getComputedStyle(document.querySelector(".podium-light[data-heli=\\"0\\"]")).opacity==="1"')
    assert page.locator('.character-details').evaluate_all('els=>els.every(e=>e.scrollHeight<=e.clientHeight&&e.scrollWidth<=e.clientWidth)')
    page.screenshot(path=str(args.artifacts/'galaxy-selection-compact.png'))
    page.set_viewport_size({'width':412,'height':915})
    expect(page.locator('#rotateNotice')).to_be_visible()
    page.screenshot(path=str(args.artifacts/'galaxy-portrait-notice.png'))
    passed('915×412 and 800×360 mobile landscape layouts, touch controls and portrait rotate notice render offline.')
    assert not external_requests, external_requests
    assert not failed_assets, failed_assets
    assert not errors, errors
    report['external_requests'] = 0
    report['failed_asset_requests'] = 0
    passed('No external HTTP requests, failed assets or uncaught JavaScript errors in the offline run.')
    browser.close()

(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
