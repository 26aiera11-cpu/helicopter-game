"""Exact type-specific interval, first-trigger preservation and native-timestep counts."""
import argparse,json,re,subprocess,shutil,threading,math
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from tanko_combat_preservation import without_tanko_cadence_changes
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--artifacts',type=Path,required=True);args=p.parse_args();args.artifacts.mkdir(parents=True,exist_ok=True)
baseline='f622f3f9c8e82f390b40883abd1abd8f6b9e7f71';before=subprocess.check_output(['git','show',baseline+':index.html'],cwd=root).decode();after=(root/'index.html').read_text()
assert without_tanko_cadence_changes(after)==before
for path in (root/'assets').rglob('*'):
 if path.is_file():assert path.read_bytes()==subprocess.check_output(['git','show',baseline+':'+str(path.relative_to(root))],cwd=root)
for script in re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>',after,re.S):subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,check=True)
report={'baseline':baseline,'passed':[],'limits':['Controlled actual Chromium updates, not physical Galaxy timing or human aim. Finite-window shot counts are quantized to the unchanged game update step.']}
def passed(m):report['passed'].append(m);print('PASS:',m,flush=True)
passed('Reversing the single Tanko cooldown multiplier restores every index byte to f622f3f; all assets/audio/UI/other gameplay are identical and JS syntax passes.')
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);rows=[]
  for version in ['before','after']:
   page=browser.new_page(viewport={'width':915,'height':412})
   if version=='before':page.route('**/cadence-baseline.html',lambda route:route.fulfill(status=200,content_type='text/html',body=before))
   page.goto(f'http://127.0.0.1:{server.server_port}/'+('cadence-baseline.html' if version=='before' else ''),wait_until='load')
   values=page.evaluate('''version=>{
    const rows=[],oldFx=gameAudio.fx,realShoot=shoot;gameAudio.fx=()=>{};let trace=[],time=0;
    shoot=()=>{const prior=bullets.length;realShoot();trace.push({time,projectiles:bullets.length-prior,damage:bullets[prior].damage,speed:bullets[prior].speed,pierce:bullets[prior].pierce})};
    try{for(let type=0;type<3;type++)for(let level=0;level<=5;level++)for(const hz of [120,60])for(const initial of [0,.18]){
     start(type);player.upgrade=level;spawn=999;invuln=999;transition=0;fireCooldown=initial;trace=[];time=0;keys.fire=true;
     let interval=null;for(let frame=0;frame<hz*12;frame++){time=(frame+1)/hz;const count=trace.length;update(1/hz);if(count<trace.length&&interval===null)interval=fireCooldown;}
     rows.push({version,type,level,hz,initial,interval,count:trace.length,trace});
    }return rows;}finally{shoot=realShoot;gameAudio.fx=oldFx;keys.fire=false}
   }''',version);rows+=values;page.close()
  assert len(rows)==144
  for row in rows:
   original=next(v for v in rows if v['version']=='before' and all(v[k]==row[k] for k in ['type','level','hz','initial']))
   scale=1.25 if row['version']=='after' and row['type']==2 else 1
   expected=[.105,.17,.28][row['type']]*(.82 if row['level']>=1 else 1)*(.85 if row['type']==1 and row['level']>=5 else 1)*scale
   assert abs(row['interval']-expected)<1e-10,(row,expected)
   assert row['trace'][0]==original['trace'][0],(row,original)
   if row['type']!=2:assert row['trace']==original['trace']
   if row['version']=='after' and row['type']==2:
    assert row['count']<original['count']
    for shot in row['trace']:assert shot['damage']==1.5 and shot['speed']==410 and shot['pierce']==[2,3,3,4,4,5][row['level']]
  report['matrix']=rows
  passed('All upgrades0..5 use exactly1.25× Tanko intervals (0.35s/0.287s), retaining the0.82 upgrade factor; projectile speed410/damage1.5 and piercing are unchanged.')
  passed('The first shot timestamp and projectile data match the baseline for every type/upgrade at120/60Hz, both with zero and pre-existing positive0.18s cooldown; no start/reset logic changes.')
  passed('Trio/Bingle full12s firing traces match exactly at both time steps and all upgrades; only Tanko subsequent volleys decrease.')
  # Prove measured spacing is the native scheduler's unchanged next-frame rule.
  for row in rows:
   spacing=math.ceil(row['interval']*row['hz']-1e-10)/row['hz']
   for a,b in zip(row['trace'],row['trace'][1:]):assert abs((b['time']-a['time'])-spacing)<=1/row['hz']+1e-9
  passed('Native-step12s counts and subsequent spacing are recorded explicitly; first-shot inclusion and frame quantization are distinguished from the exact80% ideal rate.')
  for row in rows:
   row['first_shot']=row['trace'][0]
   row['shot_times_seconds']=[shot['time'] for shot in row.pop('trace')]
  browser.close()
finally:server.shutdown();server.server_close()
(args.artifacts/'test-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
