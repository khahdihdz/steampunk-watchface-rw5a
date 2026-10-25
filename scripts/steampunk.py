"""
steampunk.py — Procedural steampunk artwork for the Redmi Watch 5 Active
(2.0" LCD, 320x385, rounded-square panel).

Everything is drawn from code: no binary assets are committed except the
bundled preview render.  Shapes are rasterised at 3x and downsampled with
LANCZOS so edges stay clean at the watch's native resolution.

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
CORNER_RADIUS: int = LAYOUT["canvas"]["corner_radius"]   # physical panel corner radius
SAFE_INSET: int = LAYOUT["canvas"]["safe_inset"]         # keep text/values inside this inset
DIAL_CENTER: tuple[int, int] = tuple(LAYOUT["dial"]["center"])   # type: ignore[assignment]
DIAL_RADIUS: int = LAYOUT["dial"]["radius"]
PIVOT: tuple[int, int] = tuple(LAYOUT["pivot"])          # type: ignore[assignment]

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

    def pieslice(self, x0, y0, x1, y1, start, end, fill=None):
        self.draw.pieslice(self._s(x0, y0, x1, y1), start, end, fill=fill)

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


def rgba(value: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = hex_rgb(value)
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
    """Radial gradient.

    With ``diameter`` a circular tile is placed at ``center``; without it the
    gradient is stretched over the whole canvas (good for vignettes/glows).
    """
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
    """Colour a mask with a gradient, preserving the mask's alpha."""
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
    """Toothed ring (or solid disc when hub > 0)."""
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
    """The panel's physical rounded-square outline."""
    return rrect_mask(size, (0, 0, size[0], size[1]), radius)


# --------------------------------------------------------------------------- #
# Textures
# --------------------------------------------------------------------------- #

