#!/usr/bin/env python3
"""Render the homepage hero panorama: Egypt on the left, Dubai on the right, in pixel art.

Writes px-scene-day.png and px-scene-night.png (identical layout, different light). The site
draws them at native resolution into the hero canvas and cross-fades day to night with the Dubai
clock, so the city lights come on at dusk. The Burj Khalifa is the CV's (build.burj_pixels());
every other landmark is drawn here at a similar level of detail: shaded faces, texture, edges.

Layout (x in PNG pixels): desert filler 0-200, core 200-1180, sea filler 1180-1380.
Core, left to right: the Giza pyramids and the Sphinx, the Nile with a felucca, Cairo Tower,
the Muhammad Ali Mosque on the Citadel wall, Dubai Frame, Museum of the Future, Burj Khalifa,
Emirates Towers, Burj Al Arab and Ain Dubai. Standard library only.

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

W, H = 1380, 366
G = 356                      # first ground row; ground occupies G..H-1
X0 = 200                     # core start
CORE = (200, 1180)
BURJ_X = X0 + 708            # left edge of the 80-px Burj Khalifa sprite; spire at BURJ_X + 40
WARM = ("#fbbf24", "#fde68a", "#f59e0b", "#fcd34d")


def hex_rgb(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def write_png(path, pixels):
    rows = []
    for y in range(H):
        row = bytearray(b"\x00")
        for x in range(W):
            c = pixels.get((x, y))
            row += bytes(hex_rgb(c) + (255,)) if c else b"\x00\x00\x00\x00"
        rows.append(bytes(row))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def h2(x, y, k=0):
    """Deterministic per-pixel hash in [0, 1): texture that is identical in both renders."""
    v = (x * 374761393 + y * 668265263 + k * 2147483647) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return (v ^ (v >> 16)) / 4294967296


class Scene:
    def __init__(self, night):
        self.night = night
        self.px = {}
        self.layout = random.Random(1987)       # building sizes: identical in day and night
        self.lights = random.Random(4242)       # window lights: always consumed, so layouts never drift

    def put(self, x, y, c):
        if c and 0 <= x < W and 0 <= y < H:
            self.px[(int(x), int(y))] = c

    def get(self, x, y):
        return self.px.get((int(x), int(y)))

    def c(self, day, night):
        return night if self.night else day

    def lit(self, rate):
        r = self.lights.random()
        return self.night and r < rate

    def warm(self):
        return self.lights.choice(WARM)

    def line(self, x0, y0, x1, y1, col):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.put(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), col)

    def tri(self, a, b, c, colf):
        xs, ys = (a[0], b[0], c[0]), (a[1], b[1], c[1])

        def side(p, q, r):
            return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                d1, d2, d3 = side((x, y), a, b), side((x, y), b, c), side((x, y), c, a)
                if not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0)):
                    self.put(x, y, colf(x, y))

    def disk(self, cx, cy, rx, ry, colf):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    self.put(x, y, colf(x, y))


# ======================================================================= Egypt
def dunes(s):
    for x in range(0, X0 + 40):
        h = 8 + 6 * math.sin(x / 26) + 4 * math.sin(x / 9.5 + 1.3) + 2 * math.sin(x / 4.1)
        h *= max(0.0, min(1.0, (X0 + 40 - x) / 50))
        top = int(G - max(0, h))
        for y in range(top, G):
            d = y - top
            sun = math.cos(x / 26) > 0                       # dune faces turned to the light
            if d == 0:
                col = s.c("#f1cd8a", "#6a6c9a")
            elif sun:
                col = s.c("#e2b46a" if d < 3 else "#d6a75e", "#55577f" if d < 3 else "#4b4c74")
            else:
                col = s.c("#c9964f" if d < 3 else "#bd8b49", "#43446a" if d < 3 else "#3c3d62")
            if (x + 3 * y) % 11 == 0:
                col = s.c("#b9874a", "#36375a")              # wind ripples
            s.put(x, y, col)


def pyramid(s, cx, hw, base=G, cap=0.0, slope=1.25):
    """Stepped pyramid: lit west face, shaded east face, block courses with staggered joints."""
    height = round(hw * slope)
    apex = base - height
    P = {
        "lit": s.c("#ebc57e", "#6c71a0"), "lit2": s.c("#dcb06a", "#62679a"), "mlit": s.c("#c99b55", "#53588a"),
        "sh": s.c("#b98749", "#3e416b"), "sh2": s.c("#ab7a41", "#373a62"), "msh": s.c("#946739", "#2e3157"),
        "ridge": s.c("#f8e0a4", "#9196c6"), "edge": s.c("#8a5f33", "#272a4c"),
        "cap": s.c("#f4e6c0", "#9a9fcb"), "cap_sh": s.c("#d3be90", "#62669a"),
    }
    for y in range(apex, base):
        d = y - apex
        half = int(d / slope)
        course = (base - y) // 3
        for x in range(cx - half, cx + half + 1):
            left = x < cx
            col = P["lit"] if left else P["sh"]
            if (base - y) % 3 == 0:
                col = P["mlit"] if left else P["msh"]                       # course line
            elif (x + course * 3) % 7 == 0:
                col = P["mlit"] if left else P["msh"]                       # staggered joint
            elif h2(x, y) < 0.12:
                col = P["lit2"] if left else P["sh2"]                       # weathering
            if cap and d < height * cap:
                col = P["cap"] if left else P["cap_sh"]                     # Khafre's surviving casing
            if x == cx:
                col = P["ridge"]
            if x == cx + half:
                col = P["edge"]
            if x == cx - half:
                col = P["ridge"] if d > 2 else col
            s.put(x, y, col)
    for y in range(base, G):                                  # bedrock plateau under a raised pyramid
        for x in range(cx - int(height / slope) - 6, cx + int(height / slope) + 7):
            s.put(x, y, s.c("#c49455" if h2(x, y, 9) > 0.2 else "#a97c43", "#3a3c63" if h2(x, y, 9) > 0.2 else "#303257"))
    for x in range(cx - int((base - apex) / slope) - 3, cx + int((base - apex) / slope) + 4):  # sand drift
        for y in range(base - 2, base):
            if h2(x, y, 7) < 0.55:
                s.put(x, y, s.c("#d9a95f", "#3f3f66"))


def sphinx(s, x0):
    """The Great Sphinx, facing left: nemes headdress with stripes, face, chest, long body, paws."""
    w, hgt = 62, 30
    top = G - hgt
    mask = {}

    def add(x, y, part):
        mask[(x, y)] = part

    for r in range(0, 16):                                    # head + nemes
        hw = 3 + min(r, 3) if r < 4 else 6 + min(r - 4, 3)
        for x in range(16 - hw, 16 + hw + 1):
            add(x, r, "head")
    for r in range(3, 13):                                    # face
        for x in range(13, 20):
            add(x, r, "face")
    for r in range(12, 28):                                   # chest
        for x in range(11, 23):
            add(x, r, "body")
    for x in range(20, 60):                                   # back and haunch
        t = (x - 20) / 40
        ytop = round(13 + t * 4 + (2.5 * math.sin((x - 48) / 12 * math.pi) if x > 48 else 0))
        for y in range(ytop, 28):
            add(x, y, "body")
    for y in range(22, 28):                                   # forepaws stretched forward
        for x in range(0, 14):
            if y >= 24 or x > 2:
                add(x, y, "paw")
    for x in range(-2, w):                                    # bedrock plinth
        for y in range(28, 30):
            add(x, y, "rock")
    C = {
        "lit": s.c("#e2b674", "#5d6192"), "mid": s.c("#cd9f5e", "#4f5384"), "dark": s.c("#ad7f45", "#3c3f69"),
        "band": s.c("#bc8d50", "#474a7a"), "edge": s.c("#86592d", "#25274a"), "hi": s.c("#f0cd8e", "#7d82b3"),
        "stripe": s.c("#b07f44", "#41447a"), "face": s.c("#e8c083", "#6a6ea0"), "eye": s.c("#5a3a1b", "#16172e"),
        "rock": s.c("#a98048", "#34375c"),
    }
    for (x, y), part in mask.items():
        if part == "rock":
            col = C["rock"] if h2(x, y) > 0.2 else C["dark"]
        elif part == "face":
            col = C["face"]
            if y == 6 and x in (14, 15, 18):
                col = C["eye"]
            if y == 5 and x in (14, 15, 18):
                col = C["dark"]
            if y == 9 and x == 16:
                col = C["dark"]                               # the missing nose
            if y == 11 and 15 <= x <= 17:
                col = C["mid"]
        elif part == "head":
            col = C["stripe"] if (y % 2 == 0 and y > 3) else C["lit"]
            if x > 19:
                col = C["dark"] if y % 2 == 0 else C["mid"]
        else:
            col = C["lit"] if y < 18 else C["mid"]
            if (y - 13) % 4 == 0:
                col = C["band"]                               # limestone layers
            if y >= 25:
                col = C["dark"] if part == "body" else C["mid"]
            if part == "paw" and x in (1, 4) and y >= 25:
                col = C["edge"]
            if h2(x, y, 3) < 0.07:
                col = C["dark"]
        if (x, y - 1) not in mask and part != "rock":
            col = C["hi"]
        if ((x + 1, y) not in mask or (x, y + 1) not in mask) and part not in ("rock",):
            col = C["edge"]
        s.put(x0 + x, top + y, col)
    s.put(x0 + 57, top + 15, C["edge"])                       # tail curl
    s.put(x0 + 58, top + 16, C["edge"])


def palm(s, x, h=26, base=G):
    trunk_a, trunk_b = s.c("#8a5a2b", "#2a2240"), s.c("#6e4520", "#211a35")
    leaf, leaf2, leaf3 = s.c("#2f6b2f", "#173231"), s.c("#4f9a43", "#22463f"), s.c("#7cc163", "#2e5a50")
    tx = ty = 0
    for i in range(h):
        bx = x + round(math.sin(i / h * 1.4) * 3)
        s.put(bx, base - 1 - i, trunk_a if i % 3 else trunk_b)
        s.put(bx + 1, base - 1 - i, trunk_b)
        tx, ty = bx, base - 1 - i
    fronds = ((-1, -0.45), (1, -0.45), (-1, 0.15), (1, 0.15), (-0.5, -1), (0.55, -0.95), (-0.9, 0.6), (0.95, 0.55))
    for k, (dx, dy) in enumerate(fronds):
        n = 10 + (k % 3)
        for i in range(1, n):
            fx, fy = tx + round(dx * i), ty + round(dy * i + 0.08 * i * i)
            s.put(fx, fy, leaf2 if i < n - 3 else leaf3)
            if i % 2 == 0 and i < n - 2:
                s.put(fx, fy + 1, leaf)                       # leaflets hanging off the rib
    for dx in (-1, 1):
        s.put(tx + dx, ty + 2, s.c("#7a4a1c", "#2a2240"))   # dates


def camel(s, x0, base=G):
    rows = [
        "..##.............",
        ".####............",
        "..###............",
        "...##....###.....",
        "...##..######....",
        "...###########...",
        "....###########..",
        "....##########.#.",
        ".....#########...",
        ".....#.#...#.#...",
        ".....#.#...#.#...",
        "....##.##.##.##..",
    ]
    body, hi = s.c("#b07a3e", "#2c2440"), s.c("#cf9b5a", "#3b3356")
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == "#":
                up = dy == 0 or row and rows[dy - 1][dx] != "#"
                s.put(x0 + dx, base - len(rows) + dy, hi if up else body)


def felucca(s, x0):
    hull, hull2, sail, seam, mast = (s.c("#7a4f2a", "#2a2238"), s.c("#5c3a1d", "#1f1a2e"),
                                     s.c("#fbf7ec", "#aab0d8"), s.c("#e2dccb", "#8d93bd"), s.c("#5c3d1e", "#1c1d38"))
    for i in range(20):                                       # curved hull on the water
        s.put(x0 + i, G, hull)
        if 2 <= i <= 17:
            s.put(x0 + i, G + 1, hull2)
    s.put(x0 - 1, G - 1, hull); s.put(x0 + 20, G - 1, hull)
    s.tri((x0 + 1, G - 6), (x0 + 21, G - 36), (x0 + 19, G - 4),       # lateen sail, yard to boom
          lambda x, y: seam if (x + y) % 5 == 0 else sail)
    s.line(x0 + 12, G - 1, x0 + 12, G - 26, mast)
    s.line(x0 + 1, G - 6, x0 + 21, G - 36, mast)              # long lateen yard
    s.line(x0 + 12, G - 4, x0 + 19, G - 4, mast)              # boom
    for i in range(16):                                       # reflection in the Nile
        if i % 2 == 0:
            s.put(x0 + 3 + i, G + 3, s.c("#8cc0f0", "#3a4f8a"))


def cairo_tower(s, cx):
    """Cairo Tower: concrete lattice shaft (the lotus stem), flaring crown, deck, mast."""
    P = {
        "lat": s.c("#e2bd8f", "#8b7aa8"), "rec": s.c("#9c7048", "#2b2440"), "lat_sh": s.c("#b98e60", "#5d4f7d"),
        "rec_sh": s.c("#7a5432", "#211b33"), "edge": s.c("#6e4a2a", "#1b1630"), "crown": s.c("#ead2aa", "#7d709f"),
        "crown_sh": s.c("#c8a97f", "#5a4e7c"), "win": s.c("#6f8399", "#fde68a"), "frame": s.c("#d6bb93", "#4b4168"),
        "pod": s.c("#cdb391", "#3d3556"), "pod_sh": s.c("#a88d6b", "#2d2744"), "mast": s.c("#9aa3b0", "#7c86a8"),
    }
    base_top, shaft_top = G - 9, G - 112
    for y in range(base_top, G):                              # podium with entrance
        for x in range(cx - 12, cx + 13):
            col = P["pod"] if x < cx + 4 else P["pod_sh"]
            if y == base_top:
                col = P["crown"]
            if abs(x - cx) <= 1 and y > G - 6:
                col = s.c("#4b3a2a", "#fbbf24")
            s.put(x, y, col)
    for y in range(shaft_top, base_top):
        t = (y - shaft_top) / (base_top - shaft_top)
        hw = round(4 + 3 * t)
        for x in range(cx - hw, cx + hw + 1):
            u = x - cx
            mesh = (u + y) % 4 == 0 or (u - y) % 4 == 0
            shade = u > hw // 3
            col = (P["lat_sh"] if shade else P["lat"]) if mesh else (P["rec_sh"] if shade else P["rec"])
            if abs(u) == hw:
                col = P["edge"] if u > 0 else P["lat"]
            s.put(x, y, col)
    # crown: lotus petals flaring out, then the observation deck and the revolving restaurant
    crown = [5, 5, 6, 6, 7, 8, 9, 10, 10, 10, 10, 10, 9, 9, 8, 6, 5, 4, 3]
    for r, hw in enumerate(crown):
        y = shaft_top - 1 - r
        for x in range(cx - hw, cx + hw + 1):
            u = x - cx
            col = P["crown"] if u < hw // 2 else P["crown_sh"]
            if r < 7 and u % 2 == 0:
                col = P["crown_sh"] if u < 0 else P["edge"]  # petal ribs
            if r in (9, 10, 13) and abs(u) < hw:
                col = P["win"] if (u % 2 == 0 or s.night) else P["frame"]
            if r in (8, 11, 12):
                col = P["frame"]
            if abs(u) == hw:
                col = P["edge"] if u > 0 else P["crown"]
            s.put(x, y, col)
    top = shaft_top - 1 - len(crown)
    for i in range(22):                                       # mast with rings
        s.put(cx, top - i, P["mast"])
        if i in (5, 11):
            s.put(cx - 1, top - i, P["mast"]); s.put(cx + 1, top - i, P["mast"])
    s.put(cx, top - 22, s.c("#cbd5e1", "#ef4444"))


def citadel_wall(s, x0, x1, top):
    for y in range(top, G):
        course = (G - y) // 3
        for x in range(x0, x1):
            col = s.c("#cdb489", "#8a6d43")
            if (G - y) % 3 == 0 or (x + course * 3) % 6 == 0:
                col = s.c("#b39a70", "#6f5634")
            if h2(x, y, 5) < 0.08:
                col = s.c("#bea67b", "#7b6039")
            s.put(x, y, col)
    for x in range(x0, x1):                                   # crenellations
        if x % 4 < 2:
            s.put(x, top - 1, s.c("#d8c196", "#9c7d4c"))
            s.put(x, top - 2, s.c("#d8c196", "#9c7d4c"))


def mosque(s, c):
    """Mosque of Muhammad Ali on the Citadel: domes cascading to a ribbed central dome, two
    pencil minarets with balconies, arcaded hall, floodlit at night."""
    P = {
        "st": s.c("#e9dcc0", "#ecc985"), "st2": s.c("#d6c49f", "#d5ad69"), "st_sh": s.c("#b9a682", "#9f7c47"),
        "win": s.c("#5c4a35", "#fde68a"), "dome": s.c("#97a3b6", "#a3a6c3"), "dome_hi": s.c("#c1cad6", "#c8cbe2"),
        "dome_sh": s.c("#69748a", "#62667f"), "rib": s.c("#7a879c", "#8487a5"), "gold": s.c("#d4a72c", "#fbbf24"),
        "min": s.c("#f2e9d4", "#f4dca0"), "min_sh": s.c("#cbbd9b", "#bf9c5e"),
    }
    wall_top = G - 12
    citadel_wall(s, c - 56, c + 57, wall_top)
    hall_top = wall_top - 16
    for y in range(hall_top, wall_top):                       # prayer hall with two arcades
        for x in range(c - 30, c + 31):
            col = P["st"] if x < c + 10 else P["st_sh"]
            if (y - hall_top) % 5 == 0:
                col = P["st2"] if x < c + 10 else P["st_sh"]
            row = y - hall_top
            if row in (2, 3, 4, 8, 9, 10, 11) and (x - c) % 5 == 0:
                col = P["win"]
            if row in (2, 8) and (x - c) % 5 in (1, 4):
                col = P["st2"]
            s.put(x, y, col)

    def dome(cx, cy, r, ribs=True):
        for y in range(cy - r, cy + 1):
            for x in range(cx - r, cx + r + 1):
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy <= r * r + r * 0.8:
                    lightv = -dx / max(r, 1) * 0.7 - dy / max(r, 1) * 0.3
                    col = P["dome_hi"] if lightv > 0.45 else P["dome"] if lightv > -0.25 else P["dome_sh"]
                    if ribs and r > 6 and dx % 4 == 0 and dy < -1:
                        col = P["rib"]
                    if dx * dx + dy * dy > (r - 1) ** 2 and dy > -r // 2 and dx > 0:
                        col = P["dome_sh"]
                    s.put(x, y, col)
        s.put(cx, cy - r - 1, P["gold"]); s.put(cx, cy - r - 2, P["gold"])

    drum_top = hall_top - 6
    for y in range(drum_top, hall_top):                       # drum with windows
        for x in range(c - 15, c + 16):
            col = P["st"] if x < c + 6 else P["st_sh"]
            if y in (drum_top + 2, drum_top + 3) and (x - c) % 3 == 0:
                col = P["win"]
            s.put(x, y, col)
    for dx in (-24, 24):
        dome(c + dx, hall_top, 4, ribs=False)
    for dx in (-18, 18):
        dome(c + dx, hall_top, 8)
    dome(c, drum_top, 15)
    for y in range(drum_top - 22, drum_top - 16):             # finial + crescent
        s.put(c, y, P["gold"])
    s.put(c - 1, drum_top - 23, P["gold"]); s.put(c + 1, drum_top - 23, P["gold"])
    for mx in (c - 35, c + 33):                               # Ottoman pencil minarets
        for y in range(wall_top - 92, wall_top):
            s.put(mx, y, P["min"]); s.put(mx + 1, y, P["min"]); s.put(mx + 2, y, P["min_sh"])
            if (wall_top - y) % 6 == 0:
                s.put(mx + 1, y, P["st2"])
        for by in (wall_top - 50, wall_top - 72):
            for x in range(mx - 2, mx + 5):
                s.put(x, by, P["st_sh"]); s.put(x, by - 1, P["min"])
            for x in range(mx - 1, mx + 4):
                s.put(x, by + 1, P["st_sh"])
            if s.night:
                s.put(mx - 2, by - 1, "#fde68a"); s.put(mx + 4, by - 1, "#fde68a")
        for i in range(12):                                   # lead cone
            w = 3 if i < 4 else 2 if i < 8 else 1
            for x in range(mx + (3 - w) // 2, mx + (3 - w) // 2 + w):
                s.put(x, wall_top - 93 - i, P["dome"] if x == mx else P["dome_sh"])
        s.put(mx + 1, wall_top - 106, P["gold"]); s.put(mx + 1, wall_top - 107, P["gold"])


def cairo_blocks(s, x_from, x_to):
    x = x_from
    while x < x_to:
        w, h = s.layout.randint(6, 10), s.layout.randint(8, 22)
        dish = s.layout.random() < 0.5
        for y in range(G - h, G):
            for xx in range(x, min(x + w, x_to)):
                col = s.c("#d3b892" if xx < x + w - 2 else "#b49a76", "#2a2840" if xx < x + w - 2 else "#221f36")
                if y == G - h:
                    col = s.c("#e3cba6", "#36334f")
                elif xx not in (x, x + w - 1) and (G - y) % 4 == 2 and (xx - x) % 3 == 1:
                    col = s.warm() if s.lit(0.35) else s.c("#7f6a4f", "#1b192c")
                s.put(xx, y, col)
        if dish and x + 3 < x_to:                             # rooftop satellite dish, a Cairo staple
            s.put(x + 2, G - h - 1, s.c("#e5e7eb", "#64748b")); s.put(x + 3, G - h - 2, s.c("#e5e7eb", "#64748b"))
        x += w + s.layout.randint(0, 2)


# ======================================================================= Dubai
def dubai_blocks(s, x_from, x_to, hmin=20, hmax=70):
    x = x_from
    while x < x_to:
        w, h = s.layout.randint(7, 12), s.layout.randint(hmin, hmax)
        crown = s.layout.choice(("flat", "step", "spire"))
        for y in range(G - h, G):
            for xx in range(x, min(x + w, x_to)):
                lit_side = xx < x + w // 2
                col = s.c("#a9b8cc" if lit_side else "#8b9bb2", "#111c31" if lit_side else "#0d1628")
                if (G - y) % 3 == 0:
                    col = s.c("#c0ccdb" if lit_side else "#9eadc2", "#18243c")
                elif xx not in (x, x + w - 1) and (xx - x) % 2 == 1:
                    col = s.warm() if s.lit(0.2) else s.c("#cfdbea" if lit_side else "#a8b7cb", "#1b2740")
                s.put(xx, y, col)
        if crown == "step":
            for xx in range(x + 2, x + w - 2):
                for y in range(G - h - 3, G - h):
                    s.put(xx, y, s.c("#b8c5d6", "#16223a"))
        elif crown == "spire":
            s.line(x + w // 2, G - h - 1, x + w // 2, G - h - 8, s.c("#94a3b8", "#475569"))
        x += w + s.layout.randint(0, 2)


RING = ["..##..", ".#..#.", "#....#", "#....#", ".#..#.", "..##.."]


def dubai_frame(s, x0):
    """Dubai Frame: two gold towers joined by a glass bridge, faced in a ring-pattern screen."""
    P = {"gold": s.c("#e8b93f", "#f7c95a"), "gold_hi": s.c("#f7d677", "#fde68a"), "pat": s.c("#b8862a", "#c48f1e"),
         "side": s.c("#b0801f", "#a8781f"), "glass": s.c("#b9ddf7", "#fff3c4"), "mull": s.c("#7fa9c9", "#f2c14e"),
         "base": s.c("#9aa3b0", "#3b4256")}
    top, wid = G - 108, 46
    pillars = (range(x0, x0 + 10), range(x0 + wid - 10, x0 + wid))
    for y in range(top, G - 3):
        for rng_ in pillars:
            for x in rng_:
                u = x - rng_.start
                col = P["gold"]
                if 1 <= u <= 6 and RING[(y - top) % 6][u - 1] == "#":
                    col = P["pat"]
                if u >= 8:
                    col = P["side"]                           # depth: the tower's east face
                if u == 0:
                    col = P["gold_hi"]
                s.put(x, y, col)
    for y in range(top, top + 13):                            # sky bridge
        for x in range(x0, x0 + wid):
            r = y - top
            col = P["gold"]
            if 1 <= r <= 6 and RING[r - 1][(x - x0) % 6] == "#":
                col = P["pat"]
            if r == 0:
                col = P["gold_hi"]
            if 7 <= r <= 10 and x0 + 2 <= x <= x0 + wid - 3:
                col = P["mull"] if (x - x0) % 4 == 0 or r == 10 else P["glass"]
            if r == 12:
                col = P["side"]
            s.put(x, y, col)
    for y in range(G - 3, G):                                 # plinths
        for x in list(range(x0 - 2, x0 + 12)) + list(range(x0 + wid - 12, x0 + wid + 2)):
            s.put(x, y, P["base"])


def museum_future(s, cx):
    """Museum of the Future: a stainless-steel torus wrapped in calligraphy windows, on a green hill."""
    cy, rx, ry, irx, iry = G - 40, 28, 33, 13, 19
    day = ["#f5f7fa", "#dde3ec", "#b8c2d0", "#8995a7", "#5f6b7e"]
    night = ["#6c789c", "#56628a", "#454f78", "#353e63", "#262d4b"]
    tones = night if s.night else day
    Lx, Ly, Lz = -0.55, -0.6, 0.58
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            dx, dy = x - cx, y - cy
            o = (dx / rx) ** 2 + (dy / ry) ** 2
            i = (dx / irx) ** 2 + ((dy - 4) / iry) ** 2
            if o > 1 or i <= 1:
                continue
            ro, ri = math.sqrt(o), math.sqrt(i)
            u = (1 - ro) / max(1e-6, (1 - ro) + (ri - 1) * 0.8)  # 0 at outer rim, 1 at the hole
            nr = 1 - 2 * u                                   # +1 faces outward, -1 faces the hole
            ang = math.atan2(dy / ry, dx / rx)
            nx, ny, nz = math.cos(ang) * nr, math.sin(ang) * nr, math.sqrt(max(0, 1 - nr * nr))
            light = nx * Lx + ny * Ly + nz * Lz
            k = 0 if light > 0.75 else 1 if light > 0.45 else 2 if light > 0.15 else 3 if light > -0.2 else 4
            col = tones[k]
            f = math.sin(0.62 * x + 1.9 * math.sin(0.23 * y)) + 0.55 * math.sin(0.4 * y + 1.1 * math.sin(0.31 * x))
            if 0.1 < u < 0.92 and abs(f) < 0.2 and h2(x // 3, y // 4, 2) > 0.22:
                col = s.c("#3f4c61" if k < 3 else "#2b3445", "#e0f2fe" if h2(x, y) > 0.3 else "#93c5fd")
            s.put(x, y, col)
    for y in range(G - 12, G):                                # landscaped hill with a ramp
        t = (G - y) / 12
        hw = int(40 * math.sqrt(max(0, 1 - t * t)))
        for x in range(cx - hw, cx + hw + 1):
            col = s.c("#5d8f45" if h2(x, y) > 0.25 else "#4a7536", "#1e3a2e" if h2(x, y) > 0.25 else "#183024")
            if y == G - 12 + int(12 * (1 - math.sqrt(max(0, 1 - ((x - cx) / 40) ** 2)))):
                col = s.c("#86b964", "#2c5240")
            if abs((x - cx) - (y - (G - 12)) * 2.4) < 1.2 and x < cx:
                col = s.c("#d6d3c4", "#4b5563")            # entrance ramp
            s.put(x, y, col)
    for x in range(cx - 4, cx + 5):                           # glass entrance
        for y in range(G - 4, G):
            s.put(x, y, s.c("#3f5873", "#fde68a"))


def burj_khalifa(s):
    _, ground, tower = burj_pixels()
    daytime = {"#e0e7ff", "#eef2ff", "#64748b"}              # the CV's clouds and birds
    body = {"#3b82f6", "#1d4ed8", "#93c5fd"}
    for (tx, ty), col in sorted(tower.items()):
        if not col or col in daytime or ty >= ground:
            continue
        lit = s.lit(0.045)
        if lit and col in body and ty > 100:
            col = s.warm()
        s.put(tx + BURJ_X, ty - (ground - G), col)


def emirates_towers(s, x0):
    """Emirates Towers: twin aluminium-and-glass towers with sloped triangular crowns on a podium."""
    def tower(xa, w, h, slope):
        for x in range(xa, xa + w):
            u = x - xa
            top = G - 10 - h - (w - 1 - u) * slope // w
            face_lit = u < w * 0.6
            for y in range(top, G - 10):
                col = s.c("#9fb7cf" if face_lit else "#7c96b2", "#1c2742" if face_lit else "#151e35")
                if (G - y) % 4 == 0:
                    col = s.c("#d4dbe4" if face_lit else "#aeb8c5", "#2a3553")   # aluminium spandrels
                elif u % 3 == 0:
                    col = s.c("#c4cfdb" if face_lit else "#9aa9bb", "#222c47")   # mullions
                if s.lit(0.18) and (G - y) % 4 == 2:
                    col = s.lights.choice(("#fde68a", "#e0f2fe", "#fbbf24"))
                if u == 0:
                    col = s.c("#e2e8f0", "#475569")
                s.put(x, y, col)
            s.put(x, top, s.c("#f1f5f9", "#94a3b8"))
            s.put(x, top + 1, s.c("#cbd5e1", "#64748b"))
        s.line(xa + w - 1, G - 10 - h, xa + w - 1, G - 10 - h - 10, s.c("#94a3b8", "#cbd5e1"))  # antenna

    tower(x0, 15, 150, 16)
    tower(x0 + 19, 12, 124, 13)
    for y in range(G - 10, G):                                # shared podium
        for x in range(x0 - 3, x0 + 35):
            col = s.c("#8fa6bf", "#1a2540")
            if (G - y) % 3 == 0:
                col = s.c("#c7d0dc", "#2b3655")
            elif s.lit(0.25) and (G - y) % 3 == 1:
                col = "#fde68a"
            s.put(x, y, col)


def burj_al_arab(s, xr):
    """Burj Al Arab: billowing sail on a man-made island, X-braced exoskeleton spine, helipad,
    the cantilevered Al Muntaha deck, and a causeway to the shore. Changes colour at night."""
    base, top = G - 10, G - 134
    for y in range(G - 6, G):                                 # island
        for x in range(xr - 50, xr + 14):
            e = ((x - (xr - 18)) / 32) ** 2 + ((y - G) / 6) ** 2
            if e <= 1:
                col = s.c("#e6d3a3", "#4f4a6b") if e < 0.7 else s.c("#c9b37f", "#3e3a58")
                if e > 0.86:
                    col = s.c("#ffffff", "#7c8cc4")         # surf around the rock armour
                s.put(x, y, col)
    for x in range(xr - 58, xr - 48):                         # causeway
        s.put(x, G - 2, s.c("#d6d3c4", "#3b4256")); s.put(x, G - 1, s.c("#a8a29e", "#2a3042"))
    for y in range(base, G - 5):                              # podium
        for x in range(xr - 34, xr + 4):
            s.put(x, y, s.c("#e5e7eb" if x < xr - 8 else "#c7ccd4", "#3a3f5c"))
    left_at = {}
    for y in range(top, base):
        t = (base - y) / (base - top)
        width = round(40 * (1 - t) ** 0.62 + 2)
        xl = xr - width
        left_at[y] = xl
        for x in range(xl, xr + 1):
            v = (x - xl) / max(1, width)
            if s.night:
                col = "#c4b5fd" if v < 0.12 else "#a78bfa" if t > 0.55 else "#8b5cf6" if t < 0.25 else "#9f7bf8"
                if (x - xl) % 5 == 0:
                    col = "#ddd6fe"
            else:
                col = "#ffffff" if v < 0.15 else "#f3f5f9" if v < 0.7 else "#dfe4ec"
                if (x - xl) % 5 == 0 and v > 0.1:
                    col = "#d3dae4"                          # fabric panel seams
            if x == xl:
                col = s.c("#c8d0da", "#7c3aed")
            s.put(x, y, col)
    for y in range(top - 4, base + 1):                        # exoskeleton: two legs + X braces
        s.put(xr + 1, y, s.c("#f8fafc", "#e0e7ff"))
        s.put(xr + 2, y, s.c("#cbd5e1", "#a5b4fc"))
        if y > top + 4:
            s.put(xr + 8, y, s.c("#e2e8f0", "#c7d2fe"))
    for yb in range(top + 6, base - 20, 26):
        s.line(xr + 2, yb, xr + 8, yb + 26, s.c("#cbd5e1", "#c7d2fe"))
        s.line(xr + 8, yb, xr + 2, yb + 26, s.c("#cbd5e1", "#c7d2fe"))
    s.line(xr + 1, top - 4, xr + 1, top - 22, s.c("#cbd5e1", "#e0e7ff"))   # mast
    if s.night:
        s.put(xr + 1, top - 23, "#ef4444")
    hy = top + 22                                             # helipad on its cantilever
    hx = left_at.get(hy, xr - 10)
    for y in range(hy - 1, hy + 2):
        for x in range(hx - 12, hx + 2):
            col = s.c("#e5e7eb", "#94a3b8")
            if y == hy - 1:
                col = s.c("#f8fafc", "#fbbf24")
            s.put(x, y, col)
    s.put(hx - 6, hy - 1, s.c("#16a34a", "#fde68a")); s.put(hx - 5, hy - 1, s.c("#16a34a", "#fde68a"))
    s.line(hx - 3, hy + 2, hx + 1, hy + 8, s.c("#94a3b8", "#64748b"))
    for y in range(top + 16, top + 21):                       # Al Muntaha, cantilevered seaward
        for x in range(xr + 3, xr + 16):
            col = s.c("#e2e8f0", "#312e81")
            if y in (top + 18, top + 19):
                col = s.c("#5b7da3", "#fde68a")
            s.put(x, y, col)


def ain_dubai(s, cx):
    """Ain Dubai: twin rims with a truss, cable spokes, 48 capsules, A-frame legs on Bluewaters."""
    r, cy = 45, G - 56
    for y in range(G - 5, G):                                 # Bluewaters island
        for x in range(cx - 40, cx + 41):
            if ((x - cx) / 40) ** 2 + ((y - G) / 5) ** 2 <= 1:
                s.put(x, y, s.c("#e6d3a3" if y > G - 4 else "#f3e7c6", "#4f4a6b"))
    spoke, rim, rim2 = s.c("#b8c2d0", "#334155"), s.c("#e5e9f0", "#f472b6"), s.c("#a3aebd", "#60a5fa")
    for a in range(32):
        ang = a * math.pi / 16
        s.line(cx + round(math.cos(ang) * 5), cy + round(math.sin(ang) * 5),
               cx + round(math.cos(ang) * (r - 4)), cy + round(math.sin(ang) * (r - 4)), spoke)
    for i in range(720):
        ang = math.radians(i / 2)
        if s.night:                                           # colour-cycling rim lights
            hue = i / 720
            col_o = "#f472b6" if hue < 0.25 else "#a78bfa" if hue < 0.5 else "#60a5fa" if hue < 0.75 else "#34d399"
            col_i = col_o
        else:
            col_o, col_i = rim, rim2
        s.put(cx + round(math.cos(ang) * r), cy + round(math.sin(ang) * r), col_o)
        s.put(cx + round(math.cos(ang) * (r - 3)), cy + round(math.sin(ang) * (r - 3)), col_i)
        if i % 20 < 10:                                       # truss zigzag between the rims
            rr = r - 1 - (i % 20) // 5
            s.put(cx + round(math.cos(ang) * rr), cy + round(math.sin(ang) * rr), col_i)
    for k in range(48):
        ang = k * math.pi / 24
        x, y = cx + round(math.cos(ang) * (r + 3)), cy + round(math.sin(ang) * (r + 3))
        for dx in (0, 1, 2):
            for dy in (0, 1):
                s.put(x + dx - 1, y + dy, s.c("#5b7da3" if dy else "#e2e8f0", "#fde68a" if dy else "#fbbf24"))
    leg, leg2 = s.c("#cbd5e1", "#94a3b8"), s.c("#94a3b8", "#64748b")
    for sx in (-1, 1):                                        # A-frame legs with cross braces
        s.line(cx, cy, cx + sx * 30, G - 5, leg)
        s.line(cx + sx, cy, cx + sx * 31, G - 5, leg2)
        s.line(cx + sx * 4, cy + 4, cx + sx * 18, G - 5, leg2)
        for t in (0.4, 0.7):
            yy = round(cy + (G - 5 - cy) * t)
            s.line(cx + sx * round(30 * t * 0.6), yy, cx + sx * round(30 * t), yy, leg2)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                s.put(cx + dx, cy + dy, s.c("#64748b" if dx * dx + dy * dy > 6 else "#e2e8f0", "#e0e7ff"))


def dhow(s, x0):
    hull, hull2, sail, seam = s.c("#8a5a2b", "#2a2238"), s.c("#6b4220", "#1f1a2e"), s.c("#f3ead6", "#9aa0c8"), s.c("#d9ccb0", "#7d84b0")
    for i in range(24):
        s.put(x0 + i, G, hull)
        if 2 <= i <= 21:
            s.put(x0 + i, G + 1, hull2)
    for i in range(4):
        s.put(x0 + 23 + i // 2, G - 1 - i, hull)               # raised stern
    s.tri((x0 + 2, G - 8), (x0 + 22, G - 30), (x0 + 20, G - 3), lambda x, y: seam if (x + y) % 5 == 0 else sail)
    s.line(x0 + 11, G - 1, x0 + 11, G - 26, hull)
    s.line(x0 + 2, G - 8, x0 + 22, G - 30, hull)


# ======================================================================= ground
def ground(s):
    for x in range(W):
        for y in range(G, H):
            d = y - G
            if x < X0 + 372:                                   # desert sand
                col = s.c("#dcac62" if (x + 2 * d) % 9 else "#c99550", "#3d3c60" if (x + 2 * d) % 9 else "#34345a")
                if d == 0:
                    col = s.c("#e8bd76", "#47476d")
            elif x < X0 + 442:                                 # the Nile
                col = s.c("#3b7dc4" if (x * 3 + d * 5) % 11 else "#8cc0f0", "#1b2a55" if (x * 3 + d * 5) % 11 else "#3a4f8a")
                if d == 0:
                    col = s.c("#2f6aa8", "#16234a")
            elif x < X0 + 826:                                 # city: pavement, road, lamps
                col = s.c("#7a8194", "#1a2132")
                if d == 0:
                    col = s.c("#a3a9b8", "#2a3348")
                if d in (4, 5):
                    col = s.c("#4b5263", "#111827")
                    if d == 4 and x % 8 < 4:
                        col = s.c("#e5e7eb", "#6b7280")      # lane marking
                if d == 2 and x % 12 == 0:
                    col = s.c("#9aa1b2", "#fbbf24")          # street lamps
            else:                                              # the Gulf
                col = s.c("#2f7fc1" if (x * 3 + d * 7) % 13 else "#86c8f2", "#13204a" if (x * 3 + d * 7) % 13 else "#2f4a8a")
                if d == 0:
                    col = s.c("#5fa8dd" if x % 5 else "#e0f2fe", "#22356a" if x % 5 else "#4a64a8")
            s.put(x, y, col)
    for x in range(X0 + 442, X0 + 826, 12):                   # lamp posts above the pavement
        for y in range(G - 5, G):
            s.put(x, y, s.c("#6b7280", "#334155"))
        s.put(x + 1, G - 5, s.c("#9ca3af", "#fde68a"))


def render(night):
    s = Scene(night)
    dunes(s)
    camel(s, 52)
    camel(s, 74)
    palm(s, 20, 24)
    palm(s, 128, 30)
    palm(s, 162, 22)
    pyramid(s, X0 + 178, 62, base=G - 3, cap=0.17)          # Khafre, on higher bedrock
    pyramid(s, X0 + 90, 66)                                   # Khufu
    pyramid(s, X0 + 266, 34)                                  # Menkaure
    sphinx(s, X0 + 300)
    palm(s, X0 + 368, 26)
    palm(s, X0 + 440, 22)
    cairo_blocks(s, X0 + 446, X0 + 478)
    cairo_tower(s, X0 + 462)
    mosque(s, X0 + 534)
    dubai_blocks(s, X0 + 592, X0 + 604, 18, 40)
    dubai_blocks(s, X0 + 648, X0 + 712, 30, 80)
    dubai_blocks(s, X0 + 786, X0 + 830, 24, 70)
    burj_khalifa(s)
    dubai_frame(s, X0 + 600)
    museum_future(s, X0 + 680)
    emirates_towers(s, X0 + 792)
    ground(s)
    felucca(s, X0 + 392)
    burj_al_arab(s, X0 + 884)
    ain_dubai(s, X0 + 934)
    dhow(s, X0 + 1060)
    return s.px


def main():
    for night, name in ((False, "px-scene-day.png"), (True, "px-scene-night.png")):
        write_png(ROOT / name, render(night))
    print(f"wrote px-scene-day.png, px-scene-night.png {W}x{H}; core {CORE}; ground row {G}; Burj Khalifa spire x={BURJ_X + 40}")


if __name__ == "__main__":
    main()
