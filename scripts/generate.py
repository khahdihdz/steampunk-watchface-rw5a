#!/usr/bin/env python3
"""
generate.py — render every artefact of the Steampunk LED RW5A watch face.

Outputs (under --out, default ./dist):

    photo/face.png          flattened 320x385 artwork (custom-photo slot)
    photo/face_rounded.png  same artwork pre-masked to the panel corner radius
    photo/face_night.png    dimmed variant for night / always-on
    photo/face_alpha.png    RGBA, alpha outside the movement/plates (see-through)
    layers/*.png            separated layers for Mi Watch Face Editor
    preview/preview.png     device mock-up for the README
    preview/rotation.gif    animated preview (giây chạy)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image

import steampunk as sp

SERIF_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
    "/system/fonts/NotoSerif-Bold.ttf",
]

MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf",
    "/system/fonts/DroidSansMono.ttf",
]


def pick_font(candidates, label: str) -> str:
    env = os.environ.get(f"WATCHFACE_FONT_{label.upper()}")
    for path in ([env] if env else []) + candidates:
        if path and Path(path).exists():
            return path
    raise SystemExit(
        f"Không tìm thấy font {label}. Cài fonts-noto-core/fonts-dejavu-core "
        "hoặc đặt biến môi trường WATCHFACE_FONT_<LABEL>."
    )


def parse_time(value: str) -> tuple[int, int, int]:
    parts = [int(p) for p in value.split(":")] + [0, 0, 0]
    hour, minute, second = parts[:3]
    if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
        raise argparse.ArgumentTypeError(f"giờ không hợp lệ: {value}")
    return hour, minute, second


def render_device_mock(face: Image.Image) -> Image.Image:
    """Wrap the artwork in a stylised case so the README shows it in context."""
    w, h = 560, 700
    out = sp.radial((w, h), [(0.0, (46, 34, 25)), (0.55, (21, 16, 13)),
                             (1.0, (9, 7, 6))]).convert("RGB")

    for y0, y1 in ((-40, 150), (524, h + 40)):
        strap = sp.rrect_mask((w, h), (206, y0, 354, y1), 30)
        out.paste((38, 28, 22), (0, 0), strap.split()[3])
        for x in (228, 332):
            line = sp.Canvas((w, h), scale=2)
            line.line([(x, max(y0, 0) + 24), (x, min(y1, h) - 24)],
                      fill=(104, 76, 51, 255), width=1.0)
            stitch = line.finish().split()[3].point(lambda v: int(v * 0.55))
            out.paste((26, 19, 15), (0, 0), stitch)

    body = sp.rrect_mask((w, h), (52, 62, 508, 611), 58)
    shadow = sp.blur(sp.solid(body, (0, 0, 0, 255)), 16)
    out.paste((0, 0, 0), (0, 0), shadow.split()[3].point(lambda v: int(v * 0.75)))
    out.paste(sp.vgrad((w, h), [(0.0, (60, 48, 37)), (0.35, (35, 27, 22)),
                                (1.0, (14, 10, 9))], top=0.08, bottom=0.94)
              .convert("RGB"), (0, 0), body.split()[3])

    ring = sp.rrect_mask((w, h), (60, 70, 500, 603), 52)
    out.paste(sp.vgrad((w, h), [(0.0, sp.hex_rgb("#f6d894")),
                                (0.18, sp.hex_rgb("#c8963e")),
                                (0.5, sp.hex_rgb("#6b4519")),
                                (0.82, sp.hex_rgb("#c8963e")),
                                (1.0, sp.hex_rgb("#6b4519"))],
                       top=0.10, bottom=0.96).convert("RGB"),
              (0, 0), ring.split()[3])

    inner = sp.rrect_mask((w, h), (76, 90, 484, 583), 46)
    out.paste((7, 5, 4), (0, 0), inner.split()[3])

    screen = face.resize((404, 487), Image.LANCZOS)
    mask = sp.rrect_mask((404, 487), (0, 0, 404, 487),
                         sp.CORNER_RADIUS * 404 / 320)
    out.paste(screen.convert("RGB"), (78, 92), mask.split()[3])
    return out


def render_gif(layers, palette, fonts, path: Path, size=(160, 193), frames=20) -> None:
    imgs = []
    for i in range(frames):
        second = i * (60 // frames)
        frame = sp.compose(layers, palette, fonts, (10, 9, second))
        small = frame.convert("RGB").resize(size, Image.LANCZOS)
        imgs.append(small.quantize(colors=128, method=Image.FASTOCTREE))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=120,
                 loop=0, optimize=True, disposal=2)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist")
    parser.add_argument("--time", default="10:09:36", type=parse_time)
    parser.add_argument("--no-gif", action="store_true")
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args(argv)

    out = Path(args.out)
    for sub in ("photo", "layers", "preview"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    palette = sp.load_palette()
    fonts = {"serif": pick_font(SERIF_CANDIDATES, "serif"),
             "mono": pick_font(MONO_CANDIDATES, "mono")}
    values = sp.LAYOUT["sample_values"]

    layers = sp.build_static(palette, fonts, values)
    face = sp.compose(layers, palette, fonts, args.time)

    face.convert("RGB").save(out / "photo" / "face.png", optimize=True)

    rounded = face.copy()
    rounded.putalpha(sp.screen_mask().split()[3])
    rounded.save(out / "photo" / "face_rounded.png", optimize=True)

    solid = dict(layers)
    solid.update({
        "nameplate": sp.nameplate_layer(palette, fonts, opacity=1.0),
        "led_panel": sp.led_panel_layer(palette, fonts, opacity=1.0),
        "date_strip": sp.date_strip_layer(palette, fonts, values, opacity=1.0),
        "complications": sp.complications_layer(palette, fonts, values, opacity=1.0),
    })
    clear = sp.compose(solid, palette, fonts, args.time, backdrop=False)
    clear.save(out / "photo" / "face_alpha.png", optimize=True)

    sp.night_variant(face).convert("RGB").save(
        out / "photo" / "face_night.png", optimize=True)

    layer_ids = {entry["id"] for entry in sp.LAYOUT["layers"]}
    key_for = {
        "00_backdrop": "backdrop", "01_movement": "movement",
        "02_crystal": "crystal", "03_nameplate": "nameplate",
        "04_led_panel": "led_panel", "06_date_strip": "date_strip",
        "07_complications": "complications", "20_glass": "glass",
    }
    for layer_id, key in key_for.items():
        if layer_id in layer_ids:
            layers[key].save(out / "layers" / f"{layer_id}.png", optimize=True)

    if "05_readout" in layer_ids:
        sp.readout_layer(palette, fonts, args.time).save(
            out / "layers" / "05_readout.png", optimize=True)

    if not args.no_preview:
        render_device_mock(face).save(out / "preview" / "preview.png", optimize=True)
    if not args.no_gif:
        render_gif(layers, palette, fonts, out / "preview" / "rotation.gif")

    (out / "layout.json").write_text(
        json.dumps(sp.LAYOUT, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"rendered {len(list(out.rglob('*.png')))} png + "
          f"{len(list(out.rglob('*.gif')))} gif into {out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
