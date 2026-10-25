# Changelog

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
phiên bản theo [SemVer](https://semver.org/lang/vi/).

## [2.0.0] — 2026-10-25

### Thay đổi

- **Bỏ mâm analog + kim Breguet**, thay bằng **LED 7 đoạn** vẽ bằng polygon:
  giờ:phút cao 78 px màu hổ phách, giây màu đỏ cam.
- **Giao diện tiếng Việt có dấu**: `GIÂY`, `PIN`, `BƯỚC CHÂN`, `NHỊP TIM`,
  dải ngày `CHỦ NHẬT · 25/10/2026`.
- 3 cửa sổ phức hợp đổi từ hình tròn Φ54 sang ô chữ nhật 82 × 42 để số 4 chữ số
  (`6428`) đọc được.
- Layer: 9 → 7 (`03_readout` thay cho 3 layer kim + nắp).

### Sửa

- Ruột sáng ("hot core") bị lệch về mép segment do dùng chung công thức toạ độ
  với `stroke` nhỏ hơn — nay giữ nguyên đường tâm và inset hai đầu.
- Ghost segment canh giữa khung gây lệch so với số thật khi có khối giây.

### Thêm

- `tests` trong `validate.py`: kiểm tra bbox readout nằm trong khung LED, đếm
  pixel LED sáng, kiểm tra tỉ lệ `stroke/digit_h`, thứ tự z của layer.
- Render glow 3 lớp cho mọi số 7 đoạn.

## [1.0.0] — 2026-10-25

### Thêm

- Renderer procedural `scripts/steampunk.py`: Canvas supersampled 3×, gradient
  nhiều stop, bánh răng, rivet, patina, vignette, kim Breguet.
- 9 layer rời + 3 ảnh phẳng (ngày / bo góc / ban đêm) ở đúng 320 × 385.
- `scripts/validate.py`: 61 kiểm tra về kích thước, mode, tâm xoay, bo góc.
- `scripts/build.py`: đóng gói zip tái lập, `manifest.json`, `SHA256SUMS.txt`.
- Workflow `ci.yml` và `release.yml` (tag `v*` → GitHub Release).
- Tài liệu: đặc tả thiết kế, hướng dẫn Mi Watch Face Editor, prompt tái tạo.

[2.0.0]: https://github.com/khahdihdz/steampunk-watchface-rw5a/releases/tag/v2.0.0
[1.0.0]: https://github.com/khahdihdz/steampunk-watchface-rw5a/releases/tag/v1.0.0
