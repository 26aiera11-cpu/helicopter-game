"""Issue15: actual volcano entry/render/events/outro and exact offline packaging."""
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
from playwright.sync_api import sync_playwright, expect
from volcano_preservation import VOLCANO_ASSETS, assert_volcano_asset, without_volcano_asset

ROOT=Path(__file__).resolve().parents[1]
BASE='7c99b909ce0d34cce3b8dcebd5042e9ee72ca7bb'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true')
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[], 'limits':[
    'Chromium mobile/touch emulation; not physical Galaxy/Samsung Internet, sensor hardware or audible speaker testing.',
    'Entry matrix uses real UI/start/spawn/hit hooks with controlled transition/spawn/aim/invulnerability for deterministic screenshots.',
    'The69-frame audit drives controlled art-state fixtures through the production renderer; it is separate from actual battle-hook checks.',
    'Offline runs the exact single HTML on a blank localhost origin with networking disabled; file security policy is not bypassed.'
]}
def passed(text):report['passed'].append(text);print('PASS:',text,flush=True)
for name in ['index.html','assets/worlds/worlds.js','assets/score/score.js']:
    assert without_volcano_asset((ROOT/name).read_text(),name)==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT).decode(),name
for path in (ROOT/'assets').rglob('*'):
    if not path.is_file():continue
    name=str(path.relative_to(ROOT))
    if name in VOLCANO_ASSETS:assert_volcano_asset(path);continue
    content=without_volcano_asset(path.read_text(),name).encode() if path.suffix in ('.js','.css') else path.read_bytes()
    assert content==subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT),name
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',(ROOT/'index.html').read_text(),re.S)+[p.read_text() for p in (ROOT/'assets').rglob('*.js')]:
    subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
passed('Only exact integration hooks/UI labels/new module; original volcano/snow art, manifest, combat, characters, controls, audio and score rules byte-protected; all JS parses.')

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def translate_path(self,path):
        if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
        return super().translate_path(path)
    def do_GET(self):
        if self.path=='/volcano-origin':
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>Offline origin</title>');return
        super().do_GET()

