# 09 — Bộ câu hỏi giáo viên kiểm tra sinh viên

[Mục lục](README.md) · [Tiếp: Đối chiếu yêu cầu và báo cáo](10_doi_chieu_yeu_cau_va_bao_cao.md)

Cách học: che phần gợi ý, trả lời bằng lời của em, sau đó mở file chỉ đúng dòng/hàm liên quan. Giáo viên có thể hỏi tiếp “ai gọi hàm này?”, “biến này cập nhật lúc nào?” và “em chứng minh bằng phép đo nào?”.

## 1. Nắm mục tiêu và khái niệm

### Câu 1. Em giới thiệu đề tài trong một phút

**Gợi ý:** Dùng STM32F103 so sánh truyền 1.000.000 byte qua USART1 bằng polling, IT, DMA ở ba baud. PC kiểm CRC và lưu báo cáo; DWT đo chi phí CPU, bước nền/GPIO chứng minh main làm việc khi truyền bất đồng bộ. Nhánh RX dùng DMA circular 1024 byte, HT/TC/IDLE cập nhật vị trí, Length cho biết tổng payload, CRC zlib xác minh dữ liệu. Phải nêu riêng phần đã có mã và phần đã có kết quả đo.

### Câu 2. TX trong tên script là TX của ai?

**Gợi ý:** Của STM32. `uart_test_dma_tx.py` trên PC nhận dữ liệu, không điều khiển DMA trực tiếp. `uart_test_dma_rx.py` gửi dữ liệu vào STM32.

### Câu 3. Tại sao 921600 baud không phải 921600 byte/s?

**Gợi ý:** Baud đang được dùng cho tốc độ bit UART; 8N1 dùng 10 bit cho mỗi byte payload. Tốc độ byte lý thuyết 92160 byte/s; 1.000.000 byte khoảng 10,851 s chưa gồm các phần bổ sung.

### Câu 4. Polling, IT, DMA đều cùng baud thì DMA có nhanh hơn nhiều không?

**Gợi ý:** Bit vẫn cùng tốc độ. Thời gian có thể khác do khoảng nghỉ và xử lý khối, nhưng lợi ích chính DMA là giảm chi phí CPU. Phải đưa số đo thay cho kết luận tuyệt đối.

### Câu 5. Blocking có phải tắt ngắt không?

**Gợi ý:** Không. Hàm chưa trả về nên main chưa làm tiếp; ngắt có thể vẫn chạy. Mã polling hiện không chạy bước nền trong khoảng truyền.

### Câu 6. CPU và DMA “song song” nghĩa là gì?

**Gợi ý:** DMA là phần cứng chuyển dữ liệu trong khi CPU chạy main. Main và ISR trên cùng CPU vẫn thay phiên; không phải hai luồng CPU chạy cùng lúc.

## 2. Kiểm tra đọc luồng chương trình

### Câu 7. Chọn TEST ở đâu? Có đổi bằng Python được không?

**Gợi ý:** Macro trong `Core/Src/main.c`, được xử lý khi biên dịch; Python hiện không có lệnh chuyển mode. Đổi TEST phải build/nạp. Kiểm tra compiler define nếu có override.

### Câu 8. USART1 dùng chân nào, DMA channel nào?

**Gợi ý:** PA9 TX, PA10 RX; TX DMA1 Channel4 NORMAL, RX DMA1 Channel5 CIRCULAR. PC13 cho việc nền. Chỉ đúng `usart.c`, `dma.c`, `gpio.c`.

### Câu 9. Tại sao phải gọi MX_DMA_Init trước bài thử?

**Gợi ý:** Bật clock DMA1 và enable NVIC channel. Cấu hình channel/link handle thực hiện trong MSP UART; cả hai phần phải đúng trước khi nhận/truyền DMA.

### Câu 10. Khi main gọi UART_DMA_Transmit trả HAL_OK, 1 MB đã xong chưa?

**Gợi ý:** Chưa. Chỉ khởi động khối đầu thành công. Callback nối khối và CRC; done chỉ đặt sau callback CRC trailer.

### Câu 11. Ai gọi HAL_UART_TxCpltCallback?

