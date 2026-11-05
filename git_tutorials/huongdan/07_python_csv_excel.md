# 07 — Giải thích các script Python, CSV và Excel

[Mục lục](README.md) · [Tiếp: Thực hành](08_thuc_hanh_do_va_xu_ly_loi.md)

## 1. Bắt đầu từ file đang mở: uart_test_dma_tx.py

[uart_test_dma_tx.py](../../TEST_PYTHON/uart_test_dma_tx.py) là nơi cấu hình bài thử ở PC, không phải nơi lập trình phần cứng DMA STM32.

| Hằng | Ý nghĩa hiện tại |
| --- | --- |
| `SERIAL_PORT = "COM4"` | Cổng USB-UART tại PC, cần sửa đúng máy |
| `BAUD_RATE = 1500000` | Baud PC; phải khớp `usart.c` |
| `FIRST_BYTE_TIMEOUT = 30` | Thời gian tối đa chờ byte đầu, thường là chờ reset STM32 |
| `READ_TIMEOUT = 2` | Timeout tối thiểu của lần đọc; luồng chung còn tự tăng theo thời gian một khối ở baud thấp |
| `TOTAL_BYTES = 1_000_000` | Số byte payload phải nhận, không gồm CRC/báo cáo |
| `READ_CHUNK_SIZE = 4096` | Khối đọc ở PC, độc lập với buffer TX 256 byte trên STM32 |
| `SHOW_PROGRESS = True` | In tiến trình trong lúc nhận; có thể ảnh hưởng phép đo PC |
| `PROGRESS_INTERVAL = 1.0` | Khoảng tối thiểu giữa các lần in tiến trình |
| `BITS_PER_BYTE = 10` | Đúng với cấu hình 8N1 |
| `CSV_PATH` | CSV đặt cùng thư mục script, không phụ thuộc terminal đang đứng ở đâu |
| `TEST_MODE_CODE = 3` | Đối chiếu mode firmware trong DWT |
| `DWT_SCOPE` | Chuỗi giải thích phạm vi phép đo khi in kết quả, không phải đoạn code đo |

`main()` truyền các hằng này bằng tham số có tên vào `run_tx_test()`. Phần cuối:

```python
if __name__ == "__main__":
    sys.exit(0 if main() else 1)
```

Khi chạy trực tiếp, `main()` trả bool rồi đổi thành mã thoát 0/1. Khi import file vào chương trình khác thì khối này không tự chạy. Ba file TX dùng chung luồng xử lý, khác cấu hình method/mode/baud/CSV; không cần sao chép thuật toán nhận sang từng file.

## 2. `run_tx_test()` điều phối một lượt

Nguồn: [uart_test_support.py](../../TEST_PYTHON/uart_test_support.py).

```text
Tạo TestResult → mở serial 8N1 → xóa dữ liệu đầu vào cũ
 → receive_data: payload và CRC, chốt thời gian
 → receive_dwt: kiểm gói/mode/clock/chu kỳ
 → receive_idle nếu DWT OK hoặc WRAP_RISK
 → đóng cổng
 → tính CRC payload thực nhận trên PC
 → đánh giá kết quả
 → finally: in → lưu CSV → cập nhật Excel nếu CSV lưu được
```

Import `serial` ở trong hàm giúp module xuất Excel có thể dùng các định nghĩa chung mà không cần mở cổng hoặc import pyserial ngay lúc import support.

PC không gửi lệnh chuyển phương pháp cho firmware. Trường mode chỉ dùng phát hiện chọn nhầm khi đã đọc tới gói DWT.

### Điều kiện thành công cần hiểu đúng

Phải nhận đủ payload, đủ 4 byte CRC, tính CRC khớp. Sau đó mã đánh giá CRC OK và DWT không phải `MODE_MISMATCH`.

Vì thế **một lượt có thể thành công về dữ liệu dù thiếu/sai gói DWT hoặc thiếu IDL1**. Những trường chưa có số đo giữ trống. Không coi kết quả THÀNH CÔNG là chứng nhận mọi chỉ số CPU và nền đều đầy đủ.

