# Kiểm tra UART và báo cáo Excel

Firmware có TX polling, TX interrupt, TX DMA và RX DMA circular + IDLE.
Thay đổi idle v2 chỉ áp dụng TX; giao thức, xử lý và CSV RX giữ nguyên.

## Thay đổi idle v2

- Sau khởi tạo GPIO/UART, gọi `CPULoad_Calibrate()` một lần trước bài TX.
- Hiệu chuẩn khoảng 1 giây và khi truyền đều gọi cùng `CPULoad_IdleStep()`:
  tăng bộ đếm idle và toggle PC13.
- `idle_result` = số vòng idle trong lượt đo.
- `idle_elapsed_ms` = thời lượng đo trên STM32, đơn vị ms.
- `idle_max_count` = số vòng idle hiệu chuẩn mỗi giây.
- `payload_bytes_sent` = số byte payload đã phát xong, không gồm CRC.
- `payload_elapsed_ms` = thời gian phát payload trên STM32.

Mốc bắt đầu đặt ngay trước lời gọi HAL phát khối payload đầu tiên, sau khi sinh khối đầu.
Polling chốt sau khi HAL đợi TC cho khối payload cuối; IT/DMA chốt tại callback USART TC
của khối payload cuối, trước khi tính CRC cuối và phát trailer CRC.
Cửa sổ idle và cửa sổ thời gian payload trùng nhau. Thời gian này gồm khoảng trống giữa
các khối, sinh dữ liệu/CRC của khối trước; không gồm CRC của khối cuối, trailer CRC,
báo cáo DWT/idle hoặc hiệu chuẩn. Main chỉ chạy idle đến khi payload cuối phát xong.
Polling blocking nên số vòng idle bằng 0, tải CPU ước tính 100% khi dữ liệu đo hợp lệ.

```text
idle_pct = idle_result / (idle_max_count * idle_elapsed_ms / 1000) * 100
tai_cpu_pct = 100 - idle_pct
thoi_gian_payload_stm32_s = payload_elapsed_ms / 1000
toc_do_payload_stm32_byte_s = payload_bytes_sent / thoi_gian_payload_stm32_s
```

Thiếu thống kê, chuẩn bằng 0 hoặc thời lượng idle bằng 0: để trống tải CPU.
Nếu idle_pct ngoài [0, 100], ghi `OUT_OF_RANGE`, giữ số đếm thô và để trống tải CPU;
không ép số về 0/100 để che sai lệch hiệu chuẩn. Thời gian payload STM32 bằng 0 thì
để trống tốc độ. `IDL1` firmware cũ chỉ có count, không đủ tính % CPU mới.
DWT giữ để xem chu kỳ riêng, không dùng DWT hoặc thời gian PC để tính tải CPU.

## Giao thức TX

```text
Payload → CRC 4 byte → DWT2 20 byte → IDL2 24 byte
```

DWT2 giữ nguyên: magic, mode, tổng chu kỳ, chu kỳ CRC32_Update và HCLK (uint32 little-endian).
IDL2 gồm magic 4 byte và 5 uint32 little-endian theo thứ tự:

| Trường | Ý nghĩa |
| --- | --- |
| idle_result | Số vòng idle trong cửa sổ payload |
| idle_elapsed_ms | Thời lượng idle STM32 (ms) |
| idle_max_count | Số vòng idle hiệu chuẩn mỗi giây |
| payload_bytes_sent | Số byte payload đã phát xong |
| payload_elapsed_ms | Thời gian phát payload STM32 (ms) |

Payload, CRC và cách chọn chế độ test giữ nguyên. Mỗi reset chạy một lượt.

## Phân biệt thời gian PC và STM32

- `thoi_gian_nhan_payload_pc_s`: giữ cách đo PC hiện tại, bắt đầu sau khi đọc được byte
  đầu tiên và kết thúc sau khi đọc đủ payload. Đây là thời gian nhận payload tại PC,
  chịu ảnh hưởng USB-UART, bộ đệm và hệ điều hành.
- `hieu_suat_nhan_pc_phan_tram`: hiệu suất từ thời gian nhận PC so với UART lý thuyết.
- `thoi_gian_payload_stm32_s`: thời gian phát payload đo bằng HAL_GetTick trên STM32.
- `toc_do_payload_stm32_byte_s`: payload STM32 báo đã phát chia thời gian STM32.
- Không lấy thời gian PC để suy ra thời gian phát STM32 hoặc tải CPU.

## File kết quả và nhóm so sánh

Sửa idle v2 tạo file mới; không chuyển đổi, sửa hoặc ghi nối vào CSV TX cũ:

| Bài TX | CSV mới |
| --- | --- |
| Polling | uart_polling_tx_v2_results.csv |
| Interrupt | uart_it_tx_v2_results.csv |
| DMA | uart_dma_tx_v2_results.csv |

Excel mới: **TEST_PYTHON/uart_summary_v2.xlsx**. `backup/uart_summary.xlsx` cũ giữ nguyên;
bộ xuất từ chối ghi vào tên đó. CSV v2 khởi đầu chỉ có header, không thêm kết quả giả.
Bộ ghi CSV kiểm tra header trước khi nối, không trộn schema cũ/mới.

Các kết quả TX cũ đã chuyển nguyên nội dung vào `TEST_PYTHON/backup/`:
`uart_polling_tx_results.csv`, `uart_it_tx_results.csv`, `uart_dma_tx_results.csv`
và `uart_summary.xlsx`. Cache Python cũ cũng nằm trong `backup/__pycache__/`;
Python có thể tự tạo cache mới khi chạy. Các script, test, kết quả v2 và CSV RX vẫn
ở thư mục chính. Bộ xuất không quét thư mục backup.

