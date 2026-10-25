#!/usr/bin/env python3
"""validate_fprj.py — kiểm tra project EasyFace trước khi đưa vào compile.exe.

Không thay thế compiler; chỉ bắt các lỗi ngớ ngẩn (thiếu ảnh, sai số ô glyph,
toạ độ ra ngoài màn hình, BitmapList lệch với Digits) để vòng CI không tốn
một lượt chạy Windows.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

W, H = 320, 385


def check(project: Path) -> list[str]:
    errors: list[str] = []
    fprj = project / "face.fprj"
    if not fprj.exists():
        return [f"không thấy {fprj}"]

    root = ET.parse(fprj).getroot()
    if root.tag != "FaceProject":
        errors.append(f"root phải là FaceProject, đang là {root.tag}")
    if not root.get("DeviceType"):
        errors.append("FaceProject thiếu DeviceType")

    screen = root.find("Screen")
    if screen is None:
        return errors + ["thiếu <Screen>"]
    for attr in ("Title", "Bitmap"):
        if not screen.get(attr):
            errors.append(f"Screen thiếu {attr}")

    preview = screen.get("Bitmap", "")
    if preview and not (project / "images" / preview).exists():
        errors.append(f"thiếu ảnh preview {preview}")

    images = {p.name for p in (project / "images").glob("*.png")}
    widgets = screen.findall("Widget")
    if not widgets:
        errors.append("không có Widget nào")

    for w in widgets:
        name = w.get("Name", "?")
        shape = w.get("Shape")
        if shape not in {"30", "31", "32"}:
            errors.append(f"{name}: Shape {shape} chưa hỗ trợ")

        if shape == "30":
            bmp = w.get("Bitmap")
            if not bmp:
                errors.append(f"{name}: thiếu Bitmap")
            elif bmp not in images:
                errors.append(f"{name}: thiếu ảnh {bmp}")

        if shape == "31":
            entries = [e for e in w.get("BitmapList", "").split("|") if e]
            if not entries:
                errors.append(f"{name}: BitmapList rỗng")
            for e in entries:
                if ":" not in e:
                    errors.append(f"{name}: BitmapList phải dạng (i):file.png")
                    break
                f = e.split(":", 1)[1]
                if f not in images:
                    errors.append(f"{name}: thiếu ảnh {f}")
            if not w.get("Index_Src"):
                errors.append(f"{name}: thiếu Index_Src")

        if shape == "32":
            entries = [e for e in w.get("BitmapList", "").split("|") if e]
            if len(entries) != 10:
                errors.append(f"{name}: cần đúng 10 ảnh glyph, có {len(entries)}")
            for f in entries:
                if f not in images:
                    errors.append(f"{name}: thiếu ảnh {f}")
            if not w.get("Value_Src"):
                errors.append(f"{name}: thiếu Value_Src")
            digits = int(w.get("Digits", "0"))
            if digits <= 0:
                errors.append(f"{name}: Digits phải > 0")

        try:
            x, y = int(w.get("X", "0")), int(w.get("Y", "0"))
            ww, hh = int(w.get("Width", "0")), int(w.get("Height", "0"))
        except ValueError:
            errors.append(f"{name}: X/Y/Width/Height không phải số nguyên")
            continue
        if ww <= 0 or hh <= 0:
            errors.append(f"{name}: Width/Height phải > 0")
        if shape == "30" and (x < 0 or y < 0 or x + ww > W or y + hh > H):
            errors.append(f"{name}: ảnh tràn canvas ({x},{y} {ww}x{hh})")

    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", default="build/fprj")
    args = parser.parse_args(argv)

    project = Path(args.project)
    errors = check(project)
    if errors:
        for e in errors:
            print(f"✗ {e}")
        return 1
    count = len(ET.parse(project / "face.fprj").getroot().findall("Screen/Widget"))
    print(f"✓ {count} widget, ảnh đầy đủ ({project})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
