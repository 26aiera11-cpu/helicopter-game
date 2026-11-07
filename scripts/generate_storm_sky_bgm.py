"""Issue28 first-listening trial: two original, reproducible 16-bar PCM scores.

Only Python/NumPy synthesis; no samples, existing scores or music files are read.
Run: python scripts/generate_storm_sky_bgm.py [--output-dir PATH]
"""
import argparse
import hashlib
import json
import wave
from pathlib import Path

import numpy as np

RATE = 22050
BARS = 16
SEEDS = {"stage": 280148, "boss": 280120}
# Independently composed D-minor/G-minor/Bb/A and F-minor/Db/Ab/C progressions.
ROOTS = {
    "stage": [38, 43, 34, 33, 38, 41, 36, 33, 34, 38, 43, 33, 38, 36, 34, 33],
    "boss": [29, 37, 32, 36, 29, 34, 25, 36, 37, 29, 32, 36, 34, 37, 29, 36],
}
STAGE_LINES = [
    [(0,74,.32),(.5,77,.28),(1.25,81,.42),(2,79,.3),(2.75,77,.3),(3.5,76,.32)],
    [(.25,79,.32),(1,82,.35),(1.75,81,.3),(2.5,77,.35),(3.25,74,.4)],
    [(0,77,.4),(.75,81,.3),(1.5,84,.4),(2.25,82,.3),(3,81,.5)],
    [(.5,76,.3),(1.25,73,.3),(2,69,.4),(3,73,.28),(3.5,76,.25)],
]
BOSS_LINES = [
    [(0,65,.52),(1.5,68,.42),(2.75,72,.45)],
    [(.5,73,.42),(2,68,.5),(3.25,65,.3)],
    [(0,68,.4),(1,75,.5),(2.5,72,.42)],
    [(.75,67,.4),(2,64,.5),(3.25,60,.3)],
]


def hz(note):
    return 440 * 2 ** ((note - 69) / 12)


def voice(note, seconds, kind):
    t = np.arange(max(1, round(seconds * RATE))) / RATE
    f = hz(note)
    phase = 2 * np.pi * f * t
    # A few harmonics, rather than discontinuous square/saw waveforms.
    if kind == "bass":
        y = (np.sin(phase) + .22*np.sin(2*phase) + .12*np.sin(3*phase))
        env = np.exp(-t*3.2)
    elif kind == "lead":
        phase += .035*np.sin(2*np.pi*5.2*t)
        y = sum(np.sin(n*phase)*np.sin(np.pi*n*.23)/n for n in range(1, 8))
        env = np.exp(-t*2.8)
    elif kind == "glass":
        y = np.sin(phase + 1.05*np.exp(-t*17)*np.sin(phase*3))
        env = np.exp(-t*12)
    else:  # gentle triangle-like air chords
        y = sum((-1)**k*np.sin((2*k+1)*phase)/(2*k+1)**2 for k in range(4))
        y += .15*np.sin(phase*1.002)
        env = .6 + .4*np.sin(np.pi*np.minimum(1,t/seconds))
    attack = np.minimum(1, t / (.018 if kind == "air" else .003))
    release = np.minimum(1, (seconds-t) / (.07 if kind == "air" else .018))
    return y * env * attack * np.maximum(0, release)


def drum(kind, rng):
    seconds = {"kick":.22, "snare":.13, "hat":.042, "tom":.19}[kind]
    t = np.arange(round(seconds*RATE))/RATE
    noise = rng.uniform(-1,1,len(t))
    if kind == "kick":
        phase = 2*np.pi*(48*t + 90*.026*(1-np.exp(-t/.026)))
        y = np.sin(phase)*np.exp(-t*22)+.07*noise*np.exp(-t*220)
    elif kind == "snare":
        # Band-limited noise keeps the effects/upper lead register clear.
        noise = np.convolve(noise, np.ones(4)/4, mode="same")
        y = (.62*noise+.24*np.sin(2*np.pi*185*t))*np.exp(-t*33)
    elif kind == "hat":
        y = (noise-np.roll(noise,1))*.17*np.exp(-t*85)
    else:
        y = np.sin(2*np.pi*(95*t+45*.04*(1-np.exp(-t/.04))))*np.exp(-t*25)
    return y*np.minimum(1,t/.0015)*np.minimum(1,(seconds-t)/.006)


