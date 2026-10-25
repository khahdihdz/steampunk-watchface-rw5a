# Prompt tạo dự án

Sao chép toàn bộ nội dung từ dòng **"BẮT ĐẦU PROMPT"** đến **"KẾT THÚC PROMPT"**
và dán vào agent (OpenCode, Claude Code, Cursor, Copilot Workspace…).

---

## BẮT ĐẦU PROMPT

Bạn là kỹ sư đồ hoạ procedural + kỹ sư CI/CD. Hãy tạo một repository hoàn chỉnh
sinh ra **mặt đồng hồ steampunk LED 7 đoạn, giao diện tiếng Việt** cho
**Redmi Watch 5 Active**, có pipeline GitHub Actions build và phát hành release.

### 1. Sự thật kỹ thuật bắt buộc (không được bỏ qua)

- Thiết bị: **Redmi Watch 5 Active** — LCD 2.0", **320 × 385 px**, 60 Hz, bo góc
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
- **Số giờ và số liệu dùng LED 7 đoạn vẽ bằng polygon**, không dùng font LED
  (không có font 7 đoạn mã nguồn mở đáng tin cậy trong môi trường CI).
- Mọi hình vẽ ở **supersampling 3×** rồi hạ về 320 × 385 bằng LANCZOS.
- Build phải **tái lập được**: cùng input ⇒ cùng SHA-256 của file zip.

### 3. Thiết kế

**Bố cục (toạ độ thiết bị, gốc trên-trái):**

| Vùng | Toạ độ |
|---|---|
| Canvas | 320 × 385, bo góc 46, vùng an toàn inset 14 |
| Bảng tên AETHER | `(62, 18)–(258, 54)`, 2 bánh răng hai bên |
| Khung LED | `(22, 64)–(298, 182)` |
| Dải thứ/ngày | `(40, 192)–(280, 226)` |
| Bảng phức hợp | `(20, 236)–(300, 356)`, 3 cửa sổ 82 × 42 tại y = 290 |

**Thông số 7 đoạn:**

| Tham số | Giờ:phút | Giây |
|---|---|---|
| `digit_w` | 36,0 | 16,0 |
| `digit_h` | 78,0 | 28,0 |
| `stroke` | 6,4 | 3,6 |
| `gap` | 1,8 | 1,1 |
| `spacing` | 9,0 | 3,0 |
| `colon_w` | 14,0 | 8,0 |
| `slant` | 0,06 | — |

**Quy tắc hình học 7 đoạn (quan trọng, dễ sai):**

1. Mỗi segment là hình lục giác, hai đầu vát 45°.
2. `gap` phải ≤ ~0,3 × `stroke`; nếu lớn hơn, các segment rời nhau và số đọc
   thành "viên thuốc".
3. `stroke < digit_h / 5`, nếu không lỗ giữa số 0 sẽ bít lại.
4. Lớp "hot core" (ruột sáng) phải **mỏng hơn nhưng giữ nguyên đường tâm**
   (`t_center`) và **ngắn hơn** hai đầu (`inset`). Nếu chỉ truyền `stroke` nhỏ
   hơn vào công thức toạ độ cũ, ruột sáng bám mép segment và số trông rỗng.
5. Segment **chưa sáng** (ghost) vẽ cùng sprite `88:88` màu `#1b100e`, và phải
   **canh đúng vị trí số thật** — canh giữa khung sẽ lệch khi có khối giây bên
   phải, tạo cảm giác "hai hàng số".

**Phong cách steampunk (bắt buộc thể hiện):**

- Khung đồng thau có vát, ốc, đinh tán 4 góc bo, vết verdigris, vignette, vân
  xước mịn; bánh răng mờ ở nền và 2 bánh răng nhỏ cạnh bảng tên.
- Bảng màu: nền gang `#1c1512`, đồng `#c8963e` / `#f6d894`, LED hổ phách
  `#ffb340`, LED giây đỏ cam `#ff5b3a`, chữ kem `#eadcbb`.
- LED có **quầng sáng 3 lớp** (blur 7 / 3,2 / 1,2 px) và ruột sáng hơn ở giữa.

**Layer (mỗi layer là PNG 320 × 385 RGBA, cùng hệ toạ độ):**

