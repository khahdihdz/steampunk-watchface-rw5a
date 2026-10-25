# Dựng mặt đồng hồ động trong Mi Watch Face Editor

> Tài liệu mô tả quy trình thủ công để biến 7 layer trong `layers/` thành mặt
> đồng hồ LED có số nhảy trên Redmi Watch 5 Active. Xiaomi không phát hành
> SDK/CLI cho định dạng HyperOS, nên **không bước nào ở đây chạy được trên
> GitHub Actions**.

## 0. Chuẩn bị

- Tải gói release mới nhất, giải nén.
- Cài Mi Watch Face Editor (bản PC) và đăng nhập tài khoản Xiaomi **đã liên kết
  thiết bị** — công cụ yêu cầu xác thực, không dùng offline được.
- Giữ nguyên canvas **320 × 385**, không resize layer.

## 1. Tạo project

1. New project → độ phân giải tuỳ chỉnh **320 × 385**.
2. Nền trong suốt, độ sâu màu RGBA.
3. Không bật widget thời gian mặc định — bố cục đã dành sẵn chỗ trong khung LED.

## 2. Import layer theo đúng thứ tự

| Bước | Tệp | Loại | Thiết lập |
|---|---|---|---|
| 1 | `00_backplate.png` | Image (static) | z = 0 |
| 2 | `01_nameplate.png` | Image (static) | z = 1 |
| 3 | `02_led_panel.png` | Image (static) | z = 2 |
| 4 | `03_readout.png` | **thay bằng widget** | z = 3, xem mục 3 |
| 5 | `04_date_strip.png` | Image (static) | z = 4 |
| 6 | `05_complications.png` | Image (static) | z = 5 |
| 7 | `20_glass.png` | Image (static) | z = 20, bỏ khi AOD |

## 3. Thay `03_readout` bằng số thật

`03_readout.png` là ảnh nung sẵn `10:09` + `36`. Muốn số nhảy theo giờ thực:

1. Ẩn (hoặc xoá) layer này.
2. Thêm widget **Time** tại khung chữ nhật `(40, 72)–(210, 150)`:
   - font 7 đoạn của công cụ, cỡ **78**, màu `#FFB340`;
   - định dạng **24 giờ**, hiển thị `HH:MM`.
3. Thêm widget **Seconds** tại `(216, 122)–(252, 150)`:
   - font 7 đoạn, cỡ **28**, màu `#FF5B3A`.
4. Nếu công cụ không có font 7 đoạn: dùng chế độ ảnh theo từng chữ số (digit
   strip 10 ảnh 0–9) và đặt đúng thông số trong `layout.json`
   (`digit_w`, `digit_h`, `stroke`, `gap`, `spacing`, `colon_w`, `slant`).

## 4. Thay 3 cửa sổ giá trị

`05_complications.png` chứa số mẫu (78 %, 6428, 72) và khung cửa sổ.

- Giữ khung: cắt 3 vùng `82 × 42` tại tâm `(70, 290)`, `(160, 290)`, `(250, 290)`.
- Thêm widget:
  | Cửa sổ | Widget | Cỡ | Màu |
  |---|---|---|---|
  | trái | Battery | 26 | `#FFB340` |
  | giữa | Steps | 24 | `#FFB340` |
  | phải | Heart rate | 26 | `#FFB340` |

Nhãn `PIN / BƯỚC CHÂN / NHỊP TIM` nằm sẵn trong layer, không cần tạo lại.

## 5. Chế độ AOD / tiết kiệm pin

- Giữ `02_led_panel` + widget giờ:phút (giảm độ sáng nếu công cụ cho phép).
- Bỏ `00_backplate`, `01_nameplate`, `20_glass`.
- Hoặc dùng `photo/face_night.png` nếu chỉ được phép một ảnh nền cho AOD.

## 6. Xuất và cài

1. Export → gói `.bin`/`.face` theo định dạng công cụ yêu cầu.
2. Ký bằng tài khoản Xiaomi (bắt buộc, không chia sẻ được).
3. Cài qua Mi Fitness hoặc chế độ nhà phát triển của công cụ.

## 7. Những điều KHÔNG làm được

| Việc | Lý do |
|---|---|
| Build APK | HyperOS không dùng Watch Face Format / Wear OS |
| Đóng gói tự động bằng CI | Định dạng đích không có spec công khai, cần tool + tài khoản |
| Phân phối lên store | Cần tài khoản nhà phát triển Xiaomi và quy trình duyệt riêng |
| Đảm bảo tương thích firmware khác | Layout có thể lệch nếu Xiaomi đổi vùng hiển thị |

Nếu chỉ cần "một mặt LED đẹp ngay hôm nay", dùng `photo/face.png` với tính năng
ảnh mặt đồng hồ — 30 giây, không cần công cụ.
