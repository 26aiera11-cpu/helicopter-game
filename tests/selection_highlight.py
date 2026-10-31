"""Browser checks for selection lighting; requires Chromium/Playwright/Pillow.

python tests/selection_highlight.py --artifacts /absolute/path/to/review
The baseline compares the unchanged click areas and panel layout with Git history.
"""
import argparse
import io
import json
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
parser.add_argument('--baseline', default='457eb80')
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
baseline = {name: subprocess.check_output(['git', 'show', f'{args.baseline}:assets/selection/{name}']).decode()
            for name in ['selection.css', 'selection.js']}
report = {'baseline': args.baseline, 'passed': [], 'limits': ['Chromium desktop/touch emulation; physical iOS/Safari not tested.']}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *arguments):
        pass


measure = '''() => {
    const rect = element => {const r=element.getBoundingClientRect();return [r.x,r.y,r.width,r.height]};
    return {hits:[...document.querySelectorAll('.select-hit')].map(rect),
        panels:[...document.querySelectorAll('.character-details')].map(element=>{
            const s=getComputedStyle(element);return {rect:rect(element),text:element.innerText,
                background:s.background,shadow:s.boxShadow,borderWidth:s.borderWidth,
                radius:s.borderRadius,padding:s.padding};
        })};
}'''
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=shutil.which('chromium'), headless=True, args=['--no-sandbox'])
        original = browser.new_page(viewport={'width':1280,'height':720})
        def serve_baseline(route):
            name = route.request.url.rsplit('/',1)[-1]
            route.fulfill(body=baseline[name], content_type='text/css' if name.endswith('.css') else 'application/javascript')
        for name in baseline:
            original.route(f'**/assets/selection/{name}', serve_baseline)
        url = f'http://127.0.0.1:{server.server_port}/'
        original.goto(url, wait_until='load')
        page = browser.new_page(viewport={'width':1280,'height':720})
        errors = []
        failures = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('requestfailed', lambda request: failures.append(request.url))
        page.goto(url, wait_until='load')
        assert page.locator('.podium-light').count() == 3

        for width, height in [(1280,720),(844,390),(568,320),(1024,768),(2560,1080)]:
            original.set_viewport_size({'width':width,'height':height})
            page.set_viewport_size({'width':width,'height':height})
            assert page.evaluate(measure) == original.evaluate(measure)
            for kind in range(3):
                page.locator(f'.select-hit[data-heli="{kind}"]').click()
                assert page.evaluate(measure) == original.evaluate(measure)
                hit = page.locator(f'.select-hit[data-heli="{kind}"]')
                assert hit.evaluate('e=>getComputedStyle(e).outlineStyle') == 'none'
                assert hit.evaluate('e=>getComputedStyle(e).boxShadow') == 'none'
                assert page.locator('.podium-light').evaluate_all('els=>els.every(e=>getComputedStyle(e).pointerEvents==="none")')
        passed('All three hit areas and panel geometry/content/background/shadow match the baseline at five screen sizes; no selected-button outline or shadow.')

        page.set_viewport_size({'width':1280,'height':720})
        page.locator('.select-hit[data-heli="0"]').click()
        page.wait_for_function('getComputedStyle(document.querySelector(".podium-light[data-heli=\\"0\\"]")).opacity === "1"')
        fade = page.evaluate('''() => {
            const old = document.querySelector('.podium-light[data-heli="0"]');
            const next = document.querySelector('.podium-light[data-heli="1"]');
            document.querySelector('.select-hit[data-heli="1"]').click();
            return [old,next].map(light=>{
                const transition=light.getAnimations().find(a=>a.transitionProperty==='opacity');
                transition.pause();
                const values=[0,120,239].map(time=>{transition.currentTime=time;return Number(getComputedStyle(light).opacity)});
                const duration=transition.effect.getTiming().duration;transition.play();
                return {values,duration};
            });
        }''')
        assert all(state['duration'] == 240 for state in fade)
        assert fade[0]['values'][0] > fade[0]['values'][1] > fade[0]['values'][2]
        assert fade[1]['values'][0] < fade[1]['values'][1] < fade[1]['values'][2]
        report['fade_samples'] = fade
        passed('Red fades out while blue fades in continuously over 240ms; selection uses opacity rather than rectangular glow.')

        for kind, name in enumerate(['trio','bingle','tanko']):
            page.locator(f'.select-hit[data-heli="{kind}"]').click()
            page.wait_for_function('(kind)=>[...document.querySelectorAll(".podium-light")].every(e=>Math.abs(Number(getComputedStyle(e).opacity)-(Number(e.dataset.heli)===kind?1:0))<.001)', arg=kind)
            panel_colors = page.locator('.character-details').evaluate_all('els=>els.map(e=>({border:getComputedStyle(e).borderColor,base:getComputedStyle(e).getPropertyValue("--card-color").trim(),selected:e.classList.contains("is-selected")}))')
            assert [value['selected'] for value in panel_colors] == [i == kind for i in range(3)]
            for index, value in enumerate(panel_colors):
                base_rgb = [int(value['base'][i:i+2],16) for i in [1,3,5]]
                border_rgb = [int(part.strip()) for part in value['border'][4:-1].split(',')]
                if index == kind:
                    assert all(0 <= bright-base <= 60 for bright,base in zip(border_rgb,base_rgb)) and border_rgb != base_rgb
                else:
                    assert border_rgb == base_rgb
            page.wait_for_function('(kind)=>document.querySelector(`#heliStage${kind}`).classList.contains("is-hovering")', arg=kind)
            page.evaluate('''() => {
                const selected=document.querySelector('.heli-stage.is-selected');
                for(const element of [selected,selected.querySelector('.heli-rotor')]) {
                    const animation=element.getAnimations().find(a=>a instanceof CSSAnimation);
                    animation.pause();animation.currentTime=0;
                }
            }''')
            page.screenshot(path=str(args.artifacts/f'selection-{name}.png'))
        passed('Red/blue/green podiums and subtle panel borders select independently; three desktop screenshots saved.')

        page.evaluate('''() => {for(let i=0;i<30;i++)document.querySelectorAll('.select-hit')[i%3].click()}''')
        page.wait_for_function('''() => [...document.querySelectorAll('.podium-light')].every(e=>
            Math.abs(Number(getComputedStyle(e).opacity)-(e.dataset.heli==='2'?1:0))<.001)''')
        assert page.locator('.podium-light.is-selected').count() == 1
        assert page.locator('.character-details.is-selected').count() == 1
        passed('After 30 rapid selections the previous lights and panel accents clear; only the last choice remains active.')

        page.keyboard.press('Tab')
        keyboard_button = page.locator('.select-hit[data-heli="1"]')
        keyboard_button.focus()
        assert keyboard_button.evaluate('e=>e.matches(":focus-visible")')
        assert keyboard_button.evaluate('e=>getComputedStyle(e).outlineStyle') == 'dashed'
        page.screenshot(path=str(args.artifacts/'selection-keyboard-focus.png'))
        page.keyboard.press('Enter')
        assert page.evaluate('selectedHeli') == 1
        page.locator('.select-hit[data-heli="0"]').click()
        assert page.locator('.select-hit[data-heli="0"]').evaluate('e=>!e.matches(":focus-visible")&&getComputedStyle(e).outlineStyle==="none"')
        passed('Keyboard retains a distinct white dashed focus indicator and Enter selection; pointer selection has no focus rectangle.')

        inspection = page.add_style_tag(content='''#menu .select-screen{background:#000!important}
            #menu .heli-stage,#menu .character-details,#menu .select-hit,#menu .selection-result,
            #menu .art-button,#menu #startSelected,#menu #audioControls{visibility:hidden!important}''')
        for kind, name in enumerate(['trio','bingle','tanko']):
            page.evaluate('(kind)=>document.querySelectorAll(".select-hit")[kind].click()', kind)
            page.wait_for_function('(kind)=>[...document.querySelectorAll(".podium-light")].every(e=>Math.abs(Number(getComputedStyle(e).opacity)-(Number(e.dataset.heli)===kind?1:0))<.001)', arg=kind)
            box=page.locator(f'.podium-light[data-heli="{kind}"]').bounding_box()
            screenshot=page.screenshot()
            image=Image.open(io.BytesIO(screenshot)).convert('RGB')
            x0,y0=round(box['x']),round(box['y']);x1,y1=round(box['x']+box['width']-1),round(box['y']+box['height']-1)
            assert all(max(image.getpixel(point)) <= 4 for point in [(x0,y0),(x1,y0),(x0,y1),(x1,y1)])
            brightest=max((image.getpixel((x,y)) for x in range(x0,x1) for y in range(y0,y1)),key=max)
            channel=[0,2,1][kind]
            assert brightest[channel] > 35 and brightest[channel] > max(v for i,v in enumerate(brightest) if i!=channel)*1.2
            if kind == 2: (args.artifacts/'podium-shape-check.png').write_bytes(screenshot)
        inspection.evaluate('e=>e.remove()')
        passed('Pixel checks on black confirm red/blue/green light, transparent ellipse corners and no rectangular lighting.')

        touch = browser.new_context(viewport={'width':844,'height':390},is_mobile=True,has_touch=True)
        mobile=touch.new_page()
        mobile.on('pageerror', lambda error: errors.append(str(error)))
        mobile.on('requestfailed', lambda request: failures.append(request.url))
        mobile.goto(url,wait_until='load')
        for kind in range(3):
            mobile.locator(f'.select-hit[data-heli="{kind}"]').tap()
            assert mobile.evaluate('selectedHeli') == kind
        mobile.wait_for_function('getComputedStyle(document.querySelector(".podium-light[data-heli=\\"2\\"]")).opacity === "1"')
        mobile.screenshot(path=str(args.artifacts/'selection-mobile.png'))
        passed('Touch selection works for all three characters on mobile landscape; screenshot saved.')
        touch.close()
        assert not errors, errors
        assert not failures, failures
        passed('No uncaught JavaScript errors or failed asset requests.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()

(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
