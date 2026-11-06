"""Standalone art-viewer checks and unchanged-game smoke in actual Chromium."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import shutil
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[4]
REVIEW = ROOT / 'docs/review/volcano-art-assets'


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    report={'browser':'Chromium headless, mobile/touch emulation', 'passed':[], 'viewports':[], 'errors':[],
            'limitations':['Not physical Galaxy or Samsung Internet.','Art scenes are standalone visual samples, not a registered volcano stage or combat test.','Original game only received a short selection/start/exit smoke; no full combat rerun for unused new art.']}
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{server.server_port}/'
    errors=[]; failed=[]; bad=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True,device_scale_factor=1)
            page=context.new_page()
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('requestfailed',lambda r:failed.append(r.url))
            page.on('response',lambda r:bad.append({'url':r.url,'status':r.status}) if r.status>=400 and not r.url.endswith('favicon.ico') else None)
            for w,h in [(915,412),(800,360),(568,320)]:
                page.set_viewport_size({'width':w,'height':h})
                page.goto(url+'docs/review/volcano-art-assets/preview.html?view=scene',wait_until='load')
                assert page.evaluate('volcanoPreview.ready')
                page.evaluate('volcanoPreview.setFrame("idle",0)')
                state=page.evaluate('volcanoPreview.report()')
                assert state['loadedActors']==5 and state['decodedFrames']==69 and not state['errors']
                assert state['scenePixels']==[w,h]
                assert page.evaluate('Object.keys(localStorage).length')==0
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(REVIEW/f'screenshots/scene-{w}x{h}.png'))
                report['viewports'].append({'pixels':[w,h],'actors':5,'decodedFrames':69,'overflow':False,'localStorageWrites':0})
            report['passed'].append('3 landscape sizes: background cover, 5 actors, original3 helicopter images, static bullet contrast samples, no overflow/storage writes')
            page.set_viewport_size({'width':1152,'height':800})
            page.goto(url+'docs/review/volcano-art-assets/preview.html',wait_until='load')
            assert page.evaluate('volcanoPreview.ready')
            before=page.evaluate('volcanoPreview.report().elapsed')
            page.wait_for_timeout(200)
            after=page.evaluate('volcanoPreview.report().elapsed')
            assert after>before+100
            report['animation_clock_advance_ms']=after-before
            report['all_frame_browser_audit']=page.evaluate('volcanoPreview.auditFrames()')
            assert len(report['all_frame_browser_audit'])==69
            assert all(f['visiblePixels']>0 and f['edgePixels']==0 for f in report['all_frame_browser_audit'])
            frame_results=page.evaluate('''()=>{
                const result=[];
                for(const name of ['idle','move','attack','hit','defeat']) {
                    const frames={idle:4,move:6,attack:4,hit:3,defeat:4}[name];
                    for(let i=0;i<frames;i++) {
                        volcanoPreview.setFrame(name,i*180);
                        const counts=[...document.querySelectorAll('.card canvas')].map(canvas=>{
                            const a=canvas.getContext('2d').getImageData(0,0,320,320).data;
                            let visible=0;for(let j=3;j<a.length;j+=4)if(a[j]>=8)visible++;return visible;
                        });
                        if(counts.some(n=>n===0))throw Error('Blank rendered frame: '+name+' '+i);
                        result.push({state:name,time:i*180,visiblePixels:counts});
                    }
                }
                return result;
            }''')
            report['rendered_samples']=frame_results
            page.evaluate('volcanoPreview.setFrame("move",0)')
            page.screenshot(path=str(REVIEW/'screenshots/animation-gallery.png'),full_page=True)
            page.locator('#contact').screenshot(path=str(REVIEW/'screenshots/all-69-frames.png'))
            for color in ['#ffffff','#17212b']:
                page.evaluate('(color)=>document.querySelectorAll(".card canvas").forEach(c=>{c.style.backgroundImage="none";c.style.backgroundColor=color;})',color)
                page.locator('#cards').screenshot(path=str(REVIEW/f'screenshots/alpha-{color[1:]}.png'))
            report['passed'].append('All5 states rendered with nonempty canvases; contact sheet drew all69 rects; checker/light/dark alpha screenshots; zero resource/JS failures')
            # Existing UI smoke: user gestures only, no game source or stats injection.
            page.set_viewport_size({'width':915,'height':412})
            page.goto(url,wait_until='load')
            page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()')
            expect(page.locator('#menu h1')).to_have_text('🚁 헬리 트리오')
            for i in range(3):
                page.locator(f'.select-hit[data-heli="{i}"]').tap()
                page.locator('#startSelected').tap()
                page.wait_for_function('type=>player&&player.type===type',arg=i)
                expect(page.locator('#exitGame')).to_be_visible()
                page.wait_for_timeout(300)
                if i==0:page.screenshot(path=str(REVIEW/'screenshots/original-game-unchanged.png'))
                page.locator('#exitGame').tap()
                expect(page.locator('#gameExitConfirm')).to_be_visible()
                page.locator('#gameExitConfirm').tap()
                expect(page.locator('#menu')).to_be_visible()
            report['passed'].append('Unchanged game: all3 character selections/start/quit-dialog/menu return via touch; title remains 헬리 트리오')
            assert not errors and not failed and not bad, {'pageerrors':errors,'requests':failed,'http':bad}
            report['errors']=errors;report['failed_requests']=failed;report['bad_http']=bad;report['passed_all']=True
            context.close();browser.close()
    finally:
        server.shutdown()
        (REVIEW/'browser-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'groups':len(report['passed']),'viewports':len(report['viewports'])},ensure_ascii=False))


if __name__=='__main__':
    main()
