import sys, subprocess, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
CLIPS, LOGO_W, OUT, PLAN = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
plan = json.load(open(PLAN))
W, H, FPS, XF = 1080, 1920, 30, 0.3
SAFE_TOP, SAFE_BOT = 230, 1470
F = '/usr/share/fonts/opentype/inter/'
BLACKF = lambda s: ImageFont.truetype(F + 'InterDisplay-Black.otf', s)
SEMI = lambda s: ImageFont.truetype(F + 'Inter-SemiBold.otf', s)
LIME = (214, 243, 107); GREEN = (24, 52, 37); GOLD = (214, 178, 92)

# 1) base: cortes + velocidad + escalado + transiciones (ffmpeg)
segs = plan['segments']; inputs = []; fc = []
for i, s in enumerate(segs):
    inputs += ['-i', f"{CLIPS}/{s['file']}"]
    fc.append(f"[{i}:v]trim={s['start']}:{s['end']},setpts=(PTS-STARTPTS)/{s['speed']},fps={FPS},"
              f"scale={W}:-2:flags=lanczos,crop={W}:{H},unsharp=5:5:0.8,setsar=1,format=yuv420p[v{i}]")
durs = [(s['end'] - s['start']) / s['speed'] for s in segs]
cur = 'v0'; acc = durs[0]
for i in range(1, len(segs)):
    off = acc - XF
    fc.append(f"[{cur}][v{i}]xfade=transition={segs[i]['trans']}:duration={XF}:offset={off:.3f}[x{i}]")
    cur = f'x{i}'; acc = off + durs[i]
base = OUT + '.base.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(fc), '-map', f'[{cur}]',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', base], check=True)
TOTAL = acc

# 2) capa de textos estilo CapCut, frame a frame
BOLD = lambda s: ImageFont.truetype(F + 'InterDisplay-Bold.otf', s)
WHITE = (255, 255, 255)
def wrap_words(words, f, maxw):
    d = ImageDraw.Draw(Image.new('RGB', (1, 1))); lines, cur = [], []
    for w in words:
        if w[0] == '|': lines.append(cur); cur = []; continue
        t = ' '.join(x for x, _ in cur + [(w[0], 0)])
        if d.textlength(t, font=f) <= maxw or not cur: cur.append(w)
        else: lines.append(cur); cur = [w]
    lines.append(cur); return [l for l in lines if l]
