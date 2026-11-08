from volcano_spawn_fixtures import FIXED_VOLCANO_SPECIES
"""Deliberately failed volcano PNG requests must not stop or show forest art."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse,json,shutil,threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
report={'passed':[],'cases':[],'limits':['Intentional request-abort fixtures in Chromium; not natural network/device-failure measurements.']}
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        for mode,pattern in [('atlas','**/assets/volcano/animations/*.png'),('all','**/assets/volcano/**/*.png')]:
            context=browser.new_context(viewport={'width':568,'height':320});blocked=[]
            def abort(route):blocked.append(route.request.url);route.abort()
            context.route(pattern,abort);page=context.new_page();page.add_init_script(FIXED_VOLCANO_SPECIES);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
            page.wait_for_function('gameSnowfield.ready()&&itemMonsters.ready()')
            rows=[]
            for phase in range(1,6):
                result=page.evaluate('''({phase,mode})=>{
                    if(started){started=false;gameVolcano.reset();menu.classList.remove('hidden');}
                    gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase});start(0);transition=0;spawn=999;invuln=999;
                    if(phase<5){vmFixedPhase();warnEnemy();warnings.forEach(w=>w.time=0);update(0);}
                    const actor=boss||enemies[0],id=gameVolcano.pose(actor,!!boss).id;
                    const drawImage=ctx.drawImage,arc=ctx.arc,seen=[],colors=[];
                    ctx.drawImage=function(im,...a){seen.push(im.id||'canvas');return drawImage.call(ctx,im,...a);};
                    ctx.arc=function(...a){colors.push(ctx.fillStyle);return arc.call(ctx,...a);};
                    try{draw();return {phase,id,seen,colors,started,hp,normalHP:actor.hp,ready:gameVolcano.ready()};}
                    finally{ctx.drawImage=drawImage;ctx.arc=arc;}
                }''',{'phase':phase,'mode':mode})
                assert result['started'] and result['hp']==4 and result['normalHP']==[1,2,2,4,80][phase-1] and not result['ready']
                if mode=='atlas':assert 'volcano-'+result['id']+'-base' in result['seen']
                else:assert ('#9240b8' if phase==3 else '#e88426') in result['colors']
                assert not any('snowfield' in x for x in result['seen'])
                rows.append(result)
            page.screenshot(path=str(args.artifacts/f'fallback-{mode}.png'))
            assert len(blocked)==(5 if mode=='atlas' else 12) and not errors,(blocked,errors)
            if mode=='all':assert page.evaluate('gameVolcanoBoss.artSnapshot().status==="failed"&&!gameVolcanoBoss.artSnapshot().maskReady')
            report['cases'].append({'mode':mode,'expected_failed_requests':blocked,'page_errors':errors,'rows':rows})
            report['passed'].append(mode+': all5 phases stay playable; base/symbol fallbacks preserve ratios and no forest/snow sprites')
            context.close()
        browser.close();report['all_passed']=True
finally:
    server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('PASS:',len(report['passed']),'fallback groups')
