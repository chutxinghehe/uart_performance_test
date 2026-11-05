# 02 — Bản đồ các file và quan hệ giữa chúng

[Mục lục](README.md) · [Tiếp: Khởi động và main](03_khoi_dong_main_va_ngat.md)

## 1. Nhìn cấu trúc theo công việc

```text
Test_hieu_nang_UART/
├── Core/Inc, Core/Src     Khởi động ứng dụng, cấu hình ngoại vi, đo và CRC
├── nhung/                Ba cách truyền TX
├── RX_UART_Lib/          Nhận DMA circular + IDLE và tiện ích DWT
├── TEST_PYTHON/          Chạy phép thử PC, kiểm tra CRC, CSV, Excel, test offline
├── Drivers/              HAL và CMSIS đi kèm project
├── MDK-ARM/              Project Keil, startup, file build
├── Test_hieu_nang_UART.ioc Cấu hình CubeMX
└── git_tutorials/huongdan/ Bộ hướng dẫn này
```

File `.h` khai báo giao diện để file khác gọi hàm/đọc biến. File `.c` chứa phần thực hiện. `#include` một header không thay thế việc thêm file `.c` tương ứng vào project build.

## 2. Nhóm Core: điều phối và công cụ chung

| File | Vai trò và hàm cần nhớ |
| --- | --- |
| [main.c](../../Core/Src/main.c) | Chọn `TEST`, khởi tạo, chạy một bài thử, vòng nền, gửi báo cáo, phân luồng callback/IRQ; xem chi tiết tài liệu 03 |
| [main.h](../../Core/Inc/main.h) | Header chung HAL; khai báo `Error_Handler`, `UART_Test_USART_IRQHandler`, `UART_Test_DMA_IRQHandler`, `UART_Test_IdleStop` |
| [usart.c](../../Core/Src/usart.c), [usart.h](../../Core/Inc/usart.h) | `huart1`, hai handle DMA; `MX_USART1_UART_Init`, `HAL_UART_MspInit`, `HAL_UART_MspDeInit`; baud, chân UART, mode DMA, liên kết DMA với UART |
| [dma.c](../../Core/Src/dma.c), [dma.h](../../Core/Inc/dma.h) | `MX_DMA_Init`: bật clock DMA1 và NVIC Channel 4/5. Cấu hình hướng/kích thước/mode của từng channel nằm trong `usart.c` |
| [gpio.c](../../Core/Src/gpio.c), [gpio.h](../../Core/Inc/gpio.h) | `MX_GPIO_Init`: bật clock port và cấu hình PC13 output |
| [crc.c](../../Core/Src/crc.c), [crc.h](../../Core/Inc/crc.h) | `hcrc`, `MX_CRC_Init`, MSP init/deinit của CRC. Bật và khởi tạo ngoại vi; thuật toán bao cho ứng dụng ở `uart_crc.c` |
| [uart_crc.c](../../Core/Src/uart_crc.c), [uart_crc.h](../../Core/Inc/uart_crc.h) | CRC phần cứng TX: Reset/Update/GetValue/Compute; CRC phần mềm RX: `CRC32_ZlibUpdate` |
| [uart_data.c](../../Core/Src/uart_data.c), [uart_data.h](../../Core/Inc/uart_data.h) | `UART_GenerateData`: xorshift32 sinh dữ liệu từng khối, giữ trạng thái qua con trỏ |
| [uart_dwt.h](../../Core/Inc/uart_dwt.h) | Hàm `static inline UART_SendDWTResult` đóng gói và gửi DWT2. Có định nghĩa hàm ngay trong header, không có `uart_dwt.c` |
| [cpu_load.c](../../Core/Src/cpu_load.c), [cpu_load.h](../../Core/Inc/cpu_load.h) | Biến `idle_counter`, `idle_max_count`; `CPULoad_Calibrate`, `CPULoad_IdleStep` |
| [stm32f1xx_it.c](../../Core/Src/stm32f1xx_it.c), [stm32f1xx_it.h](../../Core/Inc/stm32f1xx_it.h) | Các cửa vào ngắt: SysTick, USART1, DMA1 Channel 4/5, các exception CPU |
| [stm32f1xx_hal_msp.c](../../Core/Src/stm32f1xx_hal_msp.c) | `HAL_MspInit`: clock AFIO/PWR, tắt JTAG và giữ SWD; MSP UART nằm trong `usart.c` |
| [system_stm32f1xx.c](../../Core/Src/system_stm32f1xx.c) | Hạ tầng CMSIS: `SystemInit`, `SystemCoreClock`, `SystemCoreClockUpdate`; thiết lập hệ thống ban đầu và cập nhật biến tần số |
| [stm32f1xx_hal_conf.h](../../Core/Inc/stm32f1xx_hal_conf.h) | Chọn module HAL và hằng cấu hình; không phải nơi chọn polling/IT/DMA của bài thử |

