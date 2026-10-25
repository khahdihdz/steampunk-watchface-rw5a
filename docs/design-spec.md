# Đặc tả thiết kế — Steampunk Skeleton LED RW5A (v3)

## 1. Ràng buộc phần cứng

| Thông số | Giá trị | Hệ quả thiết kế |
|---|---|---|
| Màn hình | LCD 2.0", 320 × 385 px, 251 ppi | Vẽ 1:1, không scale |
| Bo góc | bán kính ≈ 46 px | Nội dung phải nằm trong vùng an toàn |
| Tấm nền | LCD | Chữ nhỏ < 1 px sẽ nhoè, segment phải ≥ 2 px |
| Hệ điều hành | HyperOS (RTOS) | Không có Watch Face Format, không có APK |

## 2. Bố cục

```
 y=0    ┌──────────────────────────┐  bo góc 46
        │ ⚙   [ AETHER ]      ⚙   │  bảng tên 18–54
 64     │  ╭────────────────────╮  │
        │  │  10:09       36    │  │  khung LED 64–182
        │  │      (GIÂY)        │  │
 182    │  ╰────────────────────╯  │
 192    │   CHỦ NHẬT · 25/10/2026  │  dải ngày 64–256
 236    │  ┌────────────────────┐  │
        │  │[78%] [6428] [72]   │  │  3 cửa sổ 78×40, tâm y=290
 356    │  └────────────────────┘  │  nhãn PIN / BƯỚC CHÂN / NHỊP TIM
        │ ⚙      bánh lắc      ⚙  │  dải máy lộ 356–385
        └──────────────────────────┘
```

Hai bên trái/phải của các bảng (x < 26 và x > 294) là **bộ máy lộ**. Toạ độ lấy
từ `assets/layout.json`; script không hard-code khung.

## 3. Bảng màu

| Token | Hex | Dùng cho |
|---|---|---|
| `ink` | `#120c08` | nền sâu, viền khung |
| `iron` / `iron_hi` | `#1c1512` / `#33261d` | nền gang |
| `brass_dark` | `#6b4519` | bóng đồng, cầu |
| `brass` | `#c8963e` | bánh răng, khung |
| `brass_hi` | `#f6d894` | highlight, chữ khắc |
| `copper` / `copper_dark` | `#a9603a` / `#5d3220` | điểm nhấn |
| `steel` | `#9aa6ad` | tóc xoắn, lò xo dây cót |
| `blued` | `#2c3f5c` | ốc thép xanh |
| `ruby` | `#c02b4a` | chân kính |
| `sapphire` | `#3a5460` | ánh kính khói |
| `patina` | `#2f6f66` | verdigris |
| `parchment` | `#eadcbb` | chữ serif |
| LED chính | `#ffb340` | giờ:phút, PIN, BƯỚC CHÂN, NHỊP TIM |
| LED giây | `#ff5b3a` | hai chữ số giây |
| LED tắt | `#1b100e` | segment không sáng |

## 4. Bộ máy lộ (layer `01_movement`)

Vẽ trên nền trong suốt, theo thứ tự: **cầu → bánh răng → chân kính/ốc**.

| Chi tiết | Cách dựng |
|---|---|
| Cầu (bridge) | polyline dày có bo đầu; đổ gradient đồng dọc, viền sáng lệch lên, bóng lệch xuống, vân xước cắt theo mask |
| Bánh răng | silhouette từ `gear_mask` + gradient radial, khoét lỗ nan hoa bằng `ImageChops.subtract`, hub và vành sáng |
| Thùng dây cót | vành răng + lò xo xoắn Archimedes (4 vòng) + bánh cót 8 rãnh |
| Bánh lắc | vành khuyên (subtract 2 hình tròn), 2 nan chữ thập, tóc xoắn 5,5 vòng, 4 ốc vành, chân kính giữa |
| Chân kính | 3 vòng đồng + ruby + chấm sáng |
| Ốc | thép xanh, rãnh vít, highlight |

Vị trí đặt sao cho phần thú vị rơi vào **dải nhìn thấy được**: hai bên sườn
(x < 26, x > 294), đáy (y > 356) và các góc.

## 5. Kính khói và độ xuyên thấu

