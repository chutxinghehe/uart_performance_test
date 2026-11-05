# 06 — Giao thức, CRC, DWT và cách hiểu tải CPU

[Mục lục](README.md) · [Tiếp: Python và Excel](07_python_csv_excel.md)

## 1. Các trường trên đường truyền TX

Theo [uart_dwt.h](../../Core/Inc/uart_dwt.h), [main.c](../../Core/Src/main.c) và [uart_test_support.py](../../TEST_PYTHON/uart_test_support.py):

| Offset tính từ đầu luồng | Kích thước | Nội dung |
| --- | ---: | --- |
| 0 | 1.000.000 | Payload |
| 1.000.000 | 4 | CRC phần cứng, little-endian |
| 1.000.004 | 4 | ASCII `DWT2` |
| 1.000.008 | 4 | Mode: 1 polling, 2 IT, 3 DMA |
| 1.000.012 | 4 | Tổng chu kỳ CPU trong phạm vi đo |
| 1.000.016 | 4 | Chu kỳ gọi `CRC32_Update` |
| 1.000.020 | 4 | HCLK, Hz |
| 1.000.024 | 4 | ASCII `IDL1` |
| 1.000.028 | 4 | Số bước nền đã chốt |

Little-endian nghĩa là byte thấp gửi trước: `0x12345678` thành `78 56 34 12`. Python giải DWT2 bằng `struct.Struct("<4sIIII")`, IDL1 bằng `"<4sI"`. Dấu `<` là little-endian với kích thước chuẩn.

Python còn đọc được DWT1 cũ, chỉ 16 byte: magic + mode + tổng chu kỳ + HCLK. DWT1 không có chu kỳ CRC để tách phần CRC khỏi tổng. Firmware hiện tại gửi DWT2.

Không có bước quét tìm magic để tự đồng bộ lại nếu mất byte giữa luồng. Mất payload có thể kéo byte CRC/báo cáo vào vị trí sai; kiểm tra độ dài/CRC giúp phát hiện lượt lỗi.

## 2. CRC TX: ngoại vi STM32F1

Nguồn: [uart_crc.c](../../Core/Src/uart_crc.c).

| Hàm | Đầu vào / kết quả | Cách hoạt động |
| --- | --- | --- |
| `CRC32_Reset()` | Không có đầu vào | Bật clock CRC và ghi bit reset, trạng thái khởi đầu `0xFFFFFFFF` |
| `CRC32_Update(data, length)` | Con trỏ dữ liệu, độ dài chia hết 4; trả HAL_OK/HAL_ERROR | Ghép mỗi 4 byte thành word little-endian, ghi word vào `CRC->DR`; tích lũy tiếp CRC cũ |
| `CRC32_GetValue()` | Trả uint32 | Đọc `CRC->DR`, không reset |
| `CRC32_Compute(data, length, result)` | Tính độc lập một vùng | Kiểm tra tham số, Reset → Update → GetValue; hiện các luồng TX dùng tích lũy thay vì hàm tiện ích này |

TX dùng cách tính CRC phần cứng STM32F1, đa thức `0x04C11DB7`, xử lý word theo cách của ngoại vi. Python mô phỏng bằng `calculate_crc32_stm32`, không gọi `zlib.crc32` cho bài TX.

Điểm cần nhớ: Python hiện đệm 0 nếu độ dài chưa chia hết 4; firmware `CRC32_Update` lại từ chối độ dài đó. Với payload 1.000.000 và các chunk 256/64 thì hai bên khớp. Nếu sửa tổng TX thành 1.000.001 mà giữ nguyên thuật toán, khối cuối có thể lỗi vì không chia hết 4; chỉ sửa `TOTAL_BYTES` là chưa đủ.

Không reset CRC mỗi khối vì cần CRC của **toàn chuỗi ghép**. CRC trả về không phải tổng các CRC từng khối.

## 3. CRC RX: phần mềm tương thích zlib

`CRC32_ZlibUpdate(crc, data, length)` dùng đa thức phản chiếu `0xEDB88320`, XOR đầu/cuối `0xFFFFFFFF`, nhận CRC của các khối trước; bắt đầu bằng 0. Hàm xử lý mọi độ dài byte.

RX gọi cho từng byte payload và bỏ qua 4 byte Length khi tính CRC. PC gọi `zlib.crc32(payload)` trên payload gốc. Các lần update liên tiếp tương đương tính CRC một lần trên toàn payload.

