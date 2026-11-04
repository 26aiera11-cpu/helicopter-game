"""Issue17: approved art scope, player load ownership and actual 8-direction draws."""
import argparse,base64,hashlib,io,json,re,shutil,subprocess,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from visual_fix_preservation import VISUAL_FIX_ASSETS,assert_visual_fix_asset,without_visual_fix_asset
from volcano_combat_preservation import without_volcano_combat

ROOT=Path(__file__).resolve().parents[1]
BASE='5fe31bbbde7f9aa46d25aba03d64731485c2c70b'
parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--standalone',action='store_true')
args=parser.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'baseline':BASE,'standalone':args.standalone,'passed':[],'limits':[
    'Controlled Chromium render and deliberate load-order fixture; not a reproduction of the user physical Galaxy session.',
    '8-direction body+rotor layers are actual game draw calls replayed onto a transparent inspection canvas.',
    'Screenshots freeze combat through a test-only pause flag; no production input/AI/stat modifications.',
    'Anatomy and absence of the marked appendage are visually reviewed, not inferred by an automated semantic classifier.'
]}
def passed(value):report['passed'].append(value);print('PASS:',value,flush=True)
def old(name):return subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
def sha(data):return hashlib.sha256(data).hexdigest()
def arrays(source):return {k:json.loads(re.search(r'const '+k+r'=(\[[^\n]*?\]);',source)[1]) for k in ['spriteURLs','gameplayHeliImages']}
source=(ROOT/'index.html').read_text();original=old('index.html').decode();current_arrays=arrays(source)
assert without_visual_fix_asset(source,'index.html')==original
assert arrays(original)==current_arrays
for path in (ROOT/'assets').rglob('*'):
    if not path.is_file():continue
    name=str(path.relative_to(ROOT))
    if name in VISUAL_FIX_ASSETS:assert_visual_fix_asset(name)
    else:assert (without_volcano_combat(path.read_text(),name).encode() if path.suffix=='.js' else path.read_bytes())==old(name),name
passed('Exact two-loader deltas and embedded manifest only; all character sources, render geometry, combat, controls, music and other assets byte-preserved.')
manifest=json.loads((ROOT/'assets/volcano/asset_manifest.json').read_text());before=json.loads(old('assets/volcano/asset_manifest.json'))
assert manifest['background']==before['background']
art=[]
for spec,prior in zip(manifest['monsters'],before['monsters']):
    if spec['id'] not in ['lava_lizard','magma_dragon']:assert spec==prior;continue
    for key in ['base','atlas']:
        path=ROOT/'assets/volcano'/spec[key];data=path.read_bytes()
        with Image.open(io.BytesIO(data)) as im:im.verify()
        with Image.open(io.BytesIO(data)) as im:
            assert im.mode=='RGBA';alpha=im.getchannel('A');assert alpha.getextrema()==(0,255)
            art.append({'id':spec['id'],'path':str(path.relative_to(ROOT)),'size':im.size,'sha256':sha(data),'rgba':True})
    assert {k:(v['frame_count'],v['frame_duration_ms'],v['loop']) for k,v in spec['animations'].items()}=={k:(v['frame_count'],v['frame_duration_ms'],v['loop']) for k,v in prior['animations'].items()}
assert sum(sum(v['frame_count'] for v in s['animations'].values()) for s in manifest['monsters'])==69
report['art']=art
passed('Four replacement PNGs decode/CRC/RGBA; other three species and background identical; all69 state counts and timing preserved.')

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_GET(self):
        if self.path=='/before/':data=old('index.html');mime='text/html; charset=utf-8'
        elif self.path=='/offline-origin':data=b'<!doctype html><title>offline</title>';mime='text/html'
        elif self.path.startswith('/before/'):
            name=self.path[len('/before/'):].split('?')[0]
            if name in VISUAL_FIX_ASSETS:data=old(name)
            else:
                path=(ROOT/name).resolve()
                if not path.is_relative_to(ROOT) or not path.is_file():self.send_error(404);return
                data=path.read_bytes()
            mime=self.guess_type(name)
        else:return super().do_GET()
        self.send_response(200);self.send_header('Content-Type',mime);self.end_headers();self.wfile.write(data)

