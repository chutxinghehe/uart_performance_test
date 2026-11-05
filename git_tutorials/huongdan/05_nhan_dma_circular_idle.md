# 05 — Nhận độ dài thay đổi bằng DMA circular + IDLE

[Mục lục](README.md) · [Tiếp: CRC, DWT và tải CPU](06_crc_dwt_va_tai_cpu.md)

Nguồn: [uart_rx_dma.c](../../RX_UART_Lib/uart_rx_dma.c), [uart_rx_dma.h](../../RX_UART_Lib/uart_rx_dma.h), [HAL UART đi kèm](../../Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c).

## 1. Bài RX nhận gì?

PC gửi một khung mỗi lần reset:

```text
Length: uint32 little-endian, 4 byte | Payload: đúng Length byte
```

Ví dụ Length = 1000 có header `E8 03 00 00`. Header cho biết số byte payload, không tính chính 4 byte header. PC không gửi CRC trailer trong bài RX này. STM32 tự tính CRC trên payload rồi trả:

```text
RESULT,DONE,<số byte payload>,<CRC32 dạng 8 ký tự hex>\r\n
```

PC đã giữ payload gốc nên tự tính CRC để đối chiếu với CRC STM32 trả về. Đây là giao thức khác TX, không có DWT2 hoặc IDL1 trong phản hồi RX hiện tại.

## 2. Một buffer, hai nửa A/B

```text
rx_buf[1024]
┌──────────────────────────┬──────────────────────────┐
│ A: chỉ số 0..511         │ B: chỉ số 512..1023       │
└──────────────────────────┴──────────────────────────┘
             HT ở 512                  TC ở 1024
DMA: 0 → ... → 1023 → 0 → ...
```

Đây là một mảng circular chia hai vùng để xử lý theo kiểu ping-pong bằng phần mềm. Mã không cấu hình hai địa chỉ bộ nhớ DMA độc lập và không có hai mảng `bufferA`/`bufferB` riêng. Khi bảo vệ cần nói rõ cách dùng từ “double buffer” của project.

HT và TC báo tiến độ đều đặn khi luồng liên tục. IDLE giúp lấy phần dư chưa đủ nửa buffer khi PC tạm dừng hoặc kết thúc. Trong HAL circular đang dùng, các sự kiện HT/TC/IDLE không tự dừng nhận; chương trình không gọi lại ReceiveToIdle sau từng callback.

## 3. Những biến theo dõi dòng dữ liệu

| Biến | Ý nghĩa |
| --- | --- |
| `rx_buf` | Vùng RAM DMA ghi dữ liệu mới |
| `last_size` | Vị trí được callback trước báo, để tính lượng đến mới |
| `dma_pos` | Vị trí mới nhất callback báo, không phải lúc nào cũng là vị trí DMA tức thời |
| `process_pos` | Mốc main đã xử lý đến; phần trước mốc đã đọc |
| `new_data_ready` | Cờ báo có cập nhật vị trí; không phải hàng đợi từng sự kiện |
| `callback_count` | Số lần callback RX được gọi, không phải số gói ứng dụng |
| `total_received` | Tổng byte ước tính từ chênh lệch các vị trí callback; gồm cả Length |
| `rx_length`, `rx_length_bytes` | Length đã ghép và số byte header đã nhận |
| `rx_payload_bytes` | Payload parser đã xử lý; không gồm Length |
| `rx_crc32` | CRC phần mềm tích lũy của payload |
| `rx_done` | Parser đã đủ payload theo Length |
| `cpu_cycles_A/B`, `cpu_time_us_A/B` | Thời gian đoạn xử lý gần nhất được gán vào nhóm A/B, không phải tổng cả phiên |

Phân biệt `total_received` và `rx_payload_bytes`: DMA có thể nhận byte vào RAM trước khi main xử lý nó. Đếm dữ liệu đã vào không tự chứng minh parser xử lý đúng và không bị ghi đè.

## 4. `UART_RX_DMA_Start()`

Hàm gọi:

```c
HAL_UARTEx_ReceiveToIdle_DMA(&huart1, rx_buf, RX_BUF_SIZE);
```

