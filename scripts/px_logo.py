#!/usr/bin/env python3
"""Make px-logo.png: a clean pixel-art version of logo.png for the footer welcome box.

Downsamples with a high-quality filter, snaps alpha to hard edges, reduces to a small palette
and adds a 1-px dark outline, so it can be shown at an exact integer scale with
`image-rendering: pixelated` and stay crisp. Needs Pillow (run locally; the PNG is committed).

Usage:  python3 scripts/px_logo.py [size]     # default 32
"""
import pathlib
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 32

src = Image.open(ROOT / "logo.png").convert("RGBA")
bbox = src.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
src = src.crop(bbox)
side = max(src.size)
sq = Image.new("RGBA", (side, side))
sq.paste(src, ((side - src.width) // 2, (side - src.height) // 2))
small = sq.resize((N, N), Image.LANCZOS)

alpha = small.getchannel("A").point(lambda a: 255 if a > 120 else 0)
rgb = Image.new("RGB", small.size, (0, 0, 0))
rgb.paste(small.convert("RGB"), mask=alpha)
pal = rgb.quantize(colors=14, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")

out = Image.new("RGBA", (N + 2, N + 2))
op = alpha.load()
for y in range(N):
    for x in range(N):
        if op[x, y]:
            out.putpixel((x + 1, y + 1), pal.getpixel((x, y)) + (255,))
outline = (26, 16, 24, 255)
o = out.copy()
for y in range(N + 2):
    for x in range(N + 2):
        if out.getpixel((x, y))[3] == 0 and any(
                0 <= x + dx < N + 2 and 0 <= y + dy < N + 2 and out.getpixel((x + dx, y + dy))[3]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            o.putpixel((x, y), outline)
o.save(ROOT / "px-logo.png")
print(f"wrote px-logo.png {N + 2}x{N + 2}")
