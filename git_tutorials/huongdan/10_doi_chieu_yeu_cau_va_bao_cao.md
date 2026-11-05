# 10 — Đối chiếu yêu cầu, số liệu hiện có và mẫu báo cáo

[Mục lục](README.md) · [Quy trình chạy](08_thuc_hanh_do_va_xu_ly_loi.md)

## 1. Tình trạng từng yêu cầu

Đây là đối chiếu từ mã nguồn và CSV đang nằm trong project ngày **17/10/2026**, không phải kết quả đo mới tạo khi viết tài liệu.

| Yêu cầu đề tài | Đã có trong project | Cần bổ sung/kiểm chứng |
| --- | --- | --- |
| TX polling/IT/DMA | Ba module truyền, chọn bằng TEST, payload 1.000.000 byte | Demo đúng firmware/mode, giữ điều kiện đo công bằng |
| Đo thời gian | Python đo payload, payload + CRC | Đối chiếu logic analyzer nếu cần thời gian thật trên dây |
| Đo chu kỳ CPU bận | DWT từng phương pháp, tách CRC | Nêu giới hạn phạm vi/IRQ/tràn và không gọi là tổng tải hệ thống |
| Đo bằng idle counter | Có counter, PC13, IDL1; có hàm hiệu chuẩn | Main chưa gọi hiệu chuẩn; chưa tính % từ mức suy giảm counter |
| Chứng minh làm việc khác khi DMA TX | Bước nền tăng counter và toggle PC13 trong main | Lưu capture đồng thời TX/GPIO và log counter; hiện chưa thấy file capture trong danh sách project đã kiểm tra |
| RX DMA circular + IDLE | ReceiveToIdle_DMA, HT/TC/IDLE, buffer 1024, parser Length | Chạy thật và kiểm deadline/ghi đè/lỗi RX |
| Double buffer | Một mảng chia hai nửa A/B | Mô tả đúng cơ chế; chưa có quản lý quyền buffer và phát hiện overrun đầy đủ |
| RX độ dài thay đổi | Header uint32, parser giữ trạng thái, script --length | Bộ thử nhiều độ dài/đứt đoạn, qua biên/wrap; một frame/reset |
| RX 1 MB không lỗi ở 921600 | Có script so số byte/CRC và lưu CSV | CSV RX hiện chưa có lượt đo, phải đo thật |
| Bảng 3 phương pháp × 3 baud | CSV/Excel nhóm theo tính năng/baud | Thiếu polling và IT ở 1500000; số lần lặp còn không đều |
| Kiểm tra toàn vẹn CRC | CRC phần cứng TX, zlib-compatible RX | Không trộn hai thuật toán, ghi PASS/FAIL và cả lượt thiếu |
| Bảng + biểu đồ + báo cáo | Excel có bảng tổng hợp/chi tiết | Exporter chưa tạo biểu đồ; cần hoàn thiện biểu đồ/báo cáo từ dữ liệu hợp lệ |

## 2. Kiểm kê dữ liệu CSV hiện có

Nguồn là ba [CSV TX](../../TEST_PYTHON/) và [CSV RX](../../TEST_PYTHON/uart_dma_rx_results.csv). Các dòng trắng không tính là lượt chạy.

| Phương pháp / baud | Số lượt | Thành công | Thất bại |
| --- | ---: | ---: | ---: |
| Polling / 461538 | 1 | 1 | 0 |
| Polling / 921600 | 3 | 3 | 0 |
| Polling / 1500000 | 0 | 0 | 0 |
| IT / 461538 | 2 | 2 | 0 |
| IT / 921600 | 1 | 1 | 0 |
| IT / 1500000 | 0 | 0 | 0 |
| DMA / 461538 | 3 | 2 | 1 |
| DMA / 921600 | 3 | 2 | 1 |
| DMA / 1500000 | 3 | 3 | 0 |
| RX DMA, mọi baud | 0 | 0 | 0 |

Các lượt TX thành công đang có CRC OK và đủ 1.000.000 byte. Hai lượt DMA thất bại nhận 411.309 byte ở 461538 và 999.941 byte ở 921600, chưa kiểm được CRC. Chưa có đủ bằng chứng để kết luận nguyên nhân các lượt lỗi.

