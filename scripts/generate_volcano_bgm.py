"""Compose the two original, first-trial Volcano loops; no imported music/samples.

Requires Python 3 and NumPy. Run: python scripts/generate_volcano_bgm.py
The fixed scores, oscillators, seeded percussion and circular tails are all here.
--output-dir can render a second copy for byte-for-byte reproducibility checks.
"""
import argparse
import hashlib
import json
import wave
from pathlib import Path
import numpy as np

RATE = 22050
BARS = 16
SEED = 230136
ROOT = Path(__file__).resolve().parents[1]


def frequency(note):
    return 440 * 2 ** ((note - 69) / 12)


def instrument(note, seconds, voice):
    t = np.arange(round(seconds * RATE)) / RATE
    f = frequency(note)
    if voice == 'bass':
        sound = .8*np.sin(2*np.pi*f*t) + .15*np.sin(4*np.pi*f*t) + .05*np.sin(6*np.pi*f*t)
        decay, attack, release = np.exp(-t*1.6), .006, .045
    elif voice == 'pad':
        sound = sum(np.sin(2*np.pi*f*(1+d)*t) for d in [-.0017, .0017]) * .26
        sound += .13*np.sin(4*np.pi*f*t)
        decay, attack, release = np.ones_like(t), .12, .22
    elif voice == 'arp':
        sound = .68*np.sin(2*np.pi*f*t + .7*np.exp(-t*14)*np.sin(4*np.pi*f*t)) + .2*np.sin(4*np.pi*f*t)
        decay, attack, release = np.exp(-t*11), .003, .035
    else:
        # Additive, bandwidth-limited pulse: softer than a discontinuous square.
        sound = np.zeros_like(t)
        for h in range(1, min(13, int(8500/f))+1):
            sound += np.sin(np.pi*h*.37)*np.sin(2*np.pi*f*h*t)/(h**1.35)
        sound *= .65
        decay, attack, release = .5+.5*np.exp(-t*8), .008, .07
    env = np.minimum(1, t/attack) * np.minimum(1, np.maximum(0, (seconds-t)/release))
    return sound * decay * env


def percussion(kind, rng):
    seconds = {'kick':.26, 'snare':.17, 'hat':.055, 'tom':.3}[kind]
    t = np.arange(round(seconds*RATE))/RATE
    noise = rng.uniform(-1,1,len(t))
    if kind == 'kick':
        # Integral of an exponential pitch fall: no external drum sample.
        phase = 2*np.pi*(43*t + 100*.025*(1-np.exp(-t/.025)))
        x = np.sin(phase)*np.exp(-t*19) + .07*noise*np.exp(-t*160)
    elif kind == 'snare':
        colored = noise - np.convolve(noise,np.ones(7)/7,'same')
        x = (.36*colored + .23*np.sin(2*np.pi*178*t))*np.exp(-t*24)
    elif kind == 'hat':
        x = (noise-np.convolve(noise,np.ones(5)/5,'same'))*.23*np.exp(-t*65)
    else:
        phase = 2*np.pi*(67*t+75*.06*(1-np.exp(-t/.06)))
        x = np.sin(phase)*np.exp(-t*13)
    return x*np.minimum(1,t/.002)*np.minimum(1,(seconds-t)/.008)


