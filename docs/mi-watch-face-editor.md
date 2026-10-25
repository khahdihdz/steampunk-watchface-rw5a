# Dựng mặt đồng hồ động trong Mi Watch Face Editor

> Tài liệu này mô tả quy trình thủ công (không tự động hoá được) để biến 9 layer
> trong `layers/` thành một mặt đồng hồ có kim chạy trên Redmi Watch 5 Active.
> Xiaomi không phát hành SDK/CLI cho định dạng mặt đồng hồ HyperOS, nên **không
> có bước nào trong tài liệu này chạy được trên GitHub Actions**.

## 0. Chuẩn bị

- Tải gói release mới nhất, giải nén.
- Cài Mi Watch Face Editor (bản PC) và đăng nhập tài khoản Xiaomi **đã liên kết
  thiết bị** — công cụ này yêu cầu xác thực, không dùng được offline.
- Giữ nguyên kích thước canvas **320 × 385**, không resize layer.

## 1. Tạo project

1. New project → chọn độ phân giải tuỳ chỉnh **320 × 385**.
2. Đặt nền (background) trong suốt; độ sâu màu RGBA.
3. Đặt chế độ hiển thị mặc định là "digital-free" (chỉ kim), không bật widget
   thời gian mặc định — thời gian đã nằm trên mâm số.

## 2. Import layer theo đúng thứ tự

| Bước | Tệp | Loại | Thiết lập |
|---|---|---|---|
| 1 | `00_backplate.png` | Image (static) | z = 0 |
| 2 | `01_nameplate.png` | Image (static) | z = 1 |
| 3 | `02_dial.png` | Image (static) | z = 2 |
| 4 | `03_complications.png` | Image (static) | z = 3 |
| 5 | `10_hand_hour.png` | Image (rotate) | z = 10, pivot (160,160), 12h/vòng |
| 6 | `11_hand_minute.png` | Image (rotate) | z = 11, pivot (160,160), 60m/vòng |
| 7 | `12_hand_second.png` | Image (rotate) | z = 12, pivot (160,160), 60s/vòng |
| 8 | `13_cap.png` | Image (static) | z = 13 |
| 9 | `20_glass.png` | Image (static) | z = 20, **bỏ khi AOD/low-power** |

Mẹo: nếu công cụ không cho nhập pivot theo pixel, chọn tâm xoay theo tỉ lệ
**50,0 % / 41,56 %** (160/320 và 160/385).

## 3. Thay layer tĩnh bằng dữ liệu thật (tuỳ chọn)

`03_complications.png` chỉ là ảnh mẫu (25 / 78% / 6.4k). Muốn số liệu sống:

1. Ẩn layer này, hoặc cắt 3 vùng tròn Φ54 ở toạ độ
   `(78,312)`, `(160,312)`, `(242,312)`.
2. Thêm 3 widget:
   - **Date** tại `(78,312)`, cỡ chữ 22, font serif, màu `#EADCBB`.
   - **Battery** tại `(160,312)`, kiểu vòng cung 140°→400°, màu `#F6D894`.
   - **Steps** tại `(242,312)`, cỡ chữ 16, màu `#EADCBB`.
3. Giữ nguyên nền tròn tối `#120C08` phía sau để chữ không chồng lên vành đồng.

## 4. Chế độ AOD / tiết kiệm pin

- Chỉ giữ `02_dial`, `03_complications` (bản mờ), 3 kim.
- Bỏ `00_backplate`, `01_nameplate`, `20_glass`.
- Dùng `photo/face_night.png` nếu công cụ chỉ cho phép một ảnh nền cho AOD.

## 5. Xuất và cài

1. Export → gói `.bin`/`.face` theo định dạng công cụ yêu cầu.
2. Ký bằng tài khoản Xiaomi (bước này bắt buộc, không chia sẻ được).
3. Cài qua Mi Fitness hoặc chế độ nhà phát triển của công cụ.

## 6. Những điều KHÔNG làm được

| Việc | Lý do |
|---|---|
| Build APK | HyperOS không dùng Watch Face Format / Wear OS |
| Đóng gói tự động bằng CI | Định dạng đích không có spec công khai, cần tool + tài khoản |
| Phân phối lên store | Cần tài khoản nhà phát triển Xiaomi và quy trình duyệt riêng |
| Đảm bảo tương thích firmware khác | Layout có thể lệch nếu Xiaomi đổi vùng hiển thị |

Nếu bạn chỉ cần "một mặt steampunk đẹp ngay hôm nay", hãy dùng
`photo/face.png` với tính năng ảnh mặt đồng hồ — 30 giây, không cần công cụ.
