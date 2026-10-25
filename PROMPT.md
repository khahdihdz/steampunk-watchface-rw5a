# Prompt tạo dự án

Sao chép toàn bộ nội dung từ dòng **"BẮT ĐẦU PROMPT"** đến **"KẾT THÚC PROMPT"**
và dán vào agent (OpenCode, Claude Code, Cursor, Copilot Workspace…).

---

## BẮT ĐẦU PROMPT

Bạn là kỹ sư đồ hoạ procedural + kỹ sư CI/CD. Hãy tạo một repository hoàn chỉnh
sinh ra **mặt đồng hồ steampunk lộ cơ, LED 7 đoạn, giao diện tiếng Việt** cho
**Redmi Watch 5 Active**, có pipeline GitHub Actions build và phát hành release.

### 1. Sự thật kỹ thuật bắt buộc (không được bỏ qua)

- Thiết bị: **Redmi Watch 5 Active** — LCD 2.0\", **320 × 385 px**, 60 Hz, bo góc
  vật lý **bán kính ≈ 46 px**, chạy **HyperOS** (RTOS), **không phải Wear OS**.
- Thiết bị **không có SDK mặt đồng hồ công khai**. Vì vậy:
  - **Không được** tạo APK, không dùng Watch Face Format của Wear OS, không
    tuyên bố "cài bằng ADB/APK".
  - Sản phẩm bàn giao là **bộ asset**: ảnh 320 × 385 cho tính năng "ảnh mặt
    đồng hồ" của Mi Fitness, **cộng** các layer rời + file toạ độ để dựng bản
    động trong Mi Watch Face Editor.
- Bước nào không tự động hoá được (thao tác trong app Xiaomi) phải ghi rõ trong
  README, không được giả vờ đã làm.

### 2. Ngôn ngữ & công nghệ

- Toàn bộ hình ảnh **sinh bằng code** (Python 3.12 + Pillow). Không commit PNG
  nguồn, không tải asset từ internet, không dùng font thương mại.
- Font: chỉ dùng font có sẵn trên runner Ubuntu (`fonts-noto-core`,
  `fonts-dejavu-core`), có fallback và biến môi trường ghi đè đường dẫn.
- **Giao diện tiếng Việt có dấu**: `GIÂY`, `PIN`, `BƯỚC CHÂN`, `NHỊP TIM`,
  dải ngày dạng `CHỦ NHẬT · 25/10/2026`. Phải kiểm tra font thật sự có glyph
  tiếng Việt, không để ra ô vuông `.notdef`.
- **Số giờ và số liệu dùng LED 7 đoạn vẽ bằng polygon**, không dùng font LED.
- Mọi hình vẽ ở **supersampling 3×** rồi hạ về 320 × 385 bằng LANCZOS.
- Build phải **tái lập được**: cùng input ⇒ cùng SHA-256 của file zip.

### 3. Thiết kế

**Bố cục (toạ độ thiết bị, gốc trên-trái):**

| Vùng | Toạ độ |
|---|---|
| Canvas | 320 × 385, bo góc 46, vùng an toàn inset 14 |
| Bảng tên AETHER | `(62, 18)–(258, 54)` |
| Khung LED | `(22, 64)–(298, 182)` |
| Dải thứ/ngày | `(64, 192)–(256, 226)` |
| Bảng phức hợp | `(26, 236)–(294, 356)`, 3 cửa sổ 78 × 40 tại y = 290 |

Hai bên sườn (x < 26 và x > 294) là **bộ máy lộ**.

**Bộ máy lộ (layer riêng, vẽ trên nền trong suốt):**

- Cầu (bridge): polyline dày bo đầu, gradient đồng dọc, viền sáng lệch lên,
  bóng lệch xuống, vân xước cắt theo mask.
- Bánh răng: silhouette từ công thức bánh răng + gradient radial + khoét lỗ nan
  hoa (`ImageChops.subtract`) + hub + vành sáng.
- Thùng dây cót: vành răng + lò xo xoắn Archimedes 4 vòng + bánh cót 8 rãnh.
- Bánh lắc: vành khuyên, 2 nan, tóc xoắn 5,5 vòng, 4 ốc vành, chân kính giữa.
- Chân kính ruby + ốc thép xanh (có rãnh vít).
- Đặt sao cho chi tiết rơi vào dải nhìn thấy: sườn trái/phải, đáy (y > 356), góc.