Đây là lịch sử trong file, chưa chứng minh mọi dòng được đo với cùng commit, tối ưu compiler, dây và adapter. CSV chưa lưu phiên bản firmware; một số giá trị DWT/counter lặp lại giữa các dòng. Không suy đoán nguồn gốc, không tự xóa dòng; nên ghi thông tin phiên đo và thực hiện một đợt đo thống nhất trước báo cáo cuối.

### Ví dụ xu hướng ở 921600 từ các lượt thành công hiện có

Các khoảng dưới đây lấy từ CSV, chỉ để tập đọc và nhận xét, không thay bảng đo mới có kiểm soát.

| Phương pháp | Thời gian payload PC | Tỷ lệ CPU ước tính theo DWT/PC | Counter nền |
| --- | --- | --- | --- |
| Polling | Khoảng 11,0103–11,0105 s | Khoảng 100,0045–100,0060% | 0 |
| IT | Khoảng 11,0189 s | Khoảng 14,4596% | 11.002.803 |
| DMA | Khoảng 11,0187–11,0188 s | Khoảng 1,7913–1,7914% | 14.679.788 |

Nhận xét có căn cứ: thời gian payload gần nhau; chi phí CPU phục vụ bài đo giảm rõ từ polling đến DMA; IT/DMA có bước nền, polling không có trong cửa sổ đo. Sai số >100% của polling cần được giải thích bằng phương pháp đo, không che đi.

Không nói bảng này đã đủ ba baud cho cả ba phương pháp, hoặc chứng minh RX. TX thành công không tự chứng minh RX DMA đạt yêu cầu.

## 3. Mẫu bảng kết quả cuối

Sau khi đo mới theo quy trình ở tài liệu 08, điền từng ô từ các lượt hợp lệ. Ghi `chưa đo` nếu không có số, không điền 0 thay cho thiếu dữ liệu.

| Baud | Phương pháp | Thành công/tổng | T payload TB (s) | C UART TB | C CRC TB | C tổng TB | CPU ước tính (%) | Bước nền/s | CRC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 461538 | Polling | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 461538 | IT | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 461538 | DMA | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 921600 | Polling | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 921600 | IT | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 921600 | DMA | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 1500000 | Polling | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 1500000 | IT | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |
| 1500000 | DMA | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo |

Trong bảng, “TB” là trung bình các lượt đo phù hợp; nêu số lượt, min/max hoặc độ phân tán kèm theo. `C UART = C tổng - C CRC`, không cộng lại CRC. Cột bước nền/s là phân tích bổ sung: IDL1 hiện chỉ gửi counter, không gửi elapsed_ms; nếu chia theo thời gian PC thì phải ghi đó là xấp xỉ, không phải cửa sổ MCU trùng tuyệt đối.

### Bảng RX riêng

| Lượt | Baud | Length yêu cầu | PC gửi | STM32 nhận | CRC PC | CRC STM32 | PASS/FAIL | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 921600 | 1000000 | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | Reset trước lượt |
| 2 | 921600 | 1000000 | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | Reset trước lượt |
| 3 | 921600 | 1000000 | chưa đo | chưa đo | chưa đo | chưa đo | chưa đo | Reset trước lượt |

Thêm bảng test độ dài ngắn/lẻ/qua biên và test cố ý gửi thiếu. Trường hợp cố ý gửi thiếu phải FAIL theo thiết kế và ghi rõ mục đích; không trộn vào tỷ lệ thành công của kịch bản gửi đủ khi so sánh mà không chú thích.

## 4. Những biểu đồ cần làm từ số liệu hợp lệ

Exporter hiện chưa vẽ, có thể tạo trong bản sao Excel sau khi đã chốt CSV:

1. **Thời gian payload theo baud**, ba chuỗi polling/IT/DMA; trục Y giây. Giúp thấy giới hạn tốc độ đường truyền.
2. **Tỷ lệ CPU ước tính theo baud**, ba chuỗi; trục Y %. Chú thích công thức DWT/thời gian PC và phạm vi đo.
3. **Chu kỳ CPU**, có thể dùng cột chồng phần UART trừ CRC và CRC để tổng đúng bằng C_total. Trục Y chu kỳ hoặc triệu chu kỳ, ghi rõ đơn vị.
4. **Việc nền**, dùng số bước/s xấp xỉ hoặc counter với điều kiện cùng cửa sổ; ghi cách chuẩn hóa.

