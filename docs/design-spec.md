# Đặc tả thiết kế — Steampunk LED RW5A (v2)

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
 18     │   ⚙  [ AETHER ]  ⚙      │  bảng tên 18–54
 64     │  ╭────────────────────╮  │
        │  │  10:09       36    │  │  khung LED 64–182
        │  │      (GIÂY)        │  │
 182    │  ╰────────────────────╯  │
 192    │    CHỦ NHẬT · 25/10/2026  │  dải ngày 192–226
 236    │  ┌────────────────────┐  │
        │  │ [78%] [6428] [72]  │  │  3 cửa sổ 82×42, tâm y=290
 356    │  └────────────────────┘  │  nhãn PIN / BƯỚC CHÂN / NHỊP TIM
        └──────────────────────────┘
```

Toạ độ lấy từ `assets/layout.json`; script không hard-code khung.

## 3. Bảng màu

| Token | Hex | Dùng cho |
|---|---|---|
| `ink` | `#120c08` | nền sâu, viền khung |
| `iron` / `iron_hi` | `#1c1512` / `#33261d` | nền gang |
| `brass_dark` | `#6b4519` | bóng đồng |
| `brass` | `#c8963e` | khung, vành |
| `brass_hi` | `#f6d894` | highlight, chữ khắc |
| `copper` | `#a9603a` | điểm nhấn |
| `patina` | `#2f6f66` | verdigris |
| `parchment` | `#eadcbb` | chữ serif |
| LED chính | `#ffb340` | giờ:phút, PIN, BƯỚC CHÂN, NHỊP TIM |
| LED giây | `#ff5b3a` | hai chữ số giây (màu nóng duy nhất) |
| LED tắt | `#1b100e` | segment không sáng |

Tương phản `#ffb340` trên nền `#0b0908` ≈ 9,5:1.

## 4. Thông số 7 đoạn

| Tham số | Giờ:phút | Giây |
|---|---|---|
| `digit_w` | 36,0 | 16,0 |
| `digit_h` | 78,0 | 28,0 |
| `stroke` | 6,4 | 3,6 |
| `gap` | 1,8 | 1,1 |
| `spacing` | 9,0 | 3,0 |
| `colon_w` | 14,0 | 8,0 |
| `slant` | 0,06 | 0,06 |

Quy tắc hình học:

- Mỗi segment là hình lục giác có hai đầu vát 45°.
- `gap` là khoảng hở giữa hai segment kề nhau. `gap > ~0,3 × stroke` sẽ làm
  các segment rời rạc, đọc thành "viên thuốc" chứ không thành số.
- Bản "hot core" được vẽ **mỏng hơn nhưng cùng đường tâm** (`t_center`), và
  ngắn hơn `inset = (stroke − stroke_hot) / 2`. Nếu chỉ giảm `stroke` mà giữ
  công thức toạ độ cũ, ruột sáng sẽ bám mép segment và số trông rỗng.
- `stroke < digit_h / 5` để lỗ giữa số 0 còn nhìn thấy.

## 5. Layer và thứ tự z

| ID | z | Động | Ghi chú |
|---|---|---|---|
| `00_backplate` | 0 | – | gang, bánh răng mờ, rivet, vignette |
| `01_nameplate` | 1 | – | bảng AETHER + 2 bánh răng |
| `02_led_panel` | 2 | – | khung LED + segment chưa sáng (ghost) |
| `03_readout` | 3 | ✔ | giờ:phút + giây đã nung sẵn |
| `04_date_strip` | 4 | – | thứ/ngày tiếng Việt |
| `05_complications` | 5 | – | 3 cửa sổ giá trị |
| `20_glass` | 20 | – | phản sáng, bỏ khi chế độ tối |

`03_readout` là layer duy nhất phải thay bằng widget khi dựng bản động.

## 6. Kỹ thuật render

- **Supersampling 3×** rồi LANCZOS về 320 × 385 → cạnh segment sắc, không răng cưa.
- **Glow 3 lớp**: blur 7 / 3,2 / 1,2 px với hệ số 0,30 / 0,55 / 0,70 × `glow`.
- **Ghost segment**: cùng sprite `88:88` vẽ ở `#1b100e`, **canh đúng vị trí**
  của số thật (nếu canh giữa khung, ghost sẽ lệch và tạo cảm giác "hai hàng số").
- **Tái lập**: noise + `random.Random(seed)` cố định, zip timestamp `1980-01-01`.

## 7. Vì sao đổi từ analog sang LED

Bản 1.0.0 dùng mâm analog + kim Breguet. Trên màn 2 inch, ba kim đồng thau
trên nền tối vẫn đọc được nhưng chi tiết cơ khí bị mất khi liếc nhanh. Bản 2.0.0
đổi sang LED 7 đoạn vì:

- đọc giờ bằng một cái liếc, không cần phân biệt kim giờ/phút;
- số 7 đoạn là hình học thuần, render sắc ở mọi kích thước;
- hợp thẩm mỹ "bảng điều khiển hơi nước" (steampunk instrument) hơn đồng hồ đeo tay cổ điển.

Nhãn giao diện chuyển hết sang tiếng Việt (`GIÂY`, `PIN`, `BƯỚC CHÂN`,
`NHỊP TIM`) để người dùng không phải đoán.

## 8. Chế độ ban đêm

`face_night.png` = giảm 40% độ sáng, 75% độ bão hoà. Không hạ sâu hơn vì LED
vẫn cần nổi trên nền LCD.
