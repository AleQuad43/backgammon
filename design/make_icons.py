"""Draws the app icon into ../docs: shesh besh, a 6 and a 5 in ivory, thrown on a walnut board inside a ring of
marquetry (mother-of-pearl, ebony and brass triangles, as on the inlaid tavla boxes of Damascus and Istanbul).
Everything sits inside the central circle so round and squircle masks on Android keep it whole."""
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import pathlib, math, random

OUT = pathlib.Path(__file__).parent.parent / 'docs'
S = 1024
rnd = random.Random(7)


def walnut():
    img = Image.new('RGB', (S, S))
    px = img.load()
    a, b = (92, 58, 34), (54, 32, 18)
    for y in range(S):
        for x in range(S):
            w = y / S * 7 + math.sin(x / 260 + y / 500) * 0.9 + math.sin(x / 71 + y / 170) * 0.18
            ring = (w - math.floor(w)) ** 4
            t = min(1, ring * 0.38 + (math.sin(x * 1.7 + y * 0.03 + math.sin(y / 9)) * 0.5 + 0.5) * 0.06)
            px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    # gentle light from the top left, darker towards the corners
    vig = Image.new('L', (S, S), 0)
    ImageDraw.Draw(vig).ellipse((-S * 0.1, -S * 0.15, S * 1.0, S * 0.95), fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new('RGB', (S, S), (24, 13, 6))
    return Image.composite(img, dark, vig.point(lambda v: int(70 + v * 185 / 255)))


img = walnut()
d = ImageDraw.Draw(img)
C = S / 2

# A ten-fold rosette of inlaid wood, like the centre panels of Syrian boards but pared down: a pearl star, ten maple
# petals edged in pearl with cherry hearts, ebony kites between them, and a fine mosaic band with brass lines around.
def at(r, a):
    return (C + r * math.cos(a), C + r * math.sin(a))
def local(rad, along, across, a):
    return (C + along * math.cos(a) - across * math.sin(a), C + along * math.sin(a) + across * math.cos(a))
PEARL, MAPLE, CHERRY, EBONY, BRASS = (238, 230, 214), (205, 160, 100), (150, 82, 46), (30, 19, 12), (201, 158, 74)
n = 10
off = -math.pi / 2
# mosaic band: tiny alternating pearl and ebony tiles between two brass lines
rb0, rb1 = 382, 404
m = 120
for i in range(m):
    a0, a1 = off + 2 * math.pi * i / m, off + 2 * math.pi * (i + 1) / m
    d.polygon([at(rb0, a0), at(rb1, a0), at(rb1, a1), at(rb0, a1)], fill=PEARL if i % 2 else EBONY)
for r, wdt in ((rb0 - 5, 8), (rb1 + 5, 8)):
    d.ellipse((C - r, C - r, C + r, C + r), outline=BRASS, width=wdt)
# ebony kites on the star's axes, each with a pearl dot
for k in range(n):
    a = off + 2 * math.pi * k / n
    d.polygon([local(0, 300, 0, a), local(0, 335, -30, a), local(0, 366, 0, a), local(0, 335, 30, a)], fill=EBONY, outline=PEARL, width=3)
    x, y = local(0, 335, 0, a); d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=PEARL)
# petals: elongated hexagons between the star's points
for k in range(n):
    a = off + 2 * math.pi * (k + 0.5) / n
    hexo = [local(0, 168, 0, a), local(0, 205, -52, a), local(0, 300, -52, a), local(0, 340, 0, a), local(0, 300, 52, a), local(0, 205, 52, a)]
    d.polygon(hexo, fill=PEARL)
    hexm = [local(0, 180, 0, a), local(0, 211, -42, a), local(0, 294, -42, a), local(0, 326, 0, a), local(0, 294, 42, a), local(0, 211, 42, a)]
    d.polygon(hexm, fill=MAPLE)
    hexi = [local(0, 214, 0, a), local(0, 232, -20, a), local(0, 270, -20, a), local(0, 290, 0, a), local(0, 270, 20, a), local(0, 232, 20, a)]
    d.polygon(hexi, fill=CHERRY)
# the star: ten points in pearl, a walnut star inside it
pts = []
for k in range(2 * n):
    a = off + math.pi * k / n
    pts.append(at(190 if k % 2 == 0 else 120, a))
