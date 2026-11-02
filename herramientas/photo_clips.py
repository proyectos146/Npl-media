# Convierte fotos en clips verticales 1080x1920 (ventana 4:5 nítida + fondo desenfocado + zoom lento)
import sys, json, math, subprocess
from PIL import Image, ImageFilter, ImageOps, ImageDraw
SRC, OUTDIR, SPEC = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS, WIN_Y, WIN_H = 1080, 1920, 30, 285, 1350
def load(n): return ImageOps.exif_transpose(Image.open(f'{SRC}/{n}')).convert('RGB')
def crop(img, w, h, z=1, cx=.5, cy=.5):
    r = max(w / img.width, h / img.height) * z; cw, ch = w / r, h / r
    x0 = (img.width - cw) * cx; y0 = (img.height - ch) * cy
    return img.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
def bg(img):
    b = crop(img, W // 4, H // 4).filter(ImageFilter.GaussianBlur(9)).resize((W, H))
    return Image.blend(b, Image.new('RGB', (W, H), (8, 18, 12)), .5)
ease = lambda t: .5 - .5 * math.cos(math.pi * min(max(t, 0), 1))
def write(name, frames_fn, dur):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '15', '-pix_fmt', 'yuv420p', f'{OUTDIR}/{name}'], stdin=subprocess.PIPE)
    n = int(dur * FPS)
    for i in range(n): p.stdin.write(frames_fn(i / FPS, dur).tobytes())
    p.stdin.close(); p.wait()
for c in json.load(open(SPEC)):
    if c.get('wipe'):
        A, B = load(c['a']), load(c['b']); bgA, bgB = bg(A), bg(B)
        def fr(t, d, A=A, B=B, bgA=bgA, bgB=bgB, c=c):
            p = ease((t - c.get('hold', .3)) / c.get('wipe_t', 1.0)); x = int(W * p)
            f = (bgA if p < .5 else bgB).copy()
            win = crop(A, W, WIN_H, 1.06, .5, c.get('acy', .5)); wb = crop(B, W, WIN_H, 1.0 + .05 * t / d, .5, c.get('bcy', .5))
            if x > 0: win.paste(wb.crop((0, 0, x, WIN_H)), (0, 0))
            if 0 < x < W: ImageDraw.Draw(win).rectangle((x - 3, 0, x + 3, WIN_H), fill=(255, 255, 255))
            f.paste(win, (0, WIN_Y)); return f
        write(c['out'], fr, c['dur'])
    else:
        img = load(c['img']); b = bg(img); z0, z1 = c.get('zoom', [1.0, 1.08])
        def fr(t, d, img=img, b=b, z0=z0, z1=z1, c=c):
            f = b.copy(); f.paste(crop(img, W, WIN_H, z0 + (z1 - z0) * t / d, c.get('cx', .5), c.get('cy', .5)), (0, WIN_Y)); return f
        write(c['out'], fr, c['dur'])
print('ok')