| File | z | Nội dung |
|---|---|---|
| `00_backplate.png` | 0 | nền gang + bánh răng mờ + rivet + vignette |
| `01_nameplate.png` | 1 | bảng AETHER + 2 bánh răng |
| `02_led_panel.png` | 2 | khung LED + segment chưa sáng |
| `03_readout.png` | 3 | giờ:phút + giây (layer duy nhất thay bằng widget) |
| `04_date_strip.png` | 4 | dải `CHỦ NHẬT · 25/10/2026` |
| `05_complications.png` | 5 | 3 cửa sổ PIN / BƯỚC CHÂN / NHỊP TIM |
| `20_glass.png` | 20 | phản sáng, bỏ khi chế độ tối |

**Ảnh phẳng:**

- `photo/face.png` — 320 × 385 RGB, phủ kín màn hình.
- `photo/face_rounded.png` — mask theo bo góc 46 (alpha ngoài góc = 0).
- `photo/face_night.png` — giảm ~40% sáng, 75% bão hoà.

### 4. Cấu trúc repo

```
.
├── .github/workflows/ci.yml        # render + validate + kiểm tra tái lập
├── .github/workflows/release.yml   # tag v* → build → GitHub Release
├── assets/layout.json              # nguồn sự thật: khung, 7 đoạn, nhãn, layer
├── assets/palette.json             # bảng màu
├── docs/design-spec.md             # đặc tả thiết kế
├── docs/mi-watch-face-editor.md    # hướng dẫn dựng bản động
├── docs/preview.png · docs/rotation.gif
├── scripts/steampunk.py            # Canvas 3x, gradient, gear, LED 7 đoạn
├── scripts/generate.py             # render artefact
├── scripts/validate.py             # kiểm tra ràng buộc
├── scripts/build.py                # zip tái lập + manifest + SHA256SUMS
├── Makefile · requirements.txt · README.md · PROMPT.md · LICENSE
```

### 5. Kiểm tra tự động (`scripts/validate.py`, khoảng 55–60 check)

Phải fail build (exit ≠ 0) khi:

1. Thiếu bất kỳ artefact nào.
2. Ảnh sai kích thước (≠ 320 × 385) hoặc sai mode (layer phải RGBA).
3. Layer rỗng (alpha bbox = None).
4. `03_readout` tràn ra ngoài khung LED.
5. Quá ít pixel màu LED sáng (< 1200 pixel gần `#ffb340`) — dấu hiệu số không render.
6. `stroke ≥ digit_h / 5` (segment dính khối) hoặc `seven_seg_width("88:88")`
   rộng hơn khung LED.
7. `face_rounded.png` còn đục ở 4 góc hoặc trong suốt ở tâm.
8. 4 góc `face.png` quá sáng (luma > 75).
9. `face_night.png` không tối hơn bản ngày.
10. `layout.json` sai canvas/bán kính bo góc, hoặc thứ tự layer không tăng dần.

In ra `✓ N kiểm tra đều đạt (320×385, bo góc 46px, LED 7 đoạn)`.

### 6. GitHub Actions

**CI** (push `main`, pull_request, workflow_dispatch):

- Ubuntu latest, Python 3.12, cài `fonts-noto-core` + `fonts-dejavu-core`.
- Chạy `python scripts/build.py`.
- Build **hai lần** (`dist/`, `dist2/`) rồi `cmp dist/*.zip dist2/*.zip`.
- `cd dist && sha256sum -c SHA256SUMS.txt` (đường dẫn trong file là tương đối).
- Upload `dist/preview/*` làm artifact.

**Release** (push tag `v*`, hoặc workflow_dispatch có input `version`):

- `permissions: contents: write`.
- `SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)` để zip ổn định.
- Build, verify checksum, rồi `gh release create` (dùng `GITHUB_TOKEN`, không cần
  action bên thứ ba) đính kèm: `.zip`, `manifest.json`, `SHA256SUMS.txt`,
  `preview.png`, `rotation.gif`.
- `--generate-notes`; **không** truyền `--target` khi tag đã tồn tại.

### 7. Tiêu chí nghiệm thu

- [ ] `make package VERSION=2.0.0` chạy < 30 s, không cảnh báo.
- [ ] Zip chứa **13 tệp**: 3 ảnh photo + 7 layer + `layout.json` +
      `INSTALL.txt` + `LICENSE`.
- [ ] Build 2 lần trên cùng runner cho zip giống nhau từng byte.
- [ ] Ở 100%, `10:09` đọc được ngay, không cần đoán; "0" có lỗ giữa rõ ràng.
- [ ] Ghost segment nằm đúng dưới số thật, không lệch thành hàng thứ hai.
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
