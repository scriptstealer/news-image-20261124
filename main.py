#!/usr/bin/env python3
"""The World Today - a newspaper front page summing up Tuesday 24 November 2026.

Draws one 1024x1024 PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR).
Stdlib + Pillow only, no network, fully deterministic.

Font loading is deliberately defensive: the program tries a list of common
font locations, scans likely font directories for .ttf/.otf files, and if
nothing at all is found it falls back to Pillow's built-in default font.
A missing font must never crash the program.

Set MAKEFUN_FONT_DIR to point the font search at a single directory
(useful to prove the fallback: point it at a directory that does not exist).
"""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- constants

W, H = 1024, 1024
MARGIN = 28

INK = (18, 18, 18)
PAPER = (250, 247, 238)
RED = (176, 0, 32)
RED_DARK = (140, 0, 26)
GREY = (90, 86, 78)
RULE = (60, 56, 48)
PANEL_BG = (255, 253, 247)
PANEL_LINE = (150, 144, 130)
SKY = (214, 230, 240)
SEA = (52, 110, 150)
GOLD = (198, 148, 32)

DATE_TEXT = "TUESDAY, 24 NOVEMBER 2026"
MASTHEAD = "THE WORLD TODAY"

# ---------------------------------------------------------------- font loading

# Preferred font file names, in order, for each role.
SERIF_BOLD_NAMES = (
    "DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf", "NotoSerif-Bold.ttf",
    "Times New Roman Bold.ttf", "timesbd.ttf", "FreeSerifBold.ttf",
)
SERIF_NAMES = (
    "DejaVuSerif.ttf", "LiberationSerif-Regular.ttf", "NotoSerif-Regular.ttf",
    "Times New Roman.ttf", "times.ttf", "FreeSerif.ttf",
)
SANS_BOLD_NAMES = (
    "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "NotoSans-Bold.ttf",
    "Arial Bold.ttf", "arialbd.ttf", "FreeSansBold.ttf",
)
SANS_NAMES = (
    "DejaVuSans.ttf", "LiberationSans-Regular.ttf", "NotoSans-Regular.ttf",
    "Arial.ttf", "arial.ttf", "FreeSans.ttf",
)

FONT_DIRS = (
    "/usr/share/fonts",
    "/usr/local/share/fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
    "/usr/share/fonts/truetype/freefont",
    "/usr/share/fonts/opentype",
    "/opt/fonts",
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
    "/System/Library/Fonts",
    "/Library/Fonts",
    "C:/Windows/Fonts",
)


def _scan_font_files(directories):
    """Return {lowercase filename: Path} for .ttf/.otf files under the dirs."""
    found = {}
    for d in directories:
        try:
            root = Path(d)
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if path.suffix.lower() in (".ttf", ".otf"):
                    found.setdefault(path.name.lower(), path)
        except Exception:
            continue
    return found


def _font_dirs():
    """Directories to search. MAKEFUN_FONT_DIR overrides the whole list."""
    override = os.environ.get("MAKEFUN_FONT_DIR")
    if override:
        return (override,)
    return FONT_DIRS


def _pick_font(names, size):
    """Try the named files, then any file whose name contains the family.

    Returns a truetype ImageFont, or None if nothing usable was found.
    """
    index = _scan_font_files(_font_dirs())
    for name in names:
        path = index.get(name.lower())
        if path is not None:
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                continue
    # Looser match: any file whose name contains a keyword from the list.
    keywords = []
    for name in names:
        stem = name.lower().replace(".ttf", "").replace(".otf", "")
        keywords.append(stem)
    for keyword in keywords:
        for fname, path in index.items():
            if keyword in fname:
                try:
                    return ImageFont.truetype(str(path), size)
                except Exception:
                    continue
    return None


def _default_font(size):
    """Pillow's built-in font; sized when the Pillow version allows it."""
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


_FONT_CACHE = {}