**Gợi ý:** HAL khi xử lý hoàn tất truyền trong đường IRQ. `main.c` định nghĩa callback rồi chuyển đến callback IT/DMA theo TEST; main không gọi tuần tự callback để giả lập hoàn tất.

### Câu 12. Tại sao DMA TX vẫn cần USART1_IRQHandler?

**Gợi ý:** DMA TC chỉ báo chuyển xong RAM → UART. Với DMA normal, HAL bật UART TC để đợi byte cuối phát hết trên dây rồi mới báo callback ứng dụng.

### Câu 13. byte_sent_dma bằng 1.000.000 đã dùng làm dấu xong được chưa?

**Gợi ý:** Chưa; biến tăng lúc giao khối thành công, khối cuối có thể còn trên dây và chưa gửi CRC. Dùng `truyen_done_dma` theo đúng luồng hiện tại.

### Câu 14. Vì sao gửi DWT từ main sau IRQ cuối?

**Gợi ý:** Callback đặt done vẫn nằm bên trong wrapper đo IRQ; tổng chỉ được cộng khi HAL trả về. Main chạy sau IRQ thì đọc được số tổng đã có IRQ cuối. Gửi báo cáo một lần cũng tránh chen báo cáo vào payload.

### Câu 15. Vì sao buffer IT/DMA là static?

**Gợi ý:** HAL/DMA còn dùng dữ liệu sau khi hàm khởi động/callback trả về. Buffer phải tồn tại đủ lâu và không bị ghi đè khi đang truyền. Buffer polling cục bộ an toàn vì truyền chặn xong trước khi rời hàm.

### Câu 16. pending_size và crc_sending để làm gì?

**Gợi ý:** pending_size lưu kích thước payload đang chờ hoàn tất, nhất là khối cuối 64 byte. crc_sending phân biệt callback payload với callback 4 byte CRC; tránh tính CRC trailer như payload và biết lúc đặt done.

### Câu 17. Vì sao bảo vệ ngắn bằng PRIMASK khi khởi động IT/DMA?

**Gợi ý:** Ngăn IRQ chen vào phép đo HAL/cập nhật byte đầu, tránh cập nhật đồng thời trạng thái. Chỉ khóa đoạn ngắn và khôi phục trạng thái cũ; không khóa hết lượt UART.

### Câu 18. Error_Handler báo lỗi gì cho người dùng?

**Gợi ý:** Hiện không gửi thông điệp; tắt ngắt và đứng trong vòng lặp. PC có thể timeout. Có cờ lỗi TX nhưng RX chưa có đường phục hồi tương đương.

## 3. CRC, DWT và phân tích số liệu

### Câu 19. Tại sao tính CRC sau mỗi chunk mà chỉ gửi một CRC cuối?

**Gợi ý:** CRC tích lũy giữ trạng thái giữa các khối, tạo CRC toàn payload mà không cần giữ 1 MB trong RAM. Reset một lần đầu phiên, Update mỗi khối, GetValue cuối.

### Câu 20. CRC TX và RX có dùng chung zlib được không?

**Gợi ý:** Không thay thế trực tiếp. TX dùng CRC ngoại vi STM32F1 theo word little-endian, Python mô phỏng. RX dùng CRC phần mềm tương thích zlib trên byte. Cần cùng thuật toán/tham số/thứ tự byte và cùng miền payload.

### Câu 21. Nếu đổi tổng TX thành 1.000.001 byte thì sao?

**Gợi ý:** CRC phần cứng wrapper yêu cầu độ dài chunk chia hết 4, khối cuối mới có thể bị từ chối. Phải thiết kế xử lý byte dư và thống nhất PC/STM32; không chỉ sửa hằng số.

### Câu 22. DWT tự đo “CPU bận UART” bằng cách nào?

**Gợi ý:** DWT chỉ đếm chu kỳ, phần mềm đặt mốc bao các đoạn muốn đo. Polling bao cả khoảng chờ; IT/DMA cộng thời gian sinh khối đầu, setup và IRQ/callback; nền ngoài các đoạn đó không được tính.

### Câu 23. Có cộng cpu_crc_cycles vào cpu_busy_cycles không?

**Gợi ý:** Không, CRC đã nằm trong tổng. Muốn tách thì `C_uart = C_total - C_crc`. “UART trừ CRC” vẫn có sinh dữ liệu và xử lý khác trong phạm vi đo.

