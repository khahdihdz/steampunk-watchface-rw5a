# Steampunk Skeleton LED RW5A

Mặt đồng hồ **steampunk lộ cơ** — nhìn thấy bộ máy bánh răng bên trong qua kính
khói — dùng **LED 7 đoạn** và **giao diện tiếng Việt**, cho **Redmi Watch 5
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
bằng ADB. Thứ được phát hành là bộ asset thật, dùng được theo ba cách:

| Cách | Cần gì | Kết quả |
|---|---|---|
| **Ảnh mặt đồng hồ** | Mi Fitness trên điện thoại | Mặt tĩnh, dùng được ngay trong 2 phút |
| **Layer + layout.json** | Mi Watch Face Editor | Mặt động, số nhảy theo thời gian thực |
| **`.bin`** (thử nghiệm) | Mi Fitness mod / app bên thứ ba | Mặt động cài thẳng lên đồng hồ — xem [docs/watchface-bin.md](docs/watchface-bin.md) |

Phần "deploy GitHub + release build bằng Actions" là **thật** — release có cả
gói thiết kế lẫn file `.bin` do `compile.exe` của Mi-Create biên dịch trên
runner Windows.

## Thiết kế

**Lộ cơ (skeleton).** Bộ máy nằm ở layer riêng, phía sau kính khói:

- cầu (bridge) vát cạnh có vân xước, ốc thép xanh, chân kính ruby;
- bánh răng nhiều cỡ ăn khớp nhau, thùng dây cót có lò xo xoắn nhìn thấy được;
- bánh lắc (balance wheel) có tóc xoắn và 4 ốc vành.

Các bảng nội dung là **kính tối đục 87–94%** nên bộ máy vẫn hiện mờ phía sau,
còn số và nhãn thì rõ. Riêng `photo/face_alpha.png` là bản **nền trong suốt
thật** ở khe giữa các bảng.

**LED 7 đoạn vẽ bằng polygon:** 4 chữ số giờ:phút cao 78 px, hổ phách `#FFB340`,
quầng sáng 3 lớp + ruột sáng; giây `#FF5B3A`. Segment chưa sáng vẫn hiện mờ —
đúng cảm giác LED thật.

**Giao diện tiếng Việt:** `GIÂY`, `PIN`, `BƯỚC CHÂN`, `NHỊP TIM`, dải ngày
`CHỦ NHẬT · 25/10/2026`. Bo góc 46 px, nội dung nằm trong vùng an toàn.

## Nội dung gói release

```
photo/face.png          320x385 RGB — dùng cho tính năng ảnh mặt đồng hồ
photo/face_rounded.png  bản đã bo góc 46px (alpha ngoài góc = 0)
photo/face_night.png    bản dịu sáng cho ban đêm
photo/face_alpha.png    RGBA — nền trong suốt ở khe giữa các bảng
layers/00_backdrop.png      đáy vỏ: gang tối, đinh tán, vignette
layers/01_movement.png      bộ máy: cầu, bánh răng, thùng dây cót, bánh lắc
layers/02_crystal.png       kính khói + khúc xạ mép kính
layers/03_nameplate.png     bảng tên AETHER
layers/04_led_panel.png     khung LED + segment chưa sáng
layers/05_readout.png       giờ:phút + giây (thay bằng widget khi dựng động)
layers/06_date_strip.png    dải thứ/ngày tiếng Việt
layers/07_complications.png 3 cửa sổ PIN / BƯỚC CHÂN / NHỊP TIM
layers/20_glass.png         phản sáng
layout.json             khung, thông số 7 đoạn, nhãn, thứ tự z
```

Release còn có `steampunk-rw5a.bin` (mặt động, biên dịch bằng `compile.exe`) và
`steampunk-rw5a.bin.sha256` — xem [docs/watchface-bin.md](docs/watchface-bin.md).

## Dùng ngay (mặt tĩnh)

1. Tải `steampunk-rw5a-<version>.zip` ở trang [Releases](../../releases),
   giải nén, copy `photo/face.png` sang điện thoại.