def brushed_texture(size, angle: str = "v", strength: int = 10,
                    seed: int = 7) -> Image.Image:
    """Fine directional grain, pinned to a seed so builds are reproducible."""
    w, h = size
    noise = Image.effect_noise(size, 26).convert("L")
    noise = noise.filter(ImageFilter.GaussianBlur(0.6))
    if angle == "v":
        noise = noise.resize((max(2, w // 6), h), Image.BILINEAR).resize(size, Image.BILINEAR)
    else:
        noise = noise.resize((w, max(2, h // 6)), Image.BILINEAR).resize(size, Image.BILINEAR)
    out = Image.new("RGBA", size, (255, 255, 255, 0))
    out.putalpha(noise.point(lambda v: int(v * strength / 255)))
    # deterministic tint shuffle so the grain is not pure grey
    tint = Image.new("RGBA", size, (255, 228, 180, 0))
    tint.putalpha(out.split()[3])
    return tint


def patina_stains(size, palette, count: int = 7, seed: int = 3) -> Image.Image:
    """Soft oxidised copper/verdigris blooms for an aged look."""
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    rnd = _rng(seed)
    for _ in range(count):
        d = int(rnd.uniform(40, 130))
        cx = int(rnd.uniform(0, w))
        cy = int(rnd.uniform(0, h))
        blob = Image.new("RGBA", size, (0, 0, 0, 0))
        cell = Image.radial_gradient("L").resize((d, d), Image.BILINEAR)
        alpha = cell.point(lambda v: int(max(0, (200 - v)) * 0.16))
        spot = Image.new("RGBA", size, rgba(palette["patina"]))
        spot.putalpha(Image.new("L", size, 0))
        spot.paste(rgba(palette["patina"], 255), (int(cx - d / 2), int(cy - d / 2)), cell)
        spot = spot.filter(ImageFilter.GaussianBlur(d * 0.18))
        spot.putalpha(spot.split()[3].point(lambda v: int(v * 0.13)))
        blob.alpha_composite(spot)
        layer.alpha_composite(blob)
    return layer


def _rng(seed: int):
    import random
    return random.Random(seed)


def vignette(size, strength: float = 0.55) -> Image.Image:
    w, h = size
    g = Image.radial_gradient("L").resize((w, h), Image.BILINEAR)
    dark = Image.new("RGBA", size, (6, 4, 3, 255))
    dark.putalpha(g.point(lambda v: int((255 - v) * 0 + v * strength)))
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


def engrave(c: Canvas, xy, s, font_path, size, dark, light,
            anchor="mm", depth=0.9):
    """Chiselled text: light edge below, dark groove on top."""
    c.text((xy[0], xy[1] + depth), s, font_path, size, light, anchor=anchor)
    c.text(xy, s, font_path, size, dark, anchor=anchor)


def drop_shadow(img: Image.Image, offset=(1.4, 2.2), radius=2.0,
                alpha=90) -> Image.Image:
    a = img.split()[3].point(lambda v: int(v * alpha / 255))
    chan = Image.new("L", img.size, 0)
    chan.paste(a, (int(offset[0]), int(offset[1])))
    chan = chan.filter(ImageFilter.GaussianBlur(radius))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste((0, 0, 0, 255), (0, 0), chan)
    return out


# --------------------------------------------------------------------------- #
# Layers
# --------------------------------------------------------------------------- #

ROMAN = ["XII", "I", "II", "III", "IV", "V", "VI",
         "VII", "VIII", "IX", "X", "XI"]


def backplate_layer(palette, fonts, size=(W, H)) -> Image.Image:
    w, h = size
    base = vgrad(size, [(0.0, hex_rgb(palette["iron_hi"])),
                        (0.42, hex_rgb(palette["iron"])),
                        (1.0, (10, 7, 5))]).convert("RGBA")

    # Ghost gear works etched into the background plate.
    ghosts = [(-6, 26, 86, 22, 9, 10), (326, 118, 104, 26, 11, 8),
              (34, 402, 78, 18, 8, 7)]
    for cx, cy, r, teeth, depth, alpha in ghosts:
        m = gear_mask(size, (cx, cy), r, teeth, depth, hub=r * 0.42)
        base.alpha_composite(solid(m, rgba(palette["brass"], alpha)))

    base.alpha_composite(patina_stains(size, palette))

    # Riveted frame just inside the physical corner radius.
    frame = Canvas(size)
    frame.rrect(6, 6, w - 6, h - 6, CORNER_RADIUS - 4,
                outline=rgba(palette["brass_dark"], 150), width=2.2)
    frame.rrect(9, 9, w - 9, h - 9, CORNER_RADIUS - 7,
                outline=(255, 235, 200, 26), width=1.0)
    base.alpha_composite(frame.finish())

    for cx, cy in [(30, 30), (w - 30, 30), (30, h - 30), (w - 30, h - 30)]:
        base.alpha_composite(rivet(size, cx, cy, 5.4, palette))

    base.alpha_composite(brushed_texture(size, "v", 9))
    base.alpha_composite(vignette(size, 0.62))
    return base


def nameplate_layer(palette, fonts, size=(W, H)) -> Image.Image:
    w, h = size
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    # two small idler gears flanking the plate
    for cx, cy, r, teeth in [(40, 30, 14, 9), (w - 40, 30, 12, 8)]:
        m = gear_mask(size, (cx, cy), r, teeth, 4, hub=r * 0.34)
        out.alpha_composite(paint(m, radial(size, [(0.0, hex_rgb(palette["brass_hi"])),
                                                   (0.55, hex_rgb(palette["brass"])),
                                                   (1.0, hex_rgb(palette["brass_dark"]))],
                                          (cx, cy), int(r * 2.6))))
        out.alpha_composite(drop_shadow(paint(m, Image.new("RGBA", size, (0, 0, 0, 255))),
                                        (0.8, 1.4), 1.6, 70))

    box = (62, 10, w - 62, 50)
    mask = rrect_mask(size, box, 15)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (0.6, 1.8), 2.0, 80))
    out.alpha_composite(paint(mask, vgrad(size, [(0.0, hex_rgb(palette["brass_hi"])),
                                                 (0.34, hex_rgb(palette["brass"])),
                                                 (1.0, hex_rgb(palette["brass_dark"]))])))
    inner = rrect_mask(size, (box[0] + 3, box[1] + 3, box[2] - 3, box[3] - 3), 12)
    out.alpha_composite(paint(inner, vgrad(size, [(0.0, hex_rgb(palette["copper_dark"])),
                                                  (1.0, hex_rgb(palette["ink"]))],
                                          top=0.0, bottom=0.5)))

    c = Canvas(size)
    engrave(c, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 0.5),
            "AETHER", fonts["serif"], 15,
            rgba(palette["brass_hi"], 235), (0, 0, 0, 150), depth=1.0)
    out.alpha_composite(c.finish())
    return out


def dial_layer(palette, fonts, values, size=(W, H)) -> Image.Image:
    cx, cy = DIAL_CENTER
    r = DIAL_RADIUS
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    # 1. toothed outer bezel
    teeth = gear_mask(size, (cx, cy), r, 64, 5, tooth_ratio=0.55)
    metal = radial(size, [(0.0, hex_rgb(palette["brass_dark"])),
                          (0.62, hex_rgb(palette["brass"])),
                          (0.80, hex_rgb(palette["brass_hi"])),
                          (0.93, hex_rgb(palette["brass"])),
                          (1.0, hex_rgb(palette["brass_dark"]))],
                   (cx, cy), (r + 6) * 2)
    out.alpha_composite(drop_shadow(solid(teeth, (0, 0, 0, 255)), (0.6, 2.4), 3.0, 105))
    out.alpha_composite(paint(teeth, metal))

    # 2. engraved bezel band
    band = Canvas(size)
    band.circle(cx, cy, r - 2, fill=(255, 255, 255, 255))
    band.circle(cx, cy, r - 15, fill=(0, 0, 0, 0))
    out.alpha_composite(paint(band.finish(), radial(
        size, [(0.0, hex_rgb(palette["brass_dark"])),
               (0.7, hex_rgb(palette["brass"])),
               (0.88, hex_rgb(palette["brass_hi"])),
               (1.0, hex_rgb(palette["brass_dark"]))], (cx, cy), (r + 4) * 2)))
    c = Canvas(size)
    c.circle(cx, cy, r - 8.5, outline=rgba(palette["copper_dark"], 190), width=1.2)
    c.circle(cx, cy, r - 8.5, outline=(255, 235, 195, 40), width=0.6)
    # bezel screws
    for ang in (135, 45, 315, 225):
        a = math.radians(ang)
        c.circle(cx + (r - 8) * math.cos(a), cy + (r - 8) * math.sin(a), 1.6,
                 fill=rgba(palette["brass_hi"]))
    out.alpha_composite(c.finish())

    # 3. oxidised iron dial face (high contrast for a 2.0" LCD)
    face_r = r - 17
    face_mask = round_mask(size, (cx, cy), face_r)
    enamel = radial(size, [(0.0, (62, 49, 36)),
                           (0.42, (42, 32, 24)),
                           (0.80, (25, 18, 13)),
                           (1.0, (11, 7, 5))],
                    (cx - 12, cy - 16), int(face_r * 2.6))
    out.alpha_composite(paint(face_mask, enamel))

    # concentric lathe marks
    brush = Canvas(size)
    rnd = _rng(5)
    for _ in range(64):
        rad = rnd.uniform(8, face_r - 3)
        start = rnd.uniform(0, 360)
        brush.arc(cx - rad, cy - rad, cx + rad, cy + rad,
                  start, start + rnd.uniform(25, 120),
                  fill=(255, 226, 180, rnd.randint(6, 16)), width=0.7)
    bimg = brush.finish()
    bimg.putalpha(ImageChops.multiply(bimg.split()[3], face_mask.split()[3]))
    out.alpha_composite(bimg)

    # 4. brass minute track + cream roman numerals
    c = Canvas(size)
    c.circle(cx, cy, face_r - 3.5, outline=rgba(palette["brass"], 130), width=0.9)
    for i in range(60):
        a = math.radians(i * 6 - 90)
        major = i % 5 == 0
        r_out = face_r - 6
        r_in = r_out - (9 if major else 4.5)
        c.line([(cx + r_in * math.cos(a), cy + r_in * math.sin(a)),
                (cx + r_out * math.cos(a), cy + r_out * math.sin(a))],
               fill=rgba(palette["brass_hi"] if major else palette["brass"],
                         235 if major else 140),
               width=1.6 if major else 0.7)
    for i, numeral in enumerate(ROMAN):
        a = math.radians(i * 30 - 90)
        tx = cx + (face_r - 24) * math.cos(a)
        ty = cy + (face_r - 24) * math.sin(a)
        c.text((tx + 0.7, ty + 0.9), numeral, fonts["serif"], 12.5, (0, 0, 0, 175))
        c.text((tx, ty), numeral, fonts["serif"], 12.5,
               rgba(palette["parchment"], 242))

    # inner engraved rings + compass rose
    c.circle(cx, cy, face_r - 43, outline=rgba(palette["brass"], 105), width=0.9)
    c.circle(cx, cy, face_r - 45, outline=(0, 0, 0, 130), width=0.7)
    for ang in range(0, 360, 45):
        a = math.radians(ang)
        c.line([(cx + 18 * math.cos(a), cy + 18 * math.sin(a)),
                (cx + (face_r - 46) * math.cos(a), cy + (face_r - 46) * math.sin(a))],
               fill=rgba(palette["brass"], 34), width=0.7)
    c.text((cx, cy + 38), "· 1887 ·", fonts["mono"], 6,
           rgba(palette["brass"], 150), anchor="mm")
    out.alpha_composite(c.finish())

    # 5. inner shadow where the bezel meets the enamel
    ring = Canvas(size)
    ring.circle(cx, cy, face_r, outline=(0, 0, 0, 120), width=3.2)
    out.alpha_composite(blur(ring.finish(), 1.2))
    return out


def gauge_arc(c: Canvas, cx, cy, r, start, end, frac, palette,
              width=4.0, track_alpha=70):
    c.arc(cx - r, cy - r, cx + r, cy + r, start, end,
          fill=rgba(palette["copper_dark"], track_alpha), width=width)
    if frac <= 0:
        return
    c.arc(cx - r, cy - r, cx + r, cy + r, start,
          start + (end - start) * max(0.0, min(1.0, frac)),
          fill=rgba(palette["brass_hi"], 235), width=width)


def complications_layer(palette, fonts, values, size=(W, H)) -> Image.Image:
    w, h = size
    box = (24, 272, w - 24, 362)
    out = Image.new("RGBA", size, (0, 0, 0, 0))

    mask = rrect_mask(size, box, 18)
    out.alpha_composite(drop_shadow(solid(mask, (0, 0, 0, 255)), (0.5, 2.0), 2.6, 95))
    out.alpha_composite(paint(mask, vgrad(size, [(0.0, hex_rgb(palette["brass_hi"])),
                                                 (0.18, hex_rgb(palette["brass"])),
                                                 (0.55, hex_rgb(palette["copper_dark"])),
                                                 (1.0, hex_rgb(palette["ink"]))],
                                          top=0.70, bottom=0.96)))
    inset = rrect_mask(size, (box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4), 15)
    out.alpha_composite(paint(inset, vgrad(size, [(0.0, hex_rgb(palette["iron_hi"])),
                                                  (1.0, (12, 8, 6))],
                                           top=0.70, bottom=0.96)))

    for cx in (30, w - 30):
        out.alpha_composite(rivet(size, cx, (box[1] + box[3]) / 2, 4.2, palette))

    centers = [(78, 312, "DATE"), (160, 312, "POWER"), (242, 312, "STEP")]
    c = Canvas(size)
    for (cx, cy, _label), key in zip(centers, ("date", "battery", "steps")):
        c.circle(cx, cy, 27, outline=rgba(palette["brass_dark"], 210), width=1.6)
        c.circle(cx, cy, 24.5, fill=rgba(palette["ink"], 150))
        c.circle(cx, cy, 24.5, outline=(255, 240, 205, 40), width=0.7)
    out.alpha_composite(c.finish())

    # date window
    dcx, dcy, _ = centers[0]
    c = Canvas(size)
    engrave(c, (dcx, dcy - 3), str(values["day"]), fonts["serif"], 22,
            rgba(palette["parchment"], 240), (0, 0, 0, 160), depth=1.0)
    c.text((dcx, dcy + 13), values["month"], fonts["mono"], 8,
           rgba(palette["brass_hi"], 220), anchor="mm")
    out.alpha_composite(c.finish())

    # battery gauge
    bcx, bcy, _ = centers[1]
    c = Canvas(size)
    gauge_arc(c, bcx, bcy, 19, 140, 400, values["battery"] / 100.0, palette, width=3.0)
    c.text((bcx, bcy - 1), f"{values['battery']}", fonts["serif"], 15,
           rgba(palette["parchment"], 240), anchor="mm")
    c.text((bcx, bcy + 11), "%", fonts["mono"], 6.5,
           rgba(palette["brass_hi"], 200), anchor="mm")
    out.alpha_composite(c.finish())

    # steps odometer
    scx, scy, _ = centers[2]
    c = Canvas(size)
    steps = values["steps"]
    label = f"{steps / 1000:.1f}k" if steps >= 1000 else str(steps)
    c.text((scx, scy - 2), label, fonts["serif"], 16,
           rgba(palette["parchment"], 240), anchor="mm")
    c.text((scx, scy + 12), "STEPS", fonts["mono"], 5.6,
           rgba(palette["brass_hi"], 190), anchor="mm")
    out.alpha_composite(c.finish())

    # engraved column labels
    c = Canvas(size)
    for cx, cy, label in centers:
        engrave(c, (cx, cy + 35), label, fonts["mono"], 7,
                rgba(palette["brass_hi"], 190), (0, 0, 0, 170), depth=0.7)
    out.alpha_composite(c.finish())
    return out


def _hand_shape(size, kind, palette, length):
    """Hand drawn pointing straight up, pivot at DIAL_CENTER."""
    cx, cy = DIAL_CENTER
    c = Canvas(size)
    if kind == "hour":
        pts = [(0, -length), (2.4, -length + 6), (7.8, -length + 18),
               (7.8, -length + 28), (3.6, -length + 32),
               (3.6, 10), (7.2, 14), (0, 22), (-7.2, 14),
               (-3.6, 10), (-3.6, -length + 32),
               (-7.8, -length + 28), (-7.8, -length + 18),
               (-2.4, -length + 6)]
        ring_y = cy - length + 22
        ring_r = 5.4
    elif kind == "minute":
        pts = [(0, -length), (1.7, -length + 8), (5.6, -length + 28),
               (4.8, -length + 34), (2.2, -length + 36),
               (2.2, 9), (5.6, 13), (0, 19), (-5.6, 13),
               (-2.2, 9), (-2.2, -length + 36),
               (-4.8, -length + 34), (-5.6, -length + 28),
               (-1.7, -length + 8)]
        ring_y = cy - length + 26
        ring_r = 3.8
    else:
        pts = [(0, -length), (1.1, -length + 10), (0.9, 20),
               (3.6, 26), (0, 34), (-3.6, 26), (-0.9, 20),
               (-1.1, -length + 10)]
        ring_y = ring_r = 0

    shape = [(cx + x, cy + y) for x, y in pts]
    c.polygon(shape, fill=(255, 255, 255, 255))

    if ring_r:
        # Breguet-style open ring near the tip: punch the hole, keep a rim
        c.circle(cx, ring_y, ring_r, fill=(0, 0, 0, 0))
        rim = Canvas(size)
        rim.circle(cx, ring_y, ring_r + 0.9, fill=(255, 255, 255, 255))
        rim.circle(cx, ring_y, ring_r, fill=(0, 0, 0, 0))
        c.img.alpha_composite(rim.img)
    return c.finish()


def hand_layer(palette, kind, length, size=(W, H)) -> Image.Image:
    mask = _hand_shape(size, kind, palette, length)
    alpha = mask.split()[3]

    if kind == "second":
        metal = Image.new("RGBA", size, rgba("#ff8a55"))
    else:
        # brushing light across the hand, not the whole canvas
        metal = vgrad(size, [(0.0, hex_rgb(palette["brass_hi"])),
                             (0.35, hex_rgb(palette["brass"])),
                             (0.62, hex_rgb(palette["brass_hi"])),
                             (0.85, hex_rgb(palette["copper"])),
                             (1.0, hex_rgb(palette["brass_dark"]))],
                      top=0.10, bottom=0.62)

    halo = alpha.filter(ImageFilter.MaxFilter(5))
    ring = ImageChops.subtract(halo, alpha)

    out = Image.new("RGBA", size, (0, 0, 0, 0))
    outline = Image.new("RGBA", size, rgba(palette["ink"], 235))
    outline.putalpha(ring)
    out.alpha_composite(outline)
    body = paint(mask, metal)
    out.alpha_composite(body)

    # specular streak along the raised centre
    gloss = Canvas(size)
    gloss.line([(DIAL_CENTER[0], DIAL_CENTER[1] - length + 8),
                (DIAL_CENTER[0], DIAL_CENTER[1] + 6)],
               fill=(255, 250, 235, 150 if kind != "second" else 90),
               width=0.8 if kind != "second" else 0.5)
    g = gloss.finish()
    g.putalpha(ImageChops.multiply(g.split()[3], alpha))
    out.alpha_composite(g)
    return out


def cap_layer(palette, size=(W, H)) -> Image.Image:
    cx, cy = DIAL_CENTER
    c = Canvas(size)
    c.circle(cx, cy, 8.0, fill=rgba(palette["brass_dark"]))
    c.circle(cx, cy, 6.6, fill=rgba(palette["brass"]))
    c.circle(cx - 1.6, cy - 1.8, 2.4, fill=rgba(palette["brass_hi"]))
    c.line([(cx - 4.4, cy + 1.2), (cx + 4.4, cy - 1.2)],
           fill=rgba(palette["ink"], 190), width=1.3)
    c.circle(cx, cy, 2.0, fill=rgba(palette["copper_dark"]))
    return c.finish()


def glass_layer(size=(W, H)) -> Image.Image:
    w, h = size
    c = Canvas(size)
    c.polygon([(20, 12), (150, 12), (60, 150), (12, 150)], fill=(255, 255, 255, 15))
    c.polygon([(24, 8), (74, 8), (16, 96), (10, 96)], fill=(255, 255, 255, 10))
    out = c.finish().filter(ImageFilter.GaussianBlur(9))
    return out


# --------------------------------------------------------------------------- #
# Composition
# --------------------------------------------------------------------------- #

HAND_LENGTHS = {k: float(v) for k, v in LAYOUT["hands"].items()}


def compose(layers: dict, palette, time=(10, 9, 36), size=(W, H)) -> Image.Image:
    hour, minute, second = time
    img = Image.new("RGBA", size, (0, 0, 0, 255))
    img.alpha_composite(layers["backplate"])
    if "nameplate" in layers:
        img.alpha_composite(layers["nameplate"])
    img.alpha_composite(layers["dial"])
    img.alpha_composite(layers["complications"])

    angles = {
        "hour": (hour % 12) * 30 + minute * 0.5,
        "minute": minute * 6 + second * 0.1,
        "second": second * 6,
    }
    for kind in ("hour", "minute", "second"):
        hand = layers[kind]
        rotated = hand.rotate(-angles[kind], resample=Image.BICUBIC,
                              center=PIVOT)
        img.alpha_composite(drop_shadow(rotated, (1.8, 2.6), 2.2, 110))
        img.alpha_composite(rotated)

    img.alpha_composite(layers["cap"])
    img.alpha_composite(layers["glass"])
    return img


def night_variant(img: Image.Image) -> Image.Image:
    """Low-light variant: dimmed and slightly desaturated for night use."""
    from PIL import ImageEnhance
    dim = ImageEnhance.Brightness(img).enhance(0.55)
    dim = ImageEnhance.Color(dim).enhance(0.72)
    return dim


def build_layers(palette, fonts, values) -> dict[str, Image.Image]:
    return {
        "backplate": backplate_layer(palette, fonts),
        "nameplate": nameplate_layer(palette, fonts),
        "dial": dial_layer(palette, fonts, values),
        "complications": complications_layer(palette, fonts, values),
        "hour": hand_layer(palette, "hour", HAND_LENGTHS["hour"]),
        "minute": hand_layer(palette, "minute", HAND_LENGTHS["minute"]),
        "second": hand_layer(palette, "second", HAND_LENGTHS["second"]),
        "cap": cap_layer(palette),
        "glass": glass_layer(),
    }
