#!/usr/bin/env python3
"""Render the website's pixel-art night skyline (px-skyline.png) from the CV's Burj Khalifa.

Reuses build.burj_pixels() (the same tower drawn on page 2 of the CV), drops the daytime clouds and
birds, lights random windows and sets it among a low pixel skyline. The PNG is written natively at
1 px per cell; the site scales it up with `image-rendering: pixelated`. Standard library only.

Usage:  python3 scripts/site_art.py
"""
import pathlib
import random
import struct
import sys
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import ROOT, burj_pixels  # noqa: E402

OUT = ROOT / "px-skyline.png"
W, OFFSET = 200, 60          # canvas width; tower (80 wide) sits at x = 60..139, centre 100
DAYTIME = {"#e0e7ff", "#eef2ff", "#64748b"}      # clouds and birds
TOWER_BODY = {"#3b82f6", "#1d4ed8", "#93c5fd"}   # slab bodies that can show a lit window
WARM = ("#fbbf24", "#fde68a", "#f59e0b")


def hex_rgba(c, a=255):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


def write_png(path, w, h, pixels):
    raw = b"".join(b"\x00" + b"".join(bytes(pixels.get((x, y), (0, 0, 0, 0))) for x in range(w)) for y in range(h))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def main():
    rng = random.Random(2026)
    tw, ground, tower = burj_pixels()
    H = ground
    out = {}

    # Low skyline: two layers of blocks with lit windows, the far layer dimmer.
    def block(x0, w, h, body, edge, lit_rate):
        for y in range(H - h, H):
            for x in range(x0, x0 + w):
                if 0 <= x < W:
                    c = edge if (x == x0 or y == H - h) else body
                    if x not in (x0, x0 + w - 1) and y > H - h + 1 and (x - x0) % 2 == 1 and (H - y) % 3 == 1:
                        c = rng.choice(WARM) if rng.random() < lit_rate else "#1e293b"
                    out[(x, y)] = hex_rgba(c)

    x = 0
    while x < W:                              # far layer
        w = rng.randint(7, 14)
        block(x, w, rng.randint(18, 44), "#0f1a2e", "#16233b", 0.10)
        x += w + rng.randint(0, 2)
    x = -3
    while x < W:                              # near layer, kept low around the tower base
        w = rng.randint(8, 16)
        near_tower = OFFSET + 20 < x + w // 2 < OFFSET + 60
        h = rng.randint(6, 12) if near_tower else rng.randint(10, 30)
        block(x, w, h, "#111c31", "#1b2a45", 0.22)
        x += w + rng.randint(1, 4)

    # The tower, drawn over the skyline.
    for (tx, ty), c in tower.items():
        if not c or c in DAYTIME or ty >= ground:
            continue
        if c in TOWER_BODY and ty > 100 and rng.random() < 0.035:
            c = rng.choice(WARM)
        out[(tx + OFFSET, ty)] = hex_rgba(c)

    write_png(OUT, W, H, out)
    # Beacon position (for the blinking CSS overlay in index.html).
    print(f"wrote {OUT.name} {W}x{H}; beacon at x={40 + OFFSET}, y=3")


if __name__ == "__main__":
    main()