Lỗi cổng, cấu hình hoặc Ctrl+C được ghi vào kết quả; `finally` vẫn cố in/lưu. Hàm lưu CSV thất bại hoặc xuất Excel thất bại có thông báo riêng; thành công nhận dữ liệu không bảo đảm file báo cáo đã được cập nhật. Kiểm tra cả đường dẫn và thông báo lưu.

## 3. Danh mục hàm dùng chung

| Hàm/lớp | Nhận gì, làm gì, trả gì? |
| --- | --- |
| `TestResult` | Dataclass giữ số byte, thời gian, CRC, DWT, clock, counter, cờ passed và chi tiết. `None` nghĩa chưa có số đo, khác số 0 |
| `calculate_crc32_stm32(data)` | Mô phỏng CRC phần cứng từ payload thực nhận; trả uint32, có đệm 0 tới bội 4 phía PC |
| `receive_data(ser, result, ...)` | Đọc byte đầu rồi đọc các khối tới `total_bytes`; lấy riêng 4 byte CRC; cập nhật result và trả bytearray payload |
| `receive_dwt(ser, result, expected_mode)` | Đọc 16 byte đầu, nếu DWT2 thì đọc thêm 4; kiểm magic/mode/clock/chu kỳ CRC; cập nhật status và thời gian CPU; không trả giá trị |
| `receive_idle(ser, result)` | Đọc 8 byte, chỉ ghi `idle_count` nếu đúng `IDL1`; thiếu/sai thì giữ None |
| `crc_status(result)` | Trả `OK`, `SAI`, `CHƯA KIỂM TRA` theo độ đầy đủ và giá trị CRC |
| `cpu_load_percent(result)` | Trả `cpu_busy_seconds / total_seconds * 100`; không đủ dữ liệu thì None |
| `append_result(csv_path, row)` | Kiểm đúng thứ tự 13 trường; CSV có sẵn phải đúng header; thêm dòng hoặc tạo mới qua file tạm |
| `print_summary(result, ...)` | In cấu hình, kết quả, thời gian, hiệu suất, CRC, DWT, việc nền; không mở serial/đo lại |
| `save_csv(result, started_at, ...)` | Biến result thành dòng 13 cột, gọi append; trả bool báo lưu được hay không |
| `save_excel(csv_path)` | Import trễ exporter, tái tạo Excel từ các CSV cùng thư mục; lỗi được thông báo để CSV vẫn dùng được |
| `run_tx_test(...)` | Hàm điều phối nói ở phần 2, trả bool kết quả dữ liệu |

`ReceiveProgress.__init__` lưu mốc và interval; `update` chỉ in khi đủ khoảng; `finish` in lần cuối sau mốc đo đã chốt; `_print` dựng dòng số byte/phần trăm/thời gian. Việc in giữa chừng vẫn thuộc thời gian PC đang nhận nên nên tắt khi so sánh hiệu năng.

### Xử lý timeout khi đọc

`receive_data` dùng:

```text
timeout mỗi lần đọc = max(READ_TIMEOUT, READ_CHUNK_SIZE × 10 / baud × 2)
```

Nếu nhận ít hơn số byte yêu cầu trong một lần đọc thì ghi lỗi timeout và dừng. Mỗi lệnh đọc chỉ lấy số byte còn thiếu của payload, nên không cố ý ăn sang CRC. Phân tách chỉ đúng khi hai phía thống nhất độ dài và luồng không mất byte.

### Các trạng thái DWT

| Trạng thái | Cần hiểu |
| --- | --- |
| `NOT_RECEIVED` | Chưa thực hiện đọc báo cáo |
| `MISSING` | Không có byte DWT |
| `INVALID` | Thiếu gói/sai magic/mode ngoài miền/clock 0 hoặc CRC cycles lớn hơn tổng |
| `MODE_MISMATCH` | Mode hợp lệ nhưng khác bài script đang chạy |
| `WRAP_RISK` | Polling dài quá giới hạn một vòng DWT theo thời gian PC |
| `OK` | Các kiểm tra DWT hiện có đều qua; vẫn phải hiểu phạm vi đo |

