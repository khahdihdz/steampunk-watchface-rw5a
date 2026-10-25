#!/usr/bin/env python3
"""
build.py — render, validate and package a release of the Steampunk RW5A face.

Produces, under --out (default ./dist):

    steampunk-rw5a-<version>.zip   importable asset pack
    manifest.json                  layer table + per-file SHA-256
    SHA256SUMS.txt                 checksums for the release assets
    preview/*.png|gif              marketing renders

The archive is written with fixed timestamps so the same inputs always
produce byte-identical output (useful for reproducible-release checks).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import zipfile
from pathlib import Path

import generate
import steampunk as sp
import validate

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
PACK_NAME = "steampunk-rw5a"

INSTALL_NOTES = """\
STEAMPUNK LED RW5A — Mặt đồng hồ LED 7 đoạn cho Redmi Watch 5 Active
===================================================================

Nội dung gói
------------
photo/face.png          320x385, ảnh phẳng dùng cho tính năng "ảnh mặt đồng hồ"
photo/face_rounded.png  bản đã bo góc theo viền máy (alpha ngoài góc = 0)
photo/face_night.png    bản dịu sáng cho ban đêm
layers/*.png            7 layer rời, cùng hệ toạ độ 320x385
layout.json             khung LED, thông số 7 đoạn, nhãn phụ, thứ tự z

Cách 1 — nhanh nhất (không cần công cụ)
---------------------------------------
1. Copy photo/face.png sang điện thoại.
2. Mi Fitness > Thiết bị > Mặt đồng hồ > Ảnh > chọn ảnh vừa copy.
3. Kéo/phóng để ảnh phủ kín màn hình, lưu.

Cách 2 — mặt đồng hồ động
--------------------------
Dùng layers/ + layout.json trong Mi Watch Face Editor.  Layer 03_readout là
giờ:phút + giây đã nung sẵn; khi dựng bản động hãy thay nó bằng widget 7 đoạn
của công cụ (xem docs/mi-watch-face-editor.md).

Nhãn giao diện: PIN · BƯỚC CHÂN · NHỊP TIM · GIÂY · thứ/ngày dạng CHỦ NHẬT.

Giấy phép: MIT.  Thiết kế gốc, không dùng asset của bên thứ ba.
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_zip(files: list[tuple[Path, str]], target: Path) -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path, arcname in files:
            info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=os.environ.get("VERSION", "0.0.0"))
    parser.add_argument("--out", default="dist")
    parser.add_argument("--time", default="10:09:36")
    parser.add_argument("--no-gif", action="store_true")
    args = parser.parse_args(argv)

    out = Path(args.out)
    version = args.version.lstrip("v")

    generate.main(["--out", str(out), "--time", args.time]
                  + (["--no-gif"] if args.no_gif else []))

    code = validate.main(["--dist", str(out)]
                         + (["--skip-preview"] if args.no_gif else []))
    if code != 0:
        print("build: validate thất bại, dừng lại", file=sys.stderr)
        return code

    payload: list[tuple[Path, str]] = []
    for rel in ("photo", "layers"):
        for path in sorted((out / rel).glob("*.png")):
            payload.append((path, f"{rel}/{path.name}"))
    payload.append((out / "layout.json", "layout.json"))

    notes = out / "INSTALL.txt"
    notes.write_text(INSTALL_NOTES, encoding="utf-8")
    payload.append((notes, "INSTALL.txt"))

    license_file = sp.ROOT / "LICENSE"
    if license_file.exists():
        payload.append((license_file, "LICENSE"))

    stamp = int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))
    manifest = {
        "name": PACK_NAME,
        "version": version,
        "device": sp.LAYOUT["device"],
        "canvas": sp.LAYOUT["canvas"],
        "led_panel": sp.LAYOUT["led_panel"],
        "seconds": sp.LAYOUT["seconds"],
        "corner_radius": sp.CORNER_RADIUS,
        "layers": sp.LAYOUT["layers"],
        "files": [
            {"path": arcname, "sha256": sha256(path), "bytes": path.stat().st_size}
            for path, arcname in payload
        ],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stamp)),
        "reproducible": True,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    archive = out / f"{PACK_NAME}-{version}.zip"
    write_zip(payload, archive)
    print(f"đã đóng gói {archive} ({archive.stat().st_size / 1024:.1f} KiB, "
          f"{len(payload)} tệp)")

    sums = [archive, out / "manifest.json"]
    sums += [p for p in (out / "preview").glob("*") if p.is_file()]
    lines = [f"{sha256(p)}  {p.relative_to(out).as_posix()}" for p in sums]
    (out / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
