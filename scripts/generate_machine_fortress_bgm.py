"""Issue37 original 16-bar listening drafts; Python/NumPy only, no sample inputs.

Reproduce: python scripts/generate_machine_fortress_bgm.py --output-dir PATH
Scores, synthesis and seeded noise are local to this file. No older song is read.
"""
import argparse
import hashlib
import json
import wave
from pathlib import Path
import numpy as np

RATE = 22050
BARS = 16
SEEDS = {'stage': 370132, 'boss': 370152}
TEMPOS = {'stage': 132, 'boss': 152}
# New A-natural-minor and E-natural-minor arrangements (MIDI roots/triad thirds).
HARMONY = {
 'stage': [(45,3),(48,4),(41,4),(43,4),(45,3),(38,3),(41,4),(43,4),
           (48,4),(43,4),(38,3),(40,3),(41,4),(43,4),(45,3),(40,3)],
 'boss': [(40,3),(40,3),(36,4),(35,3),(40,3),(38,4),(36,4),(35,3),
          (33,3),(36,4),(38,4),(35,3),(40,3),(43,4),(36,4),(35,3)]}
# Four different four-bar phrases, not transpositions of the older region scores.
STAGE = [
 [(0,76,.28),(.75,81,.26),(1.5,79,.3),(2,76,.24),(2.5,72,.24),(3.25,74,.42)],
 [(0,79,.3),(.5,76,.26),(1.25,72,.36),(2.25,74,.24),(3,76,.5)],
 [(.25,77,.32),(1,81,.26),(1.75,79,.24),(2.5,77,.32),(3.25,72,.4)],
 [(0,74,.24),(.75,79,.26),(1.5,77,.24),(2.25,74,.3),(3,71,.3),(3.5,72,.3)],
 [(0,69,.3),(.75,72,.3),(1.5,76,.28),(2.5,74,.28),(3.25,72,.45)],
 [(.25,74,.3),(1,77,.27),(1.75,76,.25),(2.5,74,.3),(3.25,69,.38)],
 [(0,72,.35),(1,77,.26),(1.5,76,.25),(2.25,72,.3),(3,69,.52)],
 [(0,71,.28),(.75,74,.26),(1.5,79,.3),(2.5,77,.25),(3.25,74,.38)],
 [(0,84,.28),(.5,79,.25),(1.25,76,.3),(2,79,.3),(3,81,.55)],
 [(.25,79,.3),(1,83,.25),(1.75,81,.25),(2.5,79,.3),(3.25,74,.4)],
 [(0,81,.25),(.75,77,.3),(1.5,74,.3),(2.5,76,.25),(3.25,77,.4)],
 [(0,79,.3),(1,76,.3),(1.75,71,.3),(2.75,74,.3),(3.5,76,.3)],
 [(0,81,.33),(.75,77,.26),(1.5,72,.26),(2.25,76,.3),(3,77,.5)],
 [(.25,79,.3),(1,74,.26),(1.75,71,.26),(2.5,74,.3),(3.25,79,.4)],
 [(0,81,.3),(.5,76,.25),(1.25,72,.32),(2,74,.3),(3,76,.5)],
 [(0,76,.3),(.75,71,.25),(1.5,74,.26),(2.25,71,.28),(3.25,76,.9)] ]
