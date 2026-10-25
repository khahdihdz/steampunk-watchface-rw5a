"""
steampunk.py — Procedural steampunk/LED artwork for the Redmi Watch 5 Active
(2.0" LCD, 320x385, rounded-square panel).

v3.0.0: exposed skeleton movement (bridges, wheels, mainspring barrel, balance
wheel, jewels) sits under a smoked crystal; the content plates are translucent
glass so the mechanism stays faintly visible while the seven-segment LED readout
and the Vietnamese labels stay legible.  Every pixel is drawn from code; shapes
are rasterised at 3x and downsampled with LANCZOS.

Coordinate system: device pixels, origin top-left, 320 x 385.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# --------------------------------------------------------------------------- #
# Design tokens (single source of truth: assets/layout.json)
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent.parent
_LAYOUT_PATH = Path(os.environ.get("WATCHFACE_LAYOUT", ROOT / "assets" / "layout.json"))
LAYOUT = json.loads(_LAYOUT_PATH.read_text(encoding="utf-8"))

W: int = LAYOUT["canvas"]["width"]
H: int = LAYOUT["canvas"]["height"]
CORNER_RADIUS: int = LAYOUT["canvas"]["corner_radius"]
SAFE_INSET: int = LAYOUT["canvas"]["safe_inset"]

LED = LAYOUT["led_panel"]
SEC = LAYOUT["seconds"]
PANEL = tuple(LED["box"])
DATE_BOX = tuple(LAYOUT["date_strip"]["box"])
COMP = LAYOUT["complications"]
PLATE = tuple(COMP["plate"])

SS = 3                     # supersampling factor


def load_palette(path: str | Path | None = None) -> dict[str, str]:
    target = Path(path) if path else ROOT / "assets" / "palette.json"
    return json.loads(target.read_text(encoding="utf-8"))


class Canvas:
    """Thin supersampled wrapper around ImageDraw with device-pixel coordinates."""

    def __init__(self, size: tuple[int, int] = (W, H), scale: int = SS,
                 bg: tuple[int, int, int, int] = (0, 0, 0, 0)):
        self.size = size
        self.scale = scale
        self.img = Image.new("RGBA", (size[0] * scale, size[1] * scale), bg)
        self.draw = ImageDraw.Draw(self.img)
        self._fonts: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    # -- helpers ---------------------------------------------------------- #
    def _s(self, *vals: float) -> tuple[float, ...]:
        return tuple(v * self.scale for v in vals)

    def _poly(self, points: Iterable[Sequence[float]]) -> list[tuple[float, float]]:
        s = self.scale
        return [(x * s, y * s) for x, y in points]

    def font(self, path: str, size: float) -> ImageFont.FreeTypeFont:
        key = (path, int(round(size * self.scale)))
        font = self._fonts.get(key)
        if font is None:
            font = ImageFont.truetype(path, key[1])
            self._fonts[key] = font
        return font

    # -- primitives ------------------------------------------------------- #
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.draw.rectangle(self._s(x0, y0, x1, y1), fill=fill,
                            outline=outline, width=int(round(width * self.scale)))

    def rrect(self, x0, y0, x1, y1, radius, fill=None, outline=None, width=1):
        self.draw.rounded_rectangle(self._s(x0, y0, x1, y1),
                                    radius=radius * self.scale, fill=fill,
                                    outline=outline,
                                    width=int(round(width * self.scale)))

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.draw.ellipse(self._s(x0, y0, x1, y1), fill=fill, outline=outline,
                          width=int(round(width * self.scale)))

    def circle(self, cx, cy, r, fill=None, outline=None, width=1):
        self.ellipse(cx - r, cy - r, cx + r, cy + r, fill=fill,
                     outline=outline, width=width)

    def polygon(self, points, fill=None, outline=None, width=1):
        self.draw.polygon(self._poly(points), fill=fill, outline=outline,
                          width=int(round(width * self.scale)))

    def line(self, points, fill=None, width=1, joint="curve"):
        self.draw.line(self._poly(points), fill=fill,
                       width=int(round(width * self.scale)), joint=joint)

    def arc(self, x0, y0, x1, y1, start, end, fill=None, width=1):
        self.draw.arc(self._s(x0, y0, x1, y1), start, end, fill=fill,
                      width=int(round(width * self.scale)))

    def text(self, xy, s, font_path, size, fill, anchor="mm",
             stroke_width=0.0, stroke_fill=None):
        self.draw.text(self._s(*xy), s, font=self.font(font_path, size),
                       fill=fill, anchor=anchor,
                       stroke_width=int(round(stroke_width * self.scale)),
                       stroke_fill=stroke_fill)

    # -- output ----------------------------------------------------------- #
    def finish(self) -> Image.Image:
        return self.img.resize(self.size, Image.LANCZOS)


# --------------------------------------------------------------------------- #
# Colour / gradient helpers
# --------------------------------------------------------------------------- #

def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgba(value: str | tuple[int, int, int], alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = hex_rgb(value) if isinstance(value, str) else value
    return (r, g, b, alpha)


def mix(a, b, t: float):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _stops_color(stops, t: float):
    stops = sorted(stops, key=lambda item: item[0])
    if t <= stops[0][0]:
        return tuple(stops[0][1])
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            k = (t - p0) / max(p1 - p0, 1e-9)
            return tuple(int(round(a + (b - a) * k)) for a, b in zip(c0, c1))
    return tuple(stops[-1][1])


def _apply_stops(gray: Image.Image, stops) -> Image.Image:
    """Map an 'L' image through an arbitrary colour ramp."""
    ramp = [_stops_color(stops, v / 255.0) for v in range(256)]
    channels = [gray.point([c[i] for c in ramp]) for i in range(3)]
    return Image.merge("RGB", channels)


def vgrad(size, stops, top: float = 0.0, bottom: float = 1.0) -> Image.Image:
    """Vertical linear gradient over an arbitrary colour ramp."""
    w, h = size
    column = Image.new("RGB", (1, h))
    px = column.load()
    for y in range(h):
        t = top + (bottom - top) * (y / max(h - 1, 1))
        px[0, y] = _stops_color(stops, t)
    return column.resize((w, h), Image.NEAREST)


def radial(size, stops, center=None, diameter: int | None = None) -> Image.Image:
    """Radial gradient; without ``diameter`` it is stretched over the canvas."""
    w, h = size
    if diameter is None:
        gray = Image.radial_gradient("L").resize((w, h), Image.BILINEAR)
        return _apply_stops(gray, stops).convert("RGBA")

    d = max(2, int(diameter))
    gray = Image.radial_gradient("L").resize((d, d), Image.BILINEAR)
    tile = _apply_stops(gray, stops).convert("RGBA")
    out = Image.new("RGBA", size, _stops_color(stops, 1.0) + (255,))
    cx, cy = center or (w / 2, h / 2)
    out.paste(tile, (int(cx - d / 2), int(cy - d / 2)))
    return out


def paint(mask: Image.Image, gradient: Image.Image) -> Image.Image:
    out = gradient.convert("RGBA").copy()
    out.putalpha(mask.split()[3])
    return out


def solid(mask: Image.Image, color: tuple[int, int, int, int]) -> Image.Image:
    return paint(mask, Image.new("RGBA", mask.size, color))


def blur(img: Image.Image, radius: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius))


# --------------------------------------------------------------------------- #
# Shape masks
# --------------------------------------------------------------------------- #

def gear_mask(size, center, radius, teeth, depth, tooth_ratio=0.58,
              hub: float = 0.0) -> Image.Image:
    cx, cy = center
    c = Canvas(size)
    pts = []
    step = 2 * math.pi / teeth
    half = step * tooth_ratio / 2
    for i in range(teeth):
        a = i * step - math.pi / 2
        pts.append((cx + radius * math.cos(a - half * 1.1), cy + radius * math.sin(a - half * 1.1)))
        pts.append((cx + (radius + depth) * math.cos(a - half * 0.75), cy + (radius + depth) * math.sin(a - half * 0.75)))
        pts.append((cx + (radius + depth) * math.cos(a + half * 0.75), cy + (radius + depth) * math.sin(a + half * 0.75)))
        pts.append((cx + radius * math.cos(a + half * 1.1), cy + radius * math.sin(a + half * 1.1)))
    c.polygon(pts, fill=(255, 255, 255, 255))
    if hub > 0:
        c.circle(cx, cy, hub, fill=(0, 0, 0, 0))
    return c.finish()


def round_mask(size, center, radius) -> Image.Image:
    c = Canvas(size)
    c.circle(center[0], center[1], radius, fill=(255, 255, 255, 255))
    return c.finish()


def rrect_mask(size, box, radius) -> Image.Image:
    c = Canvas(size)
    c.rrect(*box, radius=radius, fill=(255, 255, 255, 255))
    return c.finish()


def screen_mask(size=(W, H), radius=CORNER_RADIUS) -> Image.Image:
    return rrect_mask(size, (0, 0, size[0], size[1]), radius)


# --------------------------------------------------------------------------- #
# Textures
# --------------------------------------------------------------------------- #

def brushed_texture(size, angle: str = "v", strength: int = 10) -> Image.Image:
    w, h = size
    noise = Image.effect_noise(size, 26).convert("L")
    noise = noise.filter(ImageFilter.GaussianBlur(0.6))
    if angle == "v":
        noise = noise.resize((max(2, w // 6), h), Image.BILINEAR).resize(size, Image.BILINEAR)
    else:
        noise = noise.resize((w, max(2, h // 6)), Image.BILINEAR).resize(size, Image.BILINEAR)
    out = Image.new("RGBA", size, (255, 228, 180, 0))
    out.putalpha(noise.point(lambda v: int(v * strength / 255)))
    return out


def patina_stains(size, palette, count: int = 6, seed: int = 3) -> Image.Image:
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    rnd = _rng(seed)
    for _ in range(count):
        d = int(rnd.uniform(40, 130))
        cx = int(rnd.uniform(0, w))
        cy = int(rnd.uniform(0, h))
        spot = Image.new("RGBA", size, rgba(palette["patina"]))
        spot.putalpha(Image.new("L", size, 0))
        cell = Image.radial_gradient("L").resize((d, d), Image.BILINEAR)
        spot.paste(rgba(palette["patina"], 255), (int(cx - d / 2), int(cy - d / 2)), cell)
        spot = spot.filter(ImageFilter.GaussianBlur(d * 0.18))
        spot.putalpha(spot.split()[3].point(lambda v: int(v * 0.13)))
        layer.alpha_composite(spot)
    return layer


def _rng(seed: int):
    import random
    return random.Random(seed)


def vignette(size, strength: float = 0.55) -> Image.Image:
    w, h = size
    g = Image.radial_gradient("L").resize((w, h), Image.BILINEAR)
    dark = Image.new("RGBA", size, (6, 4, 3, 255))
    dark.putalpha(g.point(lambda v: int(v * strength)))
    return dark


# --------------------------------------------------------------------------- #
# Decorative elements
# --------------------------------------------------------------------------- #

def rivet(size, cx, cy, r, palette, light=(255, 240, 210, 110)) -> Image.Image:
    c = Canvas(size)
    c.circle(cx, cy, r, fill=rgba(palette["brass_dark"]))
    c.circle(cx, cy, r * 0.86, fill=rgba(palette["brass"]))
    c.circle(cx - r * 0.28, cy - r * 0.3, r * 0.34, fill=light)
    c.circle(cx + r * 0.25, cy + r * 0.3, r * 0.42, fill=(0, 0, 0, 46))
    return c.finish()


def engrave(c: Canvas, xy, s, font_path, size, dark, light, anchor="mm", depth=0.9):
    """Chiselled text: light edge below, dark groove on top."""
    c.text((xy[0], xy[1] + depth), s, font_path, size, light, anchor=anchor)
    c.text(xy, s, font_path, size, dark, anchor=anchor)


def drop_shadow(img: Image.Image, offset=(1.4, 2.2), radius=2.0, alpha=90) -> Image.Image:
    a = img.split()[3].point(lambda v: int(v * alpha / 255))
    chan = Image.new("L", img.size, 0)
    chan.paste(a, (int(offset[0]), int(offset[1])))
    chan = chan.filter(ImageFilter.GaussianBlur(radius))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 0), chan)
    return out


# --------------------------------------------------------------------------- #
# Skeleton movement — the exposed mechanism behind the smoked crystal
# --------------------------------------------------------------------------- #

def _panel_fade(base: float, opacity: float | None) -> float:
    """Panel glass opacity: None keeps the smoked-glass value, a number overrides."""
    return base if opacity is None else max(0.0, min(1.0, opacity))


def _fade(img: Image.Image, factor: float) -> Image.Image:
    """Scale an RGBA image's alpha: factor < 1 makes it translucent."""
    out = img.copy()
    out.putalpha(img.split()[3].point(lambda v: int(round(v * factor))))
    return out


