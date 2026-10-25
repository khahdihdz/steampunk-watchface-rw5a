#!/usr/bin/env python3
"""
binface.py — xuất project EasyFace (``.fprj`` + ``images/``) để ``compile.exe``
của Mi-Create biên dịch thành file ``.bin`` cài được cho Redmi Watch 5 Active.

Vì sao phải qua Mi-Create: firmware HyperOS chỉ kiểm tra 4 byte magic
``5A A5 34 12``, nhưng ảnh bên trong dùng bộ nén riêng (``RedmiWatch5Active
Compressor``) mà không có codec công khai. ``compile.exe`` (GPL-3.0) là bộ biên
dịch duy nhất biết định dạng đó.

    python3 scripts/binface.py --out build/fprj
    compile.exe -b build\\fprj\\face.fprj build\\bin face.face 1461256429

Mọi giá trị động (giờ, phút, giây, ngày, tháng, năm, thứ, pin, bước, nhịp tim)
được để trống trên nền và do widget của firmware vẽ lên.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

import steampunk as sp

PROJECT_ID = "1461256429"
DEVICE_TYPE = "3651"        # redmi_watch_5_active trong Mi-Create
TITLE = "AETHER Steampunk"

# Nguồn dữ liệu (id_fprj, đúng cho redmi_watch_5_active)
SRC = {
    "hour_hi": "1000911", "hour_lo": "0911",
    "min_hi": "1211", "min_lo": "1111",
    "sec_hi": "1001911", "sec_lo": "1911",
    "day": "1812", "month": "1012", "year": "0812", "week": "2012",
    "battery": "0841", "steps": "0821", "heart": "0822",
}

WEEKDAYS = ["CHỦ NHẬT", "THỨ 2", "THỨ 3", "THỨ 4", "THỨ 5", "THỨ 6", "THỨ 7"]

BIG = dict(sp.LED)
SEC = dict(sp.SEC)
MED = {"digit_w": 16.0, "digit_h": 26.0, "stroke": 3.8, "gap": 1.8,
       "spacing": 3.0, "colon_w": 7.0, "slant": 0.04}
WIDE = {"digit_w": 13.5, "digit_h": 24.0, "stroke": 3.2, "gap": 1.6,
        "spacing": 2.4, "colon_w": 6.0, "slant": 0.04}


# --------------------------------------------------------------------------- #
# Glyph sheets — mỗi ảnh là MỘT ô (cell) đúng bằng bước tiến của glyph
# --------------------------------------------------------------------------- #

class Sheet:
    """Bộ glyph 0-9 cùng kích thước ô, kèm offset đặt ảnh."""

    def __init__(self, images: dict[str, Image.Image], cell_w: int, cell_h: int,
                 x_off: int, y_off: int, order: list[str], prefix: str = "g"):
        self.images = images
        self.cell_w = cell_w
        self.cell_h = cell_h
        self.x_off = x_off
        self.y_off = y_off
        self.order = order
        self.prefix = prefix

    @property
    def names(self) -> list[str]:
        return [f"{self.prefix}{i}" for i in range(len(self.order))]

    def with_prefix(self, prefix: str) -> "Sheet":
        self.prefix = prefix
        return self


def seven_seg_sheet(cfg, color: str, glow: int, pad_v: int = 8,
                    scale: int = sp.SS) -> Sheet:
    probe = sp.led_text("0", cfg, color, glow=glow, scale=scale)
    cell_w = max(int(math.ceil(cfg["digit_w"] + cfg["spacing"])), probe.width)
    cell_h = probe.height + 2 * pad_v
    x_off = (cell_w - probe.width) // 2
    images = {}
    for d in range(10):
        spr = sp.led_text(str(d), cfg, color, glow=glow, scale=scale)
        img = Image.new("RGBA", (cell_w, cell_h), (0, 0, 0, 0))
        img.alpha_composite(spr, (x_off, pad_v))
        images[str(d)] = img
    return Sheet(images, cell_w, cell_h, x_off, pad_v, [str(d) for d in range(10)])


def text_sheet(font_path: str, size: float, color, strings: list[str],
               cell_w: float | None = None, pad_v: int = 3) -> Sheet:
    """Vẽ chuỗi vào ô cùng bề rộng (căn giữa) — dùng cho ngày/tháng/năm/thứ."""
    font = ImageFont.truetype(font_path, int(round(size * sp.SS)))
    widths = [font.getlength(s) / sp.SS for s in strings]
    cw = cell_w if cell_w is not None else (max(widths) + 1.0)
    line_h = size * 1.45
    cell_w_i = int(math.ceil(max(cw, 1)))
    cell_h_i = int(math.ceil(line_h)) + 2 * pad_v
    images = {}
    for s, w in zip(strings, widths):
        img = Image.new("RGBA", (cell_w_i * sp.SS, int(math.ceil(line_h)) * sp.SS),
                        (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((img.width / 2, img.height / 2), s, font=font, fill=color,
                  anchor="mm")
        img = img.resize((cell_w_i, int(math.ceil(line_h))), Image.LANCZOS)
        out = Image.new("RGBA", (cell_w_i, cell_h_i), (0, 0, 0, 0))
        out.alpha_composite(img, (0, pad_v))
        images[s] = out
    return Sheet(images, cell_w_i, cell_h_i, 0, pad_v, list(strings))


# --------------------------------------------------------------------------- #
# Geometry
# --------------------------------------------------------------------------- #

def clock_geometry():
    gx, clock_w, sec_w = sp.time_layout("88")
    dw, spx = sp.LED["digit_w"], sp.LED["spacing"]
    cw = sp.LED["colon_w"]
    y = 72
    sec_x = gx + clock_w + 10
    sec_y = y + (sp.LED["digit_h"] - sp.SEC["digit_h"])
    return {"hour": (gx, y), "minute": (gx + 2 * (dw + spx) + cw + spx, y),
            "second": (sec_x, sec_y), "colon": (gx + 2 * (dw + spx), y),
            "advance": dw + spx}


def date_geometry(fonts, size=10.5):
    x0, y0, x1, y1 = sp.DATE_BOX
    cy = (y0 + y1) / 2
    font = ImageFont.truetype(fonts["serif"], int(round(size)))
    digit_w = max(font.getlength(str(d)) for d in range(10)) + 0.4
    sep_w = 5.0
    wd_cell = max(font.getlength(s) for s in WEEKDAYS) + 1.0

    total = wd_cell + 6 + 2 * digit_w + sep_w + 2 * digit_w + sep_w + 4 * digit_w
    x = (x0 + x1) / 2 - total / 2

    geo = {"week": x}
    x += wd_cell + 6
    geo["day"] = x
    x += 2 * digit_w
    geo["sep1"] = x
    x += sep_w
    geo["month"] = x
    x += 2 * digit_w
    geo["sep2"] = x
    x += sep_w
    geo["year"] = x
    return {"geo": geo, "cy": cy, "digit_w": digit_w, "sep_w": sep_w,
            "wd_cell": wd_cell, "size": size}


# --------------------------------------------------------------------------- #
# Project
# --------------------------------------------------------------------------- #

class Project:
    def __init__(self, out: Path):
        self.out = out
        self.img_dir = out / "images"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.widgets: list[dict] = []
        self.images: dict[str, Image.Image] = {}

    def add(self, name: str, img: Image.Image, palettize: bool = True):
        # Bộ nén ảnh của RW5A chỉ nhận tối đa 256 màu cho mỗi ảnh trong
        # imageList ("Colors count is more than 256 pcs, unsupported now").
        if palettize and (img.getcolors(maxcolors=256) is None):
            img = img.quantize(colors=256, method=Image.FASTOCTREE,
                               dither=Image.FLOYDSTEINBERG).convert("RGBA")
        self.images[name] = img
        img.save(self.img_dir / f"{name}.png", optimize=True)

    def add_sheet(self, sheet: Sheet):
        for i, key in enumerate(sheet.order):
            self.add(f"{sheet.prefix}{i}", sheet.images[key], palettize=True)

    def widget(self, **kw):
        self.widgets.append(kw)

    def write(self):
        rows = ['<?xml version="1.0" encoding="utf-8"?>',
                f'<FaceProject DeviceType="{DEVICE_TYPE}" Id="{PROJECT_ID}">',
                f'  <Screen Title="{escape(TITLE)}" Bitmap="preview.png">']
        for w in self.widgets:
            attrs = " ".join(f'{k}="{escape(str(v))}"' for k, v in w.items())
            rows.append(f"    <Widget {attrs}/>")
        rows += ["  </Screen>", "</FaceProject>"]
        (self.out / "face.fprj").write_text("\n".join(rows) + "\n", encoding="utf-8")
        (self.out / "manifest.json").write_text(json.dumps({
            "device": "Redmi Watch 5 Active", "device_type": DEVICE_TYPE,
            "width": sp.W, "height": sp.H, "widgets": self.widgets,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def image_list(names: list[str], indexed: bool) -> str:
    if indexed:
        return "|".join(f"({i}):{n}.png" for i, n in enumerate(names))
    return "|".join(f"{n}.png" for n in names)


def src(value: str) -> str:
    return str(int(value))


def element(proj: Project, name: str, bitmap: str, x: float, y: float):
    img = proj.images[bitmap]
    proj.widget(Shape=30, Name=name, Bitmap=f"{bitmap}.png",
                X=int(round(x)), Y=int(round(y)),
                Width=img.width, Height=img.height, Alpha=255, Visible_Src=0)


def imagelist(proj: Project, name: str, sheet: Sheet, prefix: str,
              source: str, x: float, y: float):
    proj.widget(Shape=31, Name=name, BitmapList=image_list(sheet.names, True),
                X=int(round(x)), Y=int(round(y)),
                Width=sheet.cell_w, Height=sheet.cell_h, Alpha=255,
                Alignment=0, DefaultIndex=0, Value_Src=0, Spacing=0,
                Blanking=0, Visible_Src=0, Index_Src=src(source))


def number(proj: Project, name: str, sheet: Sheet, prefix: str, source: str,
           digits: int, x_right: float, y_top: float,
           align: int = 2, blanking: int = 1):
    proj.widget(Shape=32, Name=name, BitmapList=image_list(sheet.names, False),
                X=int(round(x_right - digits * sheet.cell_w)),
                Y=int(round(y_top)), Width=sheet.cell_w, Height=sheet.cell_h,
                Alpha=255, Visible_Src=0, Digits=digits, Alignment=align,
                Value_Src=src(source), Spacing=0, Blanking=blanking)


# --------------------------------------------------------------------------- #
# Build
# --------------------------------------------------------------------------- #

def build(out: Path, fonts: dict, opacity=None) -> Project:
    palette = sp.load_palette()
    proj = Project(out)

    # ---- nền tĩnh ----
    layers = sp.build_static(palette, fonts, None, opacity=opacity)
    bg = sp.static_composite(layers)

    # "%" tĩnh cạnh ô pin (trước đây vẽ chung cụm số)
    pct = sp.Canvas((sp.W, sp.H))
    pct.text((sp.COMP["centers"][0][0] + 19, sp.COMP["centers"][0][1] + 3), "%",
             fonts["mono"], 7.5, sp.rgba(palette["brass_hi"], 225), anchor="mm")
    bg.alpha_composite(pct.finish())
    proj.add("bg", bg, palettize=False)
    element(proj, "bg", "bg", 0, 0)

    # ---- glyph ----
    big = seven_seg_sheet(BIG, sp.LED["color"], 120, pad_v=8).with_prefix("h")
    sec = seven_seg_sheet(SEC, sp.SEC["color"], 170, pad_v=6).with_prefix("s")
    med = seven_seg_sheet(MED, sp.LED["color"], 110, pad_v=4).with_prefix("md")
    wide = seven_seg_sheet(WIDE, sp.LED["color"], 95, pad_v=4).with_prefix("wd")

    date = date_geometry(fonts)
    ink = sp.rgba(palette["parchment"], 232)
    dd = text_sheet(fonts["serif"], date["size"], ink,
                    [str(d) for d in range(10)], cell_w=date["digit_w"])
    dd.with_prefix("dd")
    sep = text_sheet(fonts["serif"], date["size"], ink, ["/"],
                     cell_w=date["sep_w"])
    wd = text_sheet(fonts["serif"], date["size"], ink, WEEKDAYS,
                    cell_w=date["wd_cell"])
    wd.with_prefix("wk")

    for sheet in (big, sec, med, wide, dd, wd):
        proj.add_sheet(sheet)
    proj.add("sep", sep.images["/"])
    proj.add("colon", sp.led_text(":", dict(sp.LED), sp.LED["color"], glow=110))
    proj.add("preview", bg.convert("RGB").resize((180, 216), Image.LANCZOS),
             palettize=False)

    # ---- giờ : phút (mỗi chữ số một widget -> căn tuyệt đối) ----
    geo = clock_geometry()
    for group, prefix, (cx, cy) in (("hour", "hour", geo["hour"]),
                                    ("minute", "min", geo["minute"])):
        for k, (s, dx) in enumerate(((f"{prefix}_hi", 0.0),
                                     (f"{prefix}_lo", geo["advance"]))):
            imagelist(proj, f"{group}_{k}", big, "h", SRC[s],
                      cx + dx - big.x_off, cy - big.y_off)

    element(proj, "colon", "colon", geo["colon"][0], geo["colon"][1])

    for k, (s, dx) in enumerate((("sec_hi", 0.0),
                                 ("sec_lo", sp.SEC["digit_w"] + sp.SEC["spacing"]))):
        imagelist(proj, f"second_{k}", sec, "s", SRC[s],
                  geo["second"][0] + dx - sec.x_off,
                  geo["second"][1] - sec.y_off)

    # ---- dải ngày ----
    dg, cy = date["geo"], date["cy"]
    top = cy - dd.cell_h / 2
    imagelist(proj, "weekday", wd, "wk", SRC["week"], dg["week"], top)

    number(proj, "day", dd, "dd", SRC["day"], 2,
           dg["day"] + 2 * date["digit_w"], top, align=2, blanking=1)
    number(proj, "month", dd, "dd", SRC["month"], 2,
           dg["month"] + 2 * date["digit_w"], top, align=2, blanking=1)
    number(proj, "year", dd, "dd", SRC["year"], 4,
           dg["year"] + 4 * date["digit_w"], top, align=2, blanking=0)

    element(proj, "sep1", "sep", dg["sep1"], cy - sep.cell_h / 2)
    element(proj, "sep2", "sep", dg["sep2"], cy - sep.cell_h / 2)

    # ---- phức hợp: pin / bước / nhịp tim ----
    centers = sp.COMP["centers"]
    specs = (("battery", SRC["battery"], 3, med, 58.0),
             ("steps", SRC["steps"], 4, wide, None),
             ("heart", SRC["heart"], 3, med, None))
    for name, source, digits, sheet, cx_override in specs:
        cx, cyy = centers[0] if name == "battery" else centers[1] if name == "steps" else centers[2]
        if cx_override is not None:
            cx = cx_override
        right = cx + digits * sheet.cell_w / 2
        number(proj, name, sheet, sheet.prefix, source, digits,
               right, cyy - sheet.cell_h / 2, align=2, blanking=1)

    proj.write()
    return proj


# --------------------------------------------------------------------------- #
# Dry-run cục bộ: ghép glyph theo đúng toạ độ để soi căn chỉnh
# --------------------------------------------------------------------------- #

SAMPLE = {"hour_0": 1, "hour_1": 0, "minute_0": 0, "minute_1": 9,
          "second_0": 3, "second_1": 6, "weekday": 2,
          "day": 25, "month": 10, "year": 2026,
          "battery": 78, "steps": 6428, "heart": 72}


def preview(proj: Project, path: Path):
    img = proj.images["bg"].copy()
    for w in proj.widgets:
        if w["Name"] == "bg":
            continue
        if w["Shape"] == 30:
            img.alpha_composite(proj.images[w["Bitmap"][:-4]], (w["X"], w["Y"]))
            continue
        if w["Shape"] == 31:
            names = [n.split(":", 1)[1][:-4] for n in w["BitmapList"].split("|")]
            idx = SAMPLE.get(w["Name"], 3)
            img.alpha_composite(proj.images[names[idx]], (w["X"], w["Y"]))
            continue
        value = SAMPLE.get(w["Name"], 0)
        names = [n[:-4] for n in w["BitmapList"].split("|")]
        text = str(value).zfill(w["Digits"])
        if w["Blanking"]:
            text = str(value)
        pad = w["Digits"] - len(text)
        if w["Alignment"] == 2:
            start = pad
        elif w["Alignment"] == 1:
            start = pad // 2
        else:
            start = 0
        for i, ch in enumerate(text):
            img.alpha_composite(proj.images[names[int(ch)]],
                                (w["X"] + (start + i) * w["Width"], w["Y"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(path, optimize=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="build/fprj")
    parser.add_argument("--serif", default=None)
    parser.add_argument("--mono", default=None)
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args(argv)

    from generate import pick_font, SERIF_CANDIDATES, MONO_CANDIDATES

    fonts = {"serif": args.serif or pick_font(SERIF_CANDIDATES, "serif"),
             "mono": args.mono or pick_font(MONO_CANDIDATES, "mono")}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    proj = build(out, fonts)
    print(f"{len(proj.widgets)} widget, {len(proj.images)} ảnh → {out}/face.fprj")
    if not args.no_preview:
        preview(proj, out / "preview_dryrun.png")
        print(f"dry-run: {out}/preview_dryrun.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
