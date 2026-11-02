# Pista original libre de derechos: house suave y luminosa, 116 BPM
import sys, numpy as np, subprocess
OUT, SECS = sys.argv[1], float(sys.argv[2]); BPM = float(sys.argv[3]) if len(sys.argv) > 3 else 116
SR = 44100; beat = 60 / BPM; N = int(SR * (SECS + 1)); L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)
def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[:j - i] * gain; L[i:j] += s * (1 - max(pan, 0)); R[i:j] += s * (1 + min(pan, 0))
def env(n, a=0.005, d=0.3):
    t = np.arange(n) / SR; e = np.minimum(t / a, 1) * np.exp(-t / d); return e
def kick():
    n = int(.45 * SR); t = np.arange(n) / SR; f = 48 + 90 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.9
def hat(op=False):
    n = int((.18 if op else .05) * SR); x = rng.standard_normal(n)
    x = np.diff(np.concatenate([[0], x])); return x * env(n, .001, .07 if op else .015) * .06
def clap():
    n = int(.25 * SR); x = rng.standard_normal(n); x = np.convolve(x, [1, -0.9], 'same')
    e = sum(np.roll(env(n, .001, .012), int(k * .011 * SR)) for k in range(3)) + env(n, .001, .09)
    return x * e * .08
def note(freq, dur, kind='pluck'):
    n = int(dur * SR); t = np.arange(n) / SR
    if kind == 'pluck':
        s = sum(np.sin(2 * np.pi * freq * h * t + h) / h ** 1.6 for h in range(1, 7))
        return s * env(n, .004, .35) * .09
    if kind == 'pad':
        s = sum(np.sin(2 * np.pi * freq * (1 + d) * t) for d in (-.004, 0, .005))
        a = np.minimum(t / .25, 1) * np.minimum((dur - t) / .3, 1).clip(0, 1); return s * a * .022
    if kind == 'bass':
        s = np.sin(2 * np.pi * freq * t) + .3 * np.sin(4 * np.pi * freq * t)
        return s * env(n, .006, .22) * .32
def hz(m): return 440 * 2 ** ((m - 69) / 12)
# progresión luminosa: Fmaj7 - Am7 - Dm9 - Bbmaj7 (en notas MIDI)
prog = [[53, 57, 60, 64], [57, 60, 64, 67], [50, 57, 60, 64], [46, 53, 57, 62]]
bass = [41, 45, 38, 46]
bars = int(SECS / (4 * beat)) + 2
for b in range(bars):
    t0 = b * 4 * beat; ch = prog[b % 4]
    for c in ch: add(note(hz(c + 12), 4 * beat, 'pad'), t0, pan=rng.uniform(-.4, .4))
    for k in range(8):  # arpegio/plucks en corcheas
        if k in (0, 3, 5, 6):
            add(note(hz(ch[(k * 2) % 4] + 24), beat * 0.9, 'pluck'), t0 + k * beat / 2, pan=(-.35 if k % 2 else .35))
    for q in range(4):
        tq = t0 + q * beat
        if b > 0 or q > 1: add(kick(), tq)
        add(hat(), tq + beat / 2, pan=.2); add(hat(), tq + beat * .75, pan=-.2, gain=.6)
        if q in (1, 3) and b > 0: add(clap(), tq)
        add(note(hz(bass[b % 4]), beat * .45, 'bass'), tq + beat / 2)
# mezcla: compresión suave + fundidos
mix = np.stack([L, R], 1)[: int(SECS * SR)]
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
fi = int(.4 * SR); fo = int(1.4 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
mix = mix / np.abs(mix).max() * 0.89
pcm = (mix * 32767).astype('<i2').tobytes()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', '2', '-i', '-', '-c:a', 'pcm_s16le', OUT], input=pcm, check=True)