2. **Mi Fitness** → **Thiết bị** → **Mặt đồng hồ** → **Ảnh** → chọn ảnh.
3. Phóng to để ảnh phủ kín màn hình rồi lưu.

## Dựng bản động

Xem [docs/mi-watch-face-editor.md](docs/mi-watch-face-editor.md). Tóm tắt: import
9 layer, thay `05_readout` bằng widget 7 đoạn của công cụ, giữ nguyên khung LED.
Muốn nền trong suốt hoàn toàn thì bỏ `00_backdrop` và dùng
`photo/face_alpha.png`.

## Bản `.bin` (thử nghiệm)

Release kèm `steampunk-rw5a.bin` — mặt đồng hồ **biên dịch thật**, không phải
gói asset. Nền do repo render (đã bỏ hết số), còn giờ, giây, ngày, thứ, pin,
bước chân, nhịp tim do firmware vẽ bằng 13 widget.

```bash
python scripts/binface.py --out build/fprj   # sinh project EasyFace
python scripts/validate_fprj.py build/fprj   # kiểm tra schema + ảnh
# compile.exe (Mi-Create, GPL-3.0) chạy trên Windows, xem docs/watchface-bin.md
python scripts/check_bin.py steampunk-rw5a.bin --name "AETHER Steampunk"
```

**Chưa kiểm thử trên đồng hồ thật.** File đúng cấu trúc container và qua đúng
bộ nén của RW5A, nhưng chưa ai xác nhận hiển thị. Đọc
[docs/watchface-bin.md](docs/watchface-bin.md) trước khi cài — có mục rủi ro,
cách quay về mặt mặc định, và bảng lỗi compiler đã gặp.

## Cấu trúc repo

```
assets/layout.json         nguồn sự thật: khung, thông số 7 đoạn, nhãn, layer
assets/palette.json        bảng màu (đồng, thép xanh, ruby, LED)
scripts/steampunk.py       renderer: Canvas 3x, gradient, bộ máy, LED 7 đoạn
scripts/generate.py        render ảnh phẳng, layer, mock-up, GIF
scripts/validate.py        74 kiểm tra ràng buộc thiết bị/thiết kế
scripts/binface.py         sinh project EasyFace (.fprj + images) cho compile.exe
scripts/validate_fprj.py   kiểm tra project trước khi biên dịch
scripts/check_bin.py       kiểm tra container .bin sau khi biên dịch
scripts/build.py           đóng gói zip tái lập + manifest + SHA256SUMS
docs/design-spec.md        đặc tả thiết kế chi tiết
docs/watchface-bin.md      pipeline .bin, ràng buộc compiler, rủi ro khi cài
PROMPT.md                  prompt đầy đủ để tái tạo dự án bằng AI
```

## Build tại máy

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install fonts-noto-core fonts-dejavu-core

make package VERSION=3.1.0
```

Kết quả trong `dist/`:

```
dist/steampunk-rw5a-3.1.0.zip
dist/manifest.json
dist/SHA256SUMS.txt
dist/preview/preview.png
dist/preview/rotation.gif
```

Xem trước nhanh:

```bash
make preview      # dist/preview/preview.png
make check        # render + 74 kiểm tra
```

## Phát hành

```bash
git tag v3.1.0 && git push origin v3.1.0
```

`release.yml` build, xác minh checksum rồi tạo GitHub Release kèm zip, manifest,
preview **và** `steampunk-rw5a.bin` (gọi workflow `bin.yml` để biên dịch trên
Windows). Có thể chạy tay qua **Actions → Release → Run workflow**.

Build **tái lập được**: `SOURCE_DATE_EPOCH` lấy từ ngày commit, zip ghi
timestamp cố định, nên hai lần build trên cùng runner cho ra file giống nhau
từng byte — CI kiểm tra điều này ở mỗi lần push.

## Phụ thuộc

- Python ≥ 3.10, Pillow ≥ 10.4
- Font: Noto Serif Bold / DejaVu (ghi đè bằng `WATCHFACE_FONT_SERIF`,
  `WATCHFACE_FONT_MONO`)

## Giấy phép

MIT — xem [LICENSE](LICENSE). Thiết kế gốc, không dùng asset bên thứ ba.
