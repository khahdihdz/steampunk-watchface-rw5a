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
    "layers/00_backplate.png",
    "layers/01_nameplate.png",
    "layers/02_dial.png",
    "layers/03_complications.png",
    "layers/10_hand_hour.png",
    "layers/11_hand_minute.png",
    "layers/12_hand_second.png",
    "layers/13_cap.png",
    "layers/20_glass.png",
}

failures: list[str] = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(message)


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

    for hand, max_width in (("10_hand_hour", 34), ("11_hand_minute", 30),
                            ("12_hand_second", 20)):
        box = Image.open(dist / f"layers/{hand}.png").split()[3].getbbox()
        width = box[2] - box[0]
        check(width <= max_width, f"{hand} quá rộng ({width}px) — kim bị méo")

    # pivot must sit inside every hand layer
    for hand in ("10_hand_hour", "11_hand_minute", "12_hand_second"):
        box = Image.open(dist / f"layers/{hand}.png").split()[3].getbbox()
        px, py = sp.PIVOT
        check(box[0] <= px <= box[2] and box[1] <= py <= box[3],
              f"{hand} không chứa tâm xoay {sp.PIVOT}")

    # rounded panel: transparent corners, opaque centre
    rounded = Image.open(dist / "photo/face_rounded.png")
    alpha = rounded.split()[3]
    for corner in ((0, 0), (sp.W - 1, 0), (0, sp.H - 1), (sp.W - 1, sp.H - 1)):
        check(alpha.getpixel(corner) == 0,
              f"góc {corner} chưa được bo tròn (alpha != 0)")
    check(alpha.getpixel((sp.W // 2, sp.H // 2)) == 255,
          "tâm mặt đồng hồ bị trong suốt")

    # dark corners keep the visual weight away from the rounded cut
    for x, y in ((3, 3), (sp.W - 4, 3), (3, sp.H - 4), (sp.W - 4, sp.H - 4)):
        r, g, b = face.getpixel((x, y))
        check(0.299 * r + 0.587 * g + 0.114 * b < 70,
              f"góc ({x},{y}) quá sáng — nội dung có thể bị cắt bởi bo góc")

    night = Image.open(dist / "photo/face_night.png")
    check(ImageStat.Stat(night.convert("L")).mean[0]
          < 0.85 * ImageStat.Stat(face.convert("L")).mean[0],
          "face_night.png chưa tối hơn bản ngày")

    layout = json.loads((dist / "layout.json").read_text(encoding="utf-8"))
    check(layout["canvas"]["width"] == sp.W and layout["canvas"]["height"] == sp.H,
          "layout.json sai kích thước canvas")
    check(layout["canvas"]["corner_radius"] == sp.CORNER_RADIUS,
          "layout.json sai bán kính bo góc")

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
              f"{sp.CORNER_RADIUS}px)")


if __name__ == "__main__":
    sys.exit(main())
