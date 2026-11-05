# 04 — Luồng truyền polling, interrupt và DMA

[Mục lục](README.md) · [Tiếp: RX circular + IDLE](05_nhan_dma_circular_idle.md)

## 1. Phần chung của cả ba bài

Nguồn: [polling.c](../../nhung/polling.c), [interrup.c](../../nhung/interrup.c), [dma1.c](../../nhung/dma1.c).

```text
Payload 1.000.000 byte → CRC phần cứng 4 byte → DWT2 20 byte → IDL1 8 byte
```

Không có header Length trong giao thức TX. Python phải biết trước `TOTAL_BYTES = 1_000_000` để tách payload khỏi CRC/báo cáo. Tổng luồng TX hiện tại là 1.000.032 byte.

Mỗi khối tối đa 256 byte:

```text
1.000.000 = 3906 × 256 + 64
→ 3907 khối payload, khối cuối 64 byte
```

CRC phần cứng được tích lũy qua các khối, chỉ reset trước phiên, không reset trước mỗi khối. Các độ dài 256 và 64 đều chia hết cho 4 nên phù hợp `CRC32_Update`.

`UART_GenerateData(buffer, length, &state)` dùng xorshift32:

```c
value ^= value << 13;
value ^= value >> 17;
value ^= value << 5;
buffer[i] = (uint8_t)(value >> 24);
```

Hàm giữ state cuối qua con trỏ để lần gọi sau sinh tiếp. Không giữ nguyên seed đầu cho mọi khối. Seed polling/DMA đang là `123456789U`, IT là `123456879U`: các bài không có payload giống hệt nhau. Python kiểm CRC từ dữ liệu nhận được nên không cần biết seed. Khi muốn thí nghiệm cùng mẫu dữ liệu hoàn toàn, cần thống nhất seed trước khi đo lại.

## 2. Polling: theo chân `UART_Polling_Transmit()`

1. Xóa bộ đếm byte và chu kỳ; reset CRC.
2. Tạo buffer cục bộ 256 byte và seed.
3. Bật/xóa DWT; lấy chu kỳ bắt đầu.
4. Trong khi chưa đủ 1.000.000 byte: chọn kích thước khối, sinh dữ liệu, gọi `HAL_UART_Transmit(..., HAL_MAX_DELAY)`.
5. Sau khi HAL trả `HAL_OK`, đo riêng `CRC32_Update` của khối vừa gửi, rồi tăng `byte_sent`.
6. Hết payload: đọc CRC, tách thành 4 byte little-endian và truyền chặn.
7. Chốt tổng DWT và gọi `UART_Test_IdleStop`.
8. Gửi DWT2 bằng `UART_SendDWTResult`, trả trạng thái về main. Main gửi tiếp IDL1.

```text
main gọi ── sinh → chờ UART → CRC → ... → CRC trailer → chốt đo → DWT ── trả về
```

**Blocking** nghĩa là hàm gọi chưa trả về để main chạy tiếp. Ngắt hệ thống vẫn có thể xảy ra; blocking không có nghĩa tắt mọi ngắt. Trong mã hiện tại, không có lời gọi `CPULoad_IdleStep` bên trong bài polling nên counter nền bằng 0.

Buffer cục bộ an toàn ở đây vì các lệnh truyền đều chờ xong trước khi dùng lại buffer hoặc rời hàm. Nếu đổi sang truyền bất đồng bộ rồi trả về ngay thì không thể giữ giả định đó.

Nếu HAL truyền hoặc cập nhật CRC lỗi, hàm chốt số chu kỳ hiện có và trả lỗi. Main gọi `Error_Handler`. Không có cơ chế retransmit tự động.

## 3. IT: khởi động một lần rồi callback nối tiếp

### 3.1. Các biến cần hiểu

| Biến | Ý nghĩa |
| --- | --- |
| `tx_buffer[256]` | Buffer static còn tồn tại sau khi hàm khởi động trả về |
| `byte_sent_it` | Số byte payload đã giao cho HAL, không phải số byte đã xác nhận phát hết ngay tại thời điểm tăng |
| `pending_size` | Kích thước khối đang chờ hoàn tất, dùng tính CRC đúng số byte |
| `crc_sending` | Đang truyền CRC trailer; callback kế tiếp sẽ đánh dấu xong |
| `truyen_done_it` | Payload và CRC trailer đã phát xong |
| `truyen_loi_it` | Có lỗi khi khởi động/truyền/cập nhật CRC |
| `cpu_busy_cycle_it` | Tổng chu kỳ các đoạn phục vụ bài IT được đo |
| `cpu_crc_cycles_it` | Chu kỳ `CRC32_Update`, đã nằm trong tổng |

### 3.2. `UART_Interrup_Transmit()`

Reset DWT, cờ, bộ đếm, CRC và seed. Sinh khối đầu, cộng chi phí sinh vào tổng. Đặt `pending_size = 256`. Lưu PRIMASK rồi tắt ngắt tạm thời, đo lời gọi `HAL_UART_Transmit_IT`, tăng số byte được giao nếu thành công, sau đó khôi phục PRIMASK cũ.

Đoạn khóa ngắt ngắn này giúp IRQ đầu không chen vào phép đo khởi động và cập nhật biến. Nó không kéo dài suốt quá trình truyền. Khôi phục trạng thái cũ tốt hơn bật ngắt vô điều kiện khi hàm được gọi từ bối cảnh vốn đã khóa ngắt.

Hàm trả về `HAL_OK` nghĩa là **khởi động thành công**, chưa phải truyền hết 1 MB.

### 3.3. `UART_Interrup_IRQHandler()`