## 4. Script PC gửi cho bài RX

Nguồn: [uart_test_dma_rx.py](../../TEST_PYTHON/uart_test_dma_rx.py).

`main()` dùng argparse, không lấy COM/baud từ các file TX:

| Tham số | Mặc định / mục đích |
| --- | --- |
| `--port` | COM13 |
| `--baud` | 1500000 |
| `--length` | 1000000, số byte payload khai báo |
| `--repeat` | Chỉ chấp nhận 1, vì firmware một khung/reset |
| `--truncate-to` | Cố ý gửi thiếu số byte payload để kiểm tra nhánh lỗi |

Các bước:

1. Kiểm tra tham số, tạo `header = struct.pack("<I", length)` và timeout ghi theo kích thước/baud.
2. Tạo result mặc định FAIL, mở serial 8N1, tắt flow control, xóa input buffer cũ.
3. `os.urandom(length)` sinh payload trên PC; `zlib.crc32(payload)` là CRC mong đợi.
4. Gửi `header + payload` hoặc phần payload bị cắt; kiểm tra giá trị trả `write`, gọi `flush` chờ đầu ra.
5. Đọc tối đa 64 byte tới newline. Kiểm ASCII, newline, đúng 4 trường RESULT, parse count và CRC.
6. Đạt khi status DONE, count bằng số đã gửi và bằng Length khai báo, CRC bằng CRC payload đầy đủ.
7. `finally` gọi `save_result(result)` ghi 11 cột vào CSV RX. Nếu lỗi, điểm vào in FAIL và thoát 1.

`save_result` chỉ ghi header khi file trống, thêm dòng lịch sử. Khác TX, script RX **chưa tự gọi xuất Excel**; chạy `uart_excel_report.py` sau đó để cập nhật sheet RX.

Thời gian RX đo từ trước khi `write` tới khi nhận phản hồi, gồm gửi header/payload, chờ đầu ra, độ trễ xử lý/phản hồi và đọc RESULT. Không so trực tiếp như thể đó là `payload_seconds` của TX.

## 5. Các cột CSV

### TX: 13 cột

| Cột | Nội dung |
| --- | --- |
| `thoi_diem` | Thời điểm lượt thử, có múi giờ |
| `phuong_phap`, `baud_rate` | Polling/Interrupt/DMA và baud yêu cầu |
| `so_byte_nhan` | Payload PC thực nhận |
| `thoi_gian_truyen_s` | Thời gian payload tại PC, không gồm CRC |
| `hieu_suat_phan_tram` | So tốc độ payload với baud/10 |
| `chu_ky_cpu_uart` | Tổng DWT trừ chu kỳ CRC32_Update |
| `chu_ky_cpu_crc` | Chu kỳ CRC32_Update |
| `tong_chu_ky_cpu` | Tổng DWT trong phạm vi đo |
| `tai_cpu_uoc_tinh_phan_tram` | Thời gian CPU tổng / thời gian payload + CRC PC |
| `so_tac_vu_nen` | Counter IDL1; 0 hợp lệ, trống là thiếu báo cáo |
| `trang_thai_crc` | OK / SAI / CHƯA KIỂM TRA |
| `ket_qua` | THÀNH CÔNG / THẤT BẠI theo tiêu chí dữ liệu/mode |

### RX: 11 cột

`thoi_diem, cong_com, baud_rate, so_byte_yeu_cau, so_byte_gui, so_byte_nhan, crc32_pc, crc32_stm32, thoi_gian_s, ket_qua, ghi_chu`.

Ba trường số byte phân biệt yêu cầu, PC đã ghi vào luồng và STM32 báo xử lý được. CRC giữ chuỗi hex để không mất số 0 đầu. FAIL có thể thiếu phản hồi, nên số nhận/CRC STM32 được để trống.