BOSS = [
 [(0,76,.32),(.5,83,.24),(1.5,79,.42),(3,76,.5)],
 [(.25,83,.24),(1,79,.32),(2,76,.3),(3,74,.5)],
 [(0,79,.32),(.75,76,.24),(1.5,72,.45),(3,76,.42)],
 [(0,78,.3),(.5,74,.25),(1.5,71,.4),(2.75,74,.3),(3.5,78,.3)],
 [(0,76,.4),(1,83,.32),(2.25,79,.3),(3.25,76,.35)],
 [(.25,81,.3),(1,78,.3),(2,74,.45),(3.25,78,.35)],
 [(0,79,.32),(.75,76,.26),(1.5,72,.4),(2.75,76,.3)],
 [(0,78,.3),(1,74,.3),(2,71,.3),(3,74,.7)],
 [(0,81,.3),(.5,76,.24),(1.5,72,.4),(2.75,76,.35)],
 [(0,79,.3),(.5,84,.24),(1.5,79,.3),(2.5,76,.3),(3.25,72,.35)],
 [(0,81,.3),(.75,78,.3),(1.5,74,.4),(3,78,.5)],
 [(.25,78,.28),(1,74,.26),(1.75,71,.3),(2.5,74,.3),(3.25,78,.35)],
 [(0,83,.3),(.5,79,.25),(1.5,76,.4),(2.75,79,.3)],
 [(0,83,.3),(.75,79,.3),(1.5,74,.3),(2.5,79,.3),(3.25,83,.35)],
 [(0,84,.3),(.5,79,.24),(1.5,76,.4),(3,72,.5)],
 [(0,78,.3),(.75,74,.3),(1.5,71,.4),(2.5,74,.3),(3.25,71,.95)] ]

def tone(pitch, seconds, kind):
 t=np.arange(max(1,round(seconds*RATE)))/RATE
 f=440*2**((pitch-69)/12);p=2*np.pi*f*t
 if kind=='bass':
  y=np.tanh(1.15*(np.sin(p)+.2*np.sin(2*p)+.1*np.sin(3*p)));env=np.exp(-t*4.3)
 elif kind=='lead':
  p+=.018*np.sin(2*np.pi*4.7*t)
  y=sum(np.sin(n*p)*np.sin(n*np.pi*.32)/n for n in range(1,8));env=np.exp(-t*3.8)
 elif kind=='alarm':
  y=np.sin(p)+.24*np.sin(2*p)+.11*np.sin(3*p);env=np.exp(-t*3.5)
 elif kind=='metal':
  y=np.sin(p+.65*np.exp(-t*25)*np.sin(2.76*p))+.12*np.sin(4.13*p);env=np.exp(-t*18)
 else:
  y=np.sin(p)+.1*np.sin(3*p);env=np.sin(np.pi*np.minimum(1,t/seconds))**.7
 attack=np.minimum(1,t/(.016 if kind=='pad' else .003))
 release=np.minimum(1,(seconds-t)/(.08 if kind=='pad' else .02))
 return y*env*attack*np.maximum(0,release)

def drum(kind,rng):
 seconds={'kick':.19,'snare':.12,'tick':.035,'clang':.16,'tom':.17}[kind]
 t=np.arange(round(seconds*RATE))/RATE;n=rng.uniform(-1,1,len(t))
 if kind=='kick':
  y=np.sin(2*np.pi*(46*t+78*.022*(1-np.exp(-t/.022))))*np.exp(-t*24)+n*.04*np.exp(-t*160)
 elif kind=='snare':
  n=np.convolve(n,np.ones(5)/5,mode='same');y=(.65*n+.18*np.sin(2*np.pi*168*t))*np.exp(-t*36)
 elif kind=='tick':
  y=(.18*(n-np.roll(n,1))+.16*np.sin(2*np.pi*1450*t))*np.exp(-t*115)
 elif kind=='clang':
  y=sum(g*np.sin(2*np.pi*f*t) for f,g in [(620,.45),(1013,.24),(1487,.12)])*np.exp(-t*28)
 else:
  y=np.sin(2*np.pi*(82*t+48*.035*(1-np.exp(-t/.035))))*np.exp(-t*26)
 return y*np.minimum(1,t/.0015)*np.minimum(1,(seconds-t)/.006)

