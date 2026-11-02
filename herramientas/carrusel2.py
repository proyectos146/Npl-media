import sys, json
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
SRC, OUT, LOGO_W, PLAN = sys.argv[1:5]
plan = json.load(open(PLAN))
W, H = 1080, 1350
GOLD = (214, 178, 92); GREEN = (18, 40, 28); WHITE = (255, 255, 255)
F = '/usr/share/fonts/opentype/inter/'
BOLD = lambda s: ImageFont.truetype(F + 'InterDisplay-Bold.otf', s)
MED = lambda s: ImageFont.truetype(F + 'Inter-Medium.otf', s)
SEMI = lambda s: ImageFont.truetype(F + 'Inter-SemiBold.otf', s)
LG = Image.open(LOGO_W).convert('RGBA')
D0 = ImageDraw.Draw(Image.new('RGB', (1, 1)))

def load(n): return ImageOps.exif_transpose(Image.open(f'{SRC}/{n}')).convert('RGB')
def cover(img, w, h, cy=.5):
    r = max(w / img.width, h / img.height); im = img.resize((round(img.width * r), round(img.height * r)), Image.LANCZOS)
    x = (im.width - w) // 2; y = int((im.height - h) * cy); return im.crop((x, y, x + w, y + h))
def shade(c, y0, top=0, bot=225):
    h = H - y0; m = Image.new('L', (1, h))
    for y in range(h): m.putpixel((0, y), int(top + (bot - top) * (y / h) ** 1.5))
    c.paste(Image.new('RGB', (W, h), (6, 16, 11)), (0, y0), m.resize((W, h)))
def topshade(c):
    m = Image.new('L', (1, 220)); [m.putpixel((0, y), int(130 * (1 - y / 220) ** 1.4)) for y in range(220)]
    c.paste(Image.new('RGB', (W, 220), (6, 16, 11)), (0, 0), m.resize((W, 220)))
def shadowed(c, layer, blur=8, op=.7):
    sh = Image.new('RGBA', layer.size, (0, 0, 0, 0)); sh.putalpha(layer.getchannel('A').point(lambda v: int(v * op)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), (0, 3)); c.alpha_composite(layer)
def mark(c, w, pos):
    l = LG.resize((w, round(LG.height * w / LG.width)), Image.LANCZOS)
    layer = Image.new('RGBA', c.size, (0, 0, 0, 0)); layer.alpha_composite(l, pos); shadowed(c, layer, 5, .55)
def rich_lines(text, f, maxw):
    lines, cur = [], []
    for w in text.split():
        if w == '|': lines.append(cur); cur = []; continue
        t = ' '.join(x.strip('*') for x in cur + [w])
        if D0.textlength(t, font=f) <= maxw or not cur: cur.append(w)
        else: lines.append(cur); cur = [w]
    lines.append(cur); return [l for l in lines if l]
def draw_rich(d, x, y, line, f):
    sp = D0.textlength(' ', font=f)
    for w in line:
        hl = w.startswith('*'); w = w.strip('*')
        d.text((x, y), w, font=f, fill=GOLD if hl else WHITE); x += D0.textlength(w, font=f) + sp
def label(d, x, y, text):
    t = ' '.join(text.upper()); d.text((x, y), t, font=SEMI(24), fill=GOLD)
    d.line((x, y + 40, x + 44, y + 40), fill=GOLD, width=3)
def text_block(c, lab, title, body, bottom=H - 92, size=70):
    layer = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    ft = BOLD(size); tl = rich_lines(title, ft, W - 136); lh = int(size * 1.1)
    bf = MED(34); bl = rich_lines(body, bf, W - 136) if body else []
    hgt = (64 if lab else 0) + lh * len(tl) + (22 + 46 * len(bl) if bl else 0)
    y = bottom - hgt
    if lab: label(d, 68, y, lab); y += 64
    for l in tl: draw_rich(d, 68, y, l, ft); y += lh
    y += 22
    for l in bl: d.text((68, y), ' '.join(w.strip('*') for w in l), font=bf, fill=(232, 232, 226)); y += 46
    shadowed(c, layer); return bottom - hgt
def header(c, n, total, logo):
    d = ImageDraw.Draw(c)
    if logo: mark(c, 220, (56, 46))
    else: d.text((68, 62), plan['handle'], font=SEMI(26), fill=WHITE)
    d.text((W - 68, 62), f'{n}/{total}', font=MED(26), fill=WHITE, anchor='ra')
def tag(c, x, y, text):
    t = ' '.join(text.upper()); f = SEMI(22); tw = D0.textlength(t, font=f)
    layer = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x, y, x + tw + 40, y + 46), radius=23, fill=(6, 16, 11, 150))
    d.text((x + 20, y + 23), t, font=f, fill=WHITE, anchor='lm'); c.alpha_composite(layer)

slides = plan['slides']; total = len(slides)
for i, s in enumerate(slides, 1):
    if s['type'] == 'split':
        c = Image.new('RGB', (W, H)); top_h = s.get('split', 600)
        c.paste(cover(load(s['a']), W, top_h, s.get('acy', .5)), (0, 0)); c.paste(cover(load(s['b']), W, H - top_h, s.get('bcy', .5)), (0, top_h))
        topshade(c); shade(c, top_h + 120); c = c.convert('RGBA')
        ImageDraw.Draw(c).line((0, top_h, W, top_h), fill=WHITE, width=4)
        tag(c, 68, top_h - 70, 'Antes'); tag(c, 68, top_h + 26, 'Después')
    elif s['type'] == 'stack':
        c = Image.new('RGB', (W, H)); c.paste(cover(load(s['a']), W, H // 2), (0, 0)); c.paste(cover(load(s['b']), W, H - H // 2), (0, H // 2))
        topshade(c); shade(c, 520); c = c.convert('RGBA'); ImageDraw.Draw(c).line((0, H // 2, W, H // 2), fill=WHITE, width=4)
    else:
        c = cover(load(s['img']), W, H, s.get('cy', .5)); topshade(c); shade(c, s.get('shade_from', 560)); c = c.convert('RGBA')
    header(c, i, total, logo=(i == 1 or i == total))
    if s.get('cta'):
        y = text_block(c, s.get('label'), s['title'], None, bottom=H - 330, size=86)
        layer = Image.new('RGBA', c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        d.text((68, H - 292), s['cta'], font=BOLD(46), fill=WHITE)
        bt = s['button']; bf = SEMI(32); bw = D0.textlength(bt, font=bf) + 88
        d.rounded_rectangle((68, H - 200, 68 + bw, H - 120), radius=40, fill=GOLD)
        d.text((68 + bw / 2, H - 160), bt, font=bf, fill=GREEN, anchor='mm')
        d.text((68 + bw + 28, H - 160), plan['handle'], font=SEMI(30), fill=WHITE, anchor='lm')
        shadowed(c, layer, 6, .5)
    else:
        text_block(c, s.get('label'), s['title'], s.get('body'))
    c.convert('RGB').save(f'{OUT}/{i:02d}.jpg', quality=93)

t = 340; ims = [Image.open(f'{OUT}/{k:02d}.jpg') for k in range(1, total + 1)]
cols = 3; rows = (total + 2) // 3; th = int(t * 1.25)
sheet = Image.new('RGB', (cols * (t + 10) + 10, rows * (th + 10) + 10), (230, 230, 230))
for k, im in enumerate(ims): sheet.paste(im.resize((t, th)), (10 + (k % 3) * (t + 10), 10 + (k // 3) * (th + 10)))
sheet.save(f'{OUT}/revision.jpg', quality=88)