def _stroke_mask(size, points, width) -> Image.Image:
    c = Canvas(size)
    c.line(points, fill=(255, 255, 255, 255), width=width)
    for px, py in (points[0], points[-1]):
        c.circle(px, py, width / 2, fill=(255, 255, 255, 255))
    return c.finish()


def bridge(out, palette, size, points, width) -> None:
    """Chamfered bridge: shadow, brass body, top bevel, bottom shadow, grain."""
    mask = _stroke_mask(size, points, width)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (1.2, 2.2), 3.0, 135))
    out.alpha_composite(paint(mask, vgrad(size,
                                         [(0.0, hex_rgb(palette["brass_dark"])),
                                          (0.28, hex_rgb(palette["brass"])),
                                          (0.52, hex_rgb(palette["brass_hi"])),
                                          (0.78, hex_rgb(palette["brass"])),
                                          (1.0, hex_rgb(palette["brass_dark"]))])))
    hi = _stroke_mask(size, [(x - 0.8, y - 1.0) for x, y in points], width * 0.26)
    hi.putalpha(ImageChops.multiply(hi.split()[3], mask.split()[3]))
    out.alpha_composite(paint(hi, Image.new("RGBA", size, (255, 246, 220, 78))))
    lo = _stroke_mask(size, [(x + 0.7, y + 1.1) for x, y in points], width * 0.24)
    lo.putalpha(ImageChops.multiply(lo.split()[3], mask.split()[3]))
    out.alpha_composite(paint(lo, Image.new("RGBA", size, (0, 0, 0, 84))))
    tex = brushed_texture(size, "v", 16)
    tex.putalpha(ImageChops.multiply(tex.split()[3], mask.split()[3]))
    out.alpha_composite(tex)