def compose(kind):
 bpm=TEMPOS[kind];beat=60/bpm;length=round(BARS*4*beat*RATE)
 mix=np.zeros(length,dtype=np.float64);rng=np.random.default_rng(SEEDS[kind])
 def add(at,signal,gain):np.add.at(mix,(round(at*beat*RATE)+np.arange(len(signal)))%length,signal*gain)
 def note(at,pitch,dur,voice,gain):add(at,tone(pitch,dur*beat,voice),gain)
 for bar,(root,third) in enumerate(HARMONY[kind]):
  at=4*bar;chord=[root,root+third,root+7]
  for pitch in chord:note(at+.125,pitch+24,3.4,'pad',.016 if kind=='stage' else .019)
  if kind=='stage':
   for j,interval in enumerate([0,12,0,7,0,12,7,12]):note(at+j*.5,root+interval,.26,'bass',.21 if j%2==0 else .15)
   for pos,pitch,dur in STAGE[bar]:note(at+pos,pitch,dur,'lead',.10 if bar<8 else .105)
   for j in [1,4,7,9,12,15]:note(at+j*.25,chord[(j+bar)%3]+36,.16,'metal',.04)
   kicks=[0,1,2,3];snares=[1,3];ticks=[.25,.5,.75,1.25,1.5,2.25,2.5,2.75,3.25,3.5]
  else:
   for pos,interval,dur in [(0,0,.34),(.5,0,.25),(1.25,12,.22),(2,0,.42),(2.75,7,.25),(3.5,0,.28)]:note(at+pos,root+interval,dur,'bass',.29)
   for pos,pitch,dur in BOSS[bar]:note(at+pos,pitch,dur,'alarm',.098)
   for j in ([2,5,10,13] if bar<8 else [2,5,7,10,13,15]):note(at+j*.25,chord[(j+bar)%3]+36,.15,'metal',.039)
   kicks=[0,.75,2,2.5] if bar%2==0 else [0,1.5,2.25];snares=[1,3];ticks=[.25,.5,1.25,1.75,2.25,2.75,3.25,3.75]
  for pos in kicks:add(at+pos,drum('kick',rng),.28 if kind=='stage' else .37)
  for pos in snares:add(at+pos,drum('snare',rng),.20 if kind=='stage' else .28)
  for pos in ticks:add(at+pos,drum('tick',rng),.12 if kind=='stage' else .13)
  for pos in [.5,2.5]:add(at+pos,drum('clang',rng),.075 if kind=='stage' else .095)
  if bar%4==3:
   for pos in [3.25,3.5,3.75]:add(at+pos,drum('tom',rng),.105 if kind=='stage' else .14)
 dry=mix.copy()
 for delay,gain in [(.375,.05),(.875,.025),(2.125,.012)]:mix+=np.roll(dry,round(delay*beat*RATE))*gain
 mix-=mix.mean();mix*=({'stage':.075,'boss':.096}[kind])/np.sqrt(np.mean(mix**2))
 edge=round(.0015*RATE);mix[:edge]*=np.linspace(0,1,edge);mix[-edge:]*=np.linspace(1,0,edge)
 assert np.max(np.abs(mix))<.90
 return np.rint(mix*32767).astype('<i2'),bpm

def generate(output):
 output.mkdir(parents=True,exist_ok=True);rows=[]
 for kind in ['stage','boss']:
  samples,bpm=compose(kind);p=output/f'machine_fortress_{kind}.wav'
  with wave.open(str(p),'wb') as w:w.setparams((1,2,RATE,0,'NONE','not compressed'));w.writeframes(samples.tobytes())
  x=samples.astype(float)/32768
  rows.append({'file':p.name,'title':'기어 시티' if kind=='stage' else '기가코어 경보','status':'1차 시안 / 사용자 청취 승인 대기','bpm':bpm,'key':'A minor' if kind=='stage' else 'E minor','bars':BARS,'meter':'4/4','seed':SEEDS[kind],'rate':RATE,'channels':1,'bits':16,'seconds':len(x)/RATE,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'peak':float(np.max(np.abs(x))),'rms':float(np.sqrt(np.mean(x*x))),'dc':float(x.mean()),'seam_jump':float(abs(x[0]-x[-1]))})
 assert sum(r['bytes'] for r in rows)<=3500000
 return rows

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parents[1]/'assets/audio')
 print(json.dumps(generate(p.parse_args().output_dir),ensure_ascii=False,indent=2))
