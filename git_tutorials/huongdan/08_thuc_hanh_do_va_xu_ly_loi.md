# 08 — Quy trình thực hành và xử lý lỗi

[Mục lục](README.md) · [Tiếp: Câu hỏi bảo vệ](09_cau_hoi_bao_ve.md)

## 1. Đấu dây theo cấu hình project

| STM32 | USB-UART | Mục đích |
| --- | --- | --- |
| PA9, USART1_TX | RXD | STM32 truyền sang PC |
| PA10, USART1_RX | TXD | PC gửi vào STM32 |
| GND | GND | Chung mốc điện áp |

Dùng tín hiệu UART mức logic 3,3 V phù hợp STM32; phân biệt với giao tiếp RS-232 điện áp khác. Khi cấp nguồn sẵn cho board, chỉ nối các chân cần thiết theo sơ đồ nguồn của board, tránh nối thêm hai nguồn một cách tùy tiện.

Logic analyzer nối GND chung, một kênh PA9, một kênh PA10 nếu đo RX, một kênh PC13 để quan sát việc nền. LED trên board nếu nối PC13 có thể giúp quan sát trạng thái thô, nhưng toggle nhanh không thể đếm bằng mắt.

Tên CP2102/CH340 chỉ là nhóm thiết bị dự kiến của đề tài. Xác nhận đúng phiên bản adapter, driver và baud thực của bộ đang dùng. Lưu tên thiết bị/driver trong biên bản đo; việc Python chấp nhận một giá trị baud chưa chứng minh đường truyền chạy đúng giá trị đó.

## 2. Chuẩn bị Python từ thư mục gốc

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r TEST_PYTHON/requirements.txt
.\.venv\Scripts\python.exe -m serial.tools.list_ports
```

Dùng Python từ 3.10 trở lên vì mã có annotation dạng `float | None`. Nếu chưa có `.venv`, có thể tạo môi trường trước:

```powershell
python -m venv .venv
```

Đọc tên COM từ danh sách, sửa đúng trong script TX hoặc truyền `--port` ở RX. Mỗi lúc chỉ một chương trình mở COM; đóng terminal serial khác trước khi thử. Cài thư viện cần kết nối tới nguồn gói Python nếu môi trường chưa có.

## 3. Chạy một lượt TX DMA

1. Trong [main.c](../../Core/Src/main.c), chọn duy nhất `#define TEST TXDMA`.
2. Trong [usart.c](../../Core/Src/usart.c), đặt `huart1.Init.BaudRate` theo lượt đo, ví dụ 921600.
3. Trong [uart_test_dma_tx.py](../../TEST_PYTHON/uart_test_dma_tx.py), đặt COM đúng, `BAUD_RATE = 921600`, `TOTAL_BYTES = 1_000_000`; tắt tiến trình khi đo chính thức.
4. Mở [project Keil](../../MDK-ARM/Test_hieu_nang_UART.uvprojx), build, kiểm lỗi build, nạp đúng firmware vào board.
5. Chạy script bên dưới, đợi thông báo đang chờ dữ liệu rồi reset STM32 trong thời hạn chờ byte đầu.

```powershell
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_test_dma_tx.py
```

6. Chờ nhận đủ, tính CRC và báo lưu. Kiểm 1.000.000 byte, CRC OK, DWT mode 3 hợp lệ, có counter, CSV đã lưu.
7. Nếu Excel đang mở, đóng rồi xuất lại khi cần. Lưu capture logic analyzer cho đúng lượt/mode/baud.

Firmware đang có baud 1.500.000 và script DMA cũng vậy; bước ví dụ trên chủ động đổi cả hai sang 921600 để phục vụ yêu cầu của đề tài.

## 4. Đổi sang polling và IT

| Bài | TEST trong main | Script PC | Mode báo DWT |
| --- | --- | --- | ---: |
| Polling | `TXPOLLING` | `uart_test_polling_tx.py` | 1 |
| IT | `TXIT` | `uart_test_it_tx.py` | 2 |
| DMA | `TXDMA` | `uart_test_dma_tx.py` | 3 |

Mỗi lần đổi TEST/baud firmware đều build và nạp lại. Không thay đổi riêng script rồi cho rằng STM32 đã đổi theo.

```powershell
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_test_polling_tx.py
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_test_it_tx.py
```

Hai lệnh trên minh họa hai lựa chọn, **chạy từng lệnh cho đúng firmware**, không chạy đồng thời trên cùng COM. Sau mỗi lượt TX, chạy script sẵn sàng rồi reset để STM32 gửi lại.