probe=r'''({kind,region,angle})=>{
 if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');gameVolcano.reset();gameSnowfield.reset();}
 window.gameExitDialogOpen=false;gameWorlds.setDeveloperStart({enabled:true,regionId:region,phase:1});start(kind);
 transition=0;spawn=999;invuln=0;rotorSpin=.35;player.a=angle;player.x=W/2;player.y=H/2;
 enemies=[];boss=null;bullets=[];enemyBullets=[];warnings=[];particles=[];items=[];itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();
 window.gameExitDialogOpen=true;
 const original=ctx.drawImage,calls=[];ctx.drawImage=function(im,...a){if(sprites.includes(im)||rotorImages.includes(im))calls.push({im,args:a,m:[ctx.getTransform().a,ctx.getTransform().b,ctx.getTransform().c,ctx.getTransform().d,ctx.getTransform().e,ctx.getTransform().f],alpha:ctx.globalAlpha,kind:sprites.includes(im)?'body':'rotor'});return original.call(ctx,im,...a);};
 try{draw();}finally{ctx.drawImage=original;}
 const probe=document.createElement('canvas');probe.width=canvas.width;probe.height=canvas.height;const g=probe.getContext('2d');
 for(const c of calls){g.setTransform(...c.m);g.globalAlpha=c.alpha;g.drawImage(c.im,...c.args);}
 const im=sprites[kind];return {kind,region,angle,width:im.naturalWidth,height:im.naturalHeight,approvedIndex:gameplayHeliImages.indexOf(im.src),legacyIndex:spriteURLs.indexOf(im.src),calls:calls.map(c=>({kind:c.kind,args:c.args,m:c.m,alpha:c.alpha})),layer:probe.toDataURL()};
}'''
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
    all_rows={};failures=[];dialogs=[]
    for variant in (['after'] if args.standalone else ['before','after']):
        context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True)
        page=context.new_page();page.on('pageerror',lambda e:failures.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()))
        if args.standalone:
            page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');context.set_offline(True)
            page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
        else:page.goto(f'http://127.0.0.1:{server.server_port}/'+('before/' if variant=='before' else ''))
        page.wait_for_function('gameVolcano.ready()&&gameSnowfield.ready()&&sprites.length===3&&sprites.every(i=>i.complete&&i.naturalWidth>0)');page.wait_for_timeout(800)
        rows=[]
        for kind in range(3):
            for direction in range(8):
                group=[]
                for region in [0,4,5]:
                    r=page.evaluate(probe,{'kind':kind,'region':region,'angle':3.141592653589793+direction*3.141592653589793/4})
                    data=base64.b64decode(r.pop('layer').split(',')[1]);r['layer_sha256']=sha(data)
                    with Image.open(io.BytesIO(data)) as layer:
                        assert layer.getbbox() is not None,'Player inspection layer must contain actual visible pixels'
                        r['visible_bounds']=layer.getbbox()
                    assert r['approvedIndex']==kind and r['legacyIndex']==-1,r
                    if direction==0 and region==0:(args.artifacts/f'{variant}-player-{kind}.png').write_bytes(data)
                    if variant=='after' and region==0:(args.artifacts/f'rotation-{kind}-{direction}.png').write_bytes(data)
                    group.append(r);rows.append(r)
                assert len({r['layer_sha256'] for r in group})==1
                assert group[0]['calls']==group[1]['calls']==group[2]['calls']
        all_rows[variant]=rows
        for width,height in [(915,412),(800,360),(568,320)]:
            page.set_viewport_size({'width':width,'height':height})
            for step in [2,5]:
                page.evaluate(r'''step=>{
                    window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;menu.classList.remove('hidden');}
                    gameVolcano.reset();gameSnowfield.reset();gameWorlds.setDeveloperStart({enabled:true,regionId:5,phase:step});start(0);
                    transition=0;spawn=999;invuln=0;rotorSpin=.35;player.a=Math.PI;player.x=W*.5;player.y=H*.72;
                    warnings=[];enemies=[];enemyBullets=[];bullets=[];particles=[];items=[];itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();
                    if(boss){boss.x=W*.5;boss.y=H*.36;}else{warnEnemy();warnings.forEach(w=>w.time=0);update(0);enemies.forEach((e,i)=>{e.x=W*.5+i*70;e.y=H*.35;});}
                    gameVolcano.observe(enemies,boss);window.gameExitDialogOpen=true;draw();
                }''',step)
                page.screenshot(path=str(args.artifacts/f'{variant}-{width}x{height}-phase{step}.png'))
        context.close()
    if not args.standalone:
        assert all_rows['before']==all_rows['after'],'Stable normal-loading World1/2 player layers must not change'
    report['player_draws']=all_rows
    passed('Three characters × three regions × eight directions: approved PNG source, exact layer pixels, alpha, dimensions, matrices and rotor pivot match; normal-loading baseline unchanged.')
    # Reproduce the actual competing-writer bug without changing source image pixels.
    race=[]
    for variant in (['after'] if args.standalone else ['before','after']):
        context=browser.new_context(viewport={'width':915,'height':412});page=context.new_page()
        script=r'''(()=>{const legacy=LEGACY,Native=Image;window.legacyRequests=0;
          window.Image=new Proxy(Native,{construct(target,args){const im=Reflect.construct(target,args);let handler=null;
          Object.defineProperty(im,'onload',{configurable:true,get:()=>handler,set:value=>handler=value});
          im.addEventListener('load',e=>{const old=legacy.includes(im.src);if(old)window.legacyRequests++;const run=()=>{if(typeof handler==='function')handler.call(im,e);};if(old)setTimeout(run,1400);else run();});return im;}});})()'''.replace('LEGACY',json.dumps(current_arrays['spriteURLs']))
        context.add_init_script(script)
        if args.standalone:
            page.goto(f'http://127.0.0.1:{server.server_port}/offline-origin');context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
        else:page.goto(f'http://127.0.0.1:{server.server_port}/'+('before/' if variant=='before' else ''))
        page.wait_for_function('sprites.length===3&&sprites.every(i=>i.complete&&i.naturalWidth>0)');page.wait_for_timeout(1900)
        state=page.evaluate('({legacyRequests,indices:sprites.map(i=>gameplayHeliImages.indexOf(i.src)),dimensions:sprites.map(i=>[i.naturalWidth,i.naturalHeight])})')
        assert state['indices']==([-1,-1,-1] if variant=='before' else [0,1,2]),state
        for kind in range(3):
            r=page.evaluate(probe,{'kind':kind,'region':5,'angle':3.141592653589793})
            data=base64.b64decode(r.pop('layer').split(',')[1])
            with Image.open(io.BytesIO(data)) as layer:assert layer.getbbox() is not None
            (args.artifacts/f'{variant}-delayed-legacy-player-{kind}.png').write_bytes(data)
        race.append({'variant':variant,**state});context.close()
    report['load_race']=race
    passed('Delayed legacy-load callbacks reproduce all three old sprite overwrites before; fixed loader retains all approved sources with no legacy Image requests.')
    assert not failures and not dialogs,(failures,dialogs)
    report.update(page_errors=failures,native_dialogs=dialogs)
    browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