**Kính khói (xuyên thấu nhưng vẫn đọc được):**

| Lớp | Alpha | Lý do |
|---|---|---|
| `backdrop` | 255 | đáy vỏ — bỏ được để có nền trong suốt |
| `crystal` | ~8% phủ toàn mặt | ánh lạnh + khúc xạ mép kính |
| `led_panel` (kính trong) | 94% | hạ dưới 0,90 là quầng LED mất tương phản |
| `date_strip` | 91% | chữ ngày còn rõ |
| `complications` | 89% | thấy máy mờ phía sau |
| `nameplate` | 97% | chữ khắc sắc nét |

**Thông số 7 đoạn:**

| Tham số | Giờ:phút | Giây | PIN/NHỊP TIM | BƯỚC |
|---|---|---|---|---|
| `digit_w` | 36,0 | 16,0 | 16,0 | 13,5 |
| `digit_h` | 78,0 | 28,0 | 26,0 | 24,0 |
| `stroke` | 6,4 | 3,6 | 3,8 | 3,2 |
| `gap` | 1,8 | 1,1 | 1,8 | 1,6 |
| `spacing` | 9,0 | 3,0 | 3,0 | 2,4 |

**Quy tắc hình học 7 đoạn (quan trọng, dễ sai):**

1. Mỗi segment là hình lục giác, hai đầu vát 45°.
2. `gap` phải ≤ ~0,3 × `stroke`; lớn hơn thì segment rời nhau, số đọc thành
   "viên thuốc".
3. `stroke < digit_h / 5`, nếu không lỗ giữa số 0 sẽ bít lại.
4. Lớp "hot core" (ruột sáng) phải **mỏng hơn nhưng giữ nguyên đường tâm**
   (`t_center`) và **ngắn hơn** hai đầu (`inset`).
5. Ghost segment vẽ cùng sprite `88:88` màu `#1b100e`, **canh đúng vị trí** số
   thật — canh giữa khung sẽ lệch khi có khối giây bên phải.

**Layer (PNG 320 × 385 RGBA, cùng hệ toạ độ):**

| File | z | Nội dung |
|---|---|---|
| `00_backdrop.png` | 0 | đáy vỏ gang + rivet + vignette |
| `01_movement.png` | 1 | bộ máy lộ |
| `02_crystal.png` | 2 | kính khói |
| `03_nameplate.png` | 3 | bảng AETHER |
| `04_led_panel.png` | 4 | khung LED + segment chưa sáng |
| `05_readout.png` | 5 | giờ:phút + giây (layer duy nhất thay bằng widget) |
| `06_date_strip.png` | 6 | dải `CHỦ NHẬT · 25/10/2026` |
| `07_complications.png` | 7 | 3 cửa sổ PIN / BƯỚC CHÂN / NHỊP TIM |
| `20_glass.png` | 20 | phản sáng, bỏ khi chế độ tối |

**Ảnh phẳng:**

- `photo/face.png` — 320 × 385 RGB, phủ kín màn hình.
- `photo/face_rounded.png` — mask theo bo góc 46 (alpha ngoài góc = 0).
- `photo/face_night.png` — giảm ~40% sáng, 75% bão hoà.
- `photo/face_alpha.png` — RGBA **không có backdrop**: khe giữa các bảng trong
  suốt thật, còn các bảng đục 100% để chữ vẫn đọc được.

### 4. Cấu trúc repo

```
.
├── .github/workflows/ci.yml        # render + validate + kiểm tra tái lập
├── .github/workflows/release.yml   # tag v* → build → GitHub Release
├── assets/layout.json              # nguồn sự thật: khung, 7 đoạn, nhãn, layer
├── assets/palette.json             # bảng màu (đồng, thép xanh, ruby, LED)
├── docs/design-spec.md             # đặc tả thiết kế
├── docs/mi-watch-face-editor.md    # hướng dẫn dựng bản động
├── docs/preview.png · docs/rotation.gif
├── scripts/steampunk.py            # Canvas 3x, gradient, bộ máy, LED 7 đoạn
├── scripts/generate.py             # render artefact + mock-up + GIF
├── scripts/validate.py             # kiểm tra ràng buộc
├── scripts/build.py                # zip tái lập + manifest + SHA256SUMS
├── Makefile · requirements.txt · README.md · PROMPT.md · LICENSE
```