helpers=r'''()=>{
 window.vKeys=['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'];
 window.vStorage=()=>Object.fromEntries(vKeys.map(k=>[k,localStorage.getItem(k)]));
 window.vScene=()=>{
   transition=0;spawn=999;invuln=999;keys.fire=false;
   if(phase<5){warnEnemy();warnings.forEach(w=>w.time=0);update(0);}
   gameVolcano.observe(enemies,boss);draw();
   const actor=boss||enemies[0];
   return {stage,phase,type:player.type,hp,upgrade:player.upgrade,score:runScore,
     actor:{x:actor.x,y:actor.y,r:actor.r,hp:actor.hp,id:gameVolcano.pose(actor,actor===boss).id},
     profile:gameWorlds.profile(stage),music:gameWorlds.musicProfile(stage),art:gameVolcano.snapshot()};
 };
 window.vHit=actor=>{bullets=[];shoot();Object.assign(bullets[0],{x:actor.x,y:actor.y,vx:0,vy:0});update(0);};
 window.vSettle=()=>{let i=0;while(gameVolcano.snapshot().advancing&&i++<100)update(.04);if(gameVolcano.snapshot().advancing)throw Error('Outro stalled');};
 window.vAuditFrames=()=>{
   const output=[];const original=ctx.drawImage;
   enemies=[];boss=null;warnings=[];enemyBullets=[];bullets=[];
   for(const spec of gameVolcano.species){
     gameVolcano.reset();phase=spec.kind==='boss'?5:gameVolcano.normalIds.indexOf(spec.id)+1;
     const king=spec.kind==='boss',actor={x:W/2,y:H/2,hp:10,r:king?48:16,volcanoSpeciesId:spec.id};
     gameVolcano.observe(king?[]:[actor],king?actor:null);
     for(const [name,animation] of Object.entries(spec.animations)){
       if(name==='move'){actor.x+=1;gameVolcano.observe(king?[]:[actor],king?actor:null);}
       if(name==='attack')gameVolcano.attack(actor,king);
       if(name==='hit')gameVolcano.hit(actor,king);
       if(name==='defeat'){actor.hp=0;gameVolcano.hit(actor,king);gameVolcano.tick(spec.animations.hit.frame_count*spec.animations.hit.frame_duration_ms/1000+1e-6);}
       for(let i=0;i<animation.frame_count;i++){
         if(i)gameVolcano.tick(animation.frame_duration_ms/1000);
         let drawCall=null;
         ctx.drawImage=function(image,...rest){drawCall={image,rest};return original.call(ctx,image,...rest);};
         try{if(name==='defeat')gameVolcano.drawDefeats(ctx);else gameVolcano.drawActor(ctx,actor,king);}finally{ctx.drawImage=original;}
         const selected=name==='defeat'?gameVolcano.snapshot().ghosts[0].pose:gameVolcano.pose(actor,king);
         const frame=animation.frames[i];
         if(selected.name!==name||selected.index!==i||JSON.stringify(selected.rect)!==JSON.stringify(frame.rect_px))throw Error('Wrong frame '+spec.id+name+i);
         if(!(drawCall.image instanceof HTMLCanvasElement))throw Error('Atlas not used');
         const [sx,sy,w,h]=frame.rect_px,reference=document.createElement('canvas');reference.width=w;reference.height=h;
         const rg=reference.getContext('2d');rg.drawImage(spec.atlasImage,sx,sy,w,h,0,0,w,h);
         const normalized=rg.getImageData(0,0,w,h),actual=drawCall.image.getContext('2d').getImageData(0,0,w,h).data;
         if(drawCall.image.width!==w||drawCall.image.height!==h)throw Error('Wrong crop size');
         for(let p=3;p<normalized.data.length;p+=4)if(normalized.data[p]<8)normalized.data.fill(0,p-3,p+1);
         rg.putImageData(normalized,0,0);const expected=rg.getImageData(0,0,w,h).data;
         if(expected.length!==actual.length||expected.some((v,p)=>v!==actual[p]))throw Error('Wrong source pixels '+spec.id+name+i);
         const [dx,dy,dw,dh]=drawCall.rest;
         if(Math.abs(dw/w-dh/h)>1e-9)throw Error('Aspect stretched');
         output.push({id:spec.id,state:name,index:i,rect:frame.rect_px,drawn:[dx,dy,dw,dh],exactSourcePixels:true,aspectPreserved:true});
       }
     }
     actor.hp=10;
     for(const [x,y] of [[0,0],[W,0],[0,H],[W,H],[W/2,H/2]]){
       actor.x=x;actor.y=y;const before=JSON.stringify(actor),selected=gameVolcano.frame(spec,'move',0);
       const geometry=gameVolcano.geometry(spec,x,y,W,H,selected);gameVolcano.drawActor(ctx,actor,king);
       if(before!==JSON.stringify(actor))throw Error('Rendering moved collider');
       const b=geometry.bounds;if(b.x<-.001||b.y<-.001||b.x+b.w>W+.001||b.y+b.h>H+.001)throw Error('Edge clip');
     }
   }
   return output;
 };
}'''