## 5. Ma trận thí nghiệm công bằng

Với lịch sử đang có, có thể dùng ba mức **461538, 921600, 1500000** để hoàn thiện bảng 3 phương pháp × 3 baud. Mỗi ô nên đo ít nhất 3 lượt mới trong cùng điều kiện; ghi cả lượt lỗi và nguyên nhân điều tra.

Giữ cố định payload 1.000.000 byte, kích thước khối, clock, compiler/tối ưu, dây, adapter, nguồn, tiến trình PC. Nếu cần cùng dữ liệu hoàn toàn, thống nhất seed IT với hai bài còn lại trước đợt đo và ghi lại thay đổi.

| Baud | Polling | IT | DMA |
| --- | --- | --- | --- |
| 461538 | 3 lượt | 3 lượt | 3 lượt |
| 921600 | 3 lượt | 3 lượt | 3 lượt |
| 1500000 | 3 lượt | 3 lượt | 3 lượt |

Ở mỗi ô thu: payload bytes, CRC, thời gian PC, chu kỳ tổng/CRC/UART, tỷ lệ CPU ước tính, counter, trạng thái DWT trong log, capture GPIO. Các lượt cũ có thể đến từ phiên bản khác; không tự gộp thành cùng đợt đo.

## 6. Chạy RX 1 MB ở 921600

1. Chọn `#define TEST TEST_DMA_RX`, đặt USART1 baud 921600, build/nạp.
2. Reset STM32, đợi khởi tạo xong để DMA đã sẵn sàng nhận.
3. Chạy một lượt PC gửi vào board:

```powershell
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_test_dma_rx.py --port COM4 --baud 921600 --length 1000000
```

Đổi COM4 thành cổng thực. Script gửi ngay sau khi mở cổng; không có thông báo READY/handshake từ firmware. Không đợi script gửi rồi mới reset như bài TX.

4. Đạt khi nhận `RESULT,DONE,1000000,<CRC>`, PC báo PASS, CRC PC/STM32 bằng nhau và CSV có một dòng thật.
5. Reset trước mỗi lượt kế tiếp. `--repeat` hiện chỉ nhận 1.
6. Chạy lại nhiều lượt và lưu log. Chỉ sau đó mới dùng dữ liệu này để kết luận khả năng nhận 1 MB ở điều kiện đã đo.

### Kiểm tra độ dài thay đổi và biên vòng đệm

Thử riêng các Length: 0, 1, 3, 4, 508, 509, 511, 512, 513, 1020, 1021, 1023, 1024, 1025 và 1.000.000. Mỗi lượt đều reset. Header chiếm 4 byte nên payload 508 làm tổng khung chạm mốc 512; payload 1020 làm tổng khung chạm 1024.

```powershell
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_test_dma_rx.py --port COM4 --baud 921600 --length 513
```

Độ dài lẻ giúp chứng minh RX không dựa vào CRC word chia hết 4. Khung dài hơn buffer giúp kiểm nhánh wrap. Mã PC hiện gửi một frame, chưa có tham số cố ý chia thành nhiều đoạn với thời gian nghỉ; nếu muốn kiểm IDLE giữa header/payload thì cần thêm kịch bản gửi từng đoạn hoặc dùng công cụ gửi có kiểm soát, rồi đối chiếu CRC toàn khung.

### Cố ý gửi thiếu để kiểm FAIL

```powershell
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_test_dma_rx.py --port COM4 --baud 921600 --length 1000 --truncate-to 700
```

Header vẫn khai báo 1000, chỉ gửi 700 payload. Firmware chưa đủ Length nên không trả DONE; PC timeout, ghi FAIL. Đây là kết quả mong đợi của bài kiểm tra lỗi, không phải lượt thành công bị mất. Reset trước khi thử lại, vì parser còn đang đợi phần thiếu.

## 7. Đo logic analyzer để chứng minh việc nền

1. Cấu hình decoder UART 8N1, baud khớp, kiểm đúng kênh TX hoặc RX và mức tín hiệu.
2. Chọn tần số lấy mẫu đủ để phân giải bit ở baud cao; kiểm bằng độ rộng bit thực, không chỉ tin decoder.
3. Capture PA9 và PC13 **trong cùng cửa sổ truyền**, từ reset hoặc byte đầu đến cuối dữ liệu/CRC.
4. Ở polling, dự kiến PC13 giữ thấp trong khoảng payload vì main chưa vào vòng làm nền.
5. Ở IT/DMA, dự kiến PC13 có cạnh đồng thời PA9 đang truyền. Counter IDL1 > 0 là bằng chứng phần mềm bổ sung.
6. So sánh mật độ cạnh/khoảng ngắt việc nền IT với DMA trong cùng baud; lưu cả ảnh và dữ liệu gốc của máy đo.