def font(role, size):
    """role: 'serif_bold' | 'serif' | 'sans_bold' | 'sans'."""
    key = (role, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    names = {
        "serif_bold": SERIF_BOLD_NAMES,
        "serif": SERIF_NAMES,
        "sans_bold": SANS_BOLD_NAMES,
        "sans": SANS_NAMES,
    }[role]
    got = _pick_font(names, size)
    if got is None:
        got = _default_font(size)
    _FONT_CACHE[key] = got
    return got


# ---------------------------------------------------------------- text helpers


def text_width(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap(draw, text, fnt, max_width, max_lines=None):
    """Greedy word wrap; returns a list of lines that fit max_width.

    When max_lines is given, extra lines are dropped and the last kept
    line gets an ellipsis, so text can never overflow its panel.
    """
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(draw, trial, fnt) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and text_width(draw, lines[-1] + " ...", fnt) > max_width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        lines[-1] = lines[-1] + " ..."
    return lines


def draw_centered(draw, cx, y, text, fnt, fill):
    w = text_width(draw, text, fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)
    return y + fnt.size


def draw_wrapped(draw, x, y, text, fnt, max_width, fill, leading=1.25,
                 max_lines=None):
    lines = wrap(draw, text, fnt, max_width, max_lines=max_lines)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += int(fnt.size * leading)
    return y


def draw_centered_wrapped(draw, cx, y, text, fnt, max_width, fill, leading=1.25):
    for line in wrap(draw, text, fnt, max_width):
        draw_centered(draw, cx, y, line, fnt, fill)
        y += int(fnt.size * leading)
    return y


# ---------------------------------------------------------------- illustrations
# Every illustration draws inside a box (x, y, w, h) with simple PIL shapes.


def ill_courthouse(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(226, 222, 210))
    # sky strip and ground
    draw.rectangle([x, y, x + w, y + int(h * 0.52)], fill=(196, 216, 228))
    ground = y + int(h * 0.82)
    draw.rectangle([x, ground, x + w, y + h], fill=(168, 160, 140))
    cx = x + w // 2
    base = ground
    # steps
    for i, sw in enumerate((0.86, 0.74, 0.62)):
        swpx = int(w * sw)
        draw.rectangle([cx - swpx // 2, base - 8 * (i + 1),
                        cx + swpx // 2, base - 8 * i], fill=(120, 112, 96))
    top = base - 26
    # columns
    col_w = max(6, w // 22)
    col_h = int(h * 0.34)
    for k in range(4):
        col_x = x + int(w * (0.16 + k * 0.227))
        draw.rectangle([col_x, top - col_h, col_x + col_w, top],
                       fill=(245, 242, 232))
        draw.rectangle([col_x - 3, top - col_h - 6, col_x + col_w + 3,
                        top - col_h], fill=(220, 214, 198))
    # entablature and pediment
    draw.rectangle([x + int(w * 0.08), top - col_h - 16,
                    x + int(w * 0.92), top - col_h - 6], fill=(150, 140, 118))
    draw.polygon([(x + int(w * 0.06), top - col_h - 16),
                  (cx, top - col_h - int(h * 0.22)),
                  (x + int(w * 0.94), top - col_h - 16)], fill=(176, 0, 32))
    draw.ellipse([cx - 9, top - col_h - int(h * 0.17) - 4,
                  cx + 9, top - col_h - int(h * 0.17) + 14], fill=(250, 247, 238))
    # gavel stamp
    draw.ellipse([x + w - 52, y + 10, x + w - 12, y + 50], fill=RED)
    draw.text((x + w - 32, y + 22), "!", font=font("sans_bold", 26),
              fill=(255, 255, 255), anchor="mm")


def ill_rocket(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(16, 22, 44))
    # stars
    for sx, sy, r in ((0.12, 0.15, 2), (0.85, 0.12, 2), (0.72, 0.28, 2),
                      (0.25, 0.32, 1), (0.92, 0.45, 2), (0.08, 0.55, 2),
                      (0.55, 0.08, 1), (0.38, 0.12, 2)):
        draw.ellipse([x + int(w * sx) - r, y + int(h * sy) - r,
                      x + int(w * sx) + r, y + int(h * sy) + r],
                     fill=(255, 255, 255))
    cx = x + w // 2
    # flame
    flame_top = y + int(h * 0.78)
    draw.polygon([(cx - 14, flame_top), (cx + 14, flame_top),
                  (cx, y + h - 4)], fill=(255, 176, 32))
    draw.polygon([(cx - 8, flame_top), (cx + 8, flame_top),
                  (cx, y + h - 10)], fill=(255, 90, 32))
    # fins
    draw.polygon([(cx - 16, y + int(h * 0.60)), (cx - 34, y + int(h * 0.80)),
                  (cx - 16, y + int(h * 0.80))], fill=RED)
    draw.polygon([(cx + 16, y + int(h * 0.60)), (cx + 34, y + int(h * 0.80)),
                  (cx + 16, y + int(h * 0.80))], fill=RED)
    # body
    draw.rectangle([cx - 16, y + int(h * 0.18), cx + 16, y + int(h * 0.80)],
                   fill=(240, 240, 236))
    draw.polygon([(cx - 16, y + int(h * 0.18)), (cx, y + int(h * 0.05)),
                  (cx + 16, y + int(h * 0.18))], fill=RED)
    draw.rectangle([cx - 16, y + int(h * 0.42), cx + 16, y + int(h * 0.50)],
                   fill=(0, 120, 70))
    draw.ellipse([cx - 7, y + int(h * 0.26), cx + 7, y + int(h * 0.26) + 14],
                 fill=(52, 110, 150), outline=(18, 18, 18), width=2)
    # smoke puffs
    for sx, sy, r in ((0.22, 0.88, 10), (0.78, 0.90, 12), (0.35, 0.95, 8)):
        draw.ellipse([x + int(w * sx) - r, y + int(h * sy) - r,
                      x + int(w * sx) + r, y + int(h * sy) + r],
                     fill=(200, 200, 200))


def ill_ship(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=SKY)
    # sun and clouds
    draw.ellipse([x + w - 46, y + 8, x + w - 14, y + 40], fill=(255, 214, 64))
    for cxr, cyr in ((0.18, 0.16), (0.62, 0.10)):
        draw.ellipse([x + int(w * cxr), y + int(h * cyr),
                      x + int(w * cxr) + 46, y + int(h * cyr) + 16],
                     fill=(255, 255, 255))
    sea_y = y + int(h * 0.62)
    draw.rectangle([x, sea_y, x + w, y + h], fill=SEA)
    # waves
    for wy in (sea_y + 14, sea_y + 34, sea_y + 54):
        for k in range(4):
            wx = x + 12 + k * int(w * 0.24)
            draw.arc([wx, wy - 6, wx + 34, wy + 8], 180, 360,
                     fill=(180, 220, 240), width=3)
    # ship hull and containers
    hx, hw = x + int(w * 0.16), int(w * 0.68)
    hy = sea_y - 6
    draw.polygon([(hx, hy), (hx + hw, hy), (hx + hw - 14, hy + 26),
                  (hx + 14, hy + 26)], fill=(40, 40, 44))
    draw.rectangle([hx + 14, hy - 34, hx + hw - 14, hy], fill=RED)
    draw.rectangle([hx + 14, hy - 34, hx + int(hw * 0.45), hy - 12],
                   fill=(0, 120, 70))
    draw.rectangle([hx + int(hw * 0.55), hy - 34, hx + hw - 14, hy - 12],
                   fill=(255, 176, 32))
    # bridge
    draw.rectangle([hx + hw - 34, hy - 52, hx + hw - 12, hy - 34],
                   fill=(245, 242, 232))
    # drone above the ship
    dx, dy = x + int(w * 0.78), y + int(h * 0.30)
    draw.ellipse([dx - 12, dy - 6, dx + 12, dy + 6], fill=(30, 30, 34))
    draw.line([dx - 22, dy - 8, dx + 22, dy - 8], fill=(30, 30, 34), width=3)
    draw.ellipse([dx - 28, dy - 12, dx - 16, dy - 4], fill=(120, 120, 130))
    draw.ellipse([dx + 16, dy - 12, dx + 28, dy - 4], fill=(120, 120, 130))
    # explosion burst on the water
    ex, ey = x + int(w * 0.20), sea_y + 8
    for r, col in ((16, (255, 176, 32)), (10, (255, 90, 32)), (5, (255, 255, 255))):
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=col)


def ill_store(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 226, 210))
    draw.rectangle([x, y, x + w, y + int(h * 0.24)], fill=(196, 216, 228))
    # storefront
    sx, sy = x + int(w * 0.12), y + int(h * 0.24)
    sw, sh = int(w * 0.76), int(h * 0.66)
    draw.rectangle([sx, sy, sx + sw, sy + sh], fill=(245, 242, 232),
                   outline=(60, 56, 48), width=3)
    # awning stripes
    awn = max(10, int(sh * 0.20))
    for k in range(7):
        ax = sx + k * (sw // 7)
        col = RED if k % 2 == 0 else (245, 242, 232)
        draw.polygon([(ax, sy), (ax + sw // 7, sy),
                      (ax + sw // 7 + 5, sy + awn), (ax - 5, sy + awn)],
                     fill=col)
    # sign
    sign_y0 = sy + awn + 4
    sign_y1 = sign_y0 + max(18, int(sh * 0.26))
    draw.rectangle([sx + 8, sign_y0, sx + sw - 8, sign_y1], fill=(18, 18, 18))
    draw.text((sx + sw // 2, (sign_y0 + sign_y1) // 2), "MARKET",
              font=font("sans_bold", 18), fill=(255, 255, 255), anchor="mm")
    # doors and windows
    door_y0 = sign_y1 + 6
    door_y1 = sy + sh - 6
    draw.rectangle([sx + 14, door_y0, sx + int(sw * 0.42), door_y1],
                   fill=(52, 110, 150), outline=(60, 56, 48), width=2)
    draw.rectangle([sx + int(sw * 0.58), door_y0, sx + sw - 14, door_y1],
                   fill=(120, 170, 200), outline=(60, 56, 48), width=2)
    draw.line([sx + int(sw * 0.58), door_y0, sx + int(sw * 0.58), door_y1],
              fill=(60, 56, 48), width=2)
    # police tape across the front
    ty = sy + sh - 16
    draw.rectangle([x, ty, x + w, ty + 14], fill=(255, 214, 64))
    draw.text((x + w // 2, ty + 7), "POLICE  ·  DO NOT CROSS",
              font=font("sans_bold", 12), fill=(18, 18, 18), anchor="mm")


def ill_helicopter(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(196, 216, 228))
    # hills
    draw.polygon([(x, y + h), (x, y + int(h * 0.78)),
                  (x + int(w * 0.5), y + int(h * 0.66)),
                  (x + w, y + int(h * 0.80)), (x + w, y + h)],
                 fill=(120, 150, 90))
    cx, cy = x + w // 2, y + int(h * 0.42)
    # tail boom
    draw.polygon([(cx + 10, cy - 4), (x + w - 18, cy - 16),
                  (x + w - 18, cy - 4), (cx + 10, cy + 6)], fill=(90, 90, 96))
    draw.polygon([(x + w - 20, cy - 26), (x + w - 8, cy - 26),
                  (x + w - 8, cy - 4), (x + w - 20, cy - 4)], fill=(90, 90, 96))
    # body
    draw.ellipse([cx - 58, cy - 26, cx + 58, cy + 26], fill=(64, 96, 64))
    draw.ellipse([cx + 18, cy - 18, cx + 52, cy + 4], fill=(180, 220, 235))
    # main rotor and mast
    draw.line([cx - 78, cy - 44, cx + 78, cy - 44], fill=(30, 30, 34), width=4)
    draw.line([cx, cy - 44, cx, cy - 26], fill=(30, 30, 34), width=4)
    # skids
    draw.line([cx - 44, cy + 40, cx + 44, cy + 40], fill=(30, 30, 34), width=4)
    draw.line([cx - 34, cy + 26, cx - 30, cy + 40], fill=(30, 30, 34), width=3)
    draw.line([cx + 34, cy + 26, cx + 30, cy + 40], fill=(30, 30, 34), width=3)
    # smoke plume
    for sx, sy, r in ((0.16, 0.30, 12), (0.10, 0.20, 9), (0.24, 0.18, 8)):
        draw.ellipse([x + int(w * sx) - r, y + int(h * sy) - r,
                      x + int(w * sx) + r, y + int(h * sy) + r],
                     fill=(140, 140, 140))


def ill_quake(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(226, 222, 210))
    draw.rectangle([x, y, x + w, y + int(h * 0.45)], fill=(196, 216, 228))
    # sun
    draw.ellipse([x + w - 44, y + 8, x + w - 14, y + 38], fill=(255, 214, 64))
    # mountains
    draw.polygon([(x, y + int(h * 0.62)), (x + int(w * 0.28), y + int(h * 0.18)),
                  (x + int(w * 0.52), y + int(h * 0.62))], fill=(96, 110, 120))
    draw.polygon([(x + int(w * 0.18), y + int(h * 0.62)),
                  (x + int(w * 0.45), y + int(h * 0.30)),
                  (x + int(w * 0.72), y + int(h * 0.62))], fill=(120, 132, 140))
    draw.polygon([(x + int(w * 0.52), y + int(h * 0.62)),
                  (x + int(w * 0.80), y + int(h * 0.22)),
                  (x + w, y + int(h * 0.62))], fill=(96, 110, 120))
    # snow caps
    draw.polygon([(x + int(w * 0.28), y + int(h * 0.18)),
                  (x + int(w * 0.24), y + int(h * 0.26)),
                  (x + int(w * 0.32), y + int(h * 0.26))], fill=(255, 255, 255))
    draw.polygon([(x + int(w * 0.80), y + int(h * 0.22)),
                  (x + int(w * 0.76), y + int(h * 0.30)),
                  (x + int(w * 0.84), y + int(h * 0.30))], fill=(255, 255, 255))
    # ground with a crack
    draw.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(168, 150, 120))
    crack_x = x + int(w * 0.55)
    draw.line([(crack_x, y + int(h * 0.62)), (crack_x - 10, y + int(h * 0.76)),
               (crack_x + 6, y + int(h * 0.88)), (crack_x - 4, y + h)],
              fill=(60, 50, 40), width=3)
    # small house, tilted
    hx, hy = x + int(w * 0.16), y + int(h * 0.72)
    draw.polygon([(hx, hy), (hx + 34, hy - 12), (hx + 60, hy + 4),
                  (hx + 56, hy + 26), (hx + 4, hy + 26)], fill=(176, 0, 32))
    draw.polygon([(hx - 4, hy + 2), (hx + 30, hy - 14), (hx + 64, hy + 2),
                  (hx + 56, hy + 8), (hx + 4, hy + 8)], fill=(60, 56, 48))
    # shaking lines
    for sx, sy in ((0.86, 0.75), (0.88, 0.85), (0.82, 0.68)):
        draw.arc([x + int(w * sx) - 8, y + int(h * sy) - 8,
                  x + int(w * sx) + 8, y + int(h * sy) + 8],
                 200, 340, fill=(60, 50, 40), width=2)


def ill_trophy(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(24, 90, 44))
    # pitch lines
    draw.rectangle([x + 8, y + 8, x + w - 8, y + h - 8], outline=(255, 255, 255),
                   width=2)
    draw.line([x + 8, y + h // 2, x + w - 8, y + h // 2],
              fill=(255, 255, 255), width=2)
    draw.ellipse([x + w // 2 - 26, y + h // 2 - 26,
                  x + w // 2 + 26, y + h // 2 + 26], outline=(255, 255, 255),
                 width=2)
    cx = x + int(w * 0.30)
    cy = y + int(h * 0.52)
    # trophy cup
    draw.polygon([(cx - 26, cy - 34), (cx + 26, cy - 34),
                  (cx + 16, cy + 6), (cx - 16, cy + 6)], fill=GOLD)
    draw.arc([cx - 40, cy - 38, cx - 12, cy - 6], 90, 270, fill=GOLD, width=6)
    draw.arc([cx + 12, cy - 38, cx + 40, cy - 6], 270, 90, fill=GOLD, width=6)
    draw.rectangle([cx - 6, cy + 6, cx + 6, cy + 22], fill=GOLD)
    draw.rectangle([cx - 22, cy + 22, cx + 22, cy + 32], fill=GOLD)
    # football
    bx, by, br = x + int(w * 0.72), y + int(h * 0.30), 30
    draw.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255),
                 outline=(18, 18, 18), width=2)
    draw.polygon([(bx, by - 10), (bx + 10, by - 3), (bx + 6, by + 9),
                  (bx - 6, by + 9), (bx - 10, by - 3)], fill=(18, 18, 18))
    for ang in range(5):
        import math
        a = math.radians(-90 + ang * 72)
        lx, ly = bx + int(22 * math.cos(a)), by + int(22 * math.sin(a))
        draw.line([bx, by, lx, ly], fill=(18, 18, 18), width=2)


ILLUSTRATIONS = {
    "courthouse": ill_courthouse,
    "rocket": ill_rocket,
    "ship": ill_ship,
    "store": ill_store,
    "helicopter": ill_helicopter,
    "trophy": ill_trophy,
    "quake": ill_quake,
}

# ---------------------------------------------------------------- stories

LEAD = {
    "kicker": "UNITED STATES  ·  TECHNOLOGY & LAW",
    "headline": "HUAWEI FOUND GUILTY IN U.S. TRIAL",
    "sub": ("A Brooklyn jury convicts the Chinese telecom giant on 10 of 12 "
            "counts, including bank fraud and conspiring to steal trade "
            "secrets. Huawei is cleared of racketeering; sentencing is set "
            "for September 2027."),
    "ill": "courthouse",
}

STORIES = [
    {
        "kicker": "CHINA  ·  SPACE",
        "headline": "CHINA NAMES CREW FOR SHENZHOU-24",
        "sub": ("Pakistan's Zeeshan Ali will be the first foreign astronaut "
                "aboard Tiangong."),
        "ill": "rocket",
    },
    {
        "kicker": "UKRAINE  ·  WAR AT SEA",
        "headline": "UKRAINE STRIKES RUSSIAN SHIPS AT SEA",
        "sub": ("Drones hit a cargo ship in the Gulf of Finland and a warship "
                "off Libya."),
        "ill": "ship",
    },
    {
        "kicker": "COLOMBIA  ·  CRIME",
        "headline": "GUNMEN HOLD 25 HOSTAGE IN CARTAGENA",
        "sub": ("Armed men seize a supermarket in the port city; police "
                "surround the store."),
        "ill": "store",
    },
    {
        "kicker": "TURKIYE  ·  ACCIDENT",
        "headline": "ARMY HELICOPTER CRASH KILLS FIVE",
        "sub": ("An AS-532 comes down after take-off from Eskisehir; all five "
                "crew are killed."),
        "ill": "helicopter",
    },
    {
        "kicker": "SPORT  ·  FOOTBALL",
        "headline": "2031 WOMEN'S WORLD CUP HOSTS NAMED",
        "sub": ("USA, Mexico, Costa Rica and Jamaica will stage the expanded "
                "48-team event."),
        "ill": "trophy",
    },
    {
        "kicker": "NEPAL  ·  EARTHQUAKE",
        "headline": "5.6-MAGNITUDE QUAKE HITS NEPAL",
        "sub": ("The tremor strikes near the Chinese border; damage reports "
                "are still coming in."),
        "ill": "quake",
    },
]

IN_BRIEF = ("IN BRIEF:  Solomon Islands picks Australia as top security "
            "partner  ·  North Korea orders Switzerland's envoy out  ·  US "
            "plans tariffs on China and the EU, AP sources say")


# ---------------------------------------------------------------- page build


def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # --- masthead ------------------------------------------------------
    y = 14
    draw_centered(draw, W // 2, y, MASTHEAD, font("serif_bold", 60), INK)
    y = 14 + 60 + 8
    draw.line([MARGIN, y, W - MARGIN, y], fill=RULE, width=3)
    y += 6
    draw_centered(draw, W // 2, y, "ALL THE WORLD'S NEWS  ·  ONE DAY, ONE PAGE",
                  font("sans", 16), GREY)
    y += 26

    # --- red date band --------------------------------------------------
    band_y = y
    band_h = 52
    draw.rectangle([MARGIN, band_y, W - MARGIN, band_y + band_h], fill=RED)
    draw.text((W // 2, band_y + band_h // 2), DATE_TEXT,
              font=font("sans_bold", 36), fill=(255, 255, 255), anchor="mm")
    y = band_y + band_h + 10

    # --- lead story ------------------------------------------------------
    lead_h = 230
    lead_x0, lead_y0 = MARGIN, y
    lead_x1, lead_y1 = W - MARGIN, y + lead_h
    draw.rectangle([lead_x0, lead_y0, lead_x1, lead_y1], fill=PANEL_BG,
                   outline=PANEL_LINE, width=2)
    ill_w = 330
    ILLUSTRATIONS[LEAD["ill"]](draw, lead_x0 + 2, lead_y0 + 2,
                               ill_w, lead_h - 4)
    tx = lead_x0 + ill_w + 22
    tw = lead_x1 - tx - 18
    ty = lead_y0 + 16
    draw.text((tx, ty), LEAD["kicker"], font=font("sans_bold", 17), fill=RED)
    ty += 28
    ty = draw_wrapped(draw, tx, ty, LEAD["headline"],
                      font("serif_bold", 36), tw, INK, leading=1.08,
                      max_lines=2)
    ty += 6
    draw_wrapped(draw, tx, ty, LEAD["sub"], font("sans", 19), tw, (50, 48, 44),
                 leading=1.3, max_lines=5)
    y = lead_y1 + 14

    # --- story grid: 2 rows x 3 columns ---------------------------------
    cols, rows = 3, 2
    gap = 12
    grid_w = W - 2 * MARGIN
    cell_w = (grid_w - gap * (cols - 1)) // cols
    grid_h = 512
    cell_h = (grid_h - gap * (rows - 1)) // 2
    for idx, story in enumerate(STORIES):
        r, c = divmod(idx, cols)
        cx0 = MARGIN + c * (cell_w + gap)
        cy0 = y + r * (cell_h + gap)
        cx1, cy1 = cx0 + cell_w, cy0 + cell_h
        draw.rectangle([cx0, cy0, cx1, cy1], fill=PANEL_BG,
                       outline=PANEL_LINE, width=2)
        ill_h = 108
        ILLUSTRATIONS[story["ill"]](draw, cx0 + 2, cy0 + 2, cell_w - 4, ill_h)
        tx = cx0 + 14
        tw = cell_w - 28
        ty = cy0 + ill_h + 10
        draw.text((tx, ty), story["kicker"], font=font("sans_bold", 13),
                  fill=RED)
        ty += 20
        ty = draw_wrapped(draw, tx, ty, story["headline"],
                          font("serif_bold", 20), tw, INK, leading=1.08,
                          max_lines=3)
        ty += 4
        draw_wrapped(draw, tx, ty, story["sub"], font("sans", 13), tw,
                     (50, 48, 44), leading=1.25, max_lines=2)

    y = y + grid_h + 10

    # --- in-brief strip and footer ---------------------------------------
    draw.line([MARGIN, y, W - MARGIN, y], fill=RULE, width=2)
    y += 6
    y = draw_wrapped(draw, MARGIN, y, IN_BRIEF, font("sans", 13),
                     W - 2 * MARGIN, (50, 48, 44), leading=1.3, max_lines=2)
    draw.line([MARGIN, H - 26, W - MARGIN, H - 26], fill=RULE, width=1)
    draw_centered(draw, W // 2, H - 22,
                  "Compiled from wire reports  ·  Reuters  ·  AP  ·  CNN",
                  font("sans", 12), GREY)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    out_path = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    img.save(out_path, format="PNG", optimize=True)
    print(f"wrote {out_path} ({img.size[0]}x{img.size[1]})", file=sys.stderr)


if __name__ == "__main__":
    main()