Không dùng biểu đồ để che các ô thiếu, không tự tạo số cho ô chưa đo. Đừng vẽ mỗi phương pháp ở một baud khác nhau rồi quy khác biệt hoàn toàn cho phương pháp. Nếu có nhiều lượt, thêm độ phân tán khi trình bày.

Sau khi chỉnh biểu đồ thủ công, lưu bản báo cáo riêng, ví dụ `uart_summary_bao_cao.xlsx`. Script xuất lại `uart_summary.xlsx` sẽ tạo lại workbook từ CSV và không giữ các thay đổi thủ công.

## 5. Bố cục báo cáo gợi ý

### 5.1. Mục tiêu và tiêu chí đạt

Nêu 1 MB = 1.000.000 byte, ba baud cụ thể, 8N1, nhận độ dài thay đổi, CRC và bằng chứng việc nền. Phân biệt tiêu chí dữ liệu đúng với tiêu chí phép đo đầy đủ.

### 5.2. Thiết bị và điều kiện

Ghi MCU/board, HCLK/PCLK, USB-UART và driver, dây, nguồn, logic analyzer, cấu hình lấy mẫu, máy PC, Python, compiler/tối ưu và phiên bản source. Có sơ đồ nối chân.

### 5.3. Thiết kế phần mềm

Sơ đồ main/IRQ/callback của TX; sơ đồ vòng RX, HT/TC/IDLE và parser; format hai giao thức; thuật toán CRC tương ứng. Dùng tài liệu 03–07 làm cơ sở, chọn phần chính thay vì chép nguyên mọi dòng mã.

### 5.4. Phương pháp đo

Chỉ mốc bắt đầu/kết thúc PC, DWT và counter; giới hạn tràn, phần chưa tính của IRQ; vị trí GPIO. Nêu rõ Calibrate chưa được gọi nếu báo cáo theo đúng phiên bản hiện tại. Nếu cải tiến phép đo, ghi mã và phương pháp mới đã dùng.

### 5.5. Kết quả

Bảng 3 × 3 có lặp, biểu đồ, log/capture việc nền; bảng RX 1 MB CRC PASS; các case biên và FAIL mong đợi. Giữ lịch sử lỗi để phân tích, không chỉ đưa lượt đẹp.

### 5.6. Nhận xét và giới hạn

Trả lời vì sao thời gian tương tự nhưng CPU khác; vì sao IT tốn IRQ; tại sao DMA không bằng 0 CPU; vì sao IDLE chưa đủ nếu không HT/TC; rủi ro ghi đè buffer và việc chưa hỗ trợ nhiều frame/reset. Kết luận chỉ trong điều kiện đã thử.

## 6. Kịch bản trình bày ngắn trước giáo viên

```text
1. Giới thiệu sơ đồ dây và USART1, chọn TEST/baud trong mã.
2. Chỉ ba luồng TX, giải thích callback và nơi chạy việc nền.
3. Demo một lượt TX DMA: đủ byte, CRC, DWT, IDL1; mở capture PA9/PC13.
4. So bảng ba phương pháp ở cùng baud, giải thích công thức và sai số.
5. Đổi sang firmware RX đã chuẩn bị, reset trước gửi, demo 1 MB ở 921600.
6. Chỉ RESULT/CRC/CSV PASS, giải thích wrap và một frame mỗi reset.
7. Nêu bằng chứng còn thiếu hoặc hạn chế chưa khắc phục.
```

Nếu chỉ viết báo cáo từ project hiện tại mà chưa đo thêm, phải ghi rõ: **chưa đủ ma trận 3 × 3, chưa có CSV RX PASS, chưa có biểu đồ/capture được xác minh trong đợt đọc này, chưa có tải CPU tính từ baseline idle**. Những khoảng trống đó là việc thực nghiệm cần hoàn thành, không được thay bằng mô tả lý thuyết.
