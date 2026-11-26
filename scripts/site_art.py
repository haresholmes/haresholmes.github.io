#!/usr/bin/env python3
"""Render the homepage hero panorama: Egypt on the left, Dubai on the right, in pixel art.

Writes px-scene-day.png and px-scene-night.png (same layout, different light). The site draws
them at native resolution into the hero canvas and cross-fades day to night with the Dubai clock,
so building lights come on at dusk. Reuses build.burj_pixels(), the Burj Khalifa from the CV.

Layout (x in PNG pixels): desert filler 0-200, core 200-1030, sea filler 1030-1230.
Core, left to right: Giza pyramids and the Sphinx, the Nile with a felucca, Cairo Tower,
the Muhammad Ali Mosque, Dubai Frame, Museum of the Future, Burj Khalifa, Emirates Towers,
Burj Al Arab and Ain Dubai. Standard library only.

Usage:  python3 scripts/site_art.py
"""
import math
import pathlib
import random
import struct
import sys
import zlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import ROOT, burj_pixels  # noqa: E402

W, H = 1230, 366
G = 356                      # first ground row; ground occupies G..H-1
X0 = 200                     # core start
CORE = (200, 1030)
BURJ_X = X0 + 578            # left edge of the 80-px-wide Burj Khalifa sprite (centre = BURJ_X + 40)
WARM = ("#fbbf24", "#fde68a", "#f59e0b")


def hex_rgba(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255)


def write_png(path, pixels):
    raw = b"".join(b"\x00" + b"".join(bytes(hex_rgba(pixels[(x, y)]) if (x, y) in pixels else (0, 0, 0, 0)) for x in range(W)) for y in range(H))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


class Scene:
    def __init__(self, night):
        self.night = night
        self.px = {}
        self.rng = random.Random(1987)   # same seed in both renders keeps the layout identical

    def put(self, x, y, c):
        if c and 0 <= x < W and 0 <= y < H:
            self.px[(int(x), int(y))] = c

    def c(self, day, night):
        return night if self.night else day

    def lit(self, rate=0.25):
        return self.night and self.rng.random() < rate

    def line(self, x0, y0, x1, y1, col):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.put(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), col)

    def sprite(self, x0, y0, rows, pal):
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in pal:
                    self.put(x0 + dx, y0 + dy, pal[ch])


# ------------------------------------------------------------------ Egypt
def dunes(s):
    for x in range(0, X0 + 300):
        h = 6 + 5 * math.sin(x / 23) + 4 * math.sin(x / 9.0 + 1.3)
        if x > X0 - 10:                                      # flatten toward Giza
            h *= max(0.0, 1 - (x - X0 + 10) / 40)
        for y in range(int(G - h), G):
            top = y == int(G - h)
            s.put(x, y, s.c("#e2b46a" if top else "#d29f55", "#4a4870" if top else "#3a3960"))


def pyramid(s, cx, half, cap=False):
    apex = G - half
    for y in range(apex, G):
        d = y - apex
        for x in range(cx - d, cx + d + 1):
            left = x <= cx
            col = s.c("#e8c078" if left else "#b98b4d", "#5f6390" if left else "#393c64")
            if (G - y) % 4 == 0:
                col = s.c("#d4aa60" if left else "#a77b41", "#53578a" if left else "#32355b")
            if cap and d < half * 0.16:
                col = s.c("#f3e2b4" if left else "#d3bf8e", "#8186b3" if left else "#5a5e8a")
            s.put(x, y, col)


SPHINX = [
    "....####..........................",
    "...#++++#.........................",
    "..#++++++#........................",
    ".#++o++++#........................",
    ".#+++++++##.......................",
    ".#++++++###.......................",
    "..#+++++#.........................",
    "..#+++++##################........",
    "..#++++++++++++++++++++++++##.....",
    ".#++++++++++++++++++++++++++##....",
    ".#+++++++++++++++++++++++++++#....",
    "#+++++++++++++++++++++++++++++#...",
    "#+++++++++++++++++++++++++++++#...",
    "#+++++++++++++++++++++++++++++##..",
    "##########++++++++++++++++++++++#.",
    "#++++++++#########################",
]


