# 01 — Hiểu đề tài trước khi đọc từng hàm

[Mục lục](README.md) · [Tiếp: Bản đồ các file](02_ban_do_cac_file.md)

## 1. Giáo viên muốn em chứng minh điều gì?

Không chỉ là “UART gửi được dữ liệu”. Với cùng kích thước và baud, em cần trả lời:

- Mất bao lâu để truyền xong?
- CPU tốn bao nhiêu thời gian phục vụ UART và tính CRC?
- Trong lúc truyền, vòng `main()` có làm được việc khác không?
- Nếu không biết trước độ dài mỗi đợt dữ liệu đến, chương trình lấy phần mới trong DMA thế nào?
- Bằng chứng nào cho thấy đúng số byte và dữ liệu không bị sai?

Project chia việc thành **ba bài TX** và **một bài RX**. `TEST` trong [main.c](../../Core/Src/main.c) chọn một bài khi biên dịch. Mỗi firmware chạy một bài, không tự chuyển cả ba cách TX và RX trong cùng một lượt.

## 2. UART là một dòng byte

UART đưa từng byte lên dây TX. Không có sẵn thông tin “đây là file”, “đây là gói 1 MB” hoặc “đây là CRC”. Hai phía phải thống nhất baud, cấu hình khung và thứ tự các trường.

Project dùng **8N1**: 1 bit bắt đầu, 8 bit dữ liệu, không parity, 1 bit kết thúc. Một byte dữ liệu cần **10 bit trên dây**.

```text
Tốc độ byte lý thuyết = baud / 10
Thời gian payload lý thuyết = số byte × 10 / baud
```

Ví dụ với 1.000.000 byte:

| Baud yêu cầu | Byte/s lý thuyết | Thời gian payload lý thuyết |
| --- | ---: | ---: |
| 461538 | 46153,8 | 21,666688 s |
| 921600 | 92160 | 10,850694 s |
| 1500000 | 150000 | 6,666667 s |

Đây là phép tính theo baud yêu cầu, chưa gồm CRC, báo cáo, khoảng trống giữa các khối và sai số baud thực. Không dùng bảng này thay cho kết quả đo. Logic analyzer có thể đo độ rộng bit để kiểm tra tốc độ thực.

## 3. Ba cách TX khác nhau ở chỗ CPU làm gì

| Cách | Ai đưa byte từ RAM vào UART? | Sau khi gọi hàm khởi động, main làm tiếp được không? | Chi phí đặc trưng |
| --- | --- | --- | --- |
| Polling | CPU kiểm tra cờ rồi ghi thanh ghi dữ liệu | Hàm chặn đến khi hoàn tất | CPU dành phần lớn khoảng truyền để kiểm tra/chờ UART |
| Interrupt, viết tắt IT | CPU phục vụ ngắt UART để nạp từng byte | Có | Nhiều lần vào ngắt, tần suất tăng theo tốc độ byte |
| DMA | Bộ DMA chuyển byte khi UART yêu cầu | Có | CPU thiết lập DMA và xử lý các ngắt/sự kiện của khối |

Hình dung: polling là đứng chờ máy in và đưa từng tờ; IT là máy báo mỗi lúc cần tờ mới; DMA là giao cả chồng cho bộ cấp giấy. Cả ba vẫn bị giới hạn bởi tốc độ của máy, tương ứng baud trên dây.

**DMA giảm chi phí CPU, không tự làm bit UART chạy nhanh hơn khi giữ cùng baud.** Việc main chạy song song với DMA là CPU và phần cứng DMA hoạt động đồng thời; trên một CPU, main và hàm ngắt vẫn thay phiên nhau thực thi.

## 4. DMA circular và IDLE giải quyết hai vấn đề khác nhau

**DMA circular**: DMA ghi lần lượt vào buffer. Hết cuối buffer thì quay về đầu mà không cần main khởi động lại sau từng vòng. Project dùng một mảng 1024 byte, chia hai nửa 512 byte.

**IDLE line**: UART phát hiện đường nhận nghỉ sau dữ liệu, khoảng một khung UART. Sự kiện giúp phần mềm biết có một đoạn ngắn đã đến dù chưa đầy nửa buffer.

**HT/TC**: DMA còn báo half transfer (đầy nửa buffer) và transfer complete (đầy buffer). Vì dòng 1 MB có thể liên tục và không có khoảng nghỉ ở giữa, không thể chỉ chờ IDLE cuối cùng rồi mới xử lý buffer 1024 byte.

**IDLE không xác định ranh giới bản tin của ứng dụng.** Một bản tin có thể gặp nhiều lần IDLE do PC/USB tạm ngừng. Trong project, bốn byte Length mới cho biết tổng payload phải nhận.

## 5. Cấu hình thực tế đang có

Đối chiếu [main.c](../../Core/Src/main.c), [usart.c](../../Core/Src/usart.c) và các script, không lấy bảng cũ trong README khác làm cấu hình chạy hiện tại.

| Thành phần | Giá trị đang có hiệu lực |
| --- | --- |
| MCU khai báo | STM32F103C8T6, Cortex-M3 |
| Clock mục tiêu | HSE 8 MHz × PLL 9 = HCLK 72 MHz; APB1 36 MHz, APB2 72 MHz |
| Bài firmware | `#define TEST TXDMA` |
| UART | USART1, PA9 TX, PA10 RX, 8N1, không flow control |
| Baud firmware | `1500000` |
| DMA TX | DMA1 Channel 4, NORMAL |
| DMA RX | DMA1 Channel 5, CIRCULAR |
| GPIO việc nền | PC13 |
| TX payload / buffer | 1.000.000 / 256 byte |
| RX buffer | 1024 byte |
| Script polling TX | COM4, 921600, tiến trình tắt |
| Script IT TX | COM4, 921600, tiến trình bật |
| Script DMA TX | COM4, 1500000, tiến trình bật |
| Script DMA RX mặc định | COM13, 1500000, Length = 1.000.000 |

**Baud chưa đồng bộ cho mọi script.** Muốn thử polling/IT với cấu hình hiện tại phải đổi baud script hoặc baud firmware cho khớp, rồi chọn đúng `TEST` và build/nạp lại. Script Python không đổi baud hoặc phương pháp của firmware.

## 6. Các từ thường gặp khi đọc mã

| Từ | Hiểu đơn giản |
| --- | --- |
| Payload | Phần dữ liệu chính, không gồm Length/CRC/báo cáo |
| Chunk | Một khối nhỏ xử lý trong một lần, TX ở đây thường 256 byte |
| IRQ/ISR | Ngắt/hàm chạy khi có ngắt; main bị tạm dừng trong lúc đó |
| Callback | Hàm ứng dụng được HAL gọi khi có sự kiện |
| `huart1` | Cấu trúc HAL chứa cấu hình và trạng thái USART1 |
| `volatile` | Yêu cầu trình biên dịch đọc/ghi biến đúng theo truy cập mã; thường dùng biến chia sẻ main/ngắt |
| CRC | Giá trị kiểm tra tính toàn vẹn tính từ dữ liệu |
| DWT `CYCCNT` | Bộ đếm chu kỳ CPU, dùng đo các đoạn thực thi |

`volatile` không làm cả chuỗi thao tác trở thành nguyên tử, không khóa buffer và không ngăn DMA ghi đè dữ liệu. Đây là điểm quan trọng khi học phần RX.