Đọc DWT trước và sau `HAL_UART_IRQHandler`, cộng hiệu vào tổng. Mỗi IRQ có thể chỉ nạp byte, hoặc xử lý hoàn tất và callback. Nếu callback sinh dữ liệu/tính CRC thì thời gian đó nằm trong phép đo bao ngoài.

### 3.4. `UART_Interrup_TxCpltCallback()`

```text
Không phải USART1? → bỏ qua
Đang gửi CRC? → truyen_done_it = 1 → trả về
Ngược lại → tính CRC khối payload vừa xong
  → đã giao đủ payload? → gửi CRC trailer bằng IT, đặt crc_sending
  → còn payload? → sinh khối tiếp → HAL_UART_Transmit_IT → tăng byte_sent_it
```

Chỉ sinh đè buffer sau khi khối cũ hoàn tất. Callback tự nối các khối; main không phải gọi hàm truyền cho từng khối. CRC trailer dùng mảng static `crc_bytes`, vì quá trình IT còn dùng mảng sau khi callback trả về.

Main thấy `truyen_done_it` sau khi IRQ trả về mới gửi DWT/IDL1 một lần qua biến `dwt_report_sent`. Khi chưa done, main liên tục chạy việc nền và bị các IRQ UART chen vào.

## 4. DMA: chuyển từng khối bằng phần cứng

### 4.1. `UART_DMA_Transmit()`

Tương tự hàm IT: reset trạng thái, seed/CRC/DWT; sinh và đo khối đầu; đặt `pending_size`; khóa IRQ ngắn quanh lời gọi `HAL_UART_Transmit_DMA` và cập nhật biến. Sau đó trả về để main chạy việc nền.

Một chú thích `@note` trong file nói chưa đo sinh khối đầu, nhưng mã thực thi đã có `generate_start` và cộng khoảng sinh vào tổng. Khi giải thích phải theo câu lệnh đang chạy.

### 4.2. DMA lấy dữ liệu lúc nào?

Sau khi khởi động, phần cứng DMA đọc `tx_buffer` và đưa từng byte vào USART khi có yêu cầu. CPU không cần phục vụ TXE cho từng byte. **Không sửa buffer khi DMA còn đang đọc.** Project chỉ tái sử dụng nó ở callback hoàn tất khối.

DMA TX đang NORMAL, nên mỗi khối phải được khởi động riêng. Trên đường đi có các ngắt DMA HT/TC theo cấu hình HAL; khi DMA TC, HAL chuyển sang chờ UART TC để bảo đảm byte cuối rời dây rồi mới gọi callback ứng dụng.

### 4.3. `UART_DMA_TxCpltCallback()`

Thuật toán cùng dạng IT:

1. Kiểm tra đúng USART1.
2. Nếu callback của CRC trailer, đặt `truyen_done_dma` và trả về.
3. Nếu là payload, tính CRC đúng `pending_size`, ghi số chu kỳ CRC riêng.
4. Hết payload: đóng gói CRC trong mảng static, khởi động DMA gửi 4 byte, đặt `crc_sending` nếu thành công.
5. Còn dữ liệu: tính `remaining`, chọn `min(remaining, 256)`, sinh dữ liệu và khởi động khối DMA tiếp theo.

Việc sinh khối và tính CRC đang chạy trong callback/ngắt, không chạy chồng với khối TX kế tiếp. Giữa các khối có thể có khoảng trống do CPU xử lý. Đây chưa phải TX ping-pong với hai buffer chuẩn bị trước.

### 4.4. Hai hàm đo IRQ và hàm kiểm tra done

| Hàm | Công việc |
| --- | --- |
| `UART_DMA_IRQHandler` | Đo bao `HAL_DMA_IRQHandler(huart1.hdmatx)` để tính chi phí IRQ DMA TX |
| `UART_DMA_USART_IRQHandler` | Đo bao `HAL_UART_IRQHandler(&huart1)`; gồm callback CRC/sinh khối nếu có |
| `UART_DMA_IsDone` | Trả `truyen_done_dma`; hiện main đọc trực tiếp cờ thay vì gọi hàm tiện ích này |

Đừng cộng thêm chu kỳ đo CRC vào tổng: tổng IRQ đã chứa callback, mà callback đã thực thi CRC.

## 5. Trình tự trạng thái ở cuối bài IT/DMA

```text
Callback payload cuối:
  tính CRC của 64 byte cuối → khởi động gửi 4 byte CRC → crc_sending = 1

Callback CRC:
  thấy crc_sending → đặt done = 1 → IRQ cộng xong chu kỳ → trả về main

main:
  IdleStop → gửi DWT2 → gửi IDL1 → đặt dwt_report_sent = 1
```

`byte_sent == total_byte` có thể đạt từ lúc giao khối payload cuối, trong khi khối đó chưa phát hết. Vì vậy dùng cờ done sau CRC trailer để xác định hoàn tất toàn giao thức.

## 6. Giáo viên yêu cầu so sánh thì kết luận thế nào?

Ở cùng baud, ba thời gian truyền có thể gần nhau vì đều bị tốc độ UART giới hạn. Khác biệt lớn nằm ở chi phí CPU và việc nền: polling không quay lại main; IT quay lại main nhưng ngắt dày; DMA quay lại main và giảm số lần CPU phải nạp dữ liệu.

Đây là xu hướng cần kiểm chứng bằng số liệu. Không nói “DMA bằng 0 chu kỳ CPU”: vẫn có sinh dữ liệu, CRC, thiết lập DMA, xử lý HT/TC/UART TC, callback và báo cáo. Phạm vi báo cáo được giải thích ở tài liệu 06.