def sphinx(s, x0):
    s.sprite(x0, G - len(SPHINX), SPHINX, {"#": s.c("#a8783f", "#34375e"), "+": s.c("#d8a964", "#575b88"), "o": s.c("#5c3d1e", "#1c1d38")})


def palm(s, x, h=24):
    trunk, leaf_a, leaf_b = s.c("#8a5a2b", "#2a2240"), s.c("#3f7d3a", "#1d3838"), s.c("#64a64f", "#2a514a")
    tx, ty = x, G - h
    for i in range(h):
        s.put(x + round(math.sin(i / h * 1.4) * 2), G - 1 - i, trunk)
        tx, ty = x + round(math.sin(i / h * 1.4) * 2), G - 1 - i
    for k, (dx, dy) in enumerate(((-1, -0.35), (1, -0.35), (-1, 0.25), (1, 0.25), (-0.45, -1), (0.55, -0.9), (0, 0.6))):
        for i in range(1, 9):
            s.put(tx + round(dx * i), ty + round(dy * i + 0.07 * i * i), leaf_a if (i + k) % 3 else leaf_b)


CAMEL = [
    ".##...........",
    "###...........",
    "..#.....##....",
    "..##...####...",
    "...#########..",
    "...##########.",
    "....########..",
    "....#.#..#.#..",
    "....#.#..#.#..",
    "....#.#..#.#..",
]


