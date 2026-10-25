# Prompt tạo dự án

Sao chép toàn bộ nội dung từ dòng **"BẮT ĐẦU PROMPT"** đến **"KẾT THÚC PROMPT"**
và dán vào agent (OpenCode, Claude Code, Cursor, Copilot Workspace…).

---

## BẮT ĐẦU PROMPT

Bạn là kỹ sư đồ hoạ procedural + kỹ sư CI/CD. Hãy tạo một repository hoàn chỉnh
sinh ra **mặt đồng hồ phong cách steampunk** cho **Redmi Watch 5 Active**, có
pipeline GitHub Actions build và phát hành bản release.

### 1. Sự thật kỹ thuật bắt buộc (không được bỏ qua)

- Thiết bị: **Redmi Watch 5 Active** — màn hình LCD 2.0", **320 × 385 px**,
  60 Hz, bo góc vật lý **bán kính ≈ 46 px**, chạy **HyperOS** (RTOS), **không
  phải Wear OS**.
- Thiết bị **không có SDK mặt đồng hồ công khai**. Vì vậy:
  - **Không được** tạo APK, không được dùng Watch Face Format của Wear OS,
    không được tuyên bố "cài bằng ADB/APK".
  - Sản phẩm bàn giao là **bộ asset**: ảnh 320 × 385 dùng cho tính năng "ảnh
    mặt đồng hồ" của Mi Fitness, **cộng** các layer rời + file toạ độ để dựng
    mặt đồng hồ động trong Mi Watch Face Editor.
- Nếu một bước nào đó không thể tự động hoá (ví dụ thao tác trong app Xiaomi),
  hãy ghi rõ trong README thay vì giả vờ đã làm được.

### 2. Ngôn ngữ & công nghệ

- Toàn bộ hình ảnh phải **sinh bằng code** (Python 3.12 + Pillow). Không commit
  file PNG nguồn, không dùng asset tải từ internet, không dùng font thương mại.
- Font: chỉ dùng font hệ thống có sẵn trên runner Ubuntu
  (`fonts-noto-core`, `fonts-dejavu-core`), có cơ chế fallback và biến môi
  trường để ghi đè đường dẫn font.
- Mọi hình phải vẽ ở **supersampling 3×** rồi hạ về 320 × 385 bằng LANCZOS —
  không được để răng cưa ở cung tròn và chữ.
- Build phải **tái lập được**: cùng input ⇒ cùng SHA-256 của file zip.

### 3. Thiết kế

**Bố cục (toạ độ thiết bị, gốc trên-trái):**

| Vùng | Toạ độ / kích thước |
|---|---|
| Canvas | 320 × 385, bo góc bán kính 46 |
| Vùng an toàn | inset 14 px, bo góc 40 (mọi chữ/số phải nằm trong đây) |
| Mâm số (dial) | tâm (160, 160), bán kính ngoài 104, mặt số 87 |
| Trục kim | (160, 160) |
| Kim giờ / phút / giây | dài 56 / 80 / 86 px |
| Bảng tên trên | hình chữ nhật bo góc, dải y ≈ 10–50, chữ "AETHER" |
| Bảng phức hợp dưới | y ≈ 272–362, 3 "cửa sổ" tròn Φ54: ngày, pin, số bước |

**Phong cách steampunk (bắt buộc thể hiện):**

- Bánh răng đồng thau có răng ở vành mâm số (64 răng), thêm 2–3 bánh răng mờ
  ở nền và hai bánh răng nhỏ hai bên bảng tên.
- Kim kiểu **Breguet**: có vòng tròn rỗng gần mũi kim, đối trọng phía sau.
- Đinh tán (rivet) ở 4 góc bo, vít nhỏ trên vành.
- Nền gang oxy hoá tối, vết verdigris (patina) mờ, vân xước ly tâm, vignette.
- Mặt số tối (không dùng nền giấy sáng) để tương phản tốt trên LCD: số La Mã
  màu kem, vạch phút màu đồng, kim giây màu cam nóng.
- Bảng màu tối thiểu 6 màu, khai báo trong `assets/palette.json`:

  ```
  ink #120c08 · iron #1c1512 · brass_dark #6b4519 · brass #c8963e
  brass_hi #f6d894 · copper #a9603a · patina #2f6f66 · parchment #eadcbb
  ember #e2603a
  ```

**Layer (mỗi layer là một PNG 320 × 385 RGBA, cùng hệ toạ độ):**

| File | Nội dung | Ghi chú |
|---|---|---|
| `00_backplate.png` | nền gang + bánh răng mờ + đinh tán + vignette | tĩnh |
| `01_nameplate.png` | bảng tên + 2 bánh răng nhỏ | tĩnh |
| `02_dial.png` | vành răng, vành đồng, mặt số, vạch, số La Mã | tĩnh |
| `03_complications.png` | bảng dưới + 3 cửa sổ ngày/pin/bước | tĩnh |
| `10_hand_hour.png` | kim giờ, **chỉ hướng 12h**, tâm xoay (160,160) | xoay 12h/vòng |
| `11_hand_minute.png` | kim phút, cùng quy ước | xoay 60m/vòng |
| `12_hand_second.png` | kim giây, cùng quy ước | xoay 60s/vòng |
| `13_cap.png` | ốc/bulông giữ kim ở tâm | trên cùng của kim |
| `20_glass.png` | vệt phản sáng mờ | bỏ khi chế độ tối |

