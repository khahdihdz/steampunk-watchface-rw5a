# Bản `.bin` — mặt đồng hồ biên dịch được

File `steampunk-rw5a.bin` trong release là **mặt đồng hồ thật** cho Redmi Watch
5 Active: cùng loại container mà Mi Fitness tải về máy, có giờ/phút/giây, ngày
tháng, thứ, pin, bước chân và nhịp tim do firmware tự vẽ.

> **Chưa kiểm thử trên thiết bị thật.** Mình không có đồng hồ để cài thử. File
> đã qua đúng bộ biên dịch của Mi-Create và qua kiểm tra cấu trúc, nhưng chưa ai
> xác nhận nó hiển thị đúng trên cổ tay. Đọc mục "Rủi ro" trước khi cài.

## Vì sao phải dùng `compile.exe`

Firmware chỉ kiểm tra 4 byte magic `5A A5 34 12`, không chữ ký, không CRC. Nhưng
ảnh bên trong được nén bằng codec riêng của SiFli (`RedmiWatch5Active
Compressor` / `Decompressor`) — **không có tài liệu, không có mã nguồn**. Tự
đóng gói file `.bin` bằng tay sẽ ra một file "đúng vỏ, rỗng ruột": đồng hồ nạp
vào rồi khởi động lại và rơi về mặt mặc định.

`compile.exe` (trong repo [ooflet/Mi-Create](https://github.com/ooflet/Mi-Create),
GPL-3.0) là bộ biên dịch duy nhất biết codec đó. Repo này **không** phân phối
lại `compile.exe`; CI tải nó từ GitHub rồi chạy.

## Pipeline

```
scripts/binface.py            assets/layout.json + scripts/steampunk.py
        │                     (renderer 7 đoạn, không commit PNG)
        ▼
build/fprj/face.fprj   +  build/fprj/images/*.png        ← project EasyFace
        │                     chạy trên ubuntu-latest
        ▼
compile.exe -b face.fprj  →  steampunk-rw5a.face
        │                     chạy trên windows-latest
        ▼
vá id 9 số vào offset 0x28  →  steampunk-rw5a.bin
        │
        ▼
scripts/check_bin.py          ← cổng kiểm tra trên ubuntu-latest
```

Xem `.github/workflows/bin.yml`. Release gọi workflow này qua `workflow_call`.

## Cái gì động, cái gì tĩnh

Nền (`bg`) là artwork của repo nhưng **đã bỏ** giờ, giây, ngày và ba con số phức
hợp. Firmware vẽ chúng đè lên bằng 13 widget:

| Widget | Nguồn dữ liệu | Ghi chú |
|---|---|---|
| `hour_0/1`, `minute_0/1` | `1000911`, `0911`, `1211`, `1111` | mỗi chữ số một widget, căn tuyệt đối |
| `second_0/1` | `1001911`, `1911` | 7 đoạn đỏ, cỡ nhỏ |
| `weekday` | `2012` | 7 ảnh `CHỦ NHẬT` … `THỨ 7` |
| `day`, `month`, `year` | `1812`, `1012`, `0812` | 2/2/4 chữ số, xoá số 0 đầu |
| `battery` | `0841` | 3 ô, đơn vị `%` vẽ tĩnh |
| `steps` | `0821` | 4 ô |
| `heart` | `0822` | 3 ô |

Bảng mã nguồn đo được từ `src/data/sources.json` của Mi-Create cho đúng
`redmi_watch_5_active`. `compile.exe` chuyển `id_fprj` sang mã nội bộ (`0A11`,
`1A11`, `1A12`…) — kiểm tra lại trong `check_bin.py` sau khi build.

## Ràng buộc đã gặp (và cách xử lý)

| Thông báo của compiler | Nguyên nhân | Cách sửa |
|---|---|---|
| `Colors count is more than 256 pcs` | ảnh trong `imageList` chỉ được ≤ 256 màu | lượng tử hoá `FASTOCTREE` + dither cho từng glyph |
| `Preview has wrong size: 120x108, expected 180x216` | kích thước thumbnail của RW5A | render preview `180×216` |
| `Access to the path '...\project' is denied` | `-b` nhận **file** `.fprj`, không phải thư mục | truyền `project\face.fprj` |
| `.face` không xuất hiện | compiler ghi vào `<projectdir>/output`, không phải tham số thứ 2 | tạo sẵn và đọc ở đó |
| icon/preview bị crash khi unpack | `unpack.exe` không hỗ trợ RW5A (`Watch detected: Undefined`) | bỏ bước unpack, thay bằng `check_bin.py` |

## Rủi ro

- **Chưa test trên máy thật.** Theo nghiên cứu công khai về RW5A, mặt lỗi
  thường làm đồng hồ khởi động lại và quay về mặt mặc định; không có gì bảo đảm
  điều đó đúng với mọi bản firmware.
- Cài mặt ngoài luồng chính thức có thể làm mất mặt đang dùng nếu thao tác sai.
  Giữ lại một mặt gốc trong danh sách để quay về.
- Đây là mặt đồng hồ, **không phải firmware**. Đừng nạp file này vào chế độ
  fastboot/EDL.

## Cách cài

Không có đường chính thức. File `.bin` chỉ dùng được với các cách cộng đồng:

1. **Mi Fitness đã mod** (hoặc app của bên thứ ba hỗ trợ nạp mặt cục bộ) —
   trỏ tới `steampunk-rw5a.bin`.
2. **Chặn lưu lượng Mi Fitness** rồi thay file mặt đang tải bằng file này
   (cách mà nghiên cứu của Byterialab dùng để thử nghiệm trên RW5A).

Cả hai đều là thao tác nâng cao, tự chịu rủi ro. Nếu bạn chỉ muốn mặt tĩnh
trong 2 phút, dùng `photo/face.png` với tính năng **Ảnh** của Mi Fitness.

## Tự build

Cần Windows (hoặc Linux + Wine) và Python 3.12:

```bash
python scripts/binface.py --out build/fprj
python scripts/validate_fprj.py build/fprj

# tải compile.exe từ Mi-Create (đổi <sha> nếu upstream cập nhật)
curl -sL -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/ooflet/Mi-Create/git/blobs/3c015d01143f5c4b3d0ab207baf20684027ebf89 \
  | python -c "import json,sys,base64;open('compile.exe','wb').write(base64.b64decode(json.load(sys.stdin)['content']))"

mkdir -p build/fprj/output
wine compile.exe -b build/fprj/face.fprj build/fprj/output steampunk-rw5a.face 146125642
python scripts/check_bin.py build/fprj/output/steampunk-rw5a.face --name "AETHER Steampunk"
```

Không có Windows/Wine thì để CI làm: `Actions → Face binary → Run workflow`.

## Ghi chú định dạng

Quan sát từ file mẫu và file do compiler sinh ra (dùng cho `check_bin.py`):

```
0x00  5A A5 34 12          magic
0x10  u32                  kích thước header (0x800)
0x14  u32                  0x10000
0x1C  u32                  phiên bản/định dạng
0x20  u32                  offset khối preview
0x28  64 byte              id mặt (9 chữ số, ASCII, đệm 0)
0x68  64 byte              tên mặt (UTF-8, đệm 0)
0x1C0 bảng resource, 16 byte/entry:
      u32 type            0x020000xx ảnh, 0x030000xx atlas, 0x07xxxxxx widget
      u32 flags
      u32 offset          tính từ đầu file
      u32 size
```

Kết thúc bảng là entry có `size = 0`. Ảnh có header riêng `0x28`, byte 1 là
định dạng (`0x0A`, `0x0C`…), `u16` tại +4/+6 là rộng/cao.
