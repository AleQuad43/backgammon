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

# marquetry ring: two thin brass lines with a band of alternating triangles between them
r0, r1 = 352, 410
n = 44
for i in range(n):
    a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
    am = (a0 + a1) / 2
    p = lambda r, a: (C + r * math.cos(a), C + r * math.sin(a))
    up = [p(r0, a0), p(r0, a1), p(r1, am)]
    down = [p(r1, a1 - (a1 - a0)), p(r1, am), p(r0, a0)]
    pearl = tuple(int(v) for v in (236 + rnd.randint(-8, 8), 232 + rnd.randint(-10, 10), 222 + rnd.randint(-12, 14)))
    d.polygon(up, fill=pearl)
    d.polygon([p(r1, a0), p(r1, am), p(r0, a0)], fill=(28, 18, 12))
    d.polygon([p(r1, am), p(r1, a1), p(r0, a1)], fill=(28, 18, 12))
for r, wdt in ((r0 - 6, 9), (r1 + 6, 9)):
    d.ellipse((C - r, C - r, C + r, C + r), outline=(201, 158, 74), width=wdt)
d.ellipse((C - r0 + 12, C - r0 + 12, C + r0 - 12, C + r0 - 12), outline=(150, 112, 50), width=3)

# pearl sheen on the ring
sheen = Image.new('L', (S, S), 0)
ImageDraw.Draw(sheen).ellipse((C - 520, C - 620, C + 220, C + 60), fill=70)
img = Image.composite(Image.new('RGB', (S, S), (255, 250, 240)), img, sheen.filter(ImageFilter.GaussianBlur(90)))


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


die(C - 128, C + 58, 232, 12, 6)
die(C + 122, C - 76, 232, -17, 5)

for n2 in (512, 192, 180):
    img.resize((n2, n2), Image.LANCZOS).save(OUT / f'icon2-{n2}.png')
img.resize((512, 512), Image.LANCZOS).save(pathlib.Path(__file__).parent / 'icon-preview.png')
print('icons done')
