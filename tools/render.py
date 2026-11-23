#!/usr/bin/env python3
"""Render the "Day one, day seven" TikTok video frames.

The video is about one tiny agent-built game, SPROUT SIEGE, at the same
moment on the day it was made and after seven days of daily updates. The
camera never moves: one fixed garden map, one wave of slimes entering at
the same times from the same gate. Day one is sparse and grey; day seven
is the identical shot bursting with life. Everything is drawn frame by
frame with PIL — the low-res garden is rendered at 270x480 and upscaled
x4 with NEAREST for a chunky game look, while HUD text and captions are
drawn at full 1080x1920 so they stay crisp.

Usage: python3 render.py <frames-dir>
Frames are written as f0000.png ... at 30 fps for a 26.0 s video.
Audio lives in audio.py; assembly and the make.fun end card are ffmpeg
steps (see README.md).
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- setup

LW, LH, S = 270, 480, 4            # low-res canvas and upscale factor
W, H = LW * S, LH * S              # 1080 x 1920
FPS = 30
DURATION = 26.0
FRAMES = int(FPS * DURATION)

WORK = os.path.expanduser("~/workspace/makefun/tiktok-day-work")
FONT_BLACK_CANDIDATES = [
    os.path.join(WORK, "ArchivoBlack-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


_FONT_CACHE = {}


def font_black(size):
    if ("black", size) not in _FONT_CACHE:
        _FONT_CACHE[("black", size)] = load_font(FONT_BLACK_CANDIDATES, size)
    return _FONT_CACHE[("black", size)]


def font_bold(size):
    if ("bold", size) not in _FONT_CACHE:
        _FONT_CACHE[("bold", size)] = ImageFont.truetype(FONT_BOLD, size)
    return _FONT_CACHE[("bold", size)]


DMG_FONT = ImageFont.truetype(FONT_BOLD, 11)  # damage numbers, loaded once


# ---------------------------------------------------------------- helpers

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def ease_out_back(t):
    t = clamp(t, 0.0, 1.0)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def ease_out(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


def h2(i, salt=0):
    """Deterministic pseudo-random in [0,1) from an integer id."""
    x = math.sin(i * 127.1 + salt * 311.7) * 43758.5453
    return x - math.floor(x)


def text_size(d, s, f, stroke=0):
    box = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    return box[2] - box[0], box[3] - box[1]


def draw_centered(base, s, cx, y, f, fill, stroke=0, stroke_fill=(10, 10, 14)):
    d = ImageDraw.Draw(base)
    w, h = text_size(d, s, f, stroke)
    d.text((cx - w / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return h


# ---------------------------------------------------------------- the map
# One fixed garden: sky strip, a dirt path down the middle, planting beds
# on both sides, a pond bottom-left, the cottage at the bottom. The same
# layout is drawn for both days; only what fills it changes.

PATH_X0, PATH_X1 = 117, 153
BEDS = [  # (x0, y0, x1, y1) planting beds, left and right of the path
    (16, 84, 102, 138), (168, 84, 254, 138),
    (16, 154, 102, 208), (168, 154, 254, 208),
    (16, 224, 102, 278), (168, 224, 254, 278),
    (16, 294, 102, 348), (168, 294, 254, 348),
]
FLOWERS = [(59, 111), (211, 181), (59, 251), (211, 321)]  # sunflower spots (bed centres)
SLIME_SPAWNS = [0.3, 1.5, 2.7]     # identical in both builds — the same moment


def slime_y_day1(dt):
    return 24 + 55 * dt


def slime_y_day7(idx, dt):
    """Same start as day one; from dt=1.2 the garden fights back."""
    if idx == 2:  # the big one lumbers at a steady pace
        return 24 + 40 * dt
    if dt <= 1.2:
        return 24 + 55 * dt
    return 24 + 55 * 1.2 + 30 * (dt - 1.2)


SLIME_DEATH_DAY7 = {0: 4.4, 1: 5.6, 2: 9.9}   # dt at which each slime pops (boss: in the finale)


def draw_sky(d, day7, t):
    if day7:
        for y in range(0, 54):
            f = y / 54
            d.line([(0, y), (LW, y)], fill=(int(lerp(96, 168, f)), int(lerp(186, 226, f)), int(lerp(240, 250, f))))
        # rainbow
        cx, cy = 135, 66
        cols = [(255, 107, 107), (255, 166, 66), (255, 217, 61), (106, 214, 106), (84, 160, 255)]
        for i, c in enumerate(cols):
            r = 108 - i * 6
            d.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=c, width=5)
        # sun with slow rays
        sx, sy = 232, 26
        for k in range(8):
            a = t * 0.15 + k * math.pi / 4
            d.line([(sx + 13 * math.cos(a), sy + 13 * math.sin(a)), (sx + 18 * math.cos(a), sy + 18 * math.sin(a))], fill=(255, 205, 60), width=2)
        d.ellipse([sx - 11, sy - 11, sx + 11, sy + 11], fill=(255, 214, 64), outline=(240, 176, 32), width=2)
    else:
        d.rectangle([0, 0, LW, 54], fill=(148, 163, 168))
        d.ellipse([221, 15, 243, 37], fill=(196, 200, 196))  # pale, tired sun
    # the same three clouds drift the same way on both days
    cloud_c = (255, 255, 255) if day7 else (176, 186, 188)
    for i, (bx, by, s) in enumerate([(38, 22, 1.0), (178, 14, 0.75), (108, 34, 0.6)]):
        x = bx + 5 * math.sin(t * 0.11 + i * 2.0)
        d.ellipse([x - 13 * s, by - 6 * s, x + 13 * s, by + 6 * s], fill=cloud_c)
        d.ellipse([x - 6 * s, by - 10 * s, x + 7 * s, by + 4 * s], fill=cloud_c)


def draw_field(d, day7, t):
    grass_a, grass_b = ((87, 166, 57), (96, 176, 64)) if day7 else ((116, 128, 96), (110, 121, 90))
    d.rectangle([0, 54, LW, LH], fill=grass_a)
    for i in range(9):  # mow stripes
        if i % 2 == 0:
            d.rectangle([0, 54 + i * 48, LW, 54 + (i + 1) * 48], fill=grass_b)
    # dirt path
    path_c = (217, 183, 124) if day7 else (168, 148, 116)
    d.rectangle([PATH_X0, 54, PATH_X1, LH], fill=path_c)
    for i in range(14):  # path stones, same spots both days
        x = 122 + h2(i, 1) * 26
        y = 66 + i * 29 + h2(i, 2) * 8
        d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=(196, 164, 110) if day7 else (150, 132, 100))
    # gate the slimes come through
    d.rectangle([PATH_X0 - 4, 52, PATH_X1 + 4, 60], fill=(122, 82, 46))
    d.rectangle([PATH_X0 - 4, 52, PATH_X0, 74], fill=(106, 70, 38))
    d.rectangle([PATH_X1, 52, PATH_X1 + 4, 74], fill=(106, 70, 38))
    # planting beds
    for (x0, y0, x1, y1) in BEDS:
        soil = (138, 90, 51) if day7 else (122, 98, 72)
        edge = (117, 80, 44) if day7 else (104, 84, 62)
        d.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=soil, outline=edge, width=2)
        for r in range(3):
            yy = y0 + 10 + r * 16
            d.line([(x0 + 7, yy), (x1 - 7, yy)], fill=edge, width=1)
    # pond bottom-left: full of life on day 7, a dry cracked patch on day 1
    if day7:
        d.ellipse([14, 386, 96, 438], fill=(86, 178, 232), outline=(62, 148, 205), width=2)
        d.ellipse([24, 396, 52, 408], fill=(140, 205, 245))
        # duck, bobbing
        dy = 2 * math.sin(t * 2.0)
        d.ellipse([46, 402 + dy, 74, 416 + dy], fill=(255, 255, 255))
        d.ellipse([66, 394 + dy, 78, 406 + dy], fill=(255, 255, 255))
        d.polygon([(78, 400 + dy), (84, 402 + dy), (78, 404 + dy)], fill=(255, 150, 40))
        d.point((71, 399 + dy), fill=(20, 20, 20))
    else:
        d.ellipse([14, 386, 96, 438], fill=(146, 118, 84), outline=(120, 96, 66), width=2)
        for i in range(4):
            x, y = 30 + i * 15, 398 + (i % 2) * 18
            d.line([(x, y), (x + 8, y + 6), (x + 3, y + 12)], fill=(110, 88, 60), width=1)
    # trees in the top corners: bare on day 1, leafy on day 7
    for (tx, flip) in [(24, 1), (246, -1)]:
        d.line([(tx, 84), (tx + 2 * flip, 62)], fill=(106, 70, 38), width=3)
        if day7:
            for (ox, oy, r) in [(-9, 52, 11), (9, 50, 12), (0, 42, 13)]:
                d.ellipse([tx + ox - r, oy - r, tx + ox + r, oy + r], fill=(64, 148, 62), outline=(50, 122, 50), width=1)
            for i in range(3):
                ax, ay = tx - 8 + i * 8, 48 + (i % 2) * 9
                d.ellipse([ax - 2, ay - 2, ax + 2, ay + 2], fill=(232, 64, 64))
        else:
            for a in (-0.7, -0.2, 0.4):
                d.line([(tx + 2 * flip, 62), (tx + 2 * flip + 10 * math.sin(a), 62 - 12 * math.cos(a))], fill=(106, 70, 38), width=1)


def draw_house(d, day7, t):
    # the cottage the slimes are marching on
    d.rectangle([104, 436, 166, 478], fill=(242, 227, 198), outline=(190, 160, 120), width=1)
    d.polygon([(98, 438), (172, 438), (135, 414)], fill=(181, 80, 47), outline=(150, 62, 36))
    d.rectangle([128, 452, 142, 478], fill=(122, 82, 46))
    d.rectangle([110, 446, 120, 456], fill=(255, 226, 130) if day7 else (120, 120, 116), outline=(150, 120, 84))
    d.rectangle([150, 446, 160, 456], fill=(255, 226, 130) if day7 else (120, 120, 116), outline=(150, 120, 84))
    if day7:
        d.rectangle([146, 420, 152, 436], fill=(160, 160, 160))  # chimney
        for k in range(3):  # smoke puffs
            ph = (t * 0.5 + k / 3) % 1.0
            r = 3 + ph * 5
            d.ellipse([149 - r + ph * 6, 420 - ph * 22 - r, 149 + r + ph * 6, 420 - ph * 22 + r], fill=(235, 240, 244))
        # bunting flags across the front
        cols = [(255, 107, 107), (255, 205, 60), (106, 214, 106), (84, 160, 255), (255, 111, 199)]
        for i in range(6):
            x = 106 + i * 10
            y = 440 + 3 * math.sin(i * 1.1)
            d.polygon([(x, y), (x + 9, y), (x + 4, y + 8)], fill=cols[i % len(cols)])
        # flower boxes
        for x in (108, 148):
            d.rectangle([x, 458, x + 14, 463], fill=(150, 96, 54))
            for i in range(3):
                d.ellipse([x + 2 + i * 5, 454, x + 5 + i * 5, 457], fill=(255, 111, 164))


def draw_sprout(d, x, y, t, wilt=0.0):
    """The day-one hero: one droopy sprout, drawn big enough to root for."""
    sway = 2.6 * math.sin(t * 1.3)
    d.line([(x, y), (x + sway, y - 17)], fill=(74, 128, 62), width=3)
    d.ellipse([x + sway - 10, y - 26, x + sway - 1, y - 16], fill=(96, 160, 80), outline=(70, 122, 58), width=1)
    d.ellipse([x + sway + 1, y - 27 + wilt * 5, x + sway + 10, y - 17 + wilt * 5], fill=(88, 148, 74), outline=(70, 122, 58), width=1)
    d.ellipse([x - 6, y - 2, x + 6, y + 2], fill=(104, 76, 46))  # its little mound of dirt


def draw_sunflower(d, x, y, t, fire_flash=0.0):
    sway = 1.5 * math.sin(t * 1.7 + x)
    d.line([(x, y + 14), (x + sway, y - 6)], fill=(56, 122, 52), width=2)
    d.ellipse([x - 8, y + 6, x - 2, y + 12], fill=(74, 150, 66))
    d.ellipse([x + 2, y + 4, x + 8, y + 10], fill=(74, 150, 66))
    hx, hy = x + sway, y - 12
    for k in range(8):
        a = k * math.pi / 4 + 0.3 * math.sin(t * 2 + x)
        px, py = hx + 8 * math.cos(a), hy + 8 * math.sin(a)
        d.ellipse([px - 3.4, py - 3.4, px + 3.4, py + 3.4], fill=(255, 196, 32), outline=(238, 166, 20))
    r = 6 + fire_flash * 1.5
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=(122, 80, 40), outline=(96, 62, 30))
    d.point((hx - 2, hy - 1), fill=(70, 46, 22))
    d.point((hx + 2, hy + 2), fill=(70, 46, 22))


def draw_bed_plants_day7(d, t):
    # sunflowers on four beds
    for (x, y) in FLOWERS:
        draw_sunflower(d, x, y, t)
    # berry bushes on two beds
    for (x, y) in [(59, 181), (211, 251)]:
        for (ox, oy, r) in [(-10, 2, 10), (0, -4, 12), (10, 2, 10), (0, 6, 11)]:
            d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=(58, 138, 60), outline=(44, 112, 48))
        for i in range(5):
            bx, by = x - 8 + h2(i, x) * 16, y - 4 + h2(i, y) * 10
            d.ellipse([bx - 2, by - 2, bx + 2, by + 2], fill=(236, 64, 92))
    # mushroom with drifting spores
    x, y = 59, 321
    d.rectangle([x - 3, y + 2, x + 3, y + 12], fill=(240, 230, 205))
    d.pieslice([x - 11, y - 8, x + 11, y + 10], start=180, end=360, fill=(226, 54, 64), outline=(190, 40, 52))
    for (ox, oy) in [(-5, -3), (2, -5), (6, -1)]:
        d.ellipse([x + ox - 1.6, y + oy - 1.6, x + ox + 1.6, y + oy + 1.6], fill=(255, 255, 255))
    # cactus with a flower
    x, y = 211, 111
    d.rounded_rectangle([x - 5, y - 12, x + 5, y + 14], radius=5, fill=(66, 160, 92), outline=(50, 128, 72))
    d.rounded_rectangle([x - 12, y - 4, x - 6, y + 6], radius=3, fill=(66, 160, 92), outline=(50, 128, 72))
    d.rounded_rectangle([x + 6, y - 8, x + 12, y + 4], radius=3, fill=(66, 160, 92), outline=(50, 128, 72))
    d.ellipse([x - 3, y - 17, x + 3, y - 11], fill=(255, 111, 180))


def draw_sprinklers(d, t):
    for (x, y) in [(110, 226), (160, 306)]:
        d.rectangle([x - 2, y, x + 2, y + 8], fill=(150, 158, 166))
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(110, 190, 235), outline=(70, 140, 190))
        sweep = math.sin(t * 2.3 + x) * 0.8
        for k in range(9):
            a = -math.pi / 2 + sweep + (k - 4) * 0.16
            for dist in (10, 16, 22):
                px = x + dist * math.cos(a) * 1.25
                py = y + dist * math.sin(a) + dist * dist * 0.012
                d.point((px, py), fill=(140, 205, 250))
                d.point((px + 1, py), fill=(140, 205, 250))


def draw_slime(d, x, y, t, scale, day7, hp_frac=None):
    w, h = 23 * scale, 19 * scale
    hop = abs(math.sin(t * 6.0)) * 3.2 * scale
    squash = 1 - 0.10 * math.sin(t * 12.0)
    hh, ww = h * squash, w * (2 - squash) / 1.0 * 0.95 + w * 0.05
    y2 = y - hop
    body = (96, 205, 84) if day7 else (128, 148, 116)
    edge = (62, 158, 58) if day7 else (102, 122, 96)
    d.ellipse([x - ww / 2, y2 - hh / 2, x + ww / 2, y2 + hh / 2], fill=body, outline=edge, width=max(1, int(scale)))
    d.ellipse([x - ww * 0.28, y2 - hh * 0.34, x - ww * 0.05, y2 - hh * 0.12], fill=(255, 255, 255, ) if False else (170, 235, 160) if day7 else (168, 182, 158))
    for sgn in (-1, 1):
        ex = x + sgn * ww * 0.18
        ey = y2 - hh * 0.08
        d.ellipse([ex - 2.6 * scale, ey - 3 * scale, ex + 2.6 * scale, ey + 3 * scale], fill=(255, 255, 255))
        d.ellipse([ex - 1.2 * scale, ey - 1.4 * scale, ex + 1.2 * scale, ey + 1.6 * scale], fill=(24, 28, 24))
    d.arc([x - 4 * scale, y2 + hh * 0.08, x + 4 * scale, y2 + hh * 0.34], start=15, end=165, fill=(30, 60, 30), width=1)
    if hp_frac is not None:
        bw = 46 * scale
        d.rectangle([x - bw / 2, y2 - hh / 2 - 10, x + bw / 2, y2 - hh / 2 - 5], fill=(40, 40, 48))
        d.rectangle([x - bw / 2 + 1, y2 - hh / 2 - 9, x - bw / 2 + 1 + (bw - 2) * clamp(hp_frac, 0, 1), y2 - hh / 2 - 6], fill=(240, 70, 80))


def draw_bot(d, x, y, t, awake):
    bob = abs(math.sin(t * 7)) * 1.6 if awake else 0
    y = y - bob
    d.rounded_rectangle([x - 7, y - 6, x + 7, y + 6], radius=3, fill=(240, 244, 248), outline=(120, 134, 148), width=1)
    d.rectangle([x - 5, y - 4, x + 5, y + 1], fill=(64, 200, 230))  # visor
    d.line([(x, y - 6), (x, y - 11)], fill=(120, 134, 148), width=1)
    d.ellipse([x - 2, y - 14, x + 2, y - 10], fill=(255, 111, 164))
    d.rectangle([x - 10, y - 2, x - 7, y + 3], fill=(200, 208, 216))
    d.rectangle([x + 7, y - 2, x + 10, y + 3], fill=(200, 208, 216))
    # cap
    d.pieslice([x - 7, y - 12, x + 7, y - 2], start=180, end=360, fill=(196, 28, 131))
    if not awake:
        for k in range(3):
            ph = (t * 0.45 + k / 3) % 1.0
            zx = x + 12 + ph * 10
            zy = y - 12 - ph * 16
            s = 2 + ph * 3
            d.line([(zx - s, zy + s), (zx + s, zy + s), (zx - s, zy - s), (zx + s, zy - s)], fill=(90, 110, 130), width=1)


def bot_pos_day7(t):
    pts = [(95, 120), (185, 175), (90, 255), (185, 325), (130, 392), (80, 330), (175, 250), (95, 160)]
    n = len(pts)
    seg = 1.05
    total = seg * n
    tt = t % total
    i = int(tt / seg)
    f = (tt - i * seg) / seg
    f = f * f * (3 - 2 * f)
    x = lerp(pts[i][0], pts[(i + 1) % n][0], f)
    y = lerp(pts[i][1], pts[(i + 1) % n][1], f)
    return x, y


# ---------------------------------------------------------------- scenes

def living_slimes_day7(t):
    """(idx, x, y, scale) for slimes alive at day-7 clock t."""
    out = []
    for idx, spawn in enumerate(SLIME_SPAWNS):
        dt = t - spawn
        if dt < 0 or dt >= SLIME_DEATH_DAY7[idx]:
            continue
        scale = 1.9 if idx == 2 else 1.0
        y = slime_y_day7(idx, dt)
        x = 135 + 6 * math.sin(dt * 2.1 + idx * 1.7)
        out.append((idx, x, y, scale))
    return out


def draw_projectiles_and_hits(d, t):
    """Sunflower seeds converging on the lead slime, plus damage numbers."""
    living = living_slimes_day7(t)
    if not living:
        return
    for fi, (fx, fy) in enumerate(FLOWERS):
        cycle = 0.45
        off = fi * 0.13
        lt = t - off
        if lt < 0:
            continue
        k = math.floor(lt / cycle)
        ph = (lt - k * cycle) / cycle
        # target: the living slime nearest this flower when the shot was fired
        tgt = min(living, key=lambda s: abs(s[2] - fy) + abs(s[1] - fx))
        tx, ty = tgt[1], tgt[2] - 4
        if ph < 0.36:  # seed in flight
            f = ph / 0.36
            x = lerp(fx, tx, f)
            y = lerp(fy - 12, ty, f) - math.sin(f * math.pi) * 7
            d.ellipse([x - 1.8, y - 1.8, x + 1.8, y + 1.8], fill=(255, 240, 170), outline=(214, 164, 60))
    # damage numbers: a hit lands every 0.55 s on each slime after dt 1.2
    for (idx, x, y, scale) in living:
        dt = t - SLIME_SPAWNS[idx]
        if dt < 1.2:
            continue
        last = 1.2 + math.floor((dt - 1.2) / 0.55) * 0.55
        age = dt - last
        if age < 0.75:
            val = 12 + int(h2(idx * 31 + int(last * 10), 5) * 22)
            yy = y - 20 * scale - age * 16
            alpha = 1 - age / 0.75
            col = (int(lerp(90, 255, alpha)), int(lerp(90, 90, alpha)), int(lerp(90, 60, alpha)))
            d.text((x + 10 * scale, yy), f"-{val}", font=DMG_FONT, fill=col, stroke_width=1, stroke_fill=(60, 30, 20))


def draw_bees_and_butterflies(d, t):
    for i in range(5):
        fx, fy = FLOWERS[i % len(FLOWERS)]
        a = t * 2.6 + i * 1.9
        x = fx + 15 * math.cos(a)
        y = fy - 16 + 6 * math.sin(a * 1.7)
        d.ellipse([x - 2.6, y - 2, x + 2.6, y + 2], fill=(255, 205, 40), outline=(160, 120, 20))
        flap = math.sin(t * 34 + i) * 1.6
        d.ellipse([x - 3.4, y - 4.4 - flap, x - 0.4, y - 1.8], fill=(240, 248, 255))
        d.ellipse([x + 0.4, y - 4.4 + flap, x + 3.4, y - 1.8], fill=(240, 248, 255))
    for i in range(2):
        x = 135 + 95 * math.sin(t * 0.42 + i * 2.6)
        y = 200 + 90 * math.sin(t * 0.9 + i * 1.8)
        flap = abs(math.sin(t * 10 + i * 3))
        col = (255, 140, 200) if i == 0 else (150, 190, 255)
        d.ellipse([x - 4 - 2 * flap, y - 3, x, y + 3], fill=col)
        d.ellipse([x, y - 3, x + 4 + 2 * flap, y + 3], fill=col)
        d.point((x, y), fill=(40, 40, 40))


def draw_death_burst(d, t, idx):
    """Coin burst where a slime popped (drawn for 0.9 s after its death)."""
    death = SLIME_SPAWNS[idx] + SLIME_DEATH_DAY7[idx]
    age = t - death
    if age < 0 or age > 0.9:
        return
    cx = 135 + 6 * math.sin(SLIME_DEATH_DAY7[idx] * 2.1 + idx * 1.7)
    cy = slime_y_day7(idx, SLIME_DEATH_DAY7[idx])
    for k in range(9):
        a = h2(k, idx + 40) * math.pi * 2
        v = 26 + h2(k, idx + 41) * 30
        x = cx + math.cos(a) * v * age
        y = cy + math.sin(a) * v * age + 60 * age * age
        r = 3.2 * (1 - age / 1.1)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 205, 50), outline=(206, 152, 30))
    r = 6 + age * 26
    d.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], outline=(255, 255, 255), width=2)


def scene_day1(t):
    """Segment A: the game on the day it was made. Sparse, grey, hopeful."""
    img = Image.new("RGB", (LW, LH))
    d = ImageDraw.Draw(img)
    draw_sky(d, False, t)
    draw_field(d, False, t)
    draw_house(d, False, t)
    # one sprout, bravely defending bed row 2
    sx, sy = 59, 181
    draw_sprout(d, sx, sy, t, wilt=0.4)
    # the sprout plinks a seed at slime 1 every 1.3 s — and misses, every time
    living = []
    for idx, spawn in enumerate(SLIME_SPAWNS):
        dt = t - spawn
        if dt < 0:
            continue
        y = slime_y_day1(dt)
        x = 135 + 6 * math.sin(dt * 2.1 + idx * 1.7)
        living.append((idx, x, y))
    cyc = (t % 1.3) / 1.3
    if living and t > 0.6:
        idx, tx, ty = living[0]
        f = cyc
        x = lerp(sx + 3, tx + 15, f)          # aim is... optimistic (15 px wide)
        y = lerp(sy - 16, ty + 4, f) + 26 * f * f
        if f < 0.92:
            d.ellipse([x - 1.6, y - 1.6, x + 1.6, y + 1.6], fill=(220, 200, 140))
        elif f < 1.0:  # dirt puff where it lands
            d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=(150, 124, 92))
    for (idx, x, y) in living:
        draw_slime(d, x, y, t - SLIME_SPAWNS[idx], 1.0, False)
    # the gardener bot, asleep on the job
    draw_bot(d, 92, 402, t, awake=False)
    return img


def scene_day7(t):
    """Segment B + finale: the identical moment, seven updates later."""
    img = Image.new("RGB", (LW, LH))
    d = ImageDraw.Draw(img)
    draw_sky(d, True, t)
    draw_field(d, True, t)
    draw_bed_plants_day7(d, t)
    draw_sprinklers(d, t)
    draw_house(d, True, t)
    living = living_slimes_day7(t)
    draw_projectiles_and_hits(d, t)
    for idx in range(3):
        draw_death_burst(d, t, idx)
    for (idx, x, y, scale) in living:
        hp = None
        if idx == 2:
            hp = 1 - clamp((t - SLIME_SPAWNS[2] - 1.2) / (SLIME_DEATH_DAY7[2] - 1.2), 0, 1)
        draw_slime(d, x, y, t - SLIME_SPAWNS[idx], scale, True, hp_frac=hp)
    bx, by = bot_pos_day7(t)
    draw_bot(d, bx, by, t, awake=True)
    # watering sparkles trailing the bot
    for k in range(5):
        ph = (t * 1.4 + k / 5) % 1.0
        px, py = bot_pos_day7(t - ph * 0.55)
        r = 1.8 * (1 - ph)
        d.ellipse([px - r, py + 6 - r, px + r, py + 6 + r], fill=(170, 225, 255))
    draw_bees_and_butterflies(d, t)
    return img


# ---------------------------------------------------------------- full-res layer

def pill(d, x, y, w, h, alpha=168):
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=(12, 14, 20, alpha))


def draw_hud(base, day7, t, gt):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = font_bold(42)
    # title pill, top-left (wide enough for the name and the version tag)
    pill(d, 36, 40, 560, 76)
    d.text((62, 55), "SPROUT SIEGE", font=f, fill=(255, 255, 255, 255))
    d.text((448, 55), "v1.7" if day7 else "v0.1", font=f, fill=(140, 230, 160, 255) if day7 else (200, 200, 200, 255))
    # coins pill, top-right
    pill(d, 700, 40, 344, 76)
    d.ellipse([726, 58, 766, 98], fill=(255, 205, 50, 255), outline=(206, 152, 30, 255), width=3)
    d.text((742, 62), "$", font=font_bold(34), fill=(146, 104, 16, 255))
    if day7:
        kills = sum(1 for i in range(3) if t >= SLIME_SPAWNS[i] + SLIME_DEATH_DAY7[i])
        coins = 8940 + 25 * kills + int(max(0.0, t) * 7)
    else:
        coins = 12
    s = f"{coins:,}"
    tw, _ = text_size(d, s, f)
    d.text((1024 - tw, 54), s, font=f, fill=(255, 255, 255, 255))
    # wave pill under the title
    pill(d, 36, 132, 300, 64)
    d.text((62, 143), "WAVE 7" if day7 else "WAVE 1", font=font_bold(38), fill=(255, 255, 255, 255))
    if day7:
        combo = min(24, 3 + int(max(0.0, t) * 2.2))
        pill(d, 700, 132, 344, 64)
        d.text((726, 143), f"COMBO x{combo}", font=font_bold(38), fill=(255, 214, 90, 255))
        bw = 300 * (0.35 + 0.65 * abs(math.sin(gt * 1.4)))
        d.rounded_rectangle([722, 182, 722 + bw, 190], radius=4, fill=(255, 140, 60, 220))
    base.alpha_composite(ov)


def caption(base, lines, y=1330, size=64, fill=(255, 255, 255), accent=None):
    f = font_black(size)
    d = ImageDraw.Draw(base)
    yy = y
    for line in lines:
        col = fill
        if accent and accent[0] in line:
            # draw the line in white, then the accent word over it in colour
            draw_centered(base, line, W // 2, yy, f, fill, stroke=7)
            pre = line.split(accent[0])[0]
            d2 = ImageDraw.Draw(base)
            wpre, _ = text_size(d2, pre, f, 7)
            wline, hh = text_size(d2, line, f, 7)
            d2.text((W // 2 - wline / 2 + wpre, yy), accent[0], font=f, fill=accent[1], stroke_width=7, stroke_fill=(10, 10, 14))
            yy += hh + 10
        else:
            hh = draw_centered(base, line, W // 2, yy, f, col, stroke=7)
            yy += hh + 10


def slam(base, word, gt, t0, colour, sub=None):
    """Big DAY N title: scales in with overshoot, holds, fades."""
    lt = gt - t0
    if lt < 0 or lt > 1.25:
        return
    scale = ease_out_back(min(lt / 0.28, 1.0))
    alpha = 1.0 if lt < 0.95 else 1 - (lt - 0.95) / 0.3
    size = int(215 * scale)
    if size < 8:
        return
    layer = Image.new("RGBA", (W, 560), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font_black(size)
    tw, th = text_size(d, word, f, 10)
    d.text(((W - tw) / 2, (430 - th) / 2), word, font=f, fill=colour + (255,), stroke_width=10, stroke_fill=(12, 10, 16, 255))
    if sub:
        draw_centered(layer, sub, W // 2, 330, font_bold(46), (255, 255, 255, 255), stroke=5)
    layer = layer.rotate(2.5 * math.sin(gt * 22) * (1 - lt) if lt < 0.3 else -2, resample=Image.BICUBIC, center=(W // 2, 280))
    if alpha < 1:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer.putalpha(a)
    base.alpha_composite(layer, (0, 400))


def draw_montage(base_bg, gt):
    """Patch-note montage between the two days (global 5.2 - 8.2)."""
    lt = gt - 5.2
    base = base_bg.copy()
    d = ImageDraw.Draw(base)
    # calendar card flipping DAY 2 .. DAY 7
    day = min(7, 2 + int(lt / 0.5))
    flip = (lt % 0.5)
    squash = 1 - 0.55 * max(0.0, 1 - flip / 0.09) if flip < 0.09 else 1.0
    cw, ch = 470, 540
    chh = ch * squash
    cx, cy = W // 2, 800
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([6, 6, cw - 6, ch - 6], radius=36, fill=(252, 252, 250, 255), outline=(20, 20, 26, 255), width=5)
    cd.rounded_rectangle([6, 6, cw - 6, 130], radius=36, fill=(226, 54, 84, 255))
    cd.rectangle([6, 90, cw - 6, 130], fill=(226, 54, 84, 255))
    draw_centered(card, "DAY", cw // 2, 150, font_black(120), (20, 20, 26))
    draw_centered(card, str(day), cw // 2, 270, font_black(230), (196, 28, 131))
    draw_centered(card, "of daily updates", cw // 2, 480, font_bold(40), (90, 90, 100))
    card = card.resize((cw, max(8, int(chh))), Image.BILINEAR)
    base.alpha_composite(card, (cx - cw // 2, int(cy - chh / 2)))
    # patch-note sticky chips popping in
    notes = [
        (5.75, "+ SUNFLOWERS", 120, 300, -5),
        (6.25, "+ SPRINKLERS", 600, 330, 4),
        (6.75, "+ BEES?!", 150, 1420, 3),
        (7.25, "+ NIGHT GLOW", 590, 1450, -4),
        (7.75, "+ BOSS MODE", 300, 1600, 2),
    ]
    for (t0, s, x, y, rot) in notes:
        age = lt + 5.2 - t0
        if age < 0:
            continue
        sc = ease_out_back(min(age / 0.22, 1.0))
        fw, fh = 430, 104
        chip = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        cd2 = ImageDraw.Draw(chip)
        cd2.rounded_rectangle([4, 4, fw - 4, fh - 4], radius=20, fill=(255, 217, 77, 255), outline=(20, 20, 26, 255), width=4)
        draw_centered(chip, s, fw // 2, 26, font_bold(46), (24, 22, 18))
        chip = chip.resize((max(8, int(fw * sc)), max(8, int(fh * sc))), Image.BILINEAR)
        chip = chip.rotate(rot, resample=Image.BICUBIC, expand=True)
        base.alpha_composite(chip, (x, y))
    # progress bar
    d.rounded_rectangle([140, 1820, 940, 1852], radius=16, fill=(16, 18, 24, 200))
    d.rounded_rectangle([146, 1826, 146 + 788 * clamp(lt / 3.0, 0, 1), 1846], radius=10, fill=(255, 111, 199, 255))
    return base


def victory_banner(base, gt):
    lt = gt - 21.85
    if lt < 0:
        return
    sc = ease_out_back(min(lt / 0.3, 1.0))
    layer = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font_black(int(120 * sc))
    draw_centered(layer, "VICTORY!", W // 2, 60, f, (255, 214, 64), stroke=9)
    layer = layer.rotate(1.5 * math.sin(gt * 3), resample=Image.BICUBIC, center=(W // 2, 150))
    base.alpha_composite(layer, (0, 560))
    # confetti
    d2 = ImageDraw.Draw(base)
    for k in range(46):
        t0 = 21.85 + h2(k, 77) * 0.5
        age = gt - t0
        if age < 0 or age > 1.9:
            continue
        x = h2(k, 78) * W + 26 * math.sin(age * 3 + k)
        y = 500 + age * 330 + h2(k, 79) * 60
        cols = [(255, 107, 107), (255, 205, 60), (106, 214, 106), (84, 160, 255), (255, 111, 199)]
        d2.rectangle([x, y, x + 13, y + 8], fill=cols[k % len(cols)])


# ---------------------------------------------------------------- main loop

def compose(gt, montage_bg):
    if gt < 5.2:
        low = scene_day1(gt)
        base = low.resize((W, H), Image.NEAREST).convert("RGBA")
        draw_hud(base, False, gt, gt)
        slam(base, "DAY 1", gt, 0.05, (226, 232, 236), sub="the day it was made")
        if 1.35 < gt < 3.3:
            caption(base, ["MY AI AGENT SHIPPED", "THIS GAME TODAY"])
        elif 3.5 < gt < 5.15:
            caption(base, ["ONE PLANT. THAT'S THE", "WHOLE DEFENSE."])
        return base
    if gt < 8.2:
        return montage_bg(gt)
    if gt < 23.5:
        t7 = gt - 8.9
        low = scene_day7(max(t7, 0.0))
        base = low.resize((W, H), Image.NEAREST).convert("RGBA")
        draw_hud(base, True, max(t7, 0.0), gt)
        if gt < 9.6:
            # brief white flash into the slam
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(255 * max(0.0, 1 - (gt - 8.2) / 0.25))))
            base.alpha_composite(fl)
        slam(base, "DAY 7", gt, 8.25, (255, 205, 60), sub="after a week of daily updates")
        if 9.7 < gt < 12.6:
            caption(base, ["SAME GAME. SAME CAMERA.", "SEVEN DAILY UPDATES."])
        elif 12.8 < gt < 16.0:
            caption(base, ["IT PATCHES ITSELF", "EVERY NIGHT"])
        elif 16.2 < gt < 19.4:
            caption(base, ["NOW IT'S A WHOLE", "ECOSYSTEM"])
        if 20.0 < gt < 21.6:
            caption(base, ["YOUR AGENT COULD", "BUILD THIS TOO"], y=1240)
        victory_banner(base, gt)
        if 22.1 < gt < 23.5:
            caption(base, ["START YOURS AT", "MAKE.FUN"], y=1330, accent=("MAKE.FUN", (255, 92, 168)))
        return base
    # end-card window: the victory scene keeps playing underneath (the card
    # overlay itself is composited later, in ffmpeg, per the press guide)
    t7 = gt - 8.9
    low = scene_day7(t7)
    base = low.resize((W, H), Image.NEAREST).convert("RGBA")
    draw_hud(base, True, t7, gt)
    victory_banner(base, gt)
    return base


def save_frame(frame, path):
    """Save via an in-memory buffer, then write the bytes with retries.

    Writing PNGs straight to disk here kept dying on a flaky
    "Operation not permitted" from the filesystem at file close; keeping
    PIL off the disk entirely and retrying the plain byte write (with a
    size check) makes one bad moment cost a second, not the render."""
    import io
    import time as _time

    buf = io.BytesIO()
    frame.convert("RGB").save(buf, format="PNG", compress_level=1)
    data = buf.getvalue()
    for attempt in range(6):
        try:
            with open(path, "wb") as fh:
                fh.write(data)
            if os.path.getsize(path) == len(data):
                return
        except OSError:
            pass
        _time.sleep(1.0 * (attempt + 1))
    raise OSError(f"could not write frame {path}")


def main():
    # --pipe: stream PNG frames to stdout for ffmpeg's image2pipe, so a
    # render creates no files at all (a burst of hundreds of frame files
    # tripped the sandbox's file-creation throttle mid-render, twice).
    pipe = len(sys.argv) > 1 and sys.argv[1] == "--pipe"
    out_dir = None if pipe else sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    end = int(sys.argv[3]) if len(sys.argv) > 3 else FRAMES
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    # pre-render the blurred day-7 backdrop for the montage
    bg_low = scene_day7(6.0).resize((W, H), Image.NEAREST).convert("RGBA")
    bg_blur = bg_low.filter(ImageFilter.GaussianBlur(16))
    dark = Image.new("RGBA", (W, H), (8, 8, 14, 120))
    bg_blur.alpha_composite(dark)

    def montage(gt):
        return draw_montage(bg_blur, gt)

    import io

    for i in range(start, end):
        gt = i / FPS
        frame = compose(gt, montage)
        if pipe:
            buf = io.BytesIO()
            frame.convert("RGB").save(buf, format="PNG", compress_level=1)
            sys.stdout.buffer.write(buf.getvalue())
            sys.stdout.buffer.flush()
        else:
            save_frame(frame, os.path.join(out_dir, f"f{i:04d}.png"))
        if i % 90 == 0:
            print(f"frame {i}/{FRAMES}", file=sys.stderr, flush=True)
    print("done frames", start, "to", end, file=sys.stderr)


if __name__ == "__main__":
    main()