def nile_felucca(s, x0):
    hull, sail, mast = s.c("#6b4a2a", "#241d33"), s.c("#f6f0e2", "#a3a9d3"), s.c("#5c3d1e", "#1c1d38")
    for i in range(16):                                      # hull sits on the water rows
        s.put(x0 + i, G, hull)
        if 1 <= i <= 14:
            s.put(x0 + i, G + 1, hull)
    s.line(x0 + 9, G - 1, x0 + 9, G - 22, mast)
    for i in range(20):                                      # lateen sail
        y = G - 3 - i
        width = max(1, (20 - i) * 9 // 20)
        for x in range(x0 + 9 - width // 3, x0 + 9 + width - width // 3):
            if x != x0 + 9:
                s.put(x, y, sail)
    s.line(x0 + 2, G - 4, x0 + 15, G - 25, mast)            # yard


def cairo_tower(s, cx):
    top = G - 128
    body, mesh, deck = s.c("#c99c6c", "#4b4466"), s.c("#9b7148", "#2e2947"), s.c("#e8cca2", "#5b5478")
    for y in range(top + 12, G):
        t = (y - top) / (G - top)
        hw = round(3 + 2 * t)
        for x in range(cx - hw, cx + hw + 1):
            shade = x > cx + 1
            col = mesh if ((x + y) % 3 == 0 or (x - y) % 3 == 0) else body
            if shade and not s.night:
                col = "#a57c52" if col == body else "#7f5a35"
            s.put(x, y, col)
    for r in range(12):                                      # lotus crown, flaring upward
        y = top + 11 - r
        hw = 3 + (r + 1) // 2 if r < 9 else 7 - (r - 9) * 2
        for x in range(cx - hw, cx + hw + 1):
            col = deck
            if 4 <= r <= 6:
                col = (s.rng.choice(WARM) if s.night else "#6f8399") if (x - cx) % 2 == 0 else s.c("#c9b08a", "#3a3456")
            s.put(x, y, col)
    s.line(cx, top - 1, cx, top - 18, s.c("#9aa3b0", "#5b6480"))
    if s.night:
        s.put(cx, top - 19, "#ef4444")


def mosque(s, c):
    stone, shade = s.c("#e4d5b5", "#caa86e"), s.c("#c0ae8c", "#9c7f4e")
    dome, dome_sh = s.c("#8f9aab", "#7e7b93"), s.c("#6f7a8c", "#5f5c75")
    base = G - 14
    for y in range(base, G):
        for x in range(c - 26, c + 27):
            col = stone if x < c + 8 else shade
            if base + 5 <= y <= base + 8 and (x - c) % 4 == 0:
                col = s.c("#7a6a50", "#fde68a")
            s.put(x, y, col)
    for y in range(base - 6, base):
        for x in range(c - 12, c + 13):
            s.put(x, y, stone if x < c + 4 else shade)

    def half_dome(cx, cy, r):
        for y in range(cy - r, cy + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r:
                    s.put(x, y, dome if x < cx + r // 3 else dome_sh)

    half_dome(c - 17, base, 7)
    half_dome(c + 17, base, 7)
    half_dome(c - 24, base, 3)
    half_dome(c + 24, base, 3)
    half_dome(c, base - 6, 13)
    s.line(c, base - 20, c, base - 24, s.c("#c9a227", "#fbbf24"))
    for mx in (c - 30, c + 29):                              # pencil minarets
        for y in range(G - 78, G):
            s.put(mx, y, s.c("#ece0c4", "#e0c690"))
            s.put(mx + 1, y, s.c("#cbbd9f", "#b89a62"))
        for by in (G - 44, G - 62):
            for x in range(mx - 1, mx + 3):
                s.put(x, by, s.c("#b7a684", "#fde68a" if s.night else "#b7a684"))
        for i in range(7):
            s.put(mx, G - 79 - i, dome)
            if i < 4:
                s.put(mx + 1, G - 79 - i, dome_sh)


def cairo_blocks(s, x_from, x_to):
    x = x_from
    while x < x_to:
        w, h = s.rng.randint(5, 9), s.rng.randint(7, 20)
        for y in range(G - h, G):
            for xx in range(x, min(x + w, x_to)):
                col = s.c("#cdb48d", "#2a2840")
                if xx not in (x, x + w - 1) and (G - y) % 3 == 1 and (xx - x) % 2 == 1:
                    col = s.rng.choice(WARM) if s.lit(0.3) else s.c("#8d7656", "#1d1b30")
                s.put(xx, y, col)
        x += w + s.rng.randint(0, 2)


# ------------------------------------------------------------------ Dubai
def dubai_blocks(s, x_from, x_to):
    x = x_from
    while x < x_to:
        w, h = s.rng.randint(6, 12), s.rng.randint(16, 64)
        for y in range(G - h, G):
            for xx in range(x, min(x + w, x_to)):
                col = s.c("#9fb0c6" if xx < x + w // 2 else "#8495ad", "#101b30")
                if xx not in (x, x + w - 1) and (G - y) % 3 == 1 and (xx - x) % 2 == 1:
                    col = s.rng.choice(WARM) if s.lit(0.22) else s.c("#c9d6e6", "#1c2840")
                s.put(xx, y, col)
        x += w + s.rng.randint(0, 2)


def dubai_frame(s, x0):
    gold, dark, glass = s.c("#e6b740", "#f2c14e"), s.c("#b8862a", "#a8781f"), s.c("#a9d4f5", "#fde68a")
    top = G - 100
    for y in range(top, G):
        for x in list(range(x0, x0 + 7)) + list(range(x0 + 25, x0 + 32)):
            s.put(x, y, dark if (x + y) % 4 == 0 or x in (x0 + 6, x0 + 31) else gold)
    for y in range(top, top + 9):
        for x in range(x0, x0 + 32):
            col = dark if (x + y) % 4 == 0 else gold
            if top + 3 <= y <= top + 5 and x0 + 2 <= x <= x0 + 29:
                col = glass
            s.put(x, y, col)


def museum_future(s, cx):
    cy, rx, ry, irx, iry = G - 31, 21, 25, 10, 14
    silver, shade, glyph = s.c("#d3dbe5", "#3d4766"), s.c("#a3aebd", "#2c3552"), s.c("#5d6b7e", "#e0f2fe")
    glyph2 = s.c("#788699", "#93c5fd")
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            o = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            i = ((x - cx) / irx) ** 2 + ((y - cy + 2) / iry) ** 2
            if o <= 1 and i > 1:
                col = shade if x > cx + rx * 0.35 else silver
                h = (x * 73856093 ^ y * 19349663) % 7
                if (y % 3 == 0 and h < 3) or h == 0:
                    col = glyph if h % 2 == 0 else glyph2
                s.put(x, y, col)
    for y in range(G - 8, G):                                # green mound
        hw = int(30 * math.sqrt(max(0, 1 - ((G - y) / 8) ** 2)))
        for x in range(cx - hw, cx + hw + 1):
            s.put(x, y, s.c("#5d8f45" if (x + y) % 5 else "#4a7536", "#1e3a2e" if (x + y) % 5 else "#183024"))


def burj_khalifa(s):
    _, ground, tower = burj_pixels()
    daytime = {"#e0e7ff", "#eef2ff", "#64748b"}             # the CV's clouds and birds
    body = {"#3b82f6", "#1d4ed8", "#93c5fd"}
    for (tx, ty), col in tower.items():
        if not col or col in daytime or ty >= ground:
            continue
        if s.night and col in body and ty > 100 and s.rng.random() < 0.04:
            col = s.rng.choice(WARM)
        s.put(tx + BURJ_X, ty - (ground - G), col)


def emirates_tower(s, x0, w, h):
    for x in range(x0, x0 + w):
        top = G - h - (x0 + w - 1 - x)
        for y in range(top, G):
            col = s.c("#86a9c9" if x > x0 + 1 else "#bcd3e6", "#1c2742")
            if (G - y) % 4 == 0:
                col = s.c("#c4ccd6", "#26324f")
            if s.night and (G - y) % 4 == 2 and s.rng.random() < 0.2:
                col = s.rng.choice(("#fde68a", "#e0f2fe"))
            s.put(x, y, col)
        s.put(x, top, s.c("#e2e8f0", "#94a3b8"))


def burj_al_arab(s, xr):
    base, top = G - 6, G - 100
    for y in range(G - 5, G):                                # island
        for x in range(xr - 34, xr + 9):
            s.put(x, y, s.c("#dcc89b", "#4a4566"))
    left_at = {}
    for y in range(top, base):
        t = (base - y) / (base - top)
        width = round(28 * (1 - t) ** 0.55 + 2)
        left_at[y] = xr - width
        for x in range(xr - width, xr + 1):
            if s.night:
                col = "#a78bfa" if t > 0.5 else "#818cf8"
                if x <= xr - width + 1:
                    col = "#c4b5fd"
                if (x + y) % 6 == 0:
                    col = "#60a5fa"
            else:
                col = "#f4f6fa" if (x - (xr - width)) % 4 else "#d6dde7"
            s.put(x, y, col)
    for y in range(top - 10, base + 1):                      # mast and exoskeleton
        s.put(xr + 1, y, s.c("#aab4c3", "#e0e7ff"))
        if y > top:
            s.put(xr + 3, y, s.c("#aab4c3", "#c7d2fe"))
            if (y - top) % 12 < 2:
                s.put(xr + 2, y, s.c("#aab4c3", "#c7d2fe"))
    hy = top + 18                                            # helipad
    hx = left_at.get(hy, xr - 10)
    for y in range(hy, hy + 2):
        for x in range(hx - 7, hx + 1):
            s.put(x, y, s.c("#cfd6e0", "#fbbf24" if y == hy else "#7c6fd0"))


def ain_dubai(s, cx):
    r, cy = 30, G - 38
    rim, spoke, cabin, leg = s.c("#d4dae3", "#f472b6"), s.c("#a3aebd", "#3b4a6b"), s.c("#6b7a90", "#fde68a"), s.c("#aab4c3", "#94a3b8")
    for y in range(G - 4, G):                                # Bluewaters island
        for x in range(cx - 26, cx + 27):
            s.put(x, y, s.c("#dcc89b", "#4a4566"))
    for a in range(16):
        ang = a * math.pi / 8
        s.line(cx, cy, cx + round(math.cos(ang) * (r - 1)), cy + round(math.sin(ang) * (r - 1)), spoke)
    for i in range(360):
        ang = math.radians(i)
        for rr in (r, r - 1):
            col = rim
            if s.night and (i // 15) % 2:
                col = "#60a5fa"
            s.put(cx + round(math.cos(ang) * rr), cy + round(math.sin(ang) * rr), col)
    for k in range(24):
        ang = k * math.pi / 12
        x, y = cx + round(math.cos(ang) * (r + 2)), cy + round(math.sin(ang) * (r + 2))
        for dx in (0, 1):
            for dy in (0, 1):
                s.put(x + dx, y + dy, cabin)
    s.line(cx - 16, G - 5, cx, cy, leg)
    s.line(cx - 15, G - 5, cx + 1, cy, leg)
    s.line(cx + 16, G - 5, cx, cy, leg)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            s.put(cx + dx, cy + dy, s.c("#64748b", "#e0e7ff"))


def dhow(s, x0):
    hull, sail = s.c("#7a4f2a", "#241d33"), s.c("#efe6d2", "#9aa0c8")
    for i in range(18):
        s.put(x0 + i, G, hull)
        if 2 <= i <= 15:
            s.put(x0 + i, G + 1, hull)
    s.line(x0 + 8, G - 1, x0 + 8, G - 18, hull)
    for i in range(15):
        for x in range(x0 + 9, x0 + 9 + max(1, (15 - i) * 7 // 15)):
            s.put(x, G - 3 - i, sail)


# ------------------------------------------------------------------ ground + compose
def ground(s):
    for x in range(W):
        for y in range(G, H):
            d = y - G
            if x < X0 + 300:                                 # desert sand
                col = s.c("#d9a95f" if (x + 2 * d) % 9 else "#c79450", "#3b3a5c" if (x + 2 * d) % 9 else "#33324f")
            elif x < X0 + 372:                               # the Nile
                col = s.c("#3b7dc4" if (x * 3 + d * 5) % 11 else "#8cc0f0", "#1b2a55" if (x * 3 + d * 5) % 11 else "#3a4f8a")
            elif x < X0 + 700:                               # city
                col = s.c("#7a8194", "#1a2132")
                if d == 2 and x % 6 == 0:
                    col = s.c("#9aa1b2", "#fbbf24")
            else:                                            # the Gulf
                col = s.c("#2f7fc1" if (x * 3 + d * 7) % 13 else "#86c8f2", "#13204a" if (x * 3 + d * 7) % 13 else "#2f4a8a")
            if d == 0 and X0 + 372 <= x < X0 + 700:
                col = s.c("#9aa1b2", "#2a3348")
            s.put(x, y, col)


def render(night):
    s = Scene(night)
    dunes(s)
    s.sprite(70, G - len(CAMEL), CAMEL, {"#": s.c("#a8743c", "#2a2240")})
    palm(s, 30, 22)
    palm(s, 150, 26)
    pyramid(s, X0 + 165, 52, cap=True)
    pyramid(s, X0 + 95, 58)
    pyramid(s, X0 + 228, 27)
    sphinx(s, X0 + 258)
    palm(s, X0 + 300, 22)
    palm(s, X0 + 368, 18)
    cairo_blocks(s, X0 + 376, X0 + 470)
    cairo_tower(s, X0 + 392)
    mosque(s, X0 + 440)
    dubai_blocks(s, X0 + 478, X0 + 500)
    dubai_blocks(s, X0 + 520, X0 + 548)
    dubai_blocks(s, X0 + 652, X0 + 700)
    burj_khalifa(s)
    dubai_frame(s, X0 + 486)
    museum_future(s, X0 + 548)
    emirates_tower(s, X0 + 664, 10, 118)
    emirates_tower(s, X0 + 679, 9, 96)
    ground(s)
    nile_felucca(s, X0 + 326)
    burj_al_arab(s, X0 + 742)
    ain_dubai(s, X0 + 795)
    dhow(s, X0 + 900)
    return s.px


def main():
    for night, name in ((False, "px-scene-day.png"), (True, "px-scene-night.png")):
        write_png(ROOT / name, render(night))
    print(f"wrote px-scene-day.png, px-scene-night.png {W}x{H}; core {CORE}; Burj Khalifa spire x={BURJ_X + 40}, y=2")


if __name__ == "__main__":
    main()