Một cạnh PC13 tương ứng một lần toggle; một chu kỳ sóng vuông gồm hai lần. Không lấy ảnh LED đang sáng để suy ra số việc nền hoặc tỷ lệ CPU. PC13 trong mã hiện tại là chân việc nền, **chưa có chân riêng giữ mức cao bao toàn phiên hoặc toggle bao IRQ**; muốn đo trực tiếp thời gian một hàm bằng xung cần thêm instrumentation và ghi rõ chi phí nó gây ra.

Kết luận đúng từ capture: “Trong lúc phần cứng UART/DMA truyền, CPU vẫn chạy bước nền tại main.” Bài hiện dùng counter/toggle làm việc nền giả lập; nếu giáo viên yêu cầu tác vụ hữu ích cụ thể thì cần bổ sung bài tính toán/đọc cảm biến và đo deadline của nó.

## 8. Xuất báo cáo và chạy kiểm tra PC độc lập

```powershell
.\.venv\Scripts\python.exe -X utf8 TEST_PYTHON/uart_excel_report.py
.\.venv\Scripts\python.exe -B -X utf8 -m unittest discover -s TEST_PYTHON -p test_uart_offline.py -v
```

Lệnh thứ nhất tạo Excel từ CSV, không đo lại UART. RX cần lệnh này để cập nhật Excel sau khi đo. Lệnh thứ hai kiểm logic giả lập Python, không thay thế demo UART thật. Không mở workbook bằng Excel khi muốn ghi đè cùng file.

## 9. Bảng tìm lỗi

| Hiện tượng | Kiểm tra trước | Giải thích có thể gặp |
| --- | --- | --- |
| Không mở được COM | Danh sách cổng, ứng dụng khác, driver | Sai tên hoặc cổng bị chiếm |
| TX không có byte đầu | Đã mở script trước reset chưa? TEST đúng chưa? | Firmware TX đã gửi xong trước lúc PC mở hoặc đang chạy RX |
| RX không có RESULT | Firmware RX và DMA đã chạy trước khi gửi chưa? | Reset sai thời điểm, thiếu Length/payload, lỗi RX hoặc main chưa xử lý đủ |
| Decoder/ASCII lỗi | Baud, 8N1, GND, dây chéo, mức logic | Sai cấu hình hoặc tín hiệu không ổn định |
| Nhận gần 1 MB rồi timeout | Baud thực/adapter, PC có bị chậm, dây, log firmware | Có thể mất byte; không tự gán lỗi cho DMA hay PC khi chưa đo |
| CRC sai | Hai phía dùng đúng loại CRC và độ dài không? | Nhầm zlib với CRC TX, mất/đổi byte, trộn payload và báo cáo |
| DWT mode sai | Firmware vừa nạp và file script | PC chọn bài khác firmware |
| DWT thiếu nhưng CRC OK | Có firmware gửi DWT đúng phiên bản chưa? | Dữ liệu có thể đạt, phép đo CPU vẫn thiếu |
| Counter bằng 0 | Đang polling hay IT/DMA? | Polling = 0 là hành vi thiết kế; IT/DMA cần kiểm luồng nền |
| Counter trống | Gói IDL1 đã được gửi/đọc chưa? | Trống khác 0, không tự điền số 0 |
| CPU polling hơi >100% | Mốc PC/MCU, buffering, clock thực | Sai số ước tính; trình bày số và phương pháp đo |
| Polling baud thấp DWT lạ | Thời gian có vượt 59,65 s ở 72 MHz? | Có thể tràn một vòng 32 bit |
| Không cập nhật Excel | Đóng Excel, xem header CSV, đường dẫn | File khóa hoặc schema sai; dữ liệu CSV có thể vẫn đã lưu |
| Firmware đứng hẳn | Dừng debugger, xem Error_Handler/HardFault và cờ | Mã hiện dừng vô hạn khi lỗi, không tự báo qua UART |

Sau khi CubeMX sinh lại mã, đối chiếu baud, `USER CODE`, đường gọi IRQ và các source/include trong Keil. Cấu hình `.ioc` và các sửa đổi `.c` thủ công có thể khác nhau.