def _metal_ramp(palette):
    return [(0.0, hex_rgb(palette["brass_hi"])),
            (0.40, hex_rgb(palette["brass"])),
            (0.76, hex_rgb(palette["brass_dark"])),
            (1.0, hex_rgb(palette["copper_dark"]))]


def gear_sprite(out, palette, size, cx, cy, r, teeth, depth,
                spokes=6, hole=0.24, hub=0.28, tilt=0.0) -> None:
    """Spoked wheel: silhouette gradient, milled openings, hub, rim highlight."""
    silhouette = gear_mask(size, (cx, cy), r, teeth, depth)
    body = paint(silhouette, radial(size, _metal_ramp(palette),
                                    (cx - r * 0.34, cy - r * 0.38),
                                    int((r + depth) * 2.9)))
    holes = Canvas(size)
    if spokes:
        for i in range(spokes):
            a = 2 * math.pi * i / spokes + tilt
            holes.circle(cx + math.cos(a) * r * 0.56,
                         cy + math.sin(a) * r * 0.56, r * hole,
                         fill=(255, 255, 255, 255))
    holes.circle(cx, cy, r * hub, fill=(255, 255, 255, 255))
    body.putalpha(ImageChops.subtract(body.split()[3], holes.finish().split()[3]))

    out.alpha_composite(drop_shadow(body, (1.0, 2.0), 2.6, 120))
    out.alpha_composite(body)

    c = Canvas(size)
    c.circle(cx, cy, r * hub * 1.34, fill=rgba(palette["brass_dark"]))
    c.circle(cx, cy, r * hub * 0.90, fill=rgba(palette["brass"]))
    c.circle(cx, cy, r * hub * 0.42, fill=rgba(palette["ink"]))
    c.arc(cx - r * 0.97, cy - r * 0.97, cx + r * 0.97, cy + r * 0.97,
          198, 322, fill=(255, 246, 220, 88), width=1.2)
    out.alpha_composite(c.finish())