Nếu HAL trả lỗi thì vào `Error_Handler`. Mode circular đã được đặt trong `usart.c`, không phải tên ReceiveToIdle tự biến DMA thành circular.

Hàm Start hiện không xóa các vị trí, cờ, Length, CRC và done để tạo phiên mới. Các biến bắt đầu từ trạng thái khởi tạo nhờ reset MCU. Vì vậy chỉ gọi lại Start không đủ tạo lại một bài RX sạch sau khi đã chạy xong.

## 5. `HAL_UARTEx_RxEventCallback(huart, Size)`

Callback có thể đến từ HT, TC hoặc IDLE; chương trình hiện không gọi `HAL_UARTEx_GetRxEventType` để phân biệt loại.

Với 8N1, `Size` là mốc dữ liệu trong buffer: các byte mới nhất được báo nằm trước mốc đó. Nó không phải “số byte mới kể từ callback trước”. HT thường báo 512, TC báo 1024; IDLE có thể báo vị trí giữa chừng.

Hàm kiểm tra đúng USART1, tăng `callback_count`, tính:

```text
Nếu Size >= last_size: delta = Size - last_size
Nếu Size < last_size:  delta = (1024 - last_size) + Size
```

Sau đó cộng delta vào `total_received`, cập nhật `dma_pos = Size`, bật `new_data_ready`, lưu `last_size = Size`.

Ví dụ callback báo 512 rồi 700: có thêm 188 byte. Báo 900 rồi 120: đi qua đuôi buffer, thêm 124 + 120 = 244 byte. Mốc TC 1024 hợp lệ để main đọc đến hết chỉ số 1023; đừng tự dùng 1024 làm chỉ số truy cập mảng.

Callback giữ ngắn: chỉ cập nhật trạng thái, không tính CRC từng byte ở đây. CPU sẽ xử lý ở main.

## 6. `UART_RX_DMA_Process()` đọc phần mới thế nào?

Nếu chưa có cờ, trả về ngay. Nếu có, xóa cờ, lấy `pos = dma_pos`. Nếu `pos == process_pos`, trả về. Nếu khác, xét hai trường hợp.

### Trường hợp 1: `pos > process_pos`, chưa qua đuôi buffer

Phần cần đọc là `[process_pos, pos)`: gồm đầu, không gồm cuối. Chương trình chia theo ranh giới 512.

Ví dụ `process_pos = 400`, `pos = 700`:

```text
Đọc A: rx_buf[400..511] → 112 byte
Đọc B: rx_buf[512..699] → 188 byte
Tổng 300 byte → process_pos = 700
```

Mỗi đoạn có DWT trước/sau. Mỗi byte đọc được đưa vào `UART_RX_ProcessByte`.

### Trường hợp 2: `pos < process_pos`, đã qua đuôi buffer

Đọc đuôi trước, đầu sau để giữ đúng thứ tự byte.

Ví dụ `process_pos = 900`, `pos = 120`:

```text
rx_buf[900..1023] → 124 byte
rx_buf[0..119]   → 120 byte
Tổng 244 byte → process_pos = 120
```

Sau khi xử lý xong, gán `process_pos = pos`. Đừng đảo thứ tự hai đoạn khi ghép CRC: CRC phụ thuộc thứ tự byte.

Tên biến thời gian A/B chỉ phản ánh đoạn mã được gán: trong nhánh wrap, mã gán cả đoạn đuôi vào B và cả đoạn đầu vào A; các đoạn đó có thể vượt ranh giới nửa buffer nếu main đã chậm. Không mặc định mỗi số thời gian luôn đo đúng 512 byte.

## 7. `UART_RX_ProcessByte(data)` là bộ phân tích khung

Hàm `static`, chỉ gọi bên trong file RX.

1. Nếu `rx_done` đã bật, bỏ qua byte tiếp theo.
2. Nếu chưa có đủ 4 byte Length: ghép `data << (8 * rx_length_bytes)` vào `rx_length` rồi tăng số byte header.
3. Sau header: cập nhật `rx_crc32 = CRC32_ZlibUpdate(rx_crc32, &data, 1)` và tăng `rx_payload_bytes`.
4. Khi có đủ header và `rx_payload_bytes == rx_length`, bật `rx_done`.