Schema TX v2 theo thứ tự:

```text
thoi_diem,phuong_phap,baud_rate,so_byte_payload_yeu_cau,
so_byte_nhan,thoi_gian_nhan_payload_pc_s,hieu_suat_nhan_pc_phan_tram,
chu_ky_cpu_uart,chu_ky_cpu_crc,tong_chu_ky_cpu,tai_cpu_uoc_tinh_phan_tram,
so_vong_lap_idle,idle_elapsed_ms,idle_max_count,so_byte_payload_stm32,
thoi_gian_payload_stm32_s,toc_do_payload_stm32_byte_s,tan_so_cpu_hz,
trang_thai_dwt,trang_thai_do_idle,trang_thai_crc,ket_qua
```

`so_tac_vu_nen` đổi thành `so_vong_lap_idle` trong schema mới; dữ liệu cũ giữ tên cũ.
Bảng chi tiết giữ từng lượt kể cả thất bại. Tổng hợp chỉ lấy trung bình lượt THÀNH CÔNG,
tách theo phương pháp, baud, payload yêu cầu và clock CPU. Ô thiếu không coi
là 0. DWT không hợp lệ/WRAP_RISK không đưa vào trung bình DWT; tải CPU idle độc lập DWT.

Python không còn tạo nhãn hay cột cấu hình đo. Bản CSV/Excel v2 trước khi bỏ cột
được lưu nguyên nội dung tại `backup/before_remove_measurement_config/`.

Bộ xuất chỉ quét TX `uart_*_v2_results.csv`, không gộp TX cũ dùng công thức DWT/PC.
CSV DMA RX vẫn có sheet riêng khi tồn tại, không tham gia thống kê TX.
PASS TX vẫn dựa vào đủ payload/CRC, CRC khớp và không sai mode; v2 kiểm tra thêm số byte
STM32 nếu có báo cáo. Thiếu thống kê idle vẫn có thể truyền PASS, nhưng tải CPU/tốc độ
STM32 chưa đo được để trống và có cột trạng thái riêng.

## Chạy kiểm tra và xuất báo cáo

```powershell
.\.venv\Scripts\python.exe TEST_PYTHON/uart_test_polling_tx.py
.\.venv\Scripts\python.exe TEST_PYTHON/uart_test_it_tx.py
.\.venv\Scripts\python.exe TEST_PYTHON/uart_test_dma_tx.py
# Chỉ xuất báo cáo v2, không mở UART:
.\.venv\Scripts\python.exe TEST_PYTHON/uart_excel_report.py
# Kiểm thử trong thư mục tạm, không mở UART thật:
.\.venv\Scripts\python.exe -B -X utf8 -m unittest discover -s TEST_PYTHON -p 'test_uart*.py' -v
```

Cài môi trường nếu cần: `python -m pip install -r TEST_PYTHON/requirements.txt`.
Test firmware dùng GCC host và HAL giả để chạy C polling/IT/DMA, kiểm tra hiệu chuẩn
và chốt payload trước CRC; test này được bỏ qua nếu máy không có GCC.
Script TX tự lưu CSV và cập nhật Excel. Nếu Excel mới đang mở/khóa, CSV vẫn giữ;
đóng file và chạy lại bộ xuất. Nạp firmware mới để có IDL2 và hiệu chuẩn.

RX giữ cách chạy hiện có, mỗi reset một Length + Payload, CRC tương thích zlib:

```powershell
.\.venv\Scripts\python.exe TEST_PYTHON/uart_test_dma_rx.py --port COM13 --baud 1500000 --length 1000000
```

RX có `--truncate-to` để kiểm tra gửi thiếu; kết quả ở `uart_dma_rx_results.csv`.

## Giới hạn phép đo

- Tải CPU idle là ước tính suy giảm khả năng chạy vòng idle so với chuẩn. Nó gồm ảnh hưởng
  công việc/ngắt và kiểm tra điều kiện vòng main; không đếm chính xác mọi chu kỳ UART.
- Cùng CPULoad_IdleStep nhưng kiểm tra điều kiện vòng hiệu chuẩn/main khác nhau. Sai lệch
  cố định này, chi phí GPIO, tối ưu compiler và tải ngắt khác vẫn ảnh hưởng kết quả.
  Giữ cấu hình và chạy nhiều lượt để đánh giá độ dao động.
- HAL_GetTick có độ phân giải 1 ms; hiệu chuẩn khoảng 1 giây cũng bị lượng tử hóa tick.
  Điểm cuối được phần mềm ghi khi xử lý TC nên có độ trễ ngắt, không phải dấu thời gian
  phần cứng chính xác của cạnh stop bit. Lượt ngắn có sai số tương đối lớn.
- Tick/counter idle là uint32. Phép trừ tick unsigned xử lý quay vòng nếu lượt đo ngắn hơn
  khoảng 49,7 ngày. Counter idle có thể tràn sớm hơn trong lượt cực dài; không dùng các
  lượt có nguy cơ tràn để kết luận tải CPU.
- DWT polling vẫn có giới hạn 32 bit khoảng 59,65 s ở 72 MHz. Idle và thời gian HAL_GetTick
  mới không phụ thuộc vòng quay DWT. Không halt/single-step trong lúc đo.
- Kiểm thử offline chưa xác nhận độ chính xác hoặc độ ổn định thực tế trên bo mạch.