### Câu 24. Tổng 7.200.000 chu kỳ ở 72 MHz tương ứng bao lâu?

**Gợi ý:** 0,1 s = 100 ms. Nếu thời gian PC payload + CRC là 10 s thì tỷ lệ theo công thức hiện tại là 1%.

### Câu 25. Vì sao counter DMA lớn mà tải CPU báo nhỏ?

**Gợi ý:** Tỷ lệ DWT nói CPU ít phục vụ UART; phần còn lại CPU đang chạy bước nền. Counter lớn không có nghĩa CPU đang ngủ, và tỷ lệ này không phải tổng tải toàn hệ thống.

### Câu 26. Project đã đo tải CPU từ idle counter chưa?

**Gợi ý:** Chưa hoàn thiện theo cách đó. Có Calibrate nhưng main không gọi; script tính tỷ lệ DWT/thời gian PC. Counter hiện chứng minh và định lượng số bước nền. Muốn % từ idle cần baseline cùng điều kiện và cùng cửa sổ thời gian.

### Câu 27. Tại sao polling có thể báo 100,006%?

**Gợi ý:** Mốc MCU và PC khác, USB/OS buffering, bỏ khoảng byte đầu trước start và sai số đo. Không diễn giải như CPU thực có hơn 100% công suất; báo tỷ lệ ước tính và đối chiếu đo trên dây.

### Câu 28. DWT tràn khi nào? IT/DMA có vấn đề giống polling không?

**Gợi ý:** CYCCNT 32 bit, 72 MHz khoảng 59,65 s/vòng. Polling bao một khoảng dài nên có thể mất vòng; IT/DMA cộng các đoạn ngắn, không đo thời gian chờ giữa IRQ. Vẫn có giới hạn tổng accumulator 32 bit và độ dài mỗi đoạn.

### Câu 29. CRC OK có nghĩa tất cả số đo đều dùng được không?

**Gợi ý:** Không. Có thể thiếu DWT/IDL1, DWT wrap hoặc dữ liệu lịch sử khác firmware. Script hiện cho thành công dữ liệu khi CRC khớp và không mode mismatch; cần xét riêng chất lượng phép đo.

## 4. DMA circular, IDLE và tình huống lỗi

### Câu 30. Có IDLE là hết bản tin chưa?

**Gợi ý:** Chưa chắc. IDLE là khoảng nghỉ đường truyền; PC có thể nghỉ giữa một bản tin. Parser hoàn tất theo Length, giữ trạng thái qua nhiều sự kiện.

### Câu 31. Nếu PC gửi 1 MB liên tục, chỉ dùng IDLE cuối có đủ không?

**Gợi ý:** Không với buffer 1024 nếu main chỉ xử lý lúc cuối. DMA đã ghi đè nhiều vòng. Cần HT/TC để xử lý trong lúc dòng đang chạy và IDLE để chốt phần dư.

### Câu 32. Callback Size = 700 có nghĩa vừa đến 700 byte không?

**Gợi ý:** Không, là mốc trong buffer. Nếu lần trước 512 thì mới thêm 188. Có thể báo 1024 tại TC; đó là mốc hết buffer, không phải chỉ số phần tử hợp lệ.

### Câu 33. process_pos = 900, dma_pos = 120 thì đọc gì?

**Gợi ý:** Đọc 900..1023 rồi 0..119, tổng 244 byte, giữ thứ tự, cập nhật process_pos = 120.

### Câu 34. pos bằng process_pos có chắc không có byte mới không?

**Gợi ý:** Không nếu main chậm để DMA quay trọn vòng. Mã hiện không có bộ đếm vòng đủ để phân biệt chắc chắn. Cần cơ chế theo dõi producer/consumer/overrun nếu muốn xử lý tình huống đó.

### Câu 35. Đây có phải double buffer phần cứng không?

**Gợi ý:** Mã có một mảng 1024 byte chia A/B, HT/TC báo hai nửa. Không cấu hình hai địa chỉ buffer DMA độc lập. Phải mô tả đúng cơ chế đang dùng.

### Câu 36. volatile có bảo đảm không mất sự kiện và không bị DMA ghi đè không?

