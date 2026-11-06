"""Reproduce the Issue26 manifest and source-cell atlas exports from supplied files."""
from pathlib import Path
from PIL import Image
import shutil,json,hashlib,argparse,zipfile,tempfile
parser=argparse.ArgumentParser(description='Pack supplied approved PNGs losslessly; no generated replacement poses.')
parser.add_argument('--source-zip',type=Path,required=True)
parser.add_argument('--boss-sprite',type=Path,required=True,help='Already separated RGBA boss sprite; this script does not generate/redesign it.')
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent)
args=parser.parse_args();root=args.output;root.mkdir(parents=True,exist_ok=True)
temp=tempfile.TemporaryDirectory(prefix='storm-source-');src=Path(temp.name)
with zipfile.ZipFile(args.source_zip) as archive:
 assert archive.testzip() is None
 for name in ['storm_sky_background_1920x864.png','cloud_bean.png','lightning_bat.png','tornado_spirit.png','storm_jellyfish.png','storm_overlord_visual_reference.png','storm_overlord_attack_reference.png','README.md']:
  (src/name).write_bytes(archive.read('storm_sky_assets/'+name))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['storm_sky_background_1920x864.png','cloud_bean.png','lightning_bat.png','tornado_spirit.png','storm_jellyfish.png']:
 shutil.copy2(src/n,root/n)
(root/'references').mkdir(exist_ok=True)
for n in ['storm_overlord_visual_reference.png','storm_overlord_attack_reference.png','README.md']:shutil.copy2(src/n,root/'references'/n)
if args.boss_sprite.resolve()!=(root/'storm_overlord.png').resolve():shutil.copy2(args.boss_sprite,root/'storm_overlord.png')
rows=[]
keyframes={'idle':[(1,0,1),(1.025,0,1),(1,0,1)],'move':[(1,-.045,1),(1.02,0,1),(1,.045,1),(1,0,1)],'attack':[(1,0,1),(1.07,0,1),(1,0,1)],'hit':[(.96,-.035,.65),(1,.035,1)],'defeat':[(1,0,1),(1.06,.10,.8),(.85,.22,.4),(.6,.3,0)]}
for ident,name,width,kind in [('cloud_bean','구름콩',42,'normal'),('lightning_bat','번개 박쥐',52,'normal'),('tornado_spirit','회오리 정령',44,'normal'),('storm_jellyfish','폭풍 해파리',48,'normal'),('storm_overlord','폭풍의 지배자',144,'boss')]:
 p=root/(ident+'.png');im=Image.open(p).convert('RGBA');alpha=im.getchannel('A');bounds=alpha.point(lambda v:255 if v>=16 else 0).getbbox();assert alpha.getextrema()[0]==0 and bounds
 w,h=im.size
 rows.append({'id':ident,'name_ko':name,'kind':kind,'base':p.name,'atlas':p.name,'sha256':sha(p),'pixels':[w,h],'content_bounds_px':list(bounds),'pivot_px':[w/2,h/2],'render_width':width,'has_propeller':False,'animations':{k:{'frame_duration_ms':100 if k!='defeat' else 160,'loop':k in ['idle','move'],'frames':[{'rect_px':[0,0,w,h],'pivot_px':[w/2,h/2],'scale':s,'rotation':r,'alpha':a} for s,r,a in frames]} for k,frames in keyframes.items()}})
manifest={'schema_version':1,'region':'storm_sky','issue':26,'source_zip_sha256':sha(args.source_zip),'background':{'path':'storm_sky_background_1920x864.png','sha256':sha(root/'storm_sky_background_1920x864.png'),'pixels':[1920,864],'render_mode':'cover','same_all_five_phases':True},'animation_method':'Lossless single-cell source atlases with manifest transform keyframes; no invented hand-drawn poses. Base assets stay exact. Boss isolated from approved reference with imagegen.','monsters':rows}
(root/'asset_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print([(s['id'],s['pixels'],s['content_bounds_px']) for s in rows])

temp.cleanup()
