# Đặc tả thiết kế — Steampunk RW5A

## 1. Ràng buộc phần cứng

| Thông số | Giá trị | Hệ quả thiết kế |
|---|---|---|
| Màn hình | LCD 2.0", 320 × 385 px, 251 ppi | Vẽ 1:1, không scale |
| Bo góc | bán kính ≈ 46 px | Nội dung phải nằm trong vùng an toàn |
| Tấm nền | LCD (không phải AMOLED) | Nền tối vẫn tốt, nhưng tránh chi tiết < 1 px |
| Hệ điều hành | HyperOS (RTOS) | Không có Watch Face Format, không có APK |

Vùng an toàn: chữ và số nằm trong `inset 14 px`, bo góc 40 px. Bốn góc của
`face.png` phải tối (luma < 70) để nếu máy cắt thêm vài pixel cũng không mất gì.

## 2. Bố cục

```
 y=0    ┌──────────────────────────┐  bo góc 46
 10     │   ⚙  [ AETHER ]  ⚙      │  bảng tên, dải 10–50
 56     │        ╭────────╮        │
        │      ╭─┤  dial  ├─╮      │  tâm (160,160), R=104
 160    │      │ │  ✳     │ │      │  mặt số R=87
        │      ╰─┤        ├─╯      │
 264    │        ╰────────╯        │
 272    │  ┌────────────────────┐  │
        │  │ (25) (78%) (6.4k)  │  │  3 cửa sổ Φ54, tâm y=312
 362    │  └────────────────────┘  │
        └──────────────────────────┘
```

Toạ độ và bán kính lấy từ `assets/layout.json`; không hard-code trong script.

## 3. Bảng màu

| Token | Hex | Dùng cho |
|---|---|---|
| `ink` | `#120c08` | viền kim, chữ khắc, đáy sâu |
| `iron` | `#1c1512` | nền gang |
| `iron_hi` | `#33261d` | nền gang vùng sáng |
| `brass_dark` | `#6b4519` | bóng đồng, rãnh khắc |
| `brass` | `#c8963e` | thân đồng chính |
| `brass_hi` | `#f6d894` | highlight, vạch phút lớn |
| `copper` | `#a9603a` | điểm nhấn đồng đỏ |
| `patina` | `#2f6f66` | verdigris (oxy hoá) |
| `parchment` | `#eadcbb` | số La Mã, giá trị |
| `ember` | `#e2603a` | kim giây (màu nóng duy nhất) |

Tương phản chữ `parchment` trên nền mặt số tối đạt ≈ 9:1 (WCAG AAA cho chữ lớn).

## 4. Layer và thứ tự z

| ID | Tệp | z | Động | Ghi chú |
|---|---|---|---|---|
| `00_backplate` | `layers/00_backplate.png` | 0 | – | nền, bánh răng mờ, rivet, vignette |
| `01_nameplate` | `layers/01_nameplate.png` | 1 | – | bảng tên + 2 bánh răng nhỏ |
| `02_dial` | `layers/02_dial.png` | 2 | – | vành răng, mặt số, số, vạch |
| `03_complications` | `layers/03_complications.png` | 3 | – | 3 cửa sổ giá trị |
| `10_hand_hour` | `layers/10_hand_hour.png` | 10 | 12h/vòng | kim Breguet |
| `11_hand_minute` | `layers/11_hand_minute.png` | 11 | 60m/vòng | kim Breguet mảnh |
| `12_hand_second` | `layers/12_hand_second.png` | 12 | 60s/vòng | kim cam, có đối trọng |
| `13_cap` | `layers/13_cap.png` | 13 | – | ốc giữ kim |
| `20_glass` | `layers/20_glass.png` | 20 | – | phản sáng; bỏ ở chế độ tối |

Ba layer kim được vẽ **hướng 12 giờ**; khi dựng mặt động chỉ cần xoay quanh
tâm `(160, 160)` theo đúng chu kỳ, không phải cắt ảnh.

## 5. Kỹ thuật render

- **Supersampling 3×**: mọi hình vẽ trên canvas 960 × 1155 rồi hạ LANCZOS về
  320 × 385. Cung tròn, răng bánh răng và số La Mã vì thế không bị răng cưa.
- **Gradient có stop tuỳ ý**: nội suy màu trên 256 mức xám của
  `Image.linear_gradient` / `radial_gradient` rồi `point()` LUT — nhanh và
  không cần numpy.
- **Đồng thau** = gradient dọc (sáng → tối → sáng) phủ qua mask alpha, cộng
  vân xước mịn và vignette.
- **Bóng đổ kim** tính **sau khi xoay** (nếu tính trước, bóng sẽ đứng yên ở
  12 giờ — lỗi đã từng mắc và được kiểm tra bằng pixel test).
- **Tái lập**: `Image.effect_noise` + `random.Random(seed)` cố định, không dùng
  `random` toàn cục, zip ghi timestamp `1980-01-01`.

## 6. Vì sao mặt số tối?

Bản đầu dùng mặt giấy kem. Trên màn hình 2 inch, nền sáng làm 3 kim đồng thau
chìm vào nền và tổng thể bị "bệt". Đổi sang mặt gang oxy hoá:

- kim đồng sáng trên nền tối → tương phản cao, đọc giờ trong 0,2 s;
- giữ được cảm giác "thiết bị cơ khí" thay vì "đồng hồ treo tường";
- tiết kiệm pin hơn trên LCD (ít pixel sáng).

## 7. Chế độ ban đêm

`face_night.png` = giảm 45% độ sáng, 72% độ bão hoà. Không hạ xuống quá thấp
(0,3) vì mất hết chi tiết trên tấm nền LCD thường.