def compose(boss=False):
    bpm = 114 if boss else 136
    beat = 60/bpm
    count = round(BARS*4*beat*RATE)
    mix = np.zeros(count)
    rng = np.random.default_rng(SEED+int(boss))
    def put(sample, at, gain):
        start = round(at*beat*RATE) % count
        tail = min(len(sample),count-start)
        mix[start:start+tail] += sample[:tail]*gain
        if tail<len(sample):mix[:len(sample)-tail] += sample[tail:]*gain
    def note(pitch, at, length, gain, voice):
        put(instrument(pitch,length*beat,voice),at,gain)
    def drum(kind, at, gain):
        put(percussion(kind,rng),at,gain)

    if not boss:
        # E minor: four 4-bar phrases; B dominant provides a chromatic turnaround.
        roots = [40,40,36,35, 40,43,45,35, 40,36,45,35, 40,43,36,35]
        motifs = [
            [(0,76,.5),(.75,79,.25),(1.5,78,.5),(2.5,71,.5),(3.25,74,.35)],
            [(0,71,.5),(1,76,.5),(2.25,79,.25),(3,78,.5)],
            [(.5,76,.5),(1.5,74,.5),(2.5,72,.5),(3.5,71,.25)],
            [(0,75,.5),(1.5,78,.5),(2.5,74,.5),(3.5,75,.25)],
        ]
        for bar,root in enumerate(roots):
            base=bar*4; dominant=root==35
            chord=[0,4 if dominant else 3,7,10 if dominant else 14]
            for n in chord[:3]:note(root+12+n,base,3.95,.075 if bar//4!=2 else .055,'pad')
            for i in range(8):note(root+(12 if i in [3,7] else 0),base+i*.5,.37,.30 if i%2==0 else .23,'bass')
            # Leave the fourth phrase's first half open for a lighter texture.
            arp_steps=[0,1,2,3,4,5,6,7] if bar//4!=2 else [0,2,4,6]
            for i in arp_steps:note(root+24+chord[(i+bar)%4],base+i*.5+.25,.32,.095,'arp')
            for onset,pitch,length in motifs[bar%4]:
                note(pitch+(0 if bar<12 else -12),base+onset,length,.14 if bar//4!=1 else .16,'lead')
            for pos in [0,1.5,2,3.5]:drum('kick',base+pos,.42 if pos in [0,2] else .25)
            for pos in [1,3]:drum('snare',base+pos,.30)
            for i in range(8):drum('hat',base+i*.5,.19 if i%2 else .12)
            if bar%4==3:
                for pos in [3.25,3.75]:drum('tom',base+pos,.18)
    else:
        # C minor: spacious low ostinato, broad chords and an answering warning lead.
        roots=[36,36,32,31, 36,39,29,31, 32,29,36,31, 36,32,29,31]
        motifs=[[(.5,67,.75),(2.5,63,.65)],[(1,60,.9),(3,62,.6)],
                [(0,68,.7),(2,67,.7)],[(.5,62,.6),(2,59,.6),(3.25,62,.4)]]
        for bar,root in enumerate(roots):
            base=bar*4;dominant=root==31;chord=[0,4 if dominant else 3,7]
            for n in chord:note(root+12+n,base,4.15,.13,'pad')
            for onset,length in [(0,.8),(1,.45),(1.75,.3),(2,.8),(3,.45),(3.5,.3)]:
                note(root,base+onset,length,.43 if onset in [0,2] else .30,'bass')
            # A small rising low-register answer adds tension, rather than dense soloing.
            for i in range(4):note(root+12+chord[i%3],base+i+.5,.48,.10,'arp')
            for onset,pitch,length in motifs[bar%4]:note(pitch,base+onset,length,.15,'lead')
            for pos in [0,2,2.75]:drum('kick',base+pos,.54 if pos in [0,2] else .22)
            for pos in [1,3]:drum('snare',base+pos,.25)
            for pos in [.5,1.5,2.5,3.5]:drum('hat',base+pos,.15)
            if bar%4==3:
                for pos in [2.5,3,3.5]:drum('tom',base+pos,.25)
    # Circular delay and room tails continue through the file boundary (no blank outro).
    dry=mix.copy()
    for beats,gain in [(.375,.085),(.75,.05),(1.5,.025)]:mix+=np.roll(dry,round(beats*beat*RATE))*gain
    mix-=mix.mean()
    mix*= (.103 if boss else .087)/np.sqrt(np.mean(mix*mix))
    # Only 1.5ms at either edge; removes sample jumps without a perceptible loop gap.
    edge=round(.0015*RATE);fade=np.sin(np.linspace(0,np.pi/2,edge))**2
    mix[:edge]*=fade;mix[-edge:]*=fade[::-1]
    assert np.max(np.abs(mix))<.95
    pcm=np.rint(mix*32767).astype('<i2')
    return pcm, {'bpm':bpm,'bars':BARS,'meter':'4/4','key':'C minor' if boss else 'E minor','seed':SEED+int(boss)}


def generate(output_dir):
    output_dir.mkdir(parents=True,exist_ok=True)
    rows=[]
    for boss in [False,True]:
        pcm,info=compose(boss);path=output_dir/('volcano_boss.wav' if boss else 'volcano_stage.wav')
        with wave.open(str(path),'wb') as file:
            file.setnchannels(1);file.setsampwidth(2);file.setframerate(RATE);file.writeframes(pcm.tobytes())
        x=pcm.astype(np.float64)/32768
        rows.append({**info,'file':path.name,'sample_rate':RATE,'channels':1,'pcm_bits':16,'frames':len(x),'seconds':len(x)/RATE,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'peak':float(np.max(np.abs(x))),'rms':float(np.sqrt(np.mean(x*x))),'dc_offset':float(x.mean()),'seam_jump':float(abs(x[0]-x[-1]))})
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'assets/audio');args=parser.parse_args()
    print(json.dumps(generate(args.output_dir),ensure_ascii=False,indent=2))