## 6. Bộ xuất Excel hoạt động ra sao?

Nguồn: [uart_excel_report.py](../../TEST_PYTHON/uart_excel_report.py).

| Hàm | Vai trò |
| --- | --- |
| `discover_csv_files(source)` | Tìm `uart_*_results.csv` trong thư mục nguồn; dù truyền một file vẫn đọc các file cùng mẫu trong thư mục |
| `feature_name(csv_path)` | Biến tên file thành nhãn, như `uart_it_tx_results.csv` → `INTERRUPT TX` |
| `read_results(csv_path)` | Kiểm schema TX, parse số/thời điểm, giữ trống là None, sort baud rồi thời gian |
| `read_rx_results(csv_path)` | Đọc schema RX riêng, giữ CRC text, kiểm dữ liệu, sort |
| `style_sheet(...)` | Định dạng tiêu đề, cột, table, freeze pane, màu; giữ chuỗi là text |
| `add_detail_sheet(...)` | Một sheet chi tiết cho mỗi tính năng TX, mỗi lượt một dòng |
| `build_workbook(feature_results)` | Sheet Tổng hợp và các sheet TX; nhóm theo tính năng/baud, đếm lượt và tính trung bình lượt thành công |
| `average(key)` | Hàm nội bộ trong build: chỉ lấy ô có giá trị trong các lượt thành công |
| `add_rx_sheet(workbook, results)` | Thêm DMA RX riêng, không trộn phép đo RX vào thống kê TX |
| `export_excel(csv_path, excel_path)` | Đọc tất cả nguồn hợp lệ, tạo workbook, ghi file tạm rồi thay file đích; trả Path |
| `main()` | Nhận source/`--output`, gọi exporter, in kết quả và trả mã 0/1 |

Workbook mặc định là `TEST_PYTHON/uart_summary.xlsx`. Báo cáo hiện có **bảng**, chưa tạo chart. Mỗi lần xuất là tạo lại từ CSV, nên biểu đồ/chỉnh tay trong workbook có thể mất khi xuất lại. Nếu thêm biểu đồ bằng Excel, nên lưu bản báo cáo cuối sang tên riêng.

Trung bình chỉ dùng các lượt THÀNH CÔNG; số lượt CRC hợp lệ được đếm độc lập. Ô trống không coi là 0. Sheet không tự biết firmware version hoặc mọi trạng thái DWT, nên cần lọc lượt đo phù hợp trước khi rút kết luận.

Nếu CSV sai schema hoặc dữ liệu, exporter dừng và giữ Excel cũ. Nếu Excel đang mở và bị khóa, cập nhật có thể thất bại; CSV vừa đo vẫn là dữ liệu nguồn.

## 7. Test offline kiểm được những gì?

Nguồn: [test_uart_offline.py](../../TEST_PYTHON/test_uart_offline.py).

| Hàm test | Nội dung |
| --- | --- |
| `serial_stream(data)` | Tạo mock serial đọc tuần tự từ bytes, không phải test phần cứng |
| `test_crc_and_formulas` | CRC mẫu, trạng thái CRC và công thức tải |
| `test_dwt_and_idle_frames` | DWT1/2, mode sai, gói thiếu/sai, wrap, IDL1 |
| `test_receive_timeouts_and_timing` | Thiếu byte/CRC, mốc payload và CRC |
| `test_tx_scripts_success_and_failures` | Ba script TX với nhánh thành công/lỗi giả lập |
| `test_rx_protocol_and_response_errors` | RESULT đúng/sai/timeout và ghi PASS/FAIL |
| `test_report_schema_and_atomic_errors` | Header, dữ liệu, lỗi xuất và giữ file cũ |
| `test_report_accepts_rx_with_tx` | Nguồn TX/RX cùng thư mục, sheet RX riêng và các trường đặc thù |

Test offline giúp kiểm logic PC nhưng không chạy firmware C, không đo tín hiệu UART, không kiểm DMA race/overrun và không chứng nhận USB-UART hoạt động ở baud cao.
