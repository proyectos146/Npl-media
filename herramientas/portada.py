import sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
spec = json.load(open(sys.argv[1])); LOGO = Image.open(sys.argv[2]).convert('RGBA'); OUT = sys.argv[3]
W, H = 1080, 1920; GOLD = (214, 178, 92); WHITE = (255, 255, 255)
F = '/usr/share/fonts/opentype/inter/'
BOLD = lambda s: ImageFont.truetype(F + 'InterDisplay-Bold.otf', s); SEMI = lambda s: ImageFont.truetype(F + 'Inter-SemiBold.otf', s)
D0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))
def load(p): return ImageOps.exif_transpose(Image.open(p)).convert('RGB')
def cover(img, w, h, cy=.5):
    r = max(w / img.width, h / img.height); im = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2; y = int((im.height - h) * cy); return im.crop((x, y, x + w, y + h))
c = Image.new('RGB', (W, H))
c.paste(cover(load(spec['a']), W, H // 2, spec.get('acy', .5)), (0, 0)); c.paste(cover(load(spec['b']), W, H - H // 2, spec.get('bcy', .5)), (0, H // 2))
c = c.convert('RGBA')
band = Image.new('RGBA', (W, 560), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
for y in range(560):
    a = int(200 * (1 - abs(y - 280) / 280) ** 0.8); bd.line((0, y, W, y), fill=(6, 16, 11, a))
c.alpha_composite(band, (0, H // 2 - 280))
ImageDraw.Draw(c).line((0, H // 2, W, H // 2), fill=(255, 255, 255, 90), width=2)
txt = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(txt)
def tag(x, y, t):
    t = ' '.join(t.upper()); f = SEMI(24); tw = D0.textlength(t, font=f)
    d.rounded_rectangle((x - tw / 2 - 22, y, x + tw / 2 + 22, y + 48), radius=24, fill=(6, 16, 11, 170)); d.text((x, y + 24), t, font=f, fill=WHITE, anchor='mm')
tag(W // 2, 300, spec.get('tag_a', 'Antes')); tag(W // 2, H - 360, spec.get('tag_b', 'Después'))
lab = ' '.join(spec['label'].upper()); d.text((W // 2, H // 2 - 170), lab, font=SEMI(28), fill=GOLD, anchor='mm')
d.line((W // 2 - 30, H // 2 - 140, W // 2 + 30, H // 2 - 140), fill=GOLD, width=3)
f = BOLD(96); y = H // 2 - 110
for line in spec['title']:
    words = line.split(); sp = D0.textlength(' ', font=f)
    tw = sum(D0.textlength(w.replace('*', ''), font=f) for w in words) + sp * (len(words) - 1); x = (W - tw) / 2
    for w in words:
        d.text((x, y), w.replace('*', ''), font=f, fill=GOLD if '*' in w else WHITE); x += D0.textlength(w.replace('*', ''), font=f) + sp
    y += 108
d.text((W // 2, y + 30), spec['sub'], font=SEMI(34), fill=(235, 235, 228), anchor='ma')
sh = Image.new('RGBA', txt.size, (0, 0, 0, 0)); sh.putalpha(txt.getchannel('A').point(lambda v: int(v * .7)))
c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)), (0, 4)); c.alpha_composite(txt)
lw = 230; l = LOGO.resize((lw, round(LOGO.height * lw / LOGO.width)), Image.LANCZOS); c.alpha_composite(l, ((W - lw) // 2, 120))
c.convert('RGB').save(OUT, quality=93)
# vista de la cuadrícula del perfil (recorte central 3:4)
g = c.convert('RGB').crop((0, (H - 1440) // 2, W, (H + 1440) // 2)).resize((300, 400)); g.save(OUT.replace('.jpg', '_grid.jpg'))
