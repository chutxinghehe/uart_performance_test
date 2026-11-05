# Hướng dẫn học và bảo vệ đề tài đo hiệu năng UART

Bộ tài liệu này giải thích **mã nguồn thực tế của project** theo cách một giáo viên hướng dẫn và kiểm tra sinh viên. Đọc mã và đối chiếu dữ liệu ngày **17/10/2026**. Các con số cấu hình có thể thay đổi khi em sửa chương trình; hãy kiểm tra lại dòng lệnh đang có hiệu lực trước mỗi thí nghiệm.

Đề tài: truyền khối dữ liệu lớn bằng polling, interrupt và DMA; so sánh thời gian, chi phí CPU, khả năng chạy việc nền; nhận dữ liệu độ dài thay đổi bằng DMA circular kết hợp IDLE.

## 1. Đọc theo thứ tự nào?

| Tài liệu | Nội dung em cần nắm |
| --- | --- |
| [01 — Tổng quan và kiến thức nền](01_tong_quan_va_kien_thuc_nen.md) | UART, baud, polling/IT/DMA, mục tiêu và cấu hình hiện tại |
| [02 — Bản đồ các file](02_ban_do_cac_file.md) | Mỗi thư mục/file làm gì, liên quan với file nào |
| [03 — Khởi động, main và ngắt](03_khoi_dong_main_va_ngat.md) | Từ reset đến chạy bài thử; cấu hình chân, DMA, callback |
| [04 — Ba cách truyền TX](04_luong_truyen_polling_it_dma.md) | Theo từng bước và từng hàm của polling, IT, DMA |
| [05 — Nhận DMA circular và IDLE](05_nhan_dma_circular_idle.md) | Vòng đệm A/B, con trỏ, parser Length + Payload, nguy cơ mất byte |
| [06 — CRC, DWT và tải CPU](06_crc_dwt_va_tai_cpu.md) | Giao thức nhị phân, hai loại CRC, công thức và giới hạn phép đo |
| [07 — Các script Python và Excel](07_python_csv_excel.md) | Từ file đang mở `uart_test_dma_tx.py` đến hàm xử lý dùng chung |
| [08 — Thực hành và xử lý lỗi](08_thuc_hanh_do_va_xu_ly_loi.md) | Đấu dây, chọn mode/baud, lệnh chạy, logic analyzer, kiểm tra lỗi |
| [09 — Câu hỏi kiểm tra sinh viên](09_cau_hoi_bao_ve.md) | Câu hỏi, đáp án gợi ý, bài tập đọc mã và thang điểm |
| [10 — Đối chiếu yêu cầu và báo cáo](10_doi_chieu_yeu_cau_va_bao_cao.md) | Dữ liệu đã có, bằng chứng còn thiếu, mẫu bảng và bố cục báo cáo |

Nếu chuẩn bị demo gấp: đọc **01 → 08 → 10**, sau đó học luồng **03 → 04 → 05** và tự trả lời **09**. Khi đọc trên GitHub hoặc VS Code, bấm vào đường dẫn mã nguồn trong từng tài liệu để mở file liên quan.

## 2. Bốn điều phải nói chính xác khi bảo vệ

1. **TX/RX gọi theo phía STM32.** Script có tên `dma_tx` nhưng PC đang nhận dữ liệu STM32 truyền ra. Script `dma_rx` mới là PC gửi vào STM32.
2. **1 MB trong mã là 1.000.000 byte**, không phải 1 MiB = 1.048.576 byte. TX dùng buffer 256 byte và tái sử dụng buffer, không giữ cả 1 MB trong RAM STM32.
3. **DWT và idle counter đo hai thứ khác nhau.** DWT đo các đoạn CPU phục vụ bài truyền; counter đếm số bước việc nền. Cột tải CPU hiện được ước tính từ DWT/thời gian PC, không tính từ counter.
4. **Mã có khả năng thực hiện chưa đồng nghĩa đã chứng minh yêu cầu.** CSV RX hiện chỉ có header; polling và IT chưa có lượt 1.500.000 baud trong CSV hiện có; bộ xuất Excel chưa tạo biểu đồ. Không được ghi “đã nhận 1 MB không lỗi ở 921600” khi chưa có lượt đo và CRC khớp.

## 3. Cách tự kiểm tra sau khi học

Em phải tự vẽ được hai luồng:

```text
TX: reset → main → sinh khối → truyền → tính CRC khối
    → khối tiếp theo → gửi CRC → gửi DWT2 → gửi IDL1 → PC lưu CSV/Excel

RX: PC gửi Length + Payload → USART → DMA ghi vòng đệm
    → HT/TC/IDLE báo vị trí → main đọc phần mới → parser và CRC
    → đủ Length → RESULT → PC đối chiếu độ dài và CRC
```

Các tài liệu chỉ bổ sung hướng dẫn. Những bước “đề xuất”, “cần đo thêm”, “có thể cải tiến” được ghi riêng với hành vi đang có trong chương trình.
