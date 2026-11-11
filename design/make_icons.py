"""Draws the app icon (sky gradient, two checkers) into ../docs at the sizes phones ask for."""
from PIL import Image, ImageDraw, ImageFilter
import pathlib
OUT = pathlib.Path(__file__).parent.parent / 'docs'
S = 1024
img = Image.new('RGB', (S, S))
top, mid, bot = (246, 214, 176), (226, 196, 214), (178, 204, 232)
px = img.load()
for y in range(S):
    for x in range(S):
        u = (x * 0.35 + y * 0.65) / S
        a, b, t = (top, mid, u / 0.5) if u < 0.5 else (mid, bot, (u - 0.5) / 0.5)
        px[x, y] = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def checker(cx, cy, r, face, rim, ring):
    sh = Image.new('L', (S, S), 0); ImageDraw.Draw(sh).ellipse((cx - r + 10, cy - r + 26, cx + r + 10, cy + r + 26), fill=110)
    img.paste((60, 50, 60), (0, 0), sh.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(img)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rim)
    d.ellipse((cx - r * .9, cy - r * .9, cx + r * .9, cy + r * .9), fill=face)
    d.ellipse((cx - r * .58, cy - r * .58, cx + r * .58, cy + r * .58), outline=ring, width=int(r * .06))
checker(420, 600, 250, (58, 44, 40), (40, 30, 28), (86, 68, 60))
checker(610, 430, 250, (247, 240, 226), (222, 210, 190), (210, 196, 172))
for n in (512, 192, 180):
    img.resize((n, n), Image.LANCZOS).save(OUT / f'icon-{n}.png')
print('icons done')