def compose(kind):
    bpm = 148 if kind == "stage" else 120
    beat = 60/bpm
    length = round(BARS*4*beat*RATE)
    mix = np.zeros(length, dtype=np.float64)
    rng = np.random.default_rng(SEEDS[kind])

    def add(at, signal, gain):
        # Circular placement preserves note/reverb tails at the musical seam.
        indices = (round(at*beat*RATE)+np.arange(len(signal))) % length
        np.add.at(mix, indices, signal*gain)

    def note(at, pitch, duration, instrument, gain):
        add(at, voice(pitch,duration*beat,instrument), gain)

    for bar, root in enumerate(ROOTS[kind]):
        at = bar*4
        major = (kind == "stage" and root in (34,41,36)) or (kind == "boss" and root in (37,32,36))
        third = 4 if major else 3
        chord = [root+24, root+24+third, root+31, root+38]
        for pitch in chord[:3]: note(at,pitch,3.9,"air",.024 if kind=="stage" else .03)
        if kind == "stage":
            bass_hits = [(0,0,.35),(.75,12,.22),(1.5,0,.3),(2.25,7,.22),(3,0,.28),(3.75,12,.18)]
            for pos, interval, dur in bass_hits: note(at+pos,root+interval,dur,"bass",.22)
            # Alternating ascending/descending 16th-note wind, with deliberate gaps.
            pattern = [0,1,2,3,2,1,0,2] if bar%2==0 else [3,2,1,0,1,2,3,1]
            for j in range(16):
                if j in (6,7,14) or (bar%4==1 and j in (3,11)): continue
                note(at+j*.25,chord[pattern[j%8]]+12,.19,"glass",.046)
            line = STAGE_LINES[bar%4]
            # Four-bar call/answer: a lower answer in bars5-8, spacious final turnaround.
            shift = -12 if 4<=bar<8 else 0
            for pos,pitch,dur in line:
                if bar==15 and pos>2: continue
                note(at+pos,pitch+shift,dur,"lead",.089 if bar<12 else .098)
            kicks = [0,1.75,2.5] if bar%2==0 else [0,1.25,2.75]
            snares = [1,3]
            hats = [0,.5,1,1.5,2,2.5,3,3.5]
        else:
            for pos,interval,dur in [(0,0,.65),(1,0,.32),(1.75,12,.24),(2.5,0,.6),(3.5,7,.32)]:
                note(at+pos,root+interval,dur,"bass",.31)
            for pos,pitch,dur in BOSS_LINES[bar%4]: note(at+pos,pitch,dur,"lead",.13)
            # Brief lightning answers alternate with the lead instead of a high-end wall.
            for j in range(3):
                note(at+3+j*.25,chord[(j+bar)%4]+12,.16,"glass",.06 if bar%4==3 else .035)
            kicks = [0,2.25] if bar%2==0 else [0,1.5,2.75]
            snares = [1.5,3.5]
            hats = [.5,1.25,2.5,3.25]
        for pos in kicks: add(at+pos,drum("kick",rng),.3 if kind=="stage" else .39)
        for pos in snares: add(at+pos,drum("snare",rng),.23 if kind=="stage" else .31)
        for pos in hats: add(at+pos,drum("hat",rng),.15)
        if bar%4==3:
            for pos in (3,3.5,3.75): add(at+pos,drum("tom",rng),.13)
    dry = mix.copy()
    for delay, gain in [(.5,.065),(1.25,.035),(2.25,.02)]:
        mix += np.roll(dry,round(delay*beat*RATE))*gain
    mix -= mix.mean()
    mix *= (.085 if kind=="stage" else .099)/np.sqrt(np.mean(mix**2))
    # 1.5ms endpoint taper suppresses discontinuities without a perceptible loop gap.
    edge = round(.0015*RATE)
    mix[:edge] *= np.linspace(0,1,edge)
    mix[-edge:] *= np.linspace(1,0,edge)
    assert np.max(np.abs(mix)) < .95
    return np.rint(mix*32767).astype('<i2'), bpm


def generate(output):
    output.mkdir(parents=True, exist_ok=True)
    rows=[]
    for kind in ["stage","boss"]:
        samples,bpm=compose(kind)
        path=output/f"storm_sky_{kind}.wav"
        with wave.open(str(path),'wb') as out:
            out.setparams((1,2,RATE,0,'NONE','not compressed'));out.writeframes(samples.tobytes())
        x=samples.astype(float)/32768
        rows.append({"file":path.name,"trial":"awaiting user listening approval","bpm":bpm,"key":"D minor" if kind=="stage" else "F minor","bars":BARS,"seed":SEEDS[kind],"rate":RATE,"channels":1,"bits":16,"seconds":len(x)/RATE,"bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"peak":float(abs(x).max()),"rms":float(np.sqrt(np.mean(x*x))),"dc":float(x.mean()),"seam_jump":float(abs(x[0]-x[-1]))})
    assert sum(row['bytes'] for row in rows)<=3500000
    return rows


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parents[1]/'assets/audio')
    print(json.dumps(generate(parser.parse_args().output_dir),ensure_ascii=False,indent=2))