| Bài | STM32 | Python | Dữ liệu đưa vào CRC |
| --- | --- | --- | --- |
| TX | CRC phần cứng qua word little-endian | `calculate_crc32_stm32` | Payload thực truyền/nhận |
| RX | `CRC32_ZlibUpdate` phần mềm | `zlib.crc32` | Payload, không có Length |

CRC khớp là bằng chứng mạnh để phát hiện sai dữ liệu trong thí nghiệm, nhưng CRC có thể va chạm; không phải chứng minh toán học tuyệt đối mọi byte đúng, không phải mã sửa lỗi hoặc cơ chế bảo mật. Project chưa tự truyền lại khi CRC sai.

## 4. DWT đo chu kỳ thế nào?

Nguồn: [dwt.c](../../RX_UART_Lib/dwt.c).

- `DWT_Init`: bật `CoreDebug->DEMCR.TRCENA`, xóa `DWT->CYCCNT`, bật `DWT->CTRL.CYCCNTENA`.
- `DWT_GetCycles`: đọc CYCCNT hiện tại.
- `DWT_CyclesToUs`: chia `cycles / (SystemCoreClock / 1000000U)`, kết quả nguyên nên mất phần lẻ microsecond.

Đo một đoạn:

```c
uint32_t start = DWT->CYCCNT;
/* đoạn cần đo */
uint32_t elapsed = DWT->CYCCNT - start;
```

CYCCNT tăng theo thời gian lõi chạy; nó không tự phân loại chu kỳ “UART”, “idle” hoặc “CRC”. Việc chọn vị trí bắt đầu/kết thúc mới quyết định số đo là gì. Khoảng đo có thể gồm ngắt khác chen vào.

## 5. Phạm vi DWT từng phương pháp

| Phương pháp | Có trong tổng đang báo | Chưa tính đầy đủ / ngoài phạm vi |
| --- | --- | --- |
| Polling | Toàn khoảng sinh payload, HAL chờ UART, CRC, gửi CRC trailer | Reset CRC/trạng thái trước mốc bắt đầu, gửi DWT/IDL1 |
| IT | Sinh khối đầu, HAL khởi động, tổng khoảng HAL/callback trong IRQ USART | Khởi tạo/reset CRC, phần cứng vào/ra IRQ, đường gọi ngoài wrapper, phần main; gửi báo cáo |
| DMA | Sinh khối đầu, HAL khởi động, khoảng HAL trong IRQ DMA và USART, gồm callback | Tương tự IT; không bao toàn thời gian DMA tự chạy trên dây |

Sinh khối tiếp và CRC trong callback đã nằm trong tổng IRQ. Mỗi lời gọi `CRC32_Update` được đo riêng để phân tích chi phí:

```text
C_total = tổng chu kỳ đã đo, có CRC
C_crc = chu kỳ CRC32_Update, là một phần của C_total
C_uart = C_total - C_crc
```

Tên `C_uart` không có nghĩa chỉ gồm nạp byte UART: nó vẫn gồm sinh dữ liệu, đóng gói/gửi CRC trailer và overhead trong phạm vi đo. Không cộng `C_crc` vào `C_total` lần nữa.

## 6. Hai mốc thời gian tại PC

`receive_data` chờ byte đầu bằng `ser.read(1)`, rồi mới lấy `start_time`:

```text
Chờ người dùng reset → nhận byte đầu → start_time
  → nhận hết payload → payload_finished
  → nhận 4 byte CRC → crc_finished
  → đọc DWT/IDL1 → tính CRC trên PC → ghi báo cáo
```

- `payload_seconds = payload_finished - start_time`: CSV gọi là `thoi_gian_truyen_s`.
- `total_seconds = crc_finished - start_time`: dùng ở công thức ước tính CPU.
- `observed_seconds`: thời gian tới khi dừng; nếu lỗi có thể gồm thời gian chờ timeout.

Không cộng thời gian người dùng chờ reset, đọc báo cáo hoặc tính CRC PC vào thời gian dữ liệu. Tuy nhiên byte đầu đã tới trước mốc bắt đầu, có buffering USB/OS và thời gian in tiến trình nếu bật. Đây là phép đo tại ứng dụng PC, không phải đo chính xác cạnh đầu/cuối trên dây.

