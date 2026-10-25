# Changelog

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
phiên bản theo [SemVer](https://semver.org/lang/vi/).

## [3.0.0] — 2026-10-25

### Thay đổi

- **Lộ cơ (skeleton)**: thêm layer `01_movement` vẽ bộ máy thật — cầu vát cạnh,
  bánh răng nhiều cỡ, thùng dây cót có lò xo xoắn, bánh lắc có tóc xoắn, chân
  kính ruby, ốc thép xanh.
- Thêm `02_crystal` (kính khói) và `00_backdrop`; layer tăng 7 → 9.
- Các bảng nội dung đổi sang **kính tối đục 87–94%** để thấy máy mờ phía sau.
- Bỏ hai bánh răng phẳng trang trí trên bảng tên (đã có bộ máy thật).
- Dải ngày thu hẹp `64–256`, bảng phức hợp `26–294`, cửa sổ `78 × 40` — nhường
  chỗ cho bộ máy ở hai sườn.
- Ảnh mới `photo/face_alpha.png`: nền trong suốt ở khe giữa các bảng, các bảng
  đục 100% để đọc.

### Sửa

- Cầu bị "đen" vì lớp highlight/shadow phủ gần hết bề rộng — nay thu về 24–26%
  bề rộng, cắt theo mask để không lem ra ngoài.
- Mock-up: mặt đồng hồ phủ kín lòng vỏ thay vì nằm lơ lửng như khung ảnh.

### Thêm

- `validate.py`: 74 kiểm tra (bộ máy phủ hai mép, mật độ chi tiết đồng, alpha
  của bản trong suốt, vùng số phải đục).

## [2.0.0] — 2026-10-25

### Thay đổi

- **Bỏ mâm analog + kim Breguet**, thay bằng **LED 7 đoạn** vẽ bằng polygon:
  giờ:phút cao 78 px màu hổ phách, giây màu đỏ cam.
- **Giao diện tiếng Việt có dấu**: `GIÂY`, `PIN`, `BƯỚC CHÂN`, `NHỊP TIM`,
  dải ngày `CHỦ NHẬT · 25/10/2026`.
- 3 cửa sổ phức hợp đổi từ hình tròn Φ54 sang ô chữ nhật để số 4 chữ số đọc được.

### Sửa

- Ruột sáng ("hot core") bị lệch về mép segment do dùng chung công thức toạ độ
  với `stroke` nhỏ hơn — nay giữ nguyên đường tâm và inset hai đầu.
- Ghost segment canh giữa khung gây lệch so với số thật khi có khối giây.

## [1.0.0] — 2026-10-25

### Thêm

- Renderer procedural `scripts/steampunk.py`: Canvas supersampled 3×, gradient
  nhiều stop, bánh răng, rivet, patina, vignette, kim Breguet.
- 9 layer rời + 3 ảnh phẳng (ngày / bo góc / ban đêm) ở đúng 320 × 385.
- `scripts/validate.py`: 61 kiểm tra về kích thước, mode, tâm xoay, bo góc.
- `scripts/build.py`: đóng gói zip tái lập, `manifest.json`, `SHA256SUMS.txt`.
- Workflow `ci.yml` và `release.yml` (tag `v*` → GitHub Release).
- Tài liệu: đặc tả thiết kế, hướng dẫn Mi Watch Face Editor, prompt tái tạo.

[3.0.0]: https://github.com/khahdihdz/steampunk-watchface-rw5a/releases/tag/v3.0.0
[2.0.0]: https://github.com/khahdihdz/steampunk-watchface-rw5a/releases/tag/v2.0.0
[1.0.0]: https://github.com/khahdihdz/steampunk-watchface-rw5a/releases/tag/v1.0.0
