#!/usr/bin/env python3
"""check_bin.py — kiểm tra file .bin do compile.exe sinh ra.

Không giải mã ảnh (bộ nén của RW5A là độc quyền), chỉ xác minh phần vỏ mà
firmware đọc trước: magic, kích thước header, bảng resource, ảnh nền, tên mặt
và danh sách nguồn dữ liệu của widget.

    python3 scripts/check_bin.py build/bin/steampunk-rw5a.bin --name "AETHER Steampunk"
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

MAGIC = bytes([0x5A, 0xA5, 0x34, 0x12])
TABLE = 0x1C0
ENTRY = 16

IMG_TYPES = {0x02000000, 0x02000001, 0x02000002, 0x02000003}
WIDGET_TYPES = {0x07000000 + i for i in range(0x20)}


def parse(path: Path):
    data = path.read_bytes()
    info = {"size": len(data), "entries": []}
    if len(data) < TABLE + ENTRY:
        raise SystemExit(f"✗ file quá nhỏ: {len(data)} byte")
    if data[:4] != MAGIC:
        raise SystemExit(f"✗ magic sai: {data[:4].hex()} (cần {MAGIC.hex()})")

    info["header_size"] = struct.unpack_from("<I", data, 0x10)[0]
    info["id"] = data[0x28:0x68].split(b"\0")[0].decode("ascii", "replace")
    info["name"] = data[0x68:0xA8].split(b"\0")[0].decode("utf-8", "replace")

    off = TABLE
    while off + ENTRY <= min(info["header_size"], len(data)):
        wtype, _flags, roff, rsize = struct.unpack_from("<IIII", data, off)
        if rsize == 0 or roff + rsize > len(data):
            break
        info["entries"].append((wtype, roff, rsize))
        off += ENTRY
    return data, info


def check(path: Path, expected_name: str | None) -> list[str]:
    data, info = parse(path)
    errors = []

    if info["header_size"] < TABLE or info["header_size"] > len(data):
        errors.append(f"header_size vô lý: {info['header_size']}")
    if not info["entries"]:
        errors.append("bảng resource rỗng")
    if expected_name and info["name"] != expected_name:
        errors.append(f"tên mặt sai: {info['name']!r} (cần {expected_name!r})")

    images = [(t, o, s) for t, o, s in info["entries"] if t in IMG_TYPES]
    if not images:
        errors.append("không có entry ảnh 0x020000xx")

    bg = [e for e in images if e[0] == 0x02000000]
    if not bg:
        errors.append("thiếu ảnh nền (type 0x02000000)")
    else:
        off = bg[0][1]
        if data[off] != 0x28:
            errors.append(f"header ảnh nền sai: 0x{data[off]:02X} (cần 0x28)")
        w, h = struct.unpack_from("<HH", data, off + 4)
        if (w, h) != (320, 385):
            errors.append(f"ảnh nền {w}x{h}, cần 320x385")

    if not any(t in WIDGET_TYPES for t, _, _ in info["entries"]):
        errors.append("không có widget 0x07xxxxxx")

    types = [t for t, _, _ in info["entries"]]
    if len(types) != len(set(types)):
        dup = {t for t in types if types.count(t) > 1}
        errors.append(f"type trùng trong bảng: {[hex(t) for t in dup]}")

    return errors, info


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?", default="build/bin/steampunk-rw5a.bin")
    parser.add_argument("--name", default=None)
    args = parser.parse_args(argv)

    path = Path(args.binary)
    if not path.exists():
        print(f"✗ không thấy {path}")
        return 1

    errors, info = check(path, args.name)
    if errors:
        for e in errors:
            print(f"✗ {e}")
        return 1

    widgets = sum(1 for t, _, _ in info["entries"] if t in WIDGET_TYPES)
    images = sum(1 for t, _, _ in info["entries"] if t in IMG_TYPES)
    print(f"✓ {path.name}: {info['size']} byte, id={info['id']}, "
          f"tên={info['name']!r}, {len(info['entries'])} resource "
          f"({images} ảnh, {widgets} widget)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