Length = 0 hoàn tất ngay khi nhận xong byte header thứ tư; CRC payload rỗng giữ bằng 0. Length lẻ như 513 vẫn hợp lệ vì CRC RX xử lý từng byte, không có ràng buộc chia hết cho 4 như CRC TX.

Parser giữ trạng thái giữa các lần xử lý nên header/payload có thể nằm vắt qua nhiều callback, nhiều nửa hoặc nhiều vòng buffer. IDLE không reset parser. Khi nhận thiếu payload, parser chờ tiếp, chưa gửi DONE.

## 8. main gửi RESULT

Trong mode RX, main luôn gọi Process. Khi `rx_done == 1` và `rx_result_sent == 0`, dùng `snprintf` tạo dòng RESULT trong mảng 64 byte, kiểm tra không lỗi/tràn rồi truyền polling với timeout 100 ms. Sau đó đặt cờ đã gửi.

Kết quả báo đúng một lần sau reset. DMA vẫn có thể đang chạy circular; parser bỏ qua dữ liệu sau done. Mã chưa có giao thức nhiều khung liên tục, lệnh reset phiên hay phản hồi NACK cho khung lỗi.

## 9. Vì sao chưa được khẳng định “không mất byte” chỉ từ việc dùng DMA?

Ở 921600 baud theo giá trị danh định:

```text
512 byte cần 512 × 10 / 921600 ≈ 5,556 ms
1024 byte cần ≈ 11,111 ms
```

Khi DMA vừa ghi xong A và bắt đầu B, main có khoảng một nửa vòng để xử lý A trước khi DMA quay lại ghi đè. Đây là ngân sách thời gian tham khảo; độ trễ IRQ/main và các việc khác đều chiếm ngân sách. Ở 1.500.000 baud, nửa buffer chỉ khoảng 3,413 ms.

Các giới hạn đang có:

- **Chỉ lưu vị trí cuối và một cờ.** Nếu main chậm qua nhiều sự kiện, các mốc trung gian bị gộp. Cờ 1 không cho biết có bao nhiêu lần quay vòng.
- **Vị trí bằng nhau chưa đủ kết luận không có dữ liệu mới.** DMA có thể quay trọn vòng và về cùng mốc. Không có bộ đếm vòng/overrun độc lập để phân biệt.
- **Không khóa vùng dữ liệu đang đọc.** DMA vẫn ghi; nếu main tụt lại, dữ liệu cũ có thể bị thay trước khi parser đọc.
- **Cặp thao tác main/ngắt chưa được đồng bộ đầy đủ.** `volatile` không biến chuỗi xóa cờ/lấy vị trí/cập nhật vị trí thành một snapshot nguyên tử. Cần xem xét các thời điểm ngắt chen vào; không coi cờ là cơ chế đồng bộ hoàn chỉnh.
- **Chưa có phục hồi lỗi RX.** Callback lỗi trong main không báo/khởi động lại RX; chưa có timeout Length ở firmware, giới hạn độ dài ứng dụng hoặc cơ chế tìm lại đầu khung.
- **CRC phần mềm chạy mỗi byte** là một phần tải CPU cần đo, không mặc định đủ nhanh trong mọi cấu hình.

Đây là rủi ro cần kiểm tra, không phải kết luận mọi lượt RX đều sẽ lỗi. Để chứng minh yêu cầu, phải chạy 1 MB ở 921600, kiểm số byte và CRC nhiều lượt, thử qua ranh giới vòng đệm và quan sát deadline xử lý.

Hướng cải tiến nếu đề tài yêu cầu độ tin cậy cao hơn: theo dõi producer/consumer và số vòng, phát hiện overrun; quản lý quyền sử dụng nửa buffer hoặc sao chép sang hàng đợi có dung lượng tính toán; snapshot trạng thái ngắn có đồng bộ; thêm timeout và đường phục hồi. Những mục này là đề xuất, chưa phải chức năng đã có.