Phân biệt hai cặp dễ nhầm: `crc.c` khởi tạo ngoại vi, `uart_crc.c` tính CRC cho ứng dụng; `dma.c` khởi tạo bộ điều khiển/ngắt, `nhung/dma1.c` thực hiện bài TX DMA.

## 3. Nhóm truyền và nhận

| File | Các hàm của ứng dụng |
| --- | --- |
| [polling.c](../../nhung/polling.c), [polling.h](../../nhung/polling.h) | `UART_Polling_Transmit`: tự chạy hết payload, CRC, chốt DWT, gửi DWT trước khi trả về |
| [interrup.c](../../nhung/interrup.c), [interrup.h](../../nhung/interrup.h) | `UART_Interrup_Transmit`, `UART_Interrup_TxCpltCallback`, `UART_Interrup_IRQHandler` |
| [dma1.c](../../nhung/dma1.c), [dma1.h](../../nhung/dma1.h) | `UART_DMA_Transmit`, `UART_DMA_TxCpltCallback`, `UART_DMA_IRQHandler`, `UART_DMA_USART_IRQHandler`, `UART_DMA_IsDone` |
| [uart_rx_dma.c](../../RX_UART_Lib/uart_rx_dma.c), [uart_rx_dma.h](../../RX_UART_Lib/uart_rx_dma.h) | `UART_RX_DMA_Start`, `HAL_UARTEx_RxEventCallback`, `UART_RX_DMA_Process`; hàm nội bộ `UART_RX_ProcessByte` |
| [dwt.c](../../RX_UART_Lib/dwt.c), [dwt.h](../../RX_UART_Lib/dwt.h) | `DWT_Init`, `DWT_GetCycles`, `DWT_CyclesToUs`; bộ tiện ích đọc/đổi chu kỳ |

Tên file thực tế là `interrup.c`, hàm thực tế là `UART_Interrup_...`; khi tìm mã phải dùng đúng tên này.

## 4. Nhóm Python và kết quả