| Lớp | Alpha | Hiệu quả |
|---|---|---|
| `00_backdrop` | 255 | đáy vỏ gang — chỉ dùng cho ảnh phẳng |
| `02_crystal` | ~8% phủ toàn mặt | ánh lạnh + khúc xạ mép kính |
| `04_led_panel` (kính trong) | 94% | số đọc rõ, bộ máy chỉ gợn mờ |
| `06_date_strip` (kính trong) | 91% | chữ ngày còn rõ |
| `07_complications` (nền bảng) | 89% | thấy máy mờ phía sau |
| `03_nameplate` (kính trong) | 97% | chữ khắc sắc nét |

Quy tắc: **càng nhiều chữ nhỏ càng đục**. Nếu hạ `04_led_panel` xuống dưới 0.90,
bánh răng sáng phía sau sẽ làm quầng LED mất tương phản.

## 6. Thông số 7 đoạn

| Tham số | Giờ:phút | Giây | Cửa sổ PIN/NHỊP TIM | Cửa sổ BƯỚC |
|---|---|---|---|---|
| `digit_w` | 36,0 | 16,0 | 16,0 | 13,5 |
| `digit_h` | 78,0 | 28,0 | 26,0 | 24,0 |
| `stroke` | 6,4 | 3,6 | 3,8 | 3,2 |
| `gap` | 1,8 | 1,1 | 1,8 | 1,6 |
| `spacing` | 9,0 | 3,0 | 3,0 | 2,4 |

Quy tắc hình học:

- Mỗi segment là hình lục giác, hai đầu vát 45°.
- `gap > ~0,3 × stroke` ⇒ segment rời rạc, đọc thành "viên thuốc".
- `stroke < digit_h / 5` để lỗ giữa số 0 còn thấy.
- Lớp "hot core" phải **mỏng hơn nhưng cùng đường tâm** (`t_center`) và **ngắn
  hơn** hai đầu (`inset`); nếu chỉ giảm `stroke` trong công thức cũ, ruột sáng
  bám mép segment và số trông rỗng.
- Ghost segment dùng sprite `88:88` màu `#1b100e`, canh **đúng vị trí** số thật.

## 7. Layer và thứ tự z

| ID | z | Động | Ghi chú |
|---|---|---|---|
| `00_backdrop` | 0 | – | đáy vỏ, rivet, vignette — bỏ nếu muốn nền trong suốt |
| `01_movement` | 1 | – | bộ máy lộ |
| `02_crystal` | 2 | – | kính khói |
| `03_nameplate` | 3 | – | bảng AETHER |
| `04_led_panel` | 4 | – | khung LED + ghost segment |
| `05_readout` | 5 | ✔ | giờ:phút + giây đã nung sẵn |
| `06_date_strip` | 6 | – | thứ/ngày tiếng Việt |
| `07_complications` | 7 | – | 3 cửa sổ giá trị |
| `20_glass` | 20 | – | phản sáng, bỏ khi AOD |

## 8. Ảnh phẳng

| Tệp | Mode | Ghi chú |
|---|---|---|
| `photo/face.png` | RGB | phủ kín màn hình, có đáy vỏ |
| `photo/face_rounded.png` | RGBA | bo góc 46, alpha ngoài góc = 0 |
| `photo/face_night.png` | RGB | giảm 40% sáng, 75% bão hoà |
| `photo/face_alpha.png` | RGBA | **không có `00_backdrop`**: khe giữa các bảng trong suốt thật, các bảng đục 100% để đọc |

## 9. Kỹ thuật render

- **Supersampling 3×** rồi LANCZOS về 320 × 385.
- **Glow LED 3 lớp**: blur 7 / 3,2 / 1,2 px với hệ số 0,30 / 0,55 / 0,70 × `glow`.
- **Đổ bóng** dùng alpha nhân chứ không vẽ màu — để lớp dưới còn xuyên qua.
- **Tái lập**: noise + `random.Random(seed)` cố định, zip timestamp `1980-01-01`,
  `SOURCE_DATE_EPOCH` từ ngày commit.

## 10. Lịch sử hướng thiết kế

| Phiên bản | Hướng |
|---|---|
| 1.0.0 | Mâm analog + kim Breguet |
| 2.0.0 | LED 7 đoạn, bỏ kim, Việt hoá nhãn |
| 3.0.0 | Lộ cơ: bộ máy thật phía sau kính khói + bản nền trong suốt |