d.polygon(pts, fill=PEARL)
pts2 = [at(170 if k % 2 == 0 else 106, off + math.pi * k / n) for k in range(2 * n)]
d.polygon(pts2, fill=(70, 43, 25))
pts3 = [at(120 if k % 2 == 0 else 78, off + math.pi * k / n) for k in range(2 * n)]
d.polygon(pts3, outline=PEARL, width=3)
# grain inside the wood pieces and a soft varnish sheen across the whole inlay
grain = Image.new('L', (S, S), 0)
gd = ImageDraw.Draw(grain)
for i in range(0, S, 7):
    gd.line([(0, i), (S, i + 40)], fill=28, width=2)
img = Image.composite(Image.new('RGB', (S, S), (60, 35, 18)), img, grain.filter(ImageFilter.GaussianBlur(1.5)))
d = ImageDraw.Draw(img)
sheen = Image.new('L', (S, S), 0)
ImageDraw.Draw(sheen).ellipse((C - 560, C - 640, C + 160, C + 40), fill=55)
img = Image.composite(Image.new('RGB', (S, S), (255, 248, 232)), img, sheen.filter(ImageFilter.GaussianBlur(110)))


def die(cx, cy, size, ang, val):
    """An ivory die seen from above, rounded, lit from the top left, with its shadow."""
    global img
    pad = int(size * 0.9)
    tile = Image.new('RGBA', (pad * 2, pad * 2), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    h = size / 2
    box = (pad - h, pad - h, pad + h, pad + h)
    td.rounded_rectangle(box, radius=size * 0.2, fill=(244, 236, 220, 255))
    # rounded edges: darker rim bottom right, light rim top left
    rim = Image.new('L', tile.size, 0)
    ImageDraw.Draw(rim).rounded_rectangle(box, radius=size * 0.2, fill=255)
    inner = Image.new('L', tile.size, 0)
    ImageDraw.Draw(inner).rounded_rectangle((box[0] + size * 0.07, box[1] + size * 0.07, box[2] - size * 0.04, box[3] - size * 0.04), radius=size * 0.16, fill=255)
    edge = ImageChops.subtract(rim, inner.filter(ImageFilter.GaussianBlur(size * 0.05)))
    tile = Image.composite(Image.new('RGBA', tile.size, (176, 150, 112, 255)), tile, edge)
    hl = Image.new('L', tile.size, 0)
    ImageDraw.Draw(hl).ellipse((pad - h * 1.1, pad - h * 1.2, pad + h * 0.2, pad - h * 0.1), fill=90)
    tile = Image.composite(Image.new('RGBA', tile.size, (255, 253, 247, 255)), tile, ImageChops.multiply(hl.filter(ImageFilter.GaussianBlur(size * 0.12)), rim))
    td = ImageDraw.Draw(tile)
    pips = {5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[val]
    pr, sp = size * 0.085, size * 0.27
    for (u, v) in pips:
        x, y = pad + u * sp, pad + v * sp
        td.ellipse((x - pr, y - pr + 2, x + pr, y + pr + 2), fill=(255, 250, 238, 200))
        td.ellipse((x - pr, y - pr, x + pr, y + pr), fill=(52, 30, 20, 255))
    tile = tile.rotate(ang, resample=Image.BICUBIC)
    # shadow
    sh = Image.new('L', (S, S), 0)
    ImageDraw.Draw(sh).rounded_rectangle((cx - h + 18, cy - h + 30, cx + h + 18, cy + h + 30), radius=size * 0.22, fill=150)
    img = Image.composite(Image.new('RGB', (S, S), (16, 8, 3)), img, sh.filter(ImageFilter.GaussianBlur(26)))
    img.paste(tile, (int(cx - pad), int(cy - pad)), tile)


die(C - 104, C + 64, 196, 12, 6)
die(C + 104, C - 66, 196, -17, 5)

for n2 in (512, 192, 180):
    img.resize((n2, n2), Image.LANCZOS).save(OUT / f'icon3-{n2}.png')
img.resize((512, 512), Image.LANCZOS).save(pathlib.Path(__file__).parent / 'icon-preview.png')
print('icons done')