def barrel(out, palette, size, cx, cy, r, teeth=54) -> None:
    """Mainspring barrel: toothed drum, visible spiral spring, ratchet wheel."""
    sil = gear_mask(size, (cx, cy), r, teeth, 4)
    body = paint(sil, radial(size, _metal_ramp(palette),
                             (cx - r * 0.30, cy - r * 0.34), int(r * 2.5)))
    out.alpha_composite(drop_shadow(body, (1.2, 2.2), 3.0, 125))
    out.alpha_composite(body)

    c = Canvas(size)
    pts = []
    turns = 4.0
    for i in range(int(turns * 120)):
        t = i / 120.0
        ang = t * 2 * math.pi
        rad = r * (0.20 + 0.56 * t / turns)
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    c.line(pts, fill=rgba(palette["steel"], 200), width=1.4)
    c.circle(cx, cy, r * 0.27, fill=rgba(palette["brass_dark"]))
    c.circle(cx, cy, r * 0.21, fill=rgba(palette["brass"]))
    for i in range(8):
        a = i * math.pi / 4
        c.line([(cx + math.cos(a) * r * 0.05, cy + math.sin(a) * r * 0.05),
                (cx + math.cos(a) * r * 0.20, cy + math.sin(a) * r * 0.20)],
               fill=rgba(palette["ink"], 170), width=0.9)
    c.arc(cx - r * 0.95, cy - r * 0.95, cx + r * 0.95, cy + r * 0.95,
          196, 330, fill=(255, 246, 220, 78), width=1.4)
    out.alpha_composite(c.finish())


def balance_wheel(out, palette, size, cx, cy, r) -> None:
    outer = round_mask(size, (cx, cy), r)
    inner = round_mask(size, (cx, cy), r * 0.80)
    ring = Image.new("RGBA", size, (0, 0, 0, 0))
    ring.putalpha(ImageChops.subtract(outer.split()[3], inner.split()[3]))
    ring = paint(ring, radial(size, _metal_ramp(palette), (cx, cy), int(r * 2.2)))
    out.alpha_composite(drop_shadow(ring, (1.0, 2.0), 2.6, 115))
    out.alpha_composite(ring)

    sp = Canvas(size)
    sp.line([(cx - r * 0.98, cy), (cx + r * 0.98, cy)],
            fill=rgba(palette["brass"], 235), width=r * 0.10)
    sp.line([(cx, cy - r * 0.98), (cx, cy + r * 0.98)],
            fill=rgba(palette["brass"], 235), width=r * 0.10)
    out.alpha_composite(sp.finish())

    hs = Canvas(size)
    pts = []
    turns = 5.5
    for i in range(int(turns * 90)):
        t = i / 90.0
        ang = t * 2 * math.pi
        rad = r * (0.12 + 0.64 * t / turns)
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    hs.line(pts, fill=rgba(palette["steel"], 220), width=0.9)
    out.alpha_composite(hs.finish())

    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        screw(out, palette, size, cx + math.cos(a) * r * 0.90,
               cy + math.sin(a) * r * 0.90, max(1.5, r * 0.095))
    jewel(out, palette, size, cx, cy, max(2.0, r * 0.15))


def screw(out, palette, size, cx, cy, r, angle=0.6) -> None:
    c = Canvas(size)
    c.circle(cx + 0.6, cy + 1.0, r, fill=(0, 0, 0, 110))
    c.circle(cx, cy, r, fill=rgba(palette["blued"]))
    c.circle(cx, cy, r * 0.76, fill=rgba(mix(hex_rgb(palette["blued"]), (255, 255, 255), 0.22)))
    d = r * 0.66
    c.line([(cx - math.cos(angle) * d, cy - math.sin(angle) * d),
            (cx + math.cos(angle) * d, cy + math.sin(angle) * d)],
           fill=rgba(palette["ink"], 225), width=max(0.7, r * 0.26))
    c.circle(cx - r * 0.30, cy - r * 0.34, r * 0.20, fill=(255, 255, 255, 125))
    out.alpha_composite(c.finish())


def jewel(out, palette, size, cx, cy, r) -> None:
    c = Canvas(size)
    c.circle(cx, cy, r * 1.55, fill=rgba(palette["brass_dark"], 235))
    c.circle(cx, cy, r * 1.30, fill=rgba(palette["brass"]))
    c.circle(cx, cy, r, fill=rgba(palette["ruby"]))
    c.circle(cx - r * 0.22, cy - r * 0.28, r * 0.34, fill=(255, 255, 255, 150))
    c.circle(cx, cy, r * 0.28, fill=(255, 255, 255, 45))
    out.alpha_composite(c.finish())


# --------------------------------------------------------------------------- #
# Seven-segment renderer
# --------------------------------------------------------------------------- #

SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    "-": "g", " ": "",
}