## 7. Công thức đang dùng

```text
T_CPU = C_total / f_CPU
T_CRC = C_crc / f_CPU
T_UART = (C_total - C_crc) / f_CPU

Tải CPU ước tính (%) = T_CPU / T_payload_và_CRC_đo_tại_PC × 100
Tốc độ payload = N / T_payload_đo_tại_PC
Hiệu suất (%) = (N × 10 / baud) / T_payload_đo_tại_PC × 100
```

Ví dụ minh họa, không phải số liệu mới đo: tổng 14.400.000 chu kỳ, HCLK 72.000.000 Hz → CPU phục vụ bài đo 0,2 s. PC đo 11 s thì tỷ lệ khoảng 1,82%.

Con số đó không phải tổng mức CPU toàn hệ thống. Trong lúc truyền DMA, main vẫn chạy tác vụ nền rất nhiều; CPU có thể vẫn hoạt động liên tục, chỉ là ít thời gian dành cho phục vụ UART. Không nói “DMA tải 2% nên CPU ngủ 98%” với mã hiện tại.

Sai lệch mốc PC và MCU có thể làm polling hơi vượt 100%; CSV hiện có các giá trị khoảng 100,00x%. Không cắt số về 100 để che sai số. Ghi công thức, nguồn thời gian và sai số, dùng logic analyzer để đối chiếu.

## 8. Idle counter và GPIO

Nguồn: [cpu_load.c](../../Core/Src/cpu_load.c).

`CPULoad_IdleStep()` làm hai việc: tăng `idle_counter` và toggle **PC13**. Nó là một bước việc nền giả lập; không phải lệnh ngủ hay nhàn rỗi thực sự. IT/DMA gọi trong main lúc chưa done; polling không gọi trong khoảng truyền.

`CPULoad_Calibrate()` có sẵn: đếm/toggle cùng kiểu trong khoảng 1000 ms, lưu `idle_max_count`, xóa counter để chuẩn bị lượt sau. **main hiện không gọi hàm này**, nên không có mốc hiệu chuẩn idle hợp lệ từ luồng chạy hiện tại.

Nếu thiết kế thêm phép đo bằng idle, công thức tham khảo là:

```text
R0 = số bước/giây khi chưa chạy UART, cùng clock/compiler/tác vụ nền
R  = số bước trong lượt / số giây của cùng cửa sổ đo
Tải theo suy giảm việc nền ≈ (1 - R/R0) × 100%
```

Đây là phương pháp đề xuất, không phải cách Python hiện tính cột tải CPU. Không so sánh raw counter giữa hai baud khi thời gian khác nhau rồi kết luận tải; cần ít nhất xét số bước trên giây.

Một số comment trong `cpu_load.h/.c` nhắc PA1; câu lệnh GPIO thực tế dùng PC13 và `gpio.c` cũng cấu hình PC13. Đấu logic analyzer theo mã thực thi. Mỗi lần toggle là một cạnh; một chu kỳ sóng vuông gồm hai bước nền, không phải một.

## 9. Tràn bộ đếm 32 bit

Ở 72 MHz:

```text
2^32 / 72.000.000 ≈ 59,652324 s
```

Phép trừ uint32 cho khoảng ngắn vẫn đúng qua điểm quay vòng nếu khoảng thực nhỏ hơn một vòng. Nhưng polling đo một khoảng dài liên tục: 1 MB ở 115200 danh định cần khoảng 86,806 s, vượt một vòng nên số chu kỳ cuối bị mất vòng.

Python đánh dấu `WRAP_RISK` với polling nếu thời gian PC ≥ một vòng; giữ chu kỳ thô nhưng không đổi thành thời gian/tải. IT/DMA cộng nhiều đoạn đo ngắn nên CYCCNT quay vòng **giữa** các IRQ không tự làm sai hiệu mỗi đoạn. Tuy nhiên từng đoạn và tổng tích lũy vẫn phải không vượt giới hạn biểu diễn.

CSV TX không lưu trạng thái DWT trong cột riêng; bộ tổng hợp hiện có thể lấy cả chu kỳ thô của lượt thành công về CRC để tính trung bình. Do đó bảng báo cáo phải xét lại tính hợp lệ của phép đo, nhất là baud thấp hoặc lịch sử từ firmware khác.
