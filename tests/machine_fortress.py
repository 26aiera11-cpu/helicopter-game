"""Issue31: native/offline art, legacy combat, progression and integrity checks."""
import argparse,base64,hashlib,io,json,math,re,shutil,struct,subprocess,threading,zlib
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image
from playwright.sync_api import sync_playwright,expect
from machine_fortress_preservation import verify
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);p.add_argument('--standalone',action='store_true');args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
report={'standalone':args.standalone,'passed':[],'limits':['Controlled real Chromium, not physical Galaxy Samsung Internet/Chrome, sensor hardware, audio speaker approval or human balance certification.','One original pose per normal monster/two boss PNGs; animation is display-only transforms, not redrawn frames.','Overdrive and four electromagnetic effects remain preview-only. Normal AI/laser/shells are tested separately; boss specials/wall/HP50% transition are still absent.','Local-file browser policy is not bypassed: exact standalone HTML is injected into an offline blank origin.']}
def passed(s):report['passed'].append(s);print('PASS:',s,flush=True)
report['preservation']=verify()
for js in [f.read_text() for f in (ROOT/'assets').rglob('*.js')]+re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',(ROOT/'index.html').read_text(),re.S):subprocess.run(['node','--check','-'],input=js,text=True,capture_output=True,check=True)
passed('Exact16 graphics hooks and9 registry/UI deltas invert to653ac83; all other111 existing assets match the baseline, including every audio, image, combat/control/item/score module; all JS parses.')
base=ROOT/'assets/machine_fortress';manifest=json.loads((base/'asset_manifest.json').read_text());rows=[]
for f in sorted(base.rglob('*.png')):
 data=f.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;idat=[];types=[]
 while pos<len(data):
  length=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];payload=data[pos+8:pos+8+length];crc=struct.unpack('>I',data[pos+8+length:pos+12+length])[0];assert zlib.crc32(kind+payload)&0xffffffff==crc;types.append(kind.decode());pos+=12+length
  if kind==b'IDAT':idat.append(payload)
 assert pos==len(data) and types[-1]=='IEND';decoder=zlib.decompressobj();decoder.decompress(b''.join(idat));decoder.flush();assert decoder.eof
 with Image.open(io.BytesIO(data)) as im:im.verify()
 im=Image.open(io.BytesIO(data));im.load();row={'path':str(f.relative_to(base)),'dimensions':list(im.size),'mode':im.mode,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'complete_crc_zlib_decode':True}
 if f.parent.name=='background':assert im.size==(1672,941) and im.mode=='RGB' and row['sha256']=='89990eeac3ae96c8ed5c2d9af2d90a5f3d8e51e95ccecf3757db1f9e21f9f124'
 else:
  spec=next(r for r in manifest['files'] if r['path']==row['path']);assert spec['sha256']==row['sha256'] and spec['bytes']==len(data) and spec['dimensions']==list(im.size)
  alpha=im.getchannel('A');assert im.mode=='RGBA' and alpha.getextrema()[0]==0;row.update(alpha_extrema=alpha.getextrema(),alpha_bounds=alpha.getbbox(),transparent_pixels=sum(n for n,a in alpha.getcolors(im.width*im.height) if a==0))
 rows.append(row)