**Gợi ý:** Không. Nó không là mutex, không đếm vòng, không khóa vùng RAM. Ngắt/main có thể xen thao tác, DMA tiếp tục ghi khi main đọc.

### Câu 37. Nửa buffer 512 byte ở 921600 cho bao nhiêu thời gian?

**Gợi ý:** Khoảng 5,556 ms theo baud danh định. Trong khoảng đó cần xử lý vùng vừa hoàn tất trước khi bị quay lại ghi đè, đồng thời xét độ trễ ngắt và main.

### Câu 38. Nhận Length = 0 hoặc payload lẻ có được không?

**Gợi ý:** Có trong parser RX: Length 0 done sau header, CRC rỗng 0; payload lẻ dùng CRC byte tương thích zlib. Không áp dụng ràng buộc chia hết 4 của TX cho RX.

### Câu 39. Gửi khung thứ hai ngay sau DONE có được xử lý không?

**Gợi ý:** Hiện không. `rx_done` làm parser bỏ qua byte sau; trạng thái không tự reset và RESULT chỉ gửi một lần. Reset MCU trước lượt mới.

### Câu 40. Em đưa bằng chứng gì cho câu “nhận 1 MB không lỗi ở 921600”?

**Gợi ý:** Cấu hình firmware/PC đúng baud, log thực gửi/nhận 1.000.000, RESULT và CRC khớp, CSV PASS nhiều lượt, bài thử wrap/độ dài biến đổi, capture kiểm tín hiệu và tốc độ. CSV RX hiện chưa có dòng dữ liệu nên chưa đưa kết luận đã đạt.

## 5. Bài tập trực tiếp tại bàn bảo vệ

| Bài | Yêu cầu | Kết quả mong đợi |
| --- | --- | --- |
| Lần luồng DMA | Chỉ từ DMA1_Channel4_IRQHandler đến callback và giải thích UART TC | Nêu đúng vai trò hai ngắt, không nói DMA TC là đã rời dây |
| Tính khối cuối | Chia 1.000.000 cho 256 | 3906 khối đầy và 64 byte, tổng 3907 khối |
| Giải little-endian | `40 42 0F 00` trong header RX là gì? | 1.000.000; chỉ Length, không phải CRC |
| Dò nhầm mode | Chạy script polling với firmware DMA cùng baud | DWT báo mode mismatch nếu nhận đủ tới báo cáo |
| Kiểm thiếu payload | Length 1000, truncate 700 | Không DONE, PC FAIL/timeout, cần reset |
| Kiểm việc nền | Capture PA9 và PC13 ở IT/DMA | Có cạnh PC13 trong cửa sổ TX và counter > 0 |
| Đọc CSV | Phân biệt ô counter trống với 0 | Trống là chưa nhận báo cáo, 0 có thể là polling hợp lệ |
| Đọc báo cáo | Chỉ ô thiếu ở ma trận 3 × 3 | Polling/IT chưa có dữ liệu 1.500.000 trong CSV hiện có |

## 6. Gợi ý chấm 10 điểm

Đây là rubric luyện bảo vệ, không phải điểm đã chấm project.

| Nhóm | Điểm | Điều kiện đạt |
| --- | ---: | --- |
| Hiểu UART và kiến trúc | 1,5 | Đúng 8N1, TX/RX, baud và vai trò các lớp file |
| Luồng TX ba cách | 2,0 | Giải thích blocking, IRQ, DMA, callback, CRC trailer và buffer lifetime |
| RX circular + IDLE | 2,0 | Đúng vị trí/độ dài, HT/TC, wrap, parser và rủi ro overrun |
| Phép đo CPU/thời gian | 2,0 | Đúng phạm vi DWT, CRC nằm trong tổng, idle, sai số, tràn |
| Thực nghiệm và toàn vẹn | 1,5 | Có 3 × 3 dữ liệu, RX 1 MB CRC PASS, capture việc nền |
| Báo cáo và trung thực số liệu | 1,0 | Bảng/biểu đồ có đơn vị, ghi điều kiện, chỉ rõ phần chưa hoàn thành |

Một câu trả lời tốt luôn đi cùng vị trí mã hoặc bằng chứng đo. Nếu chưa đo, nói rõ “đây là thiết kế/kịch bản dự kiến”, không biến xu hướng lý thuyết thành kết quả thực nghiệm.
