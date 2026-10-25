# Changelog

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
phiên bản theo [SemVer](https://semver.org/lang/vi/).

## [1.0.0] — 2026-10-25

### Thêm

- Renderer procedural `scripts/steampunk.py`: Canvas supersampled 3×, gradient
  nhiều stop, bánh răng, rivet, patina, vignette, kim Breguet.
- 9 layer rời + 3 ảnh phẳng (ngày / bo góc / ban đêm) ở đúng 320 × 385.
- `scripts/validate.py`: 61 kiểm tra về kích thước, mode, tâm xoay, bo góc,
  độ tương phản góc và tính nhất quán của `layout.json`.
- `scripts/build.py`: đóng gói zip tái lập, `manifest.json`, `SHA256SUMS.txt`.
- Workflow `ci.yml` (render + kiểm tra tái lập + artifact preview) và
  `release.yml` (tag `v*` → GitHub Release).
- Tài liệu: đặc tả thiết kế, hướng dẫn Mi Watch Face Editor, prompt tái tạo.

### Ghi chú

- Không phát hành APK: Redmi Watch 5 Active chạy HyperOS, không có SDK mặt
  đồng hồ công khai.

[1.0.0]: https://github.com/khahdihdz/steampunk-watchface-rw5a/releases/tag/v1.0.0