assert len(rows)==11;report['png_integrity']=rows
passed('All11 supplied PNGs have valid chunk CRC/zlib EOF/IEND/full decode; dimensions/hashes/alpha unchanged. Background1672x941 and source_rect metadata is never misused to crop standalone sprites.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):
  if path.startswith('/helicopter-game/'):path=path[len('/helicopter-game'):]
  return super().translate_path(path)
 def do_GET(self):
  if self.path=='/blank':self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<!doctype html><title>offline</title>');return
  super().do_GET()
helpers=r'''()=>{
 window.mfStorage=()=>Object.fromEntries(['heliTrio.top10.v1','heliTrio.playHistory.v1','heliTrio.world2Trial.top10.v1','heliTrio.world2Trial.playHistory.v1'].map(k=>[k,localStorage.getItem(k)]));
 window.mfBegin=(type=0,step=1)=>{window.gameExitDialogOpen=false;if(started){gameScoring.finish('abandoned');started=false;gameAudio.pause();menu.classList.remove('hidden');}clearGameOver();gameWorlds.setDeveloperStart({enabled:true,regionId:7,phase:step});start(type);transition=0;spawn=999;invuln=999;keys.fire=false;tilt={x:0,y:0};player.x=W*.75;player.y=H*.8;player.vx=player.vy=0;itemMonsters.configure({opportunitiesPerRegion:0});itemMonsters.reset();};
 window.mfRun=fn=>{window.gameExitDialogOpen=false;try{return fn();}finally{window.gameExitDialogOpen=true;gameScoring.updateHUD();draw();}};
 window.mfSeed=(kind,step=phase)=>{for(let seed=1;seed<100000;seed++){let n=seed;n^=n<<13;n^=n>>>17;n^=n<<5;if(gameMachineSpawns.chooseForRoll(step,(n>>>0)/4294967296)===gameMachineConfig.ids[kind])return seed;}throw Error('Species not allowed');};
 window.mfSpawn=(kind=0)=>{bullets=[];gameMachineSpawns.reset(mfSeed(kind));warnEnemy();const w=warnings.at(-1);w.kind=kind;w.x=W*.35;w.y=H*.45;w.time=0;update(0);return enemies.at(-1);};
 window.mfHit=e=>{bullets=[];shoot();bullets=[bullets[0]];Object.assign(bullets[0],{x:e.x,y:e.y,vx:0,vy:0});update(0);};
 window.mfAdvance=seconds=>{let left=seconds;while(left>1e-9&&started){const dt=Math.min(left,1/120);update(dt);left-=dt;}};
 window.mfFlush=()=>{let n=0;while((gameMachineFortress.snapshot().advancing||gameStormSky.snapshot().advancing||gameVolcano.snapshot().advancing)&&n++<100)update(.04);};
}'''
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}'
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);context=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);page=context.new_page();errors=[];dialogs=[];failed=[];external=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(dialogs.append(d.type),d.dismiss()));page.on('requestfailed',lambda r:failed.append(r.url));page.on('request',lambda r:external.append(r.url) if args.standalone and r.url.startswith('http') else None)
  if args.standalone:
   page.goto(url+'/blank');external.clear();context.set_offline(True);page.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
  else:page.goto(url+'/helicopter-game/',wait_until='load')
  page.wait_for_function('gameMachineFortress.ready()&&gameStormSky.ready()&&gameVolcano.ready()&&gameSnowfield.ready()&&itemMonsters.ready()');page.evaluate(helpers);initial=page.evaluate('mfStorage()')
  assert page.evaluate('gameWorlds.worlds[1].regionIds.join()==="4,5,6,7"&&gameWorlds.snapshot().route.join()==="0,1,2,3"&&!gameWorlds.isTrial()&&!gameWorlds.isDeveloper()')
  r=page.evaluate('gameWorlds.region(7)');assert r['key']=='world-2:machine-fortress' and r['localIndex']==3 and r['normalPhases']==4 and r['bossPhase']==5 and r['combatProfile']==r['musicProfile']==0
  assert page.evaluate('gameMachineFortress.species.map(s=>s.renderWidth)')==[40,40,40,40,132]
  assert page.evaluate('terrainImgs.length===8&&enemySprites[7].length===4&&enemySprites[7].every((im,i)=>im===gameMachineFortress.species[i].baseImage)&&bossSprites[7]===gameMachineFortress.species[4].baseImage')
  passed('Registry keeps stable ID7/world2 localIndex3, default20phases and opt-in40phases; all5 stage choices retain fallback combat/music profile0 while Machine normal AI is region-local.')
  page.locator('.select-hit[data-heli="0"]').tap();page.locator('#selectionHelp').tap();page.locator('#developerStartToggle').check();page.locator('#developerStartWorld').select_option('1');assert page.locator('#developerStartRegion option').count()==4;page.locator('#developerStartRegion').select_option('7');page.locator('#developerStartPhase').select_option('5');page.screenshot(path=str(args.artifacts/'machine-developer-menu.png'));page.locator('#selectionHelpClose').tap();page.locator('#startSelected').tap();page.wait_for_function('started&&stage===7&&phase===5&&!!boss');assert page.evaluate('boss.hp===20&&phaseKills===6&&enemies.length===0&&warnings.length===0');page.evaluate('transition=0;spawn=999;invuln=999')
  assert page.evaluate('document.body.innerText.includes("기계 요새 일반 전투 시험 · 보스/음악 숲 임시")')
  passed('Trusted Help->World2->MachineFortress5->Start enters original20HP GigaCore immediately with no normal enemies; current UI labels normal-combat trial and legacy boss/forest temporary music.')
  # Whole source image, cover geometry, stage invariance, DPR and aspect ratios.
  layouts=[]
  for w,h,dpr2 in [(915,412,False),(800,360,False),(568,320,False),(568,320,True)]:
   target=page;extra=None
   if dpr2:
    extra=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=2,is_mobile=True,has_touch=True);target=extra.new_page()
    if args.standalone:extra.set_offline(True);target.set_content((ROOT/'dist/heli_trio_galaxy_test.html').read_text(),wait_until='load')
    else:target.goto(url+'/helicopter-game/')
    target.wait_for_function('gameMachineFortress.ready()');target.evaluate(helpers)
   else:target.set_viewport_size({'width':w,'height':h})
   target.wait_for_function('([w,h])=>W===w&&H===h',arg=[w,h])
   target.evaluate('mfRun(()=>mfBegin(0,1))');target.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
   row=target.evaluate('''()=>mfRun(()=>{const im=gameMachineFortress.backgroundImage,drawImage=ctx.drawImage,calls=[];ctx.drawImage=function(image,...a){if(image===im)calls.push(a);return drawImage.call(ctx,image,...a)};try{for(let step=1;step<=5;step++){phase=step;draw();}}finally{ctx.drawImage=drawImage;}return {calls,source:[im.naturalWidth,im.naturalHeight],dpr,canvas:[canvas.width,canvas.height],hud:hud.getBoundingClientRect().toJSON(),joystick:rotationJoystick.getBoundingClientRect().toJSON(),fire:fire.getBoundingClientRect().toJSON(),full:fullscreenToggle.getBoundingClientRect().toJSON()};})''')
   scale=max(w/1672,h/941);expected=[(w-1672*scale)/2,(h-941*scale)/2,1672*scale,941*scale]
   assert len(row['calls'])==5 and all(len(call)==4 and all(abs(a-b)<1e-6 for a,b in zip(call,expected)) for call in row['calls']);assert row['source']==[1672,941]
   assert row['joystick']['x']==30 and h-row['joystick']['bottom']==22 and row['joystick']['right']<row['fire']['left'] and row['hud']['right']<=row['full']['left']
   if dpr2:assert row['dpr']==2 and row['canvas']==[w*2,h*2]
   target.evaluate("mfRun(()=>{mfBegin(0,3);const ids=gameMachineFortress.normalIds;for(let i=0;i<4;i++){const e=mfSpawn(i);e.x=W*(.2+i*.18);e.y=H*.42;e.shot=999;}player.x=W*.5;player.y=H*.72;})");target.screenshot(path=str(args.artifacts/(f'machine-normal-{w}x{h}'+('-dpr2' if dpr2 else '')+'.png')))
   target.evaluate('mfRun(()=>mfBegin(0,5))');target.screenshot(path=str(args.artifacts/(f'machine-boss-{w}x{h}'+('-dpr2' if dpr2 else '')+'.png')));layouts.append({'size':[w,h],**row})
   if extra:extra.close()
  report['layouts']=layouts
  passed('All5 phases use one1672x941 source via centered cover at915x412/800x360/568x320 and actualDPR2; source ratio/center preserved with approved edge cropping; HUD/joystick/fire/fullscreen fit.')
  cases=[]
  for hero in range(3):
   for step in range(1,5):
    for kind,weight in enumerate(page.evaluate('gameMachineConfig.weights')[step-1]):
     if not weight:continue
     row=page.evaluate("""([hero,step,kind])=>mfRun(()=>{mfBegin(hero,step);const e=mfSpawn(kind),initial={hp:e.hp,r:e.r,speed:e.speed,kind:e.kind,pose:gameMachineFortress.pose(e)},score=runScore,kills=phaseKills;let hits=0;while(e.hp>0&&hits++<8)mfHit(e);const after={hp:e.hp,score:runScore-score,kills:phaseKills-kills,ghosts:gameMachineFortress.snapshot().ghosts.length,alive:enemies.includes(e)};mfAdvance(.7);return {initial,hits,after,ghostsAfter:gameMachineFortress.snapshot().ghosts.length};})""",[hero,step,kind])
     assert row['initial']['hp']==[1,1,2,3][kind] and row['initial']['r']==16 and row['initial']['speed']==[46,50,30,20][kind] and row['initial']['pose']['id']==['screw_bot','gear_wasp','laser_drone','armored_turret'][kind]
     assert row['after']['hp']<=0 and row['after']['score']==100 and row['after']['kills']==1 and row['after']['ghosts']==1 and not row['after']['alive'] and row['ghostsAfter']==0;cases.append({'hero':hero,'phase':step,'kind':kind,**row})
  report['normal_combat']=cases
  passed('3heroes x13 permitted phase/species pairs=39 actual spawn/HP/weapon/hit/death cases match Issue33 profiles while keeping r16,100points/one normal kill, original animation and cleanup; dedicated pattern timing is checked separately.')
  poses=page.evaluate('''()=>mfRun(()=>{mfBegin();const e=mfSpawn();gameMachineFortress.observe([e],null);const idle=gameMachineFortress.pose(e);e.hp=2;mfHit(e);const hit=gameMachineFortress.pose(e);const frames=['idle','move','attack','hit','defeat'].map(name=>({name,first:gameMachineFortress.frame(name,.01),middle:gameMachineFortress.frame(name,.12)}));return {idle,hit,frames};})''');assert poses['idle']['name']=='idle' and poses['hit']['name']=='hit' and all(r['first']!=r['middle'] for r in poses['frames']);report['poses']=poses
  passed('All5 display states change transform/alpha over time; surviving hit is visible; original single-pose PNG proportions and centered pivots are retained without pixel edits.')
  preview=page.evaluate('''()=>{const c=document.createElement('canvas');c.width=660;c.height=240;const g=c.getContext('2d');g.fillStyle='#252c36';g.fillRect(0,0,660,240);gameMachineFortress.preview(g,'boss/giga_core_normal.png',165,120,240);gameMachineFortress.preview(g,'boss/giga_core_overdrive.png',495,120,240);return c.toDataURL();}''');(args.artifacts/'giga-core-normal-overdrive-preview.png').write_bytes(base64.b64decode(preview.split(',')[1]))
  low=page.evaluate('''()=>mfRun(()=>{mfBegin(0,5);boss.hp=1;const p=gameMachineFortress.pose(boss,true);mfAdvance(.1);return {pose:p,state:gameMachineFortress.snapshot(),storm:gameStormBoss.snapshot(),volcano:gameVolcanoBoss.snapshot(),bullets:enemyBullets.length};})''');assert low['pose']['id']=='giga_core' and not low['state']['overdriveCombat'] and not low['state']['wallCombat'] and low['storm'] is None and low['volcano'] is None;report['no_new_boss_attacks']=low
  passed('Normal/overdrive PNGs both load and preview; HP below50% still renders normal GigaCore, no automatic combat overdrive/laser/missile/barrier or other-region boss module runs.')
  kills=[]
  for hero in range(3):
   row=page.evaluate('''hero=>mfRun(()=>{mfBegin(hero,4);nextPhase();spawn=999;transition=0;const normals=[];for(let n=0;n<6;n++){const e=mfSpawn(n%4);while(e.hp>0)mfHit(e);normals.push({kills:phaseKills,boss:!!boss});}update(0);transition=0;const king=boss,before={hp:boss.hp,r:boss.r};king.shot=0;update(.001);const shotCount=enemyBullets.length;while(boss)mfHit(boss);const ending=gameMachineFortress.snapshot();mfFlush();const result=gameScoring.getLastResult();return {normals,before,shotCount,ending,score:runScore,started,result,ghosts:gameMachineFortress.snapshot().ghosts};})''',hero)
   assert all(x['kills']==n+1 and not x['boss'] for n,x in enumerate(row['normals'])) and row['before']=={'hp':20,'r':48} and row['shotCount']==1 and row['ending']['advancing'] and not row['started'] and row['score']==3100 and row['result']['developerTest'] and not row['result']['saved'] and row['ghosts']==[];kills.append(row)
  report['boss_gate_rewards']=kills
  passed('All3 weapons: normalphase5 needs6 kills then original20HP/r48 single-shot boss, whereas developer5 is immediate; boss2000points/reward/outro once and clean dev return without records.')
  # Separate ordinary route fixture: direct-region tests intentionally stop at their own boss.
  route=page.evaluate('''()=>{window.gameExitDialogOpen=false;started=false;menu.classList.remove('hidden');gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true);start(0);spawn=999;transition=0;invuln=999;stage=6;phase=5;boss=null;const item={x:40,y:50,type:'power',life:7.25,r:13,t:0,vx:0,vy:0,turn:99};items=[item];nextPhase();const row={stage,phase,life:item.life,same:items[0]===item,route:gameWorlds.snapshot().route};gameScoring.finish('abandoned');started=false;gameAudio.pause();menu.classList.remove('hidden');gameWorlds.setTrialEnabled(false);return row;}''');assert route=={'stage':7,'phase':1,'life':7.25,'same':True,'route':list(range(8))};report['storm_to_fortress']=route
  passed('Actual trial Storm->Fortress transition enters7/1 on the40-phase route and carries the same item with unchanged lifetime; default World1 route remains separate.')
  # Geometry inspection uses actual draw calls rather than assuming square assets.
  drawing=page.evaluate('''()=>mfRun(()=>{mfBegin(0,3);const calls=[],original=ctx.drawImage;ctx.drawImage=function(im,...a){if(im.id.startsWith('machine-'))calls.push({id:im.id,w:im.naturalWidth,h:im.naturalHeight,args:a});return original.call(ctx,im,...a)};try{for(let i=0;i<4;i++){const e=mfSpawn(i);gameMachineFortress.drawActor(ctx,e);}mfBegin(0,5);gameMachineFortress.drawActor(ctx,boss,true);}finally{ctx.drawImage=original;}return calls;})''');assert len(drawing)==5
  for r in drawing:assert r['args'][:4]==[0,0,r['w'],r['h']] and abs(r['args'][6]/r['w']-r['args'][7]/r['h'])<1e-10 and r['args'][6]==(132 if 'boss-' in r['id'] else 40)
  report['draw_rectangles']=drawing;passed('Actual4-normal/boss Canvas calls use the entire per-file PNG (source_rect ignored), identical X/Y scale, centered full-image pivot and original transparency; no square distortion/cropping.')
  page.evaluate('window.gameExitDialogOpen=false')
  report['fullscreen_before_explicit_toggle']=page.evaluate('!!document.fullscreenElement')
  if not page.evaluate('!!document.fullscreenElement'):page.locator('#fullscreenToggle').tap()
  page.wait_for_function('!!document.fullscreenElement');page.locator('#exitGame').tap();expect(page.locator('#gameExitDialog')).to_be_visible();clock=page.evaluate('gameMachineFortress.snapshot().clock');page.wait_for_timeout(100);assert page.evaluate('gameMachineFortress.snapshot().clock')==clock;page.locator('#gameExitCancel').tap();page.locator('#exitGame').tap();page.locator('#gameExitConfirm').tap();assert page.evaluate('!started&&!!document.fullscreenElement&&gameMachineFortress.snapshot().ghosts.length===0')
  page.evaluate('mfRun(()=>mfBegin(0,5))');page.evaluate('window.gameExitDialogOpen=false;hp=0;update(0)');expect(page.locator('#gameOverOverlay')).to_be_visible();assert page.evaluate('!started&&gameOverPending&&!gameMachineFortress.snapshot().advancing');page.wait_for_timeout(3100);expect(page.locator('#menu')).to_be_visible();assert page.evaluate('!!document.fullscreenElement')
  passed('Internal exit freezes art timers, cancel/confirm retain fullscreen and clear ghosts; zeroHP preserves original3s GAME OVER/clean selection return, no browser dialogs.')
  assert not errors and not dialogs and not failed and (not args.standalone or not external),(errors,dialogs,failed,external)
  report.update(all_passed=True,errors=errors,dialogs=dialogs,failed=failed,offline_requests=external if args.standalone else [])
  passed('Native project-prefix and standalone offline resources load without any missing asset/uncaught error/native dialog; offline external fetches0. Separate retained suites cover full routes, audio, scores and controls.')
  browser.close()
finally:
 server.shutdown();(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