def caption_img(text, label=None, size=74):
    f = BOLD(size); words = [(w.replace('*', ''), '*' in w) for w in text.split()]
    lines = wrap_words(words, f, W - 2 * 110); lh = int(size * 1.16)
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1))); sp = d0.textlength(' ', font=f)
    top = 70 if label else 20
    im = Image.new('RGBA', (W, top + lh * len(lines) + 40), (0, 0, 0, 0))
    txt = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
    if label:
        lf = SEMI(28); lab = '  '.join(label)  # letras espaciadas
        lab = ' '.join(label.upper()); d.text((W // 2, 10), lab, font=lf, fill=GOLD, anchor='ma')
        d.line((W // 2 - 26, 52, W // 2 + 26, 52), fill=GOLD, width=3)
    for k, line in enumerate(lines):
        tw = sum(d0.textlength(w, font=f) for w, _ in line) + sp * (len(line) - 1)
        x = (W - tw) / 2; y = top + k * lh
        for w, hl in line:
            d.text((x, y), w, font=f, fill=GOLD if hl else WHITE); x += d0.textlength(w, font=f) + sp
    shadow = Image.new('RGBA', im.size, (0, 0, 0, 0)); shadow.putalpha(txt.getchannel('A').point(lambda v: int(v * .75)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    im.alpha_composite(shadow, (0, 4)); im.alpha_composite(txt); return im
CAPS = [(c['t0'], c['t1'], caption_img(c['text'], c.get('label'))) for c in plan['captions']]
# velo oscuro suave detrás del texto central
VEIL = Image.new('RGBA', (W, 640), (0, 0, 0, 0))
for y in range(640):
    a_ = int(95 * math.sin(math.pi * y / 640) ** 1.5)
    ImageDraw.Draw(VEIL).line((0, y, W, y), fill=(6, 14, 10, a_))
LG = Image.open(LOGO_W).convert('RGBA'); lw = 160; LG = LG.resize((lw, round(LG.height * lw / LG.width)), Image.LANCZOS)
sh = Image.new('RGBA', LG.size, (0, 0, 0, 0)); sh.putalpha(LG.getchannel('A').point(lambda v: int(v * .6))); sh = sh.filter(ImageFilter.GaussianBlur(5))
def cta_img():
    pad = 52; big = LG.resize((220, round(LG.height * 220 / LG.width)), Image.LANCZOS)
    t1f, bf = BOLD(56), SEMI(34)
    d0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    bw = int(d0.textlength(plan['cta2'], font=bf)) + 2 * 44; bh = 80
    extra = 58 if plan.get('cta3') else 0
    hgt = pad + big.height + 36 + 64 + 34 + bh + extra + pad
    im = Image.new('RGBA', (W, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 0, W - 90, hgt - 1), radius=40, fill=(18, 40, 28, 238))
    d.rounded_rectangle((90, 0, W - 90, hgt - 1), radius=40, outline=(214, 178, 92, 120), width=2)
    im.alpha_composite(big, ((W - big.width) // 2, pad)); y = pad + big.height + 36
    d.text((W // 2, y), plan['cta1'], font=t1f, fill=WHITE, anchor='ma'); y += 64 + 34
    d.rounded_rectangle(((W - bw) // 2, y, (W + bw) // 2, y + bh), radius=bh // 2, fill=GOLD)
    d.text((W // 2, y + bh // 2), plan['cta2'], font=bf, fill=GREEN, anchor='mm')
    if plan.get('cta3'): d.text((W // 2, y + bh + 26), plan['cta3'], font=SEMI(38), fill=WHITE, anchor='ma')
    return im
CTA = cta_img(); CTA_T = TOTAL - plan['cta_secs']

dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', base, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        *(['-i', plan['music']] if plan.get('music') else ['-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo']),
                        '-shortest', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
n = 0; fs = W * H * 3
while True:
    raw = dec.stdout.read(fs)
    if len(raw) < fs: break
    t = n / FPS; n += 1
    fr = Image.frombytes('RGB', (W, H), raw).convert('RGBA')
    fr.alpha_composite(sh, (62, SAFE_TOP + 4)); fr.alpha_composite(LG, (60, SAFE_TOP))
    cy = plan.get('cap_y', 820)
    if any(t0 <= t < t1 for t0, t1, _ in CAPS) and t < CTA_T:
        fr.alpha_composite(VEIL, (0, int(cy - 320)))
    for t0, t1, im in CAPS:
        if t0 <= t < t1:
            pin = min((t - t0) / 0.28, 1); pout = min((t1 - t) / 0.18, 1); p = min(pin, pout)
            e = 1 - (1 - pin) ** 3
            c = im.copy(); c.putalpha(c.getchannel('A').point(lambda v: int(v * p)))
            fr.alpha_composite(c, (0, int(cy - c.height / 2 + (1 - e) * 26)))
    if t >= CTA_T:
        p = min((t - CTA_T) / 0.3, 1); e = 1 - (1 - p) ** 3
        c = CTA.copy(); c.putalpha(c.getchannel('A').point(lambda v: int(v * p)))
        fr.alpha_composite(c, (0, int((SAFE_TOP + SAFE_BOT) / 2 - CTA.height / 2 + 60 + (1 - e) * 50)))
    enc.stdin.write(fr.convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); dec.wait()
print('dur', round(TOTAL, 2), 'frames', n)