def _bar_h(xa: float, xb: float, yc: float, t: float):
    return [(xa + t / 2, yc - t / 2), (xb - t / 2, yc - t / 2), (xb, yc),
            (xb - t / 2, yc + t / 2), (xa + t / 2, yc + t / 2), (xa, yc)]


def _bar_v(xc: float, ya: float, yb: float, t: float):
    return [(xc - t / 2, ya + t / 2), (xc, ya), (xc + t / 2, ya + t / 2),
            (xc + t / 2, yb - t / 2), (xc, yb), (xc - t / 2, yb - t / 2)]


def _segments(ch: str, ox: float, oy: float, dw: float, dh: float,
              t: float, gap: float, t_center: float | None = None,
              inset: float = 0.0):
    """Polygons for one character, origin top-left of its cell.

    ``t_center`` keeps thin (hot-core) passes on the same centreline as the
    full-thickness pass, ``inset`` trims the segment length symmetrically.
    """
    tc = t if t_center is None else t_center
    xr, yb, ym = ox + dw, oy + dh, oy + dh / 2
    lo, hi = gap + inset, gap + inset
    segs = SEGMENTS.get(ch, "")
    out = []
    if "a" in segs:
        out.append(_bar_h(ox + lo, xr - hi, oy + tc / 2, t))
    if "g" in segs:
        out.append(_bar_h(ox + lo, xr - hi, ym, t))
    if "d" in segs:
        out.append(_bar_h(ox + lo, xr - hi, yb - tc / 2, t))
    if "f" in segs:
        out.append(_bar_v(ox + tc / 2, oy + lo + tc / 2, ym - hi, t))
    if "b" in segs:
        out.append(_bar_v(xr - tc / 2, oy + lo + tc / 2, ym - hi, t))
    if "e" in segs:
        out.append(_bar_v(ox + tc / 2, ym + lo, yb - hi - tc / 2, t))
    if "c" in segs:
        out.append(_bar_v(xr - tc / 2, ym + lo, yb - hi - tc / 2, t))
    return out


def seven_seg_width(text: str, cfg) -> float:
    dw, sp, cw = cfg["digit_w"], cfg["spacing"], cfg["colon_w"]
    total = sum(cw if ch == ":" else dw for ch in text) + sp * max(len(text) - 1, 0)
    if cfg.get("slant"):
        total += cfg["slant"] * cfg["digit_h"]
    return total


def render_seven_seg(text: str, cfg, color, stroke: float | None = None,
                     scale: int = SS) -> Image.Image:
    """Render a seven-segment string; returns an RGBA sprite at device pixels."""
    dw, dh = cfg["digit_w"], cfg["digit_h"]
    sp, cw = cfg["spacing"], cfg["colon_w"]
    base_t = cfg["stroke"]
    t = base_t if stroke is None else stroke
    gap = cfg["gap"]
    slant = cfg.get("slant", 0.0)
    inset = max(0.0, (base_t - t) / 2)

    base_w = sum(cw if ch == ":" else dw for ch in text) + sp * max(len(text) - 1, 0)
    pad = abs(slant) * dh + 2
    width = int(math.ceil(base_w + pad))
    height = int(math.ceil(dh))

    c = Canvas((width, height), scale=scale)
    x = 0.0
    for ch in text:
        if ch == ":":
            dot = max(1.8, base_t * 0.92)
            for cy in (dh * 0.31, dh * 0.69):
                c.rrect(x + cw / 2 - dot / 2, cy - dot / 2,
                        x + cw / 2 + dot / 2, cy + dot / 2, dot * 0.34, fill=color)
            x += cw + sp
            continue
        for poly in _segments(ch, x, 0, dw, dh, t, gap, t_center=base_t, inset=inset):
            c.polygon(poly, fill=color)
        x += dw + sp

    img = c.finish()
    if slant:
        w, h = img.size
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sheared = img.transform((w, h), Image.AFFINE,
                                (1, -slant, slant * dh, 0, 1, 0),
                                resample=Image.BICUBIC)
        out.alpha_composite(sheared)
        return out
    return img


def led_text(text: str, cfg, color: str, glow: int = 120,
             scale: int = SS) -> Image.Image:
    """Lit LED string: halo + glow + body + hot core."""
    base = render_seven_seg(text, cfg, rgba(color), scale=scale)
    hot = render_seven_seg(text, cfg, rgba(mix(hex_rgb(color), (255, 255, 255), 0.62)),
                           stroke=cfg["stroke"] * 0.46, scale=scale)
    alpha = base.split()[3]

    out = Image.new("RGBA", base.size, (0, 0, 0, 0))
    for radius, factor in ((7.0, 0.30), (3.2, 0.55), (1.2, 0.70)):
        halo = Image.new("RGBA", base.size, rgba(color, 255))
        halo.putalpha(alpha.filter(ImageFilter.GaussianBlur(radius))
                      .point(lambda v, f=factor: int(v * f * glow / 255)))
        out.alpha_composite(halo)
    out.alpha_composite(base)
    out.alpha_composite(hot)
    return out


# --------------------------------------------------------------------------- #
# Layers
# --------------------------------------------------------------------------- #

