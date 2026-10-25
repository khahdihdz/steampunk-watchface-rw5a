#!/usr/bin/env python3
"""Assert that the rendered artefacts match the device and design constraints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageStat

import steampunk as sp

EXPECTED = {
    "photo/face.png",
    "photo/face_rounded.png",
    "photo/face_night.png",
    "photo/face_alpha.png",
    "layers/00_backdrop.png",
    "layers/01_movement.png",
    "layers/02_crystal.png",
    "layers/03_nameplate.png",
    "layers/04_led_panel.png",
    "layers/05_readout.png",
    "layers/06_date_strip.png",
    "layers/07_complications.png",
    "layers/20_glass.png",
}

failures: list[str] = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def count_near(img: Image.Image, color: str, tolerance: int = 46) -> int:
    target = sp.hex_rgb(color)
    px = img.convert("RGB").getdata()
    limit = tolerance ** 2 * 3
    return sum(1 for p in px
               if sum((a - b) ** 2 for a, b in zip(p, target)) < limit)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", default="dist")
    parser.add_argument("--skip-preview", action="store_true")
    args = parser.parse_args(argv)
    dist = Path(args.dist)

    for rel in sorted(EXPECTED):
        check((dist / rel).exists(), f"thiếu tệp {rel}")
    if failures:
        report()
        return 1

    face = Image.open(dist / "photo/face.png")
    check(face.size == (sp.W, sp.H), f"face.png sai kích thước {face.size}")
    check(face.mode == "RGB", f"face.png phải là RGB, đang là {face.mode}")

    for rel in sorted(EXPECTED):
        if not rel.startswith("layers/"):
            continue
        layer = Image.open(dist / rel)
        check(layer.size == (sp.W, sp.H), f"{rel} sai kích thước {layer.size}")
        check(layer.mode == "RGBA", f"{rel} phải là RGBA")
        check(layer.split()[3].getbbox() is not None, f"{rel} rỗng (alpha trắng)")

    # --- LED readout ------------------------------------------------------ #
    readout = Image.open(dist / "layers/05_readout.png")
    box = readout.split()[3].getbbox()
    panel = sp.PANEL
    check(panel[0] <= box[0] and box[2] <= panel[2]
          and panel[1] <= box[1] and box[3] <= panel[3],
          f"readout {box} tràn ra ngoài khung LED {panel}")

    lit = count_near(readout, sp.LED["color"], 60)
    check(lit > 1200, f"quá ít pixel LED sáng ({lit}) — số 7 đoạn có thể không render")

    ghost = Image.open(dist / "layers/04_led_panel.png")
    ghost_box = ghost.split()[3].getbbox()
    check(ghost_box is not None
          and ghost_box[0] <= panel[0] and ghost_box[1] <= panel[1]
          and ghost_box[2] >= panel[2] and ghost_box[3] >= panel[3],
          f"led_panel không phủ khung LED {panel}: {ghost_box}")
    check(ghost_box is not None and (ghost_box[2] - ghost_box[0]) < sp.W,
          f"led_panel tràn toàn canvas: {ghost_box}")

    # digit sprites must be wide enough for 5 glyphs at the configured metrics
    cfg = sp.LED
    five = sp.seven_seg_width("88:88", cfg)
    check(five <= (panel[2] - panel[0] - 14),
          f"chuỗi 88:88 ({five:.0f}px) rộng hơn khung LED")
    check(cfg["stroke"] < cfg["digit_h"] / 5,
          "stroke quá dày so với chiều cao số — 7 đoạn sẽ dính khối")
    check(sp.SEC["stroke"] < sp.SEC["digit_h"] / 4,
          "stroke giây quá dày")

    # --- skeleton movement ------------------------------------------------ #
    movement = Image.open(dist / "layers/01_movement.png")
    mbox = movement.split()[3].getbbox()
    check(mbox is not None, "layer movement rỗng — không thấy bộ máy")
    check(mbox is not None and mbox[0] <= 2 and mbox[2] >= sp.W - 2,
          f"bộ máy không phủ hai mép trái/phải: {mbox}")
    check(count_near(movement, sp.load_palette()["brass"], 70) > 3000,
          "quá ít chi tiết đồng trong bộ máy")

    backdrop = Image.open(dist / "layers/00_backdrop.png")
    check(backdrop.split()[3].getpixel((0, 0)) == 255,
          "backdrop phải đục hoàn toàn ở tâm góc")

    # --- transparent variant ---------------------------------------------- #
    clear = Image.open(dist / "photo/face_alpha.png")
    check(clear.mode == "RGBA", f"face_alpha phải là RGBA, đang là {clear.mode}")
    ca = clear.split()[3]
    check(ca.getpixel((0, 0)) == 0, "face_alpha: góc phải trong suốt")
    check(ca.getpixel((sp.W // 2, 120)) >= 230,
          "face_alpha: vùng số phải đục để đọc được")
    check(ca.getpixel((sp.W // 2, 231)) < 40,
          "face_alpha: khe giữa các bảng vẫn đục — nền chưa xuyên thấu")

    # --- rounded panel ---------------------------------------------------- #
    rounded = Image.open(dist / "photo/face_rounded.png")
    alpha = rounded.split()[3]
    for corner in ((0, 0), (sp.W - 1, 0), (0, sp.H - 1), (sp.W - 1, sp.H - 1)):
        check(alpha.getpixel(corner) == 0,
              f"góc {corner} chưa được bo tròn (alpha != 0)")
    check(alpha.getpixel((sp.W // 2, sp.H // 2)) == 255,
          "tâm mặt đồng hồ bị trong suốt")

    for x, y in ((3, 3), (sp.W - 4, 3), (3, sp.H - 4), (sp.W - 4, sp.H - 4)):
        r, g, b = face.getpixel((x, y))
        check(0.299 * r + 0.587 * g + 0.114 * b < 75,
              f"góc ({x},{y}) quá sáng — nội dung có thể bị cắt bởi bo góc")

    # --- night variant ---------------------------------------------------- #
    night = Image.open(dist / "photo/face_night.png")
    check(ImageStat.Stat(night.convert("L")).mean[0]
          < 0.85 * ImageStat.Stat(face.convert("L")).mean[0],
          "face_night.png chưa tối hơn bản ngày")

    # --- layout tokens ---------------------------------------------------- #
    layout = json.loads((dist / "layout.json").read_text(encoding="utf-8"))
    check(layout["canvas"]["width"] == sp.W and layout["canvas"]["height"] == sp.H,
          "layout.json sai kích thước canvas")
    check(layout["canvas"]["corner_radius"] == sp.CORNER_RADIUS,
          "layout.json sai bán kính bo góc")

    ids = [layer["id"] for layer in layout["layers"]]
    check(ids == sorted(ids, key=lambda s: s), "thứ tự layer không tăng dần")
    check("05_readout" in ids, "layout.json thiếu layer readout")
    check(all(label for label in layout["complications"]["labels"]),
          "layout.json thiếu nhãn phức hợp")

    if not args.skip_preview:
        for rel in ("preview/preview.png", "preview/rotation.gif"):
            check((dist / rel).exists(), f"thiếu {rel}")

    report()
    return 1 if failures else 0


def report() -> None:
    if failures:
        print(f"✗ {len(failures)}/{checks} kiểm tra thất bại:")
        for item in failures:
            print(f"  - {item}")
    else:
        print(f"✓ {checks} kiểm tra đều đạt ({sp.W}×{sp.H}, bo góc "
              f"{sp.CORNER_RADIUS}px, LED 7 đoạn)")


if __name__ == "__main__":
    sys.exit(main())