server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
        page=context.new_page();errors=[];dialogs=[];failed=[];requests=[]
        page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
        page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:requests.append(r.url) if r.url.startswith('http') else None)
        def load():
            if args.standalone:
                context.set_offline(False);page.goto(url+'volcano-origin');requests.clear();context.set_offline(True)
                page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
            else:page.goto(url+'helicopter-game/',wait_until='load')
            page.wait_for_function('window.gameVolcano&&gameVolcano.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');page.evaluate(helpers)
        load()
        registry=page.evaluate('({worlds:gameWorlds.worlds,regions:gameWorlds.regions,mode:gameWorlds.snapshot(),keys:vStorage()})')
        assert [w['regionIds'] for w in registry['worlds']]==[[0,1,2,3],[4,5]] and not registry['mode']['trialEnabled']
        assert registry['regions'][5]['key']=='world-2:volcano' and all(registry['regions'][5][k]==0 for k in ['combatProfile','assetProfile','musicProfile'])
        report['registry']=registry
        page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1')
        assert page.locator('#developerStartRegion').evaluate('(e)=>[...e.options].map(o=>Number(o.value))')==[4,5]
        page.locator('#developerStartRegion').select_option('5');page.locator('#developerStartPhase').select_option('5')
        page.screenshot(path=str(args.artifacts/'developer-volcano-help.png'));page.locator('#selectionHelpClose').tap()
        initial=page.evaluate('vStorage()');page.locator('#startSelected').tap()
        assert page.evaluate('stage===5&&phase===5&&!!boss&&phaseKills===6&&enemies.length===0&&boss.maxHp===20')
        passed('RegistryIDs0–4 stable, volcano5; defaultOFF20-stage mode; actual Help world2/volcano/phase5 starts dragon directly with forest profile0.')
        page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible()
        before=page.evaluate('gameVolcano.snapshot()');page.wait_for_timeout(200)
        assert page.evaluate('gameVolcano.snapshot()')==before
        page.locator('#gameExitCancel').tap();page.wait_for_timeout(120)
        assert page.evaluate('gameVolcano.snapshot().clock')>before['clock']
        passed('In-page exit pauses volcano clock/poses exactly, Continue resumes them without leaving fullscreen.')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        entries=[];report['entry_progress']=entries
        for width,height in [(915,412),(800,360),(568,320)]:
            page.set_viewport_size({'width':width,'height':height})
            for kind in range(3):
                for step in range(1,6):
                    assert page.evaluate('(step)=>gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:step})',step)
                    page.locator(f'.select-hit[data-heli="{kind}"]').tap();page.locator('#startSelected').tap()
                    state=page.evaluate('vScene()');expected=['ember_bean','lava_lizard','volcano_bat','magma_beetle','magma_dragon'][step-1]
                    assert state['stage']==5 and state['phase']==step and state['type']==kind and state['actor']['id']==expected
                    assert state['actor']['r']==(48 if step==5 else 16) and state['actor']['hp']==[1,2,2,4,20][step-1]
                    assert state['profile']==state['music']==0 and state['score']==0 and state['hp']==[4,6,9][kind]
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth&&!!document.fullscreenElement')
                    if kind==0 and (not args.standalone or width==568):page.screenshot(path=str(args.artifacts/f'volcano-phase{step}-{width}x{height}.png'))
                    entries.append({'viewport':[width,height],'type':kind,'phase':step,'species':expected,'collider':state['actor']['r'],'hp':state['actor']['hp']})
                    # Real movement, firing and hit hooks, without inventing combat stats.
                    event=page.evaluate('''()=>{const actor=boss||enemies[0],king=actor===boss;
                        update(.1);const movement=gameVolcano.pose(actor,king).name;
                        actor.shot=0;update(0);const attack=gameVolcano.pose(actor,king).name,enemyShots=enemyBullets.length;
                        if(king)vHit(actor);else{let hits=0;while(actor.hp>0&&hits++<8)vHit(actor);if(actor.hp>0)throw Error('Normal kill stalled');}draw();return {movement,attack,hit:gameVolcano.snapshot(),score:runScore,enemyShots};}''')
                    entries[-1]['events']=event
                    assert event['movement']=='move' and event['attack']=='attack' and event['enemyShots']>=1,entries[-1]
                    if step<5:assert event['score']==100 and event['hit']['ghosts'][0]['pose']['name']=='hit'
                    else:assert event['score']==0 and event['hit']['actors'][0]['pose']['name']=='hit'
                    page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();expect(page.locator('#menu')).to_be_visible()
                    assert page.evaluate('!gameVolcano.snapshot().advancing&&gameVolcano.snapshot().ghosts.length===0')
        report['entries']=entries
        assert page.evaluate('vStorage()')==initial
        passed('45 real starts (3characters×3viewports×5phases): correct species/profile/HP/radius, movement/fire/hit events,100point kills, fullscreen and exit/reset; developer writes0.')
        page.evaluate('gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:1});start(0);transition=0;spawn=999;invuln=999;')
        audit=page.evaluate('vAuditFrames()');assert len(audit)==69
        report['frames']=audit;report['cache']=page.evaluate('gameVolcano.snapshot()')
        assert report['cache']['cachedFrames']==69
        passed('All69 production-rendered frames match exact manifest source pixels after render-only alpha cleanup; aspect, virtual pivots, edge clamp/collider immutability and bounded69-frame cache verified.')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        # Normal phase5 prelude is beetles, not an extra normal species or direct boss.
        prelude=page.evaluate('''()=>{gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:4});start(0);nextPhase();transition=0;spawn=999;warnEnemy();warnings.forEach(w=>w.time=0);update(0);return {boss:!!boss,id:gameVolcano.pose(enemies[0]).id,hp:enemies[0].hp,phaseKills};}''')
        assert prelude=={'boss':False,'id':'magma_beetle','hp':4,'phaseKills':0}
        passed('Normal entry to phase5 retains the6-kill prelude with beetle visuals; only developer phase5 bypasses it.')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        # Boss rewards/clear stay singular and wait for the real death animation.
        finale=page.evaluate('''()=>{gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:5});start(2);transition=0;spawn=999;invuln=999;window.vRewards=0;document.addEventListener('bossreward',()=>vRewards++);while(boss)vHit(boss);const before={started,score:runScore,advance:gameVolcano.snapshot().advancing,rewards:vRewards};update(.3);const during=started;vSettle();return {before,during,after:{started,score:runScore,rewards:vRewards,art:gameVolcano.snapshot(),heading:menu.querySelector('h1').textContent,bullets:bullets.length,enemy:enemyBullets.length,particles:particles.length}};}''')
        assert finale['before']=={'started':True,'score':2000,'advance':True,'rewards':1} and finale['during']
        assert not finale['after']['started'] and finale['after']['rewards']==1 and finale['after']['score']==2000
        assert finale['after']['bullets']==finale['after']['enemy']==finale['after']['particles']==0
        report['finale']=finale;assert page.evaluate('vStorage()')==initial
        passed('Dragon reward/2000score exactly once; hit+defeat holds play then clears without bullets/effects; test result remains unsaved.')
        # New continuation must not leave the old terminal-only snow outro pending.
        continuation=page.evaluate('''()=>{gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true);start(0);stage=4;phase=5;transition=0;invuln=999;spawn=999;spawnBossEncounter();transition=0;while(boss)vHit(boss);const before={stage,phase,started,advance:gameVolcano.snapshot().advancing};vSettle();return {before,after:{stage,phase,started,snowFinale:gameSnowfield.snapshot().finale,volcano:gameVolcano.snapshot()}};}''')
        assert continuation['before']=={'stage':4,'phase':5,'started':True,'advance':True}
        assert continuation['after']['stage']==5 and continuation['after']['phase']==1 and continuation['after']['started']
        assert continuation['after']['snowFinale']=={'active':False,'pending':False}
        report['continuation']=continuation
        passed('Snow boss retains its death animation then enters volcano1; old snow-finale active/pending is cleared, without changing snow combat files.')
        page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap()
        # Real game-over lifecycle on the new region.
        page.evaluate('gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:1});start(1);spawn=999;hp=0;window.vDeath=performance.now();update(0);')
        expect(page.locator('#gameOverOverlay')).to_be_visible();page.wait_for_timeout(2500);expect(page.locator('#gameOverOverlay')).to_be_visible()
        expect(page.locator('#menu')).to_be_visible(timeout=3000);assert page.evaluate('performance.now()-vDeath')>=2990
        assert page.locator('#selectionResult').inner_text()=='' and page.evaluate('!!document.fullscreenElement')
        assert page.evaluate('gameVolcano.snapshot().clock===0&&gameVolcano.snapshot().ghosts.length===0&&!gameVolcano.snapshot().advancing')
        passed('Volcano HP0 freezes immediately, retains3s GAME OVER, returns clean menu in fullscreen; native dialogs0.')
        assert not errors and not dialogs and not failed,(errors,dialogs,failed)
        if args.standalone:assert not requests,requests
        report.update(page_errors=errors,native_dialogs=dialogs,failed_requests=failed,offline_external_requests=requests if args.standalone else [],all_passed=True)
        passed('Native GitHub-project subpath/offline exact HTML resources load; no JS/request failures, offline external requests0.')
        context.close();browser.close()
finally:
    server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