### 5. Kiểm tra tự động (`scripts/validate.py`, ~74 check)

Phải fail build (exit ≠ 0) khi:

1. Thiếu bất kỳ artefact nào (4 ảnh photo + 9 layer).
2. Ảnh sai kích thước (≠ 320 × 385) hoặc sai mode (layer phải RGBA).
3. Layer rỗng (alpha bbox = None).
4. `05_readout` tràn ra ngoài khung LED.
5. Quá ít pixel màu LED sáng (< 1200 pixel gần `#ffb340`).
6. `stroke ≥ digit_h / 5` hoặc `seven_seg_width("88:88")` rộng hơn khung LED.
7. `01_movement` rỗng, hoặc không phủ hai mép trái/phải, hoặc < 3000 pixel đồng.
8. `face_rounded.png` còn đục ở 4 góc hoặc trong suốt ở tâm.
9. 4 góc `face.png` quá sáng (luma > 75).
10. `face_alpha.png` không phải RGBA, góc không trong suốt, vùng số không đục,
    hoặc khe giữa các bảng vẫn đục (mất tính xuyên thấu).
11. `face_night.png` không tối hơn bản ngày.
12. `layout.json` sai canvas/bán kính bo góc, hoặc thứ tự layer không tăng dần.

In ra `✓ N kiểm tra đều đạt (320×385, bo góc 46px, LED 7 đoạn)`.

### 6. GitHub Actions

**CI** (push `main`, pull_request, workflow_dispatch):

- Ubuntu latest, Python 3.12, cài `fonts-noto-core` + `fonts-dejavu-core`.
- Chạy `python scripts/build.py`.
- Build **hai lần** (`dist/`, `dist2/`) rồi `cmp dist/*.zip dist2/*.zip`.
- `cd dist && sha256sum -c SHA256SUMS.txt`.
- Upload `dist/preview/*` làm artifact.

**Release** (push tag `v*`, hoặc workflow_dispatch có input `version`):

- `permissions: contents: write`.
- `SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)`.
- Build, verify checksum, rồi `gh release create` (dùng `GITHUB_TOKEN`) đính kèm:
  `.zip`, `manifest.json`, `SHA256SUMS.txt`, `preview.png`, `rotation.gif`.
- `--generate-notes`; **không** truyền `--target` khi tag đã tồn tại.

### 7. Tiêu chí nghiệm thu

- [ ] `make package VERSION=3.0.0` chạy < 60 s, không cảnh báo.
- [ ] Zip chứa **16 tệp**: 4 ảnh photo + 9 layer + `layout.json` +
      `INSTALL.txt` + `LICENSE`.
- [ ] Build 2 lần trên cùng runner cho zip giống nhau từng byte.
- [ ] Ở 100%, `10:09` đọc được ngay; "0" có lỗ giữa rõ ràng.
- [ ] Bộ máy (bánh răng, bánh lắc, thùng dây cót) nhìn thấy ở sườn và đáy.
- [ ] Qua kính khói vẫn thấy máy mờ, nhưng số/nhãn không bị giảm tương phản.
- [ ] `face_alpha.png` để nền trong suốt ở khe giữa các bảng, không lộ viền
      răng cưa.
- [ ] Chữ tiếng Việt có dấu hiển thị đúng (không ô vuông).
- [ ] Không pixel nội dung nào lọt ra ngoài bo góc.
- [ ] README nói trung thực giới hạn "không có APK" + 2 cách sử dụng.

### 8. Quy tắc chống ảo giác

- Không bịa tên SDK, API, lệnh CLI hay endpoint không tồn tại.
- Không tuyên bố "đã test trên thiết bị thật" khi chưa có.
- Không cam kết thời lượng pin hay tính năng nào của máy.
- Thiếu font/Pillow phải báo lỗi rõ ràng kèm cách cài, không render ảnh trắng.
- Mọi con số trong README (kích thước, số layer, số check) phải khớp build thật.

### 9. Định dạng trả lời

1. Cây thư mục đã tạo.
2. Giải thích ngắn 3 quyết định thiết kế quan trọng.
3. Lệnh build và xem kết quả.
4. Danh sách việc **chưa** làm được và lý do.

## KẾT THÚC PROMPT