| File | Vai trò |
| --- | --- |
| [uart_test_dma_tx.py](../../TEST_PYTHON/uart_test_dma_tx.py) | File đang mở trong IDE: cấu hình COM/baud/DMA mode và `main()` gọi luồng dùng chung |
| [uart_test_it_tx.py](../../TEST_PYTHON/uart_test_it_tx.py) | Cấu hình bài IT TX, mode 2 |
| [uart_test_polling_tx.py](../../TEST_PYTHON/uart_test_polling_tx.py) | Cấu hình bài polling TX, mode 1 |
| [uart_test_support.py](../../TEST_PYTHON/uart_test_support.py) | Nhận TX, giữ `TestResult`, CRC STM32, giải DWT/IDL1, tính chỉ số, in và lưu kết quả |
| [uart_test_dma_rx.py](../../TEST_PYTHON/uart_test_dma_rx.py) | PC gửi Length + Payload ngẫu nhiên; kiểm tra dòng RESULT và ghi CSV RX |
| [uart_excel_report.py](../../TEST_PYTHON/uart_excel_report.py) | Đọc tất cả CSV đúng mẫu trong thư mục và tạo workbook tổng hợp/chi tiết |
| [test_uart_offline.py](../../TEST_PYTHON/test_uart_offline.py) | Giả lập serial và dữ liệu để kiểm tra phần Python, không kiểm tra tín hiệu thật |
| [requirements.txt](../../TEST_PYTHON/requirements.txt) | `pyserial` để dùng COM, `openpyxl` để xuất Excel |
| [README_UART_EXCEL.md](../../TEST_PYTHON/README_UART_EXCEL.md) | Hướng dẫn sẵn có về script và báo cáo; một số giá trị baud trong bảng cũ chưa khớp mã hiện tại |
| `uart_polling_tx_results.csv`, `uart_it_tx_results.csv`, `uart_dma_tx_results.csv` | Lịch sử ba bài TX cùng schema 13 cột |
| `uart_dma_rx_results.csv` | Lịch sử RX với schema riêng 11 cột; hiện chỉ có header |
| `uart_summary.xlsx` | Báo cáo tái tạo từ CSV; không phải nguồn duy nhất lưu số liệu |

File `~$uart_summary.xlsx` là file tạm khóa do Excel tạo. `__pycache__` là bytecode Python; `.venv` là môi trường thư viện. Không học thuật toán UART từ các file này.

## 5. Cấu hình và thư viện nền

- [Test_hieu_nang_UART.ioc](../../Test_hieu_nang_UART.ioc): cấu hình CubeMX, MCU, chân, DMA, clock, NVIC. Khi sinh lại mã cần kiểm tra các sửa đổi thủ công ngoài vùng `USER CODE`, đặc biệt baud và đường gọi IRQ.
- [Test_hieu_nang_UART.uvprojx](../../MDK-ARM/Test_hieu_nang_UART.uvprojx): project Keil, danh sách source, include path, compiler/linker. Có đường dẫn include cho `nhung` và `RX_UART_Lib`.
- [startup_stm32f103xb.s](../../MDK-ARM/startup_stm32f103xb.s): vector table, stack và Reset_Handler; nối tên ngắt phần cứng với hàm C.
- Thư mục `MDK-ARM/Test_hieu_nang_UART/`: file linker `.sct`, log, báo cáo build/call graph và sản phẩm build khi có. Log cũ không chứng minh mã hiện tại vừa build thành công.
- [HAL UART](../../Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_uart.c), [HAL DMA](../../Drivers/STM32F1xx_HAL_Driver/Src/stm32f1xx_hal_dma.c): triển khai HAL đang dùng; có thể mở để lần từ IRQ tới callback.
- `Drivers/CMSIS`: định nghĩa thanh ghi, lõi Cortex-M3, DWT, NVIC và hỗ trợ thiết bị.
- `.mxproject`: metadata CubeMX; `.vscode`: cấu hình IDE; `.gitignore`: quy tắc Git bỏ qua file. Các bài `git_tutorials/git_*.md` hướng dẫn Git, không tham gia firmware.

## 6. Ba chuỗi liên kết quan trọng nhất

```text
main.c → nhung/dma1.c → HAL_UART_Transmit_DMA → DMA và USART
ngắt USART → stm32f1xx_it.c → main.c phân luồng → dma1.c → HAL → callback

ngắt RX → HAL → uart_rx_dma.c cập nhật vị trí
main.c → UART_RX_DMA_Process → UART_RX_ProcessByte → CRC32_ZlibUpdate

uart_test_dma_tx.py → uart_test_support.py → CSV
                                         → uart_excel_report.py → Excel
```

Giáo viên có thể yêu cầu chỉ đường gọi một hàm thay vì chỉ định nghĩa hàm. Em cần phân biệt hàm do `main` gọi, hàm do IRQ gọi và callback do HAL gọi.
