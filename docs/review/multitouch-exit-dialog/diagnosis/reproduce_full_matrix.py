import json,shutil,threading,time,subprocess
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path('/tmp/exit-tap-tests/diagnosis-live');OUT.mkdir(parents=True,exist_ok=True)
probe=r'''()=>{
 window.tapTrace=[];window.tapOpens=0;window.plainClicks=0;window.tapDomChanges=0;
 const names=['pointerdown','pointermove','pointerup','pointercancel','gotpointercapture','lostpointercapture','touchstart','touchend','touchcancel','mousedown','mouseup','click'];
 const record=(phase,e)=>{const target=e.target?.id||e.target?.tagName;const owners=window.gameControls?.snapshot();const r={phase,type:e.type,target,id:e.pointerId,pointer:e.pointerType,primary:e.isPrimary,trusted:e.isTrusted,time:performance.now(),x:e.clientX,y:e.clientY,prevented:e.defaultPrevented,stopped:e.cancelBubble,path:e.composedPath().slice(0,4).map(n=>n.id||n.tagName||n.constructor.name),touches:e.touches&&[...e.touches].map(t=>t.identifier),changed:e.changedTouches&&[...e.changedTouches].map(t=>t.identifier),owners};tapTrace.push(r);if(tapTrace.length>1800)tapTrace.shift();};
 for(const n of names){window.addEventListener(n,e=>record('window-capture',e),true);document.addEventListener(n,e=>record('document-capture',e),true);document.addEventListener(n,e=>record('document-bubble',e));window.addEventListener(n,e=>record('window-bubble',e));}
 window.tapAttach=()=>{for(const id of ['exitGame','probePlain']){const el=document.getElementById(id);if(!el||el.dataset.audited)continue;el.dataset.audited='true';for(const n of names){el.addEventListener(n,e=>record('button-capture',e),true);el.addEventListener(n,e=>record('button-bubble',e));}new MutationObserver(ms=>tapDomChanges+=ms.length).observe(el,{attributes:true,childList:true});}};
}'''
BASE_HTML=subprocess.check_output(['git','show','3c085442bba6490bfa41cae64ac4007af570ba2e:index.html'],cwd=ROOT)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/':
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(BASE_HTML);return
  super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':915,'height':412},is_mobile=True,has_touch=True);ctx.add_init_script('('+probe+')()');page=ctx.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load');page.wait_for_function('gameMachineFortress.ready()&&gameSnowfield.ready()');page.wait_for_function("[...document.querySelectorAll('audio')].every(a=>!a.error&&a.readyState>=2&&a.buffered.length&&a.buffered.end(a.buffered.length-1)>=a.duration-.01)")
  page.evaluate("gameWorlds.setDeveloperStart({enabled:true,regionId:4,phase:5})");page.locator('#startSelected').tap();page.wait_for_function('started');page.evaluate("const show=showGameExitDialog;window.showGameExitDialog=cb=>{tapOpens++;return show(cb)};const b=document.createElement('button');b.id='probePlain';b.textContent='plain native button';b.style='position:fixed;z-index:200;top:45px;left:40%;width:150px;height:35px';b.onclick=()=>plainClicks++;document.body.append(b);tapAttach()")
  cdp=ctx.new_cdp_session(page);rows=[];details=[];serial=100
  def gesture(count,end,plain=False):
   points={};coords=page.evaluate("()=>{const c=id=>{const r=document.getElementById(id).getBoundingClientRect();return {x:r.x+r.width*.7,y:r.y+r.height*.5}};return [c('rotationJoystick'),c('fire'),{x:innerWidth*.55,y:innerHeight*.45},{x:innerWidth*.35,y:innerHeight*.5}]}") if not plain else [{'x':70+i*180,'y':280} for i in range(4)]
   for i in range(count):
    points[i+1]={'id':i+1,**coords[i]};cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':list(points.values())})
   
   # Reproduce the original joystick/canvas movement, not a stationary multi-tap.
   points[1]['x']+=40;cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':list(points.values())})
   if count>=3:
    points[3]['x']+=75;cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':list(points.values())})
   page.wait_for_timeout(80)
   for i in range(count):
    p=points.pop(i+1);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[p] if end=='point' or points else []})
  def tap(id,method,end,fresh):
   nonlocal_dummy=None
   global serial
   if method=='pw':page.locator('#'+id).tap();return
   serial+=1;rid=serial if fresh else 50;r=page.locator('#'+id).bounding_box();p={'id':rid,'x':r['x']+r['width']/2,'y':r['y']+r['height']/2};cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[p]});page.wait_for_timeout(60);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[p] if end=='point' else []})
  for pure in [False,True]:
   if pure:
    page.goto('about:blank');page.set_content('<style>html,body{margin:0;touch-action:none}button{position:absolute;right:10px;top:10px;width:130px;height:40px}</style><button id="probePlain">native button</button>');page.evaluate('('+probe+')()');page.evaluate("probePlain.onclick=()=>plainClicks++;for(let i=0;i<4;i++){const d=document.createElement('div');d.style='position:absolute;left:'+(30+i*180)+'px;top:240px;width:90px;height:90px;background:#456';d.addEventListener('pointerdown',e=>{e.preventDefault();d.setPointerCapture(e.pointerId)});document.body.append(d)};tapAttach()")
   for count in [2,3,4]:
    for end in ['empty','point']:
     for fresh in [False,True]:
      for method in ['cdp','pw']:
       for target in (['exitGame','probePlain'] if not pure else ['probePlain']):
        
        if not pure:
         if page.evaluate('window.gameExitDialogOpen'):page.evaluate('document.getElementById("gameExitConfirm").click()')
         elif page.evaluate('started'):page.evaluate('document.getElementById("exitGame").click();document.getElementById("gameExitConfirm").click()')
         page.evaluate('gameWorlds.setDeveloperStart({enabled:false});gameWorlds.setTrialEnabled(true);itemMonsters.configure({opportunitiesPerRegion:0})');tap('startSelected','cdp',end,False);page.wait_for_function('started');page.evaluate('stage=3;phase=5;boss=null;nextPhase();transition=0;spawn=999;invuln=999;player.x=W/2;player.y=H*.55;gameScoring.updateHUD();draw()')
        page.evaluate('tapTrace=[];tapDomChanges=0');before=page.evaluate('({open:tapOpens,plain:plainClicks})');gesture(count,end,pure);page.wait_for_timeout(550);
        if not pure:page.evaluate('phase=5;phaseKills=requiredKills;update(0);transition=0;gameScoring.updateHUD();draw()')
        tap(target,method,end,fresh);page.wait_for_timeout(150)
        state=page.evaluate("({open:window.gameExitDialogOpen||false,opens:tapOpens,plain:plainClicks,dom:tapDomChanges,trace:tapTrace,controls:window.gameControls?.snapshot()})");events=[e for e in state['trace'] if e['target']==target and e['phase']=='window-capture'];clicks=sum(e['type']=='click' for e in events);ups=sum(e['type']=='pointerup' for e in events)
        row={'pure':pure,'contacts':count,'end':end,'freshID':fresh,'tap':method,'target':target,'clicks':clicks,'pointerups':ups,'openDelta':state['opens']-before['open'],'plainDelta':state['plain']-before['plain'],'domChanges':state['dom']};assert ups==1,('Invalid event probe',row);rows.append(row)
        if len(details)<3 or not clicks:details.append({'case':row,'events':state['trace'],'controls':state.get('controls')})
        if not pure and state['open']:page.evaluate('document.getElementById("gameExitCancel").click()')
        print(json.dumps(row),flush=True)
  (OUT/'results.json').write_text(json.dumps({'cases':rows,'detailed_traces':details,'baseline':'3c085442bba6490bfa41cae64ac4007af570ba2e'},indent=2)+'\n');browser.close()
finally:server.shutdown()
