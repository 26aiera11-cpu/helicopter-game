from progression_preservation import without_progression_ui
"""Real DOM exit modal, native fullscreen and touch regression checks."""
import argparse
import json
import re
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--artifacts', type=Path, required=True)
args = parser.parse_args()
args.artifacts.mkdir(parents=True, exist_ok=True)
root = Path(__file__).resolve().parents[1]
report = {'passed': [], 'native_dialogs': [], 'limits': [
    'Actual headless Chromium with the standard Fullscreen API and mobile touch emulation.',
    'Physical Galaxy/Samsung Internet address-bar, Android navigation and audio/sensor behavior need device testing.',
    'Game-over and final-clear paths use controlled game state, not a manual full playthrough.'
]}


def passed(message):
    report['passed'].append(message)
    print('PASS:', message, flush=True)


for name in ['assets/selection/selection.js', 'assets/selection/selection.css']:
    baseline = subprocess.check_output(['git', 'show', 'f36ab92076636a7bec3ccc9ef084ccdaf3455007:' + name], cwd=root)
    assert without_progression_ui((root / name).read_text(), name).encode().startswith(baseline), name
source = (root / 'index.html').read_text() + (root / 'assets/selection/selection.js').read_text()
assert not re.search(r'\b(?:window\.)?(?:confirm|alert)\s*\(', source)
passed('Existing selection animations/fullscreen controls are unchanged; active source contains no confirm() or alert() calls.')


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
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('dialog', lambda dialog: (report['native_dialogs'].append(dialog.type), dialog.dismiss()))
        page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='load')
        # Explicitly retain the old20-stage final-clear input contract.
        page.evaluate('gameWorlds.setTrialEnabled(false)')
        page.evaluate('''() => {
            window.fullscreenRequests = 0;
            const nativeRequest = Element.prototype.requestFullscreen;
            Element.prototype.requestFullscreen = function(...args) {
                window.fullscreenRequests++;
                return nativeRequest.apply(this, args);
            };
        }''')
        toggle = page.locator('#fullscreenToggle')
        dialog = page.locator('#gameExitDialog')
        toggle.tap()
        page.wait_for_function('document.fullscreenElement === document.documentElement')
        page.locator('#startSelected').tap()
        page.wait_for_function('started && player.type === 0')
        page.locator('#exitGame').tap()
        expect(dialog).to_be_visible()
        expect(dialog).to_have_accessible_name('게임을 종료할까요?')
        expect(page.locator('#gameExitCancel')).to_be_focused()
        assert page.evaluate('gameExitDialogOpen && started && !!document.fullscreenElement && document.querySelector("#gameExitDialog").matches(":modal")')
        snapshot = 'JSON.stringify({worldScroll,rotorSpin,hp,runScore,stage,phase,transition,player,bullets,enemyBullets,enemies,warnings,items,particles})'
        before = page.evaluate(snapshot)
        page.wait_for_timeout(300)
        assert page.evaluate(snapshot) == before
        page.screenshot(path=str(args.artifacts / 'exit-confirm-fullscreen.png'))
        passed('The centered in-game modal opens in native fullscreen, focuses Continue, and pauses gameplay state without a native browser prompt.')

        fire = page.locator('#fire').bounding_box()
        page.touchscreen.tap(fire['x'] + fire['width'] / 2, fire['y'] + fire['height'] / 2)
        page.wait_for_timeout(120)
        assert page.evaluate(snapshot) == before
        assert page.evaluate('!keys.left && !keys.right && !keys.fire && drag === null')
        expect(dialog).to_be_visible()
        page.locator('#gameExitCancel').focus()
        page.keyboard.press('Tab')
        expect(page.locator('#gameExitConfirm')).to_be_focused()
        page.keyboard.press('Shift+Tab')
        expect(page.locator('#gameExitCancel')).to_be_focused()
        passed('Modal backdrop blocks underlying touch controls; focus stays in the modal and no fire/movement input remains held.')

        scroll = page.evaluate('worldScroll')
        page.locator('#gameExitCancel').tap()
        expect(dialog).not_to_be_visible()
        page.wait_for_function(f'started && worldScroll > {scroll}')
        assert page.evaluate('!gameExitDialogOpen && !!document.fullscreenElement && !keys.fire && drag === null')
        cdp = context.new_cdp_session(page)

        def hold(control, condition):
            box = page.locator('#' + control).bounding_box()
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [
                {'x': box['x'] + (box['width'] - 26 if control == 'rotationJoystick' else box['width'] / 2), 'y': box['y'] + box['height'] / 2, 'id': 1}]})
            page.wait_for_function(condition)
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})

        angle = page.evaluate('player.a')
        hold('rotationJoystick', f'player.a > {angle} + .05')
        hold('fire', 'bullets.length > 0')
        passed('Continue resumes the same game in fullscreen; actual held touch rotation/fire still work after cancellation.')

        page.locator('#exitGame').tap()
        page.locator('#gameExitConfirm').tap()
        expect(page.locator('#menu')).to_be_visible()
        assert page.evaluate('!started && !gameExitDialogOpen && !!document.fullscreenElement && player === null && !bullets.length && !enemyBullets.length && !enemies.length && !window.gameAudioStarted')
        page.screenshot(path=str(args.artifacts / 'selection-after-exit.png'))
        passed('Confirm runs the existing exit cleanup and returns to character selection while native fullscreen remains active.')

        for kind in [0, 1, 2, 0, 1, 2]:
            page.locator(f'.select-hit[data-heli="{kind}"]').tap()
            page.locator('#startSelected').tap()
            page.wait_for_function(f'started && player.type === {kind}')
            page.locator('#exitGame').tap()
            page.locator('#gameExitCancel').tap()
            assert page.evaluate('started && !!document.fullscreenElement && !gameExitDialogOpen')
            page.locator('#exitGame').tap()
            page.locator('#gameExitConfirm').tap()
            expect(page.locator('#menu')).to_be_visible()
            assert page.evaluate('!started && !!document.fullscreenElement && !gameExitDialogOpen')
        # Old queued close events must not cancel a newly reopened dialog.
        page.locator('#startSelected').tap()
        page.wait_for_function('started')
        page.evaluate('''() => {
            document.getElementById('exitGame').click();
            document.getElementById('gameExitCancel').click();
            document.getElementById('exitGame').click();
        }''')
        page.wait_for_timeout(100)
        expect(dialog).to_be_visible()
        page.locator('#gameExitConfirm').tap()
        passed('All three helicopters survive repeated start/cancel/confirm cycles; immediate dialog reopening leaves no stale close state.')

        for width, height in [(915, 412), (800, 360), (568, 320)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.locator('#startSelected').tap()
            page.wait_for_function('started')
            page.locator('#exitGame').tap()
            bounds = dialog.bounding_box()
            assert bounds['x'] >= 0 and bounds['y'] >= 0
            assert bounds['x'] + bounds['width'] <= width and bounds['y'] + bounds['height'] <= height
            assert abs(bounds['x'] + bounds['width'] / 2 - width / 2) < 2
            assert abs(bounds['y'] + bounds['height'] / 2 - height / 2) < 2
            assert dialog.evaluate('e => e.scrollWidth <= e.clientWidth && e.scrollHeight <= e.clientHeight')
            for button in ['gameExitCancel', 'gameExitConfirm']:
                b = page.locator('#' + button).bounding_box()
                assert b['height'] >= (40 if height <= 350 else 44)
            if width == 568:
                page.screenshot(path=str(args.artifacts / 'exit-confirm-compact.png'))
            page.locator('#gameExitConfirm').tap()
        passed('The modal remains centered, unclipped and usable at three landscape sizes (915×412, 800×360, 568×320).')

        page.set_viewport_size({'width': 915, 'height': 412})
        for action in ['gameExitCancel', 'gameExitConfirm']:
            if action == 'gameExitCancel':
                page.locator('#startSelected').tap()
                page.wait_for_function('started')
            page.locator('#exitGame').tap()
            page.evaluate('document.exitFullscreen()')
            page.wait_for_function('!document.fullscreenElement')
            expect(toggle).to_have_attribute('aria-pressed', 'false')
            count = page.evaluate('fullscreenRequests')
            page.locator('#' + action).tap()
            page.wait_for_timeout(150)
            assert page.evaluate('!document.fullscreenElement && !gameExitDialogOpen')
            assert page.evaluate('fullscreenRequests') == count
            toggle.tap()
            page.wait_for_function('!!document.fullscreenElement')
        passed('If fullscreen ends while the modal is open, neither action forces re-entry; the existing manual fullscreen button works again.')

        page.locator('#startSelected').tap()
        page.wait_for_function('started')
        page.evaluate('hp = 0')
        page.wait_for_function('!started')
        expect(page.locator('#gameOverOverlay')).to_be_visible()
        expect(page.locator('#menu')).to_be_visible(timeout=4000)
        expect(page.locator('#selectionResult')).to_have_text('')
        assert page.evaluate('!!document.fullscreenElement && !gameExitDialogOpen')
        page.locator('#startSelected').tap()
        page.wait_for_function('started')
        page.evaluate('stage = 3; phase = 5; nextPhase()')
        expect(page.locator('#selectionResult')).to_contain_text('클리어')
        assert page.evaluate('!started && !!document.fullscreenElement && !gameExitDialogOpen')
        passed('Game over and final clear return to the selection screen without exiting native fullscreen (controlled game-state checks).')

        toggle.tap()
        page.wait_for_function('!document.fullscreenElement')
        # Starting via the existing start button requests fullscreen, as before.
        page.locator('#startSelected').tap()
        page.wait_for_function('started')
        if page.evaluate('!!document.fullscreenElement'):
            page.evaluate('document.exitFullscreen()')
            page.wait_for_function('!document.fullscreenElement')
        page.locator('#exitGame').tap()
        page.keyboard.press('Escape')
        expect(dialog).not_to_be_visible()
        assert page.evaluate('started && !gameExitDialogOpen && !document.fullscreenElement')
        page.locator('#exitGame').tap()
        page.locator('#gameExitConfirm').tap()
        assert not report['native_dialogs'], report['native_dialogs']
        assert not errors, errors
        passed('Escape safely cancels in normal screen; all tested paths produce zero browser confirm/alert dialogs and zero uncaught JavaScript errors.')
        browser.close()
finally:
    server.shutdown()
    server.server_close()

(args.artifacts / 'test-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
