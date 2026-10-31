"""Selection and gameplay regression checks; requires Playwright and Chromium.

Run: python tests/selection_smoke.py --artifacts /absolute/path/to/review
Uses a temporary loopback-only server; no account, publishing or external requests.
"""
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

from PIL import Image
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
before = (root / 'backups/index.before-selection.html').read_text()
after = (root / 'index.html').read_text()
report = {'passed': [], 'limits': ['Physical sensor motion and audible output require a real device.']}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


old_scripts = re.findall(r'<script[^>]*>(.*?)</script>', before, re.S)
game_scripts = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', after, re.S)
assert old_scripts == game_scripts
assert hashlib.sha1(b'blob ' + str(len(before.encode())).encode() + b'\0' + before.encode()).hexdigest() == '19d3426b649a1ba77e4b7bd80019ea809fdf832d'
passed('Backup matches the original Git blob; all original game/audio scripts and embedded game assets are byte-identical.')
for source in game_scripts + [(root / 'assets/selection/selection.js').read_text()]:
    subprocess.run(['node', '--check', '-'], input=source, text=True, check=True, capture_output=True)
passed('All original JavaScript blocks and selection.js pass syntax checks.')
for asset in (root / 'assets/selection').glob('*.png'):
    image = Image.open(asset)
    if asset.name != 'background-clean.png':
        assert image.mode == 'RGBA' and image.getchannel('A').getextrema()[0] == 0
        assert all(image.getpixel(point)[3] == 0 for point in [(0,0), (image.width-1,0), (0,image.height-1), (image.width-1,image.height-1)])