def backdrop_layer(palette, fonts, size=(W, H)) -> Image.Image:
    """Case interior behind the movement: dark metal, frame, rivets, vignette."""
    w, h = size
    base = vgrad(size, [(0.0, (28, 21, 18)), (0.42, (17, 13, 11)),
                        (1.0, (12, 9, 8))]).convert("RGBA")
    base.alpha_composite(patina_stains(size, palette, count=5, seed=7))

    frame = Canvas(size)
    frame.rrect(6, 6, w - 6, h - 6, CORNER_RADIUS - 4,
                outline=rgba(palette["brass_dark"], 160), width=2.2)
    frame.rrect(9, 9, w - 9, h - 9, CORNER_RADIUS - 7,
                outline=(255, 235, 200, 30), width=1.0)
    base.alpha_composite(frame.finish())

    for cx, cy in [(29, 29), (w - 29, 29), (29, h - 29), (w - 29, h - 29)]:
        base.alpha_composite(rivet(size, cx, cy, 5.2, palette))

    base.alpha_composite(brushed_texture(size, "v", 12))
    base.alpha_composite(vignette(size, 0.36))
    return base


def movement_layer(palette, fonts, size=(W, H)) -> Image.Image:
    """Exposed skeleton movement: bridges, wheels, barrel, balance, jewels."""
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    w, h = size

    # bridges first — wheels sit on top of them
    bridge(out, palette, size, [(-8, 304), (34, 274), (88, 262), (130, 276)], 26)
    bridge(out, palette, size, [(w + 8, 98), (274, 68), (216, 46), (172, 40)], 22)
    bridge(out, palette, size, [(100, h + 6), (150, 368), (202, 374), (240, h + 8)], 18)

    barrel(out, palette, size, 300, 306, 46)
    gear_sprite(out, palette, size, 4, 118, 44, 46, 5)
    gear_sprite(out, palette, size, 2, 42, 30, 32, 4)
    gear_sprite(out, palette, size, 6, 198, 30, 32, 4)
    gear_sprite(out, palette, size, 322, 214, 34, 34, 4)
    gear_sprite(out, palette, size, 318, 272, 24, 26, 3)
    gear_sprite(out, palette, size, 300, 252, 21, 22, 3)
    gear_sprite(out, palette, size, 98, 374, 26, 28, 3)
    gear_sprite(out, palette, size, 214, h - 2, 30, 32, 3)
    gear_sprite(out, palette, size, 302, 34, 24, 26, 3)
    gear_sprite(out, palette, size, 158, 32, 15, 16, 2, spokes=4)

    balance_wheel(out, palette, size, 50, 364, 28)

    for cx, cy, r in [(98, 374, 26), (300, 306, 46), (4, 118, 44), (322, 214, 34)]:
        jewel(out, palette, size, cx, cy, max(2.0, r * 0.13))
    for cx, cy, r, a in [(40, 272, 3.2, 0.5), (270, 70, 3.0, 1.2),
                         (152, 368, 3.0, 0.2), (174, 40, 2.8, 0.9),
                         (246, 182, 2.6, 1.5)]:
        screw(out, palette, size, cx, cy, r, a)
    return out


def crystal_layer(palette, size=(W, H)) -> Image.Image:
    """Smoked sapphire: cool tint over the movement + crystal-edge refraction."""
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    m = screen_mask(size)
    out.alpha_composite(_fade(paint(m, Image.new("RGB", size, (56, 82, 94))), 0.08))
    rim = Canvas(size)
    rim.rrect(7, 7, W - 7, H - 7, CORNER_RADIUS - 5,
              outline=(196, 224, 238, 34), width=2.0)
    out.alpha_composite(blur(rim.finish(), 2.2))
    return out


def nameplate_layer(palette, fonts, size=(W, H), opacity=None) -> Image.Image:
    w, h = size
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    box = (62, 18, w - 62, 54)
    mask = rrect_mask(size, box, 14)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (0.6, 1.8), 2.0, 80))
    out.alpha_composite(paint(mask, vgrad(size, [(0.0, hex_rgb(palette["brass_hi"])),
                                                 (0.34, hex_rgb(palette["brass"])),
                                                 (1.0, hex_rgb(palette["brass_dark"]))])))
    inner = rrect_mask(size, (box[0] + 3, box[1] + 3, box[2] - 3, box[3] - 3), 11)
    out.alpha_composite(_fade(paint(inner, vgrad(size, [(0.0, hex_rgb(palette["copper_dark"])),
                                                        (1.0, hex_rgb(palette["ink"]))],
                                                top=0.0, bottom=0.5)),
                                  _panel_fade(0.97, opacity)))

    c = Canvas(size)
    engrave(c, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 0.5),
            "AETHER", fonts["serif"], 14,
            rgba(palette["brass_hi"], 235), (0, 0, 0, 150), depth=1.0)
    out.alpha_composite(c.finish())
    return out


def time_layout(second_text: str = "00"):
    """Shared geometry for the lit clock, the seconds block and the ghost."""
    clock_w = seven_seg_width("88:88", LED)
    sec_w = seven_seg_width(second_text, SEC)
    group = clock_w + 10 + sec_w
    gx = (PANEL[0] + PANEL[2]) / 2 - group / 2
    return gx, clock_w, sec_w


