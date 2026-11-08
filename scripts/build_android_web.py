"""Create offline app assets without editing index.html or any game asset."""
import base64,hashlib,json,re,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'android-web'
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir()
(OUT/'embedded').mkdir(exist_ok=True)
original=(ROOT/'index.html').read_text()
embedded={}
extensions={'image/png':'png','image/jpeg':'jpg','image/webp':'webp','audio/wav':'wav','audio/mpeg':'mp3'}
def externalize(match):
 mime,encoded=match.groups();data=base64.b64decode(encoded,validate=True)
 if mime not in extensions:raise ValueError('Unsupported embedded media: '+mime)
 digest=hashlib.sha256(data).hexdigest();name=f'embedded/{digest}.{extensions[mime]}'
 (OUT/name).write_bytes(data);embedded[name]={'sha256':digest,'bytes':len(data),'mime':mime}
 return name
page=re.sub(r'data:([^;\s]+);base64,([A-Za-z0-9+/=]+)',externalize,original)
# Native bridge is served by Capacitor; the copied core also permits web smoke tests.
page=page.replace('<meta name="viewport"', '<script src="app-shell/capacitor-core.js"></script><script src="app-shell/bootstrap.js"></script><meta name="viewport"',1)
before,after=page.rsplit('</html>',1)
page=before+'<link rel="stylesheet" href="app-shell/android.css"><script src="app-shell/android.js"></script></html>'+after
(OUT/'index.html').write_text(page)
shutil.copytree(ROOT/'assets',OUT/'assets',dirs_exist_ok=True)
shutil.copytree(ROOT/'app-shell',OUT/'app-shell',dirs_exist_ok=True)
shutil.copy2(ROOT/'node_modules/@capacitor/core/dist/capacitor.js',OUT/'app-shell/capacitor-core.js')
sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'assets').rglob('*')) if p.is_file()}
sources['index.html']=hashlib.sha256(original.encode()).hexdigest()
receipt={'original_index_bytes':len(original.encode()),'app_index_bytes':len(page.encode()),'embedded_files':embedded,'source_sha256':sources,'web_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'source_game_modified':False}
(OUT/'build-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['embedded_files','source_sha256']},indent=2))