passed('Character and blade PNG files contain real alpha transparency.')

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    errors = []
    failures = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('requestfailed', lambda request: failures.append(request.url))
    page.on('dialog', lambda dialog: dialog.accept())
    page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
    page.wait_for_function('''() => [...terrainImgs,...sprites,...bossSprites,
        ...enemySprites.flat(),...rotorImages,...bulletSprites,...document.images]
        .every(image => image.complete && image.naturalWidth > 0)''')
    page.evaluate('''async () => {
        await Promise.all([...document.querySelectorAll('.heli-stage image')].map(element => {
            const image = new Image(); image.src = element.getAttribute('href'); return image.decode();
        }));
    }''')
    expect(page.locator('#menu')).to_be_visible()
    assert page.locator('.heli-stage').count() == 3
    assert page.locator('.heli-rotor').count() == 3
    passed('Desktop selection, PNG layers, all stage/enemy/boss/projectile images load without failures.')

    # Freeze the old helicopter at the highest hover pose, then sample its landing.
    page.wait_for_function("document.querySelector('#heliStage0').classList.contains('is-hovering')")
    landing = page.evaluate('''() => {
        const previous = document.querySelector('#heliStage0');
        const hover = previous.getAnimations().find(a => a.animationName === 'selection-hover');
        hover.pause(); hover.currentTime = 1050;
        document.querySelector('.select-hit[data-heli="1"]').click();
        const movement = previous.getAnimations().find(a => a.constructor.name === 'Animation');
        movement.pause();
        const y = [0,110,219].map(time => {
            movement.currentTime = time;
            return new DOMMatrix(getComputedStyle(previous).transform).m42;
        });
        movement.play();
        return {y, rotor:getComputedStyle(previous.querySelector('.heli-rotor')).animationName};
    }''')
    assert landing['y'][0] < -7.9 and landing['y'][0] < landing['y'][1] < landing['y'][2] < .1
    assert landing['rotor'] == 'none'
    page.wait_for_function("Math.abs(new DOMMatrix(getComputedStyle(document.querySelector('#heliStage0')).transform).m42) < .01")
    assert page.locator('#heliStage0').evaluate("e => !e.classList.contains('is-hovering')")
    passed('Deselection stops the rotor immediately and lowers the previous helicopter continuously to its podium in 220ms.')

    page.evaluate('''() => {
        for (let i=0;i<24;i++) document.querySelectorAll('.select-hit')[i%3].click();
    }''')
    page.wait_for_function("document.querySelector('#heliStage2').classList.contains('is-hovering')")
    assert page.locator('.heli-stage.is-selected').count() == 1
    assert page.locator('.heli-stage.is-hovering').count() == 1
    passed('Rapid re-selection cancels earlier movements without leaving another helicopter floating or spinning.')

    for kind in range(3):
        page.locator(f'.select-hit[data-heli="{kind}"]').click()
        expect(page.locator(f'.select-hit[data-heli="{kind}"]')).to_have_attribute('aria-pressed', 'true')
        states = page.locator('.heli-stage').evaluate_all('''elements => elements.map(element => ({
            selected: element.classList.contains('is-selected'),
            rotor: getComputedStyle(element.querySelector('.heli-rotor')).animationName
        }))''')
        assert [state['selected'] for state in states] == [i == kind for i in range(3)]
        assert all(state['rotor'] == ('selection-rotor' if i == kind else 'none') for i, state in enumerate(states))
    values = page.locator('#heliStage2 .heli-rotor').evaluate('''element => {
        const animation = element.getAnimations()[0]; animation.pause();
        return [0,165,330].map(time => {animation.currentTime=time;
            const m = new DOMMatrix(getComputedStyle(element).transform);
            return {x:m.a,b:m.b,c:m.c};});
    }''')
    assert values[0]['x'] > .99 and abs(values[1]['x']) < .05 and values[2]['x'] < -.99
    assert all(abs(value['b']) < .001 and abs(value['c']) < .001 for value in values)
    assert page.locator('#heliStage2 .heli-body').evaluate('element => getComputedStyle(element).transform') == 'none'
    passed('Only the selected helicopter floats/spins; previous rotors stop; blades compress left/right while the body/hub stays fixed.')
    page.emulate_media(reduced_motion='reduce')
    assert page.locator('#heliStage2 .heli-rotor').evaluate('element => getComputedStyle(element).animationName') == 'none'
    page.locator('#heliStage2').evaluate("element => element.classList.add('is-hovering')")
    assert page.locator('#heliStage2').evaluate('element => getComputedStyle(element).animationName') == 'none'
    page.emulate_media(reduced_motion='no-preference')
    passed('Reduced-motion preference stops decorative animation.')

    # Inspect fully extended blades at the largest hover scale on varied screens.
    for width, height in [(1280,720),(844,390),(568,320),(1024,768),(2560,1080)]:
        page.set_viewport_size({'width':width,'height':height})
        for kind in range(3):
            page.locator(f'.select-hit[data-heli="{kind}"]').click()
            page.wait_for_function('(kind) => document.querySelector(`#heliStage${kind}`).classList.contains("is-hovering")', arg=kind)
            poses = page.evaluate('''() => {
                const selected = document.querySelector('.heli-stage.is-selected');
                const hover = selected.getAnimations().find(a=>a.animationName==='selection-hover');
                hover.pause(); hover.currentTime=1050;
                return [...document.querySelectorAll('.heli-stage')].map(element => {
                    const body=element.querySelector('.heli-body').getBoundingClientRect();
                    const rotor=element.querySelector('.heli-rotor-position').getBoundingClientRect();
                    return {cx:body.x+body.width/2,left:rotor.left,right:rotor.right,top:rotor.top,bottom:body.bottom};
                });
            }''')
            for pose, center in zip(poses, [.2225,.5,.7645]):
                assert abs(pose['cx']/width-center) < .002
                assert pose['left'] >= 0 and pose['right'] <= width and pose['top'] > 0
                assert .55*height-12 < pose['bottom'] <= .55*height+1
            assert poses[0]['right']+2 < poses[1]['left']
            assert poses[1]['right']+2 < poses[2]['left']
            assert page.locator('.character-details').evaluate_all('els=>els.every(e=>e.scrollHeight<=e.clientHeight&&e.scrollWidth<=e.clientWidth)')
    passed('All podium centers align; PNG outlines and fully extended rotors fit without overlap; panels fit at five desktop/mobile/tablet/ultrawide sizes.')

    page.set_viewport_size({'width':1280,'height':720})
    for kind, name in enumerate(['trio','bingle','tanko']):
        page.locator(f'.select-hit[data-heli="{kind}"]').click()
        page.wait_for_function('(kind) => document.querySelector(`#heliStage${kind}`).classList.contains("is-hovering")', arg=kind)
        page.evaluate('''() => {
            const selected=document.querySelector('.heli-stage.is-selected');
            for(const element of [selected,selected.querySelector('.heli-rotor')]) {
                const animation=element.getAnimations().find(a=>a instanceof CSSAnimation);
                animation.pause();animation.currentTime=0;
            }
        }''')
        page.screenshot(path=str(args.artifacts/f'selection-{name}.png'))

    # Browser-only inspection surfaces; these styles never enter the application.
    inspection = page.add_style_tag(content='#menu .select-screen{background-image:none;background:repeating-conic-gradient(#aaa 0% 25%,#fff 0% 50%) 0 0 / 20px 20px}')
    page.screenshot(path=str(args.artifacts/'selection-alpha-check.png'))
    inspection.evaluate('element=>element.remove()')
    inspection = page.add_style_tag(content='#menu .heli-stage,#menu .character-details,#menu .select-hit{visibility:hidden}')
    page.screenshot(path=str(args.artifacts/'selection-background-only.png'))
    inspection.evaluate('element=>element.remove()')
    passed('Screenshots captured for all three selections, transparent PNG outlines and the background with character layers hidden.')

    for selector in ['#musicToggle', '#sfxToggle']:
        button = page.locator(selector)
        button.click()
        expect(button).to_have_attribute('aria-pressed', 'false')
        assert 'OFF' in button.inner_text()
        assert button.evaluate('element => getComputedStyle(element).color') != 'rgba(0, 0, 0, 0)'
        button.click()
        expect(button).to_have_attribute('aria-pressed', 'true')
    page.locator('#selectionSettings').click()
    expect(page.locator('#selectionSettings')).to_have_attribute('aria-expanded', 'true')
    page.keyboard.press('Escape')
    page.locator('#selectionHelp').click()
    expect(page.locator('#selectionHelpDialog')).to_be_visible()
    page.locator('#selectionHelpClose').click()
    passed('Original music/SFX toggles retain their state and visible ON/OFF labels; settings/help buttons work.')

    for kind, hp in enumerate([4, 6, 9]):
        page.locator(f'.select-hit[data-heli="{kind}"]').click()
        page.locator('#startSelected').click()
        page.wait_for_function('(kind) => started && player.type === kind', arg=kind)
        expect(page.locator('#menu')).to_be_hidden()
        assert page.evaluate('hp') == hp
        page.wait_for_function('worldScroll > 1')
        initial = page.evaluate('player.a')
        right = page.locator('#right').bounding_box()
        page.mouse.move(right['x'] + right['width']/2, right['y'] + right['height']/2)
        page.mouse.down()
        page.wait_for_function('(initial) => player.a > initial + .15', arg=initial)
        page.mouse.up()
        initial_x = page.evaluate('player.x')
        page.mouse.move(640, 360)
        page.mouse.down()
        page.mouse.move(715, 360)
        page.wait_for_function('(initial) => player.x > initial + 5', arg=initial_x)
        page.mouse.up()
        fire = page.locator('#fire').bounding_box()
        page.mouse.move(fire['x'] + fire['width']/2, fire['y'] + fire['height']/2)
        page.mouse.down()
        page.wait_for_function('bullets.length > 0')
        assert page.evaluate('bullets.every(bullet => bullet.kind === player.type)')
        page.mouse.up()
        page.locator('#exitGame').click()
        expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!started && player === null && bullets.length === 0')
    passed('All three helicopters start with HP 4/6/9 and retain gameplay scrolling, rotation, drag, firing and return-to-menu.')

    page.locator('#startSelected').click()
    page.wait_for_function('started && enemies.length > 0', timeout=15000)
    for stage in range(4):
        state = page.evaluate('''index => {stage=index;phase=4;nextPhase();
            phaseKills=requiredKills;transition=0;boss=null;update(.01);
            return {stage,phase,bossHP:boss.hp,enemies:enemySprites[stage].length};}''', stage)
        assert state['stage'] == stage and state['phase'] == 5 and state['bossHP'] == 20 + stage*15
    page.evaluate('stage=3;phase=5;nextPhase()')
    expect(page.locator('#menu')).to_be_visible()
    expect(page.locator('#selectionResult')).to_contain_text('모든 지역 클리어')
    passed('Normal enemy spawning, all four stage/boss configurations and final-clear return work; original hint target is present.')

    page.reload(wait_until='load')
    page.set_viewport_size({'width':844,'height':390})
    page.locator('.select-hit[data-heli="0"]').click()
    page.screenshot(path=str(args.artifacts / 'selection-mobile.png'))
    expect(page.locator('#startSelected')).to_be_in_viewport()
    expect(page.locator('#musicToggle')).to_be_in_viewport()
    page.set_viewport_size({'width':390,'height':844})
    expect(page.locator('#rotateNotice')).to_be_visible()
    page.set_viewport_size({'width':1280,'height':720})
    page.screenshot(path=str(args.artifacts / 'selection-desktop.png'))
    passed('Mobile landscape layout and portrait rotation notice render; desktop/mobile review screenshots saved.')
    assert not errors, errors
    assert not failures, failures
    passed('No uncaught JavaScript errors or failed asset requests.')
    browser.close()
server.shutdown()
server.server_close()

(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