def led_panel_layer(palette, fonts, size=(W, H), opacity=None) -> Image.Image:
    x0, y0, x1, y1 = PANEL
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    mask = rrect_mask(size, PANEL, 20)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (0.5, 2.4), 3.2, 120))
    out.alpha_composite(paint(mask, vgrad(size,
                                         [(0.0, hex_rgb(palette["brass_hi"])),
                                          (0.22, hex_rgb(palette["brass"])),
                                          (0.55, hex_rgb(palette["copper_dark"])),
                                          (1.0, hex_rgb(palette["brass_dark"]))],
                                         top=0.10, bottom=0.62)))

    inner_box = (x0 + 7, y0 + 7, x1 - 7, y1 - 7)
    inner = rrect_mask(size, inner_box, 14)
    out.alpha_composite(_fade(paint(inner, vgrad(size, [(0.0, (13, 10, 9)),
                                                        (0.55, (8, 6, 5)),
                                                        (1.0, (14, 11, 9))])),
                                  _panel_fade(0.94, opacity)))

    # unlit segments — the tell-tale LED look, aligned under the lit digits
    gx, clock_w, sec_w = time_layout("88")
    ghost = render_seven_seg("88:88", dict(LED), rgba(LED["color_ghost"]))
    out.alpha_composite(ghost, (int(gx), 72))
    ghost_sec = render_seven_seg("88", dict(SEC), rgba(SEC["color_ghost"]))
    out.alpha_composite(ghost_sec, (int(gx + clock_w + 10),
                                    int(72 + (LED["digit_h"] - SEC["digit_h"]))))

    # inner shadow where glass meets the bezel
    ring = Canvas(size)
    ring.rrect(*inner_box, radius=14, outline=(0, 0, 0, 170), width=3.0)
    out.alpha_composite(blur(ring.finish(), 1.4))

    # brushed glare across the glass
    glare = Canvas(size)
    glare.polygon([(x0 + 10, y1 - 10), (x1 - 40, y0 + 8),
                   (x1 - 18, y0 + 8), (x0 + 34, y1 - 10)],
                  fill=(255, 255, 240, 8))
    out.alpha_composite(blur(glare.finish(), 3))
    return out


def readout_layer(palette, fonts, time, size=(W, H)) -> Image.Image:
    hour, minute, second = time
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    cfg = dict(LED)
    gx, clock_w, _ = time_layout(f"{second:02d}")
    clock = led_text(f"{hour:02d}:{minute:02d}", cfg, LED["color"])
    out.alpha_composite(clock, (int(gx), 72))

    sec_cfg = dict(SEC)
    sec = led_text(f"{second:02d}", sec_cfg, SEC["color"], glow=170)
    sec_x = int(gx + clock_w + 10)
    out.alpha_composite(sec, (sec_x, int(72 + (LED["digit_h"] - SEC["digit_h"]))))

    c = Canvas(size)
    c.text((sec_x + sec.width / 2, 163), "GIÂY", fonts["mono"], 6.5,
           rgba(palette["brass_hi"], 190), anchor="mm")
    out.alpha_composite(c.finish())
    return out


def date_strip_layer(palette, fonts, values, size=(W, H), opacity=None) -> Image.Image:
    x0, y0, x1, y1 = DATE_BOX
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    mask = rrect_mask(size, DATE_BOX, 12)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (0.4, 1.8), 2.4, 90))
    out.alpha_composite(paint(mask, vgrad(size,
                                         [(0.0, hex_rgb(palette["brass"])),
                                          (0.40, hex_rgb(palette["copper_dark"])),
                                          (1.0, hex_rgb(palette["ink"]))],
                                         top=0.40, bottom=0.68)))
    inner = rrect_mask(size, (x0 + 3, y0 + 3, x1 - 3, y1 - 3), 10)
    out.alpha_composite(_fade(paint(inner, vgrad(size, [(0.0, (26, 18, 13)),
                                                        (1.0, (12, 8, 6))],
                                                top=0.40, bottom=0.68)),
                                  _panel_fade(0.91, opacity)))

    if values is None:
        return out

    label = (f"{values['weekday']} · {values['day']:02d}/{values['month']:02d}/"
             f"{values['year']}")
    c = Canvas(size)
    c.text(((x0 + x1) / 2, (y0 + y1) / 2 + 0.5), label, fonts["serif"], 10.5,
           rgba(palette["parchment"], 232), anchor="mm")
    out.alpha_composite(c.finish())
    return out


def _window(out, palette, box, size):
    """Inset brass window (rectangular gauge slot) punched into the plate."""
    w, h = box[2] - box[0], box[3] - box[1]
    radius = min(20.0, h / 2)
    c = Canvas(size)
    c.rrect(box[0] - 3, box[1] - 3, box[2] + 3, box[3] + 3, radius + 2,
            fill=rgba(palette["ink"], 190))
    c.rrect(box[0] - 1.5, box[1] - 1.5, box[2] + 1.5, box[3] + 1.5, radius + 1,
            fill=rgba(palette["brass"]))
    c.rrect(*box, radius=radius, fill=(8, 6, 5, 246))
    c.rrect(*box, radius=radius, outline=(0, 0, 0, 170), width=1.2)
    out.alpha_composite(c.finish())

    gl = Canvas(size)
    gl.rrect(box[0] + 3, box[1] + 3, box[2] - 3, box[3] - 10, radius,
             outline=(255, 250, 230, 26), width=1.2)
    out.alpha_composite(blur(gl.finish(), 0.8))


