# Steampunk LED RW5A

Mặt đồng hồ **steampunk LED 7 đoạn**, giao diện tiếng Việt, cho **Redmi Watch 5
Active** (320 × 385, bo góc theo viền máy). Sinh 100% bằng code, phát hành tự
động qua GitHub Actions.

[![CI](https://github.com/khahdihdz/steampunk-watchface-rw5a/actions/workflows/ci.yml/badge.svg)](https://github.com/khahdihdz/steampunk-watchface-rw5a/actions/workflows/ci.yml)
[![Release](https://github.com/khahdihdz/steampunk-watchface-rw5a/actions/workflows/release.yml/badge.svg)](https://github.com/khahdihdz/steampunk-watchface-rw5a/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-c8963e.svg)](LICENSE)

![Preview](docs/preview.png)

![Giây chạy](docs/rotation.gif)

## Đọc trước: giới hạn của thiết bị

Redmi Watch 5 Active chạy **HyperOS**, **không phải Wear OS** và **không có SDK
mặt đồng hồ công khai**. Vì vậy repo này **không** tạo APK và **không** cài được
bằng ADB. Thứ được phát hành là bộ asset thật, dùng được theo hai cách:

| Cách | Cần gì | Kết quả |
|---|---|---|
| **Ảnh mặt đồng hồ** | Mi Fitness trên điện thoại | Mặt tĩnh, dùng được ngay trong 2 phút |
| **Layer + layout.json** | Mi Watch Face Editor | Mặt động, số nhảy theo thời gian thực |

Phần "deploy GitHub + release build bằng Actions" là **thật** — chỉ có điều
artefact là gói thiết kế đã render, không phải APK.

## Thiết kế

- **LED 7 đoạn** vẽ bằng polygon: 4 chữ số giờ:phút cao 78 px, màu hổ phách
  `#FFB340`, có quầng sáng 3 lớp và "hot core" sáng hơn ở giữa segment.
- **Segment chưa sáng** (ghost) vẫn hiện mờ — đúng cảm giác LED thật.
- Khung đồng thau, đinh tán, bánh răng, vết verdigris, vignette.
- Giao diện **tiếng Việt**: `GIÂY`, `PIN`, `BƯỚC CHÂN`, `NHỊP TIM`,
  dải ngày dạng `CHỦ NHẬT · 25/10/2026`.
- Bo góc 46 px, mọi nội dung nằm trong vùng an toàn.

## Nội dung gói release

```
photo/face.png          320x385 RGB — dùng cho tính năng ảnh mặt đồng hồ
photo/face_rounded.png  bản đã bo góc 46px (alpha ngoài góc = 0)
photo/face_night.png    bản dịu sáng cho ban đêm
layers/00_backplate.png      nền gang + bánh răng mờ
layers/01_nameplate.png      bảng tên AETHER
layers/02_led_panel.png      khung LED + segment chưa sáng
layers/03_readout.png        giờ:phút + giây (thay bằng widget khi dựng động)
layers/04_date_strip.png     dải thứ/ngày tiếng Việt
layers/05_complications.png  3 cửa sổ PIN / BƯỚC CHÂN / NHỊP TIM
layers/20_glass.png          phản sáng
layout.json             khung, thông số 7 đoạn, nhãn, thứ tự z
```

## Dùng ngay (mặt tĩnh)

1. Tải `steampunk-rw5a-<version>.zip` ở trang [Releases](../../releases),
   giải nén, copy `photo/face.png` sang điện thoại.
2. **Mi Fitness** → **Thiết bị** → **Mặt đồng hồ** → **Ảnh** → chọn ảnh.
3. Phóng to để ảnh phủ kín màn hình rồi lưu.

## Dựng bản động

Xem [docs/mi-watch-face-editor.md](docs/mi-watch-face-editor.md). Tóm tắt: import
7 layer, thay `03_readout` bằng widget 7 đoạn của công cụ, giữ nguyên khung LED.

## Cấu trúc repo

```
assets/layout.json         nguồn sự thật: khung, thông số 7 đoạn, nhãn, layer
assets/palette.json        bảng màu
scripts/steampunk.py       renderer: Canvas 3x, gradient, gear, LED 7 đoạn
scripts/generate.py        render ảnh phẳng, layer, mock-up, GIF
scripts/validate.py        57 kiểm tra ràng buộc thiết bị/thiết kế
scripts/build.py           đóng gói zip tái lập + manifest + SHA256SUMS
docs/design-spec.md        đặc tả thiết kế chi tiết
PROMPT.md                  prompt đầy đủ để tái tạo dự án bằng AI
```

## Build tại máy

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install fonts-noto-core fonts-dejavu-core

make package VERSION=2.0.0
```

Kết quả trong `dist/`:

```
dist/steampunk-rw5a-2.0.0.zip
dist/manifest.json
dist/SHA256SUMS.txt
dist/preview/preview.png
dist/preview/rotation.gif
```

Xem trước nhanh:

```bash
make preview      # dist/preview/preview.png
make check        # render + 57 kiểm tra
```

## Phát hành

```bash
git tag v2.0.0 && git push origin v2.0.0
```

`release.yml` build, xác minh checksum rồi tạo GitHub Release kèm zip, manifest,
preview. Có thể chạy tay qua **Actions → Release → Run workflow**.

Build **tái lập được**: `SOURCE_DATE_EPOCH` lấy từ ngày commit, zip ghi
timestamp cố định, nên hai lần build trên cùng runner cho ra file giống nhau
từng byte — CI kiểm tra điều này ở mỗi lần push.

## Phụ thuộc

- Python ≥ 3.10, Pillow ≥ 10.4
- Font: Noto Serif Bold / DejaVu (ghi đè bằng `WATCHFACE_FONT_SERIF`,
  `WATCHFACE_FONT_MONO`)

## Giấy phép

MIT — xem [LICENSE](LICENSE). Thiết kế gốc, không dùng asset bên thứ ba.