**Ảnh phẳng để dùng ngay:**

- `photo/face.png` — 320 × 385 RGB, phủ kín màn hình.
- `photo/face_rounded.png` — bản đã mask theo bo góc 46 (alpha ngoài góc = 0).
- `photo/face_night.png` — bản dịu sáng (giảm ~45% độ sáng) cho ban đêm.

### 4. Cấu trúc repo

```
.
├── .github/workflows/ci.yml        # render + validate + kiểm tra tái lập
├── .github/workflows/release.yml   # tag v* → build → GitHub Release
├── assets/layout.json              # nguồn sự thật: toạ độ, layer, tâm xoay
├── assets/palette.json             # bảng màu
├── docs/design-spec.md             # đặc tả thiết kế
├── docs/mi-watch-face-editor.md    # hướng dẫn dựng bản động
├── docs/preview.png                # ảnh mock-up cho README
├── scripts/steampunk.py            # thư viện vẽ (Canvas supersampled, gradient…)
├── scripts/generate.py             # render toàn bộ artefact
├── scripts/validate.py             # kiểm tra ràng buộc
├── scripts/build.py                # đóng gói zip + manifest + SHA256SUMS
├── Makefile · requirements.txt · README.md · PROMPT.md · LICENSE
```

### 5. Kiểm tra tự động (`scripts/validate.py`)

Phải fail build (exit ≠ 0) khi:

1. Thiếu bất kỳ artefact nào ở trên.
2. Ảnh sai kích thước (khác 320 × 385) hoặc sai mode (layer phải RGBA).
3. Layer kim rỗng, quá rộng (> 34 px với kim giờ) hoặc **không chứa tâm xoay**.
4. `face_rounded.png` còn đục ở 4 góc hoặc trong suốt ở tâm.
5. 4 góc của `face.png` quá sáng (luma > 70) — dấu hiệu nội dung bị bo góc cắt.
6. `face_night.png` không tối hơn bản ngày.
7. `layout.json` sai kích thước canvas hoặc sai bán kính bo góc.

In ra số kiểm tra đạt/tổng, ví dụ: `✓ 61 kiểm tra đều đạt (320×385, bo góc 46px)`.

### 6. GitHub Actions

**CI** (push `main`, pull_request, workflow_dispatch):

- Ubuntu latest, Python 3.12, cài `fonts-noto-core` + `fonts-dejavu-core`.
- Chạy `python scripts/build.py`.
- Build **hai lần** vào `dist/` và `dist2/` rồi `cmp dist/*.zip dist2/*.zip`
  để chứng minh tính tái lập.
- `sha256sum -c dist/SHA256SUMS.txt`.
- Upload `dist/preview/*` làm artifact.

**Release** (push tag `v*`, workflow_dispatch có input `version`):

- `permissions: contents: write`.
- `SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)` để zip ổn định.
- Build, verify checksum, rồi `gh release create` (dùng `GITHUB_TOKEN`, không
  cần action bên thứ ba) đính kèm: file `.zip`, `manifest.json`,
  `SHA256SUMS.txt`, `preview.png`, `rotation.gif`.
- `--generate-notes` để tự sinh changelog.

### 7. Tiêu chí nghiệm thu

- [ ] `make package VERSION=1.0.0` chạy < 30 s trên máy 4 core, không cảnh báo.
- [ ] Zip chứa 15 tệp, mở ra thấy đúng cấu trúc `photo/`, `layers/`,
      `layout.json`, `INSTALL.txt`, `LICENSE`.
- [ ] Chạy build 2 lần cho ra zip **giống nhau từng byte**.
- [ ] Ảnh xem ở 100% vẫn sắc nét: không răng cưa ở vành răng, số La Mã đọc
      được, kim giây nổi bật.
- [ ] Không có pixel nội dung nào lọt ra ngoài vùng bo góc.
- [ ] README giải thích trung thực giới hạn "không có APK" và 2 cách sử dụng.
- [ ] Workflow YAML hợp lệ (`actionlint` hoặc `python -c "import yaml"`).

### 8. Quy tắc chống ảo giác

- Không bịa tên SDK, API, lệnh CLI hay endpoint không tồn tại.
- Không tuyên bố "đã test trên thiết bị thật" khi chưa có.
- Không cam kết thời lượng pin, độ sáng hay tính năng nào của máy.
- Nếu thiếu font hoặc thiếu Pillow, báo lỗi rõ ràng kèm cách cài, không render
  ra ảnh trắng.
- Mọi con số trong README (kích thước, số layer, số kiểm tra) phải khớp với
  kết quả build thật.

### 9. Định dạng trả lời

1. Cây thư mục đã tạo.
2. Giải thích ngắn 3 quyết định thiết kế quan trọng.
3. Lệnh để build và xem kết quả.
4. Danh sách việc **chưa** làm được và lý do.

## KẾT THÚC PROMPT