def complications_layer(palette, fonts, values, size=(W, H), opacity=None) -> Image.Image:
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    mask = rrect_mask(size, PLATE, 18)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (0.5, 2.0), 2.6, 95))
    out.alpha_composite(paint(mask, vgrad(size,
                                         [(0.0, hex_rgb(palette["brass_hi"])),
                                          (0.16, hex_rgb(palette["brass"])),
                                          (0.52, hex_rgb(palette["copper_dark"])),
                                          (1.0, hex_rgb(palette["ink"]))],
                                         top=0.62, bottom=0.96)))
    inset = rrect_mask(size, (PLATE[0] + 4, PLATE[1] + 4,
                              PLATE[2] - 4, PLATE[3] - 4), 15)
    out.alpha_composite(_fade(paint(inset, vgrad(size, [(0.0, hex_rgb(palette["iron_hi"])),
                                                        (1.0, (11, 8, 6))],
                                                 top=0.62, bottom=0.96)),
                                  _panel_fade(0.89, opacity)))

    for cx in (PLATE[0] + 11, PLATE[2] - 11):
        out.alpha_composite(rivet(size, cx, PLATE[1] + 13, 4.0, palette))

    centers = COMP["centers"]
    labels = COMP["labels"]
    win_w, win_h = COMP["window"]
    boxes = [(cx - win_w / 2, cy - win_h / 2, cx + win_w / 2, cy + win_h / 2)
             for cx, cy in centers]
    for box in boxes:
        _window(out, palette, box, size)

    medium = {"digit_w": 16.0, "digit_h": 26.0, "stroke": 3.8, "gap": 1.8,
              "spacing": 3.0, "colon_w": 7.0, "slant": 0.04}
    wide = {"digit_w": 13.5, "digit_h": 24.0, "stroke": 3.2, "gap": 1.6,
            "spacing": 2.4, "colon_w": 6.0, "slant": 0.04}

    if values is not None:
        battery = led_text(f"{values['battery']:02d}", medium, LED["color"], glow=110)
        heart = led_text(f"{values['heart']:02d}", medium, LED["color"], glow=110)
        steps = led_text(str(values["steps"]), wide, LED["color"], glow=95)

        def place(sprite, cx, cy, dx=0.0, dy=0.0):
            out.alpha_composite(sprite, (int(cx - sprite.width / 2 + dx),
                                         int(cy - sprite.height / 2 + dy)))

        place(battery, centers[0][0] - 5, centers[0][1])
        place(steps, centers[1][0], centers[1][1])
        place(heart, centers[2][0], centers[2][1])

    c = Canvas(size)
    if values is not None:
        c.text((centers[0][0] + 19, centers[0][1] + 3), "%", fonts["mono"], 7.5,
               rgba(palette["brass_hi"], 225), anchor="mm")
    for (cx, cy), label in zip(centers, labels):
        engrave(c, (cx, PLATE[3] - 22), label, fonts["serif"], 8.2,
                rgba(palette["brass_hi"], 210), (0, 0, 0, 190), depth=0.7)
    out.alpha_composite(c.finish())
    return out


def glass_layer(size=(W, H)) -> Image.Image:
    c = Canvas(size)
    c.polygon([(20, 12), (150, 12), (60, 150), (12, 150)], fill=(255, 255, 255, 13))
    c.polygon([(24, 8), (74, 8), (16, 96), (10, 96)], fill=(255, 255, 255, 9))
    return c.finish().filter(ImageFilter.GaussianBlur(9))


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #

def build_static(palette, fonts, values, opacity=None) -> dict[str, Image.Image]:
    return {
        "backdrop": backdrop_layer(palette, fonts),
        "movement": movement_layer(palette, fonts),
        "crystal": crystal_layer(palette),
        "nameplate": nameplate_layer(palette, fonts, opacity=opacity),
        "led_panel": led_panel_layer(palette, fonts, opacity=opacity),
        "date_strip": date_strip_layer(palette, fonts, values, opacity=opacity),
        "complications": complications_layer(palette, fonts, values, opacity=opacity),
        "glass": glass_layer(),
    }


def compose(layers: dict, palette, fonts, time, size=(W, H),
            backdrop: bool = True) -> Image.Image:
    img = Image.new("RGBA", size, (0, 0, 0, 255) if backdrop else (0, 0, 0, 0))
    if backdrop:
        img.alpha_composite(layers["backdrop"])
    img.alpha_composite(layers["movement"])
    img.alpha_composite(layers["crystal"])
    img.alpha_composite(layers["nameplate"])
    img.alpha_composite(layers["led_panel"])
    img.alpha_composite(readout_layer(palette, fonts, time))
    img.alpha_composite(layers["date_strip"])
    img.alpha_composite(layers["complications"])
    img.alpha_composite(layers["glass"])
    return img


def static_composite(layers: dict, size=(W, H), backdrop: bool = True) -> Image.Image:
    """Flatten the artwork without the LED readout / date text.

    This is the plate the firmware draws its own widgets on top of (``.bin``
    build), so every value that changes at runtime must be left blank.
    """
    img = Image.new("RGBA", size, (0, 0, 0, 255) if backdrop else (0, 0, 0, 0))
    order = ["movement", "crystal", "nameplate", "led_panel",
             "date_strip", "complications", "glass"]
    if backdrop:
        img.alpha_composite(layers["backdrop"])
    for key in order:
        img.alpha_composite(layers[key])
    return img


def night_variant(img: Image.Image) -> Image.Image:
    """Low-light variant: dimmed and slightly desaturated."""
    from PIL import ImageEnhance
    dim = ImageEnhance.Brightness(img).enhance(0.60)
    dim = ImageEnhance.Color(dim).enhance(0.75)
    return dim
