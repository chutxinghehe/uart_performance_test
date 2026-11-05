# 03 — Từ reset đến main, ngoại vi và ngắt

[Mục lục](README.md) · [Tiếp: Ba cách TX](04_luong_truyen_polling_it_dma.md)

Nguồn chính: [main.c](../../Core/Src/main.c), [usart.c](../../Core/Src/usart.c), [stm32f1xx_it.c](../../Core/Src/stm32f1xx_it.c).

## 1. Chọn bài trước khi biên dịch

Trong `main.c`:

```c
#define TXPOLLING 1
#define TXIT 2
#define TXDMA 3
#define TEST_DMA_RX 4

#ifndef TEST
#define TEST TXDMA
#endif
```

`#if TEST == ...` là quyết định ở bước tiền xử lý. Ví dụ chọn TXDMA thì các nhánh thực thi dành cho TXIT/RX trong `main.c` không được đưa vào bản biên dịch đó. Đây không phải menu chọn lúc firmware đang chạy.

`#ifndef TEST` cho phép build system định nghĩa `TEST` từ bên ngoài; nếu đã định nghĩa trong compiler thì dòng mặc định trong file không áp dụng. Kiểm tra cả cấu hình compiler khi firmware có hành vi khác dòng đang nhìn thấy. Mã có `#error` chặn giá trị TEST ngoài bốn mode hợp lệ.

## 2. Thứ tự khởi động

```text
Reset_Handler trong startup
  → SystemInit và runtime C khởi tạo RAM/biến toàn cục
  → main()
      → HAL_Init()
      → SystemClock_Config()
      → DWT_Init()
      → MX_GPIO_Init()
      → MX_DMA_Init()
      → MX_CRC_Init()
      → MX_USART1_UART_Init()
      → bắt đầu bài thử theo TEST
      → while (1)
```

| Hàm | Nó làm gì trong project? | Vì sao cần? |
| --- | --- | --- |
| `HAL_Init` | Khởi tạo nền HAL, time base SysTick và gọi MSP chung | Các hàm HAL và `HAL_GetTick` cần nền hệ thống |
| `SystemClock_Config` | Chọn HSE, PLL ×9, SYSCLK/HCLK, chia APB1/APB2 | Baud và đổi chu kỳ sang thời gian phụ thuộc clock |
| `DWT_Init` | Bật trace, xóa CYCCNT, bật bộ đếm chu kỳ | Chuẩn bị công cụ đo CPU |
| `MX_GPIO_Init` | PC13 output push-pull, ban đầu thấp | Quan sát việc nền bằng GPIO/LED |
| `MX_DMA_Init` | Bật clock DMA1 và ngắt Channel 4/5 | DMA và IRQ cần được cấp clock/enable |
| `MX_CRC_Init` | Khởi tạo ngoại vi CRC | Các bài TX dùng CRC phần cứng |
| `MX_USART1_UART_Init` | Đặt USART1, baud, 8N1 và gọi HAL init | UART có cấu hình thống nhất trước khi truyền/nhận |

`HAL_UART_Init` dẫn đến `HAL_UART_MspInit` trong `usart.c`: bật clock USART1/GPIOA, cấu hình PA9/PA10, khởi tạo DMA TX/RX, liên kết handle và bật NVIC USART1.

## 3. Các cấu hình DMA cần giải thích

| Thuộc tính | TX | RX |
| --- | --- | --- |
| Instance | DMA1_Channel4 | DMA1_Channel5 |
| Direction | MEMORY_TO_PERIPH | PERIPH_TO_MEMORY |
| PeriphInc | DISABLE | DISABLE |
| MemInc | ENABLE | ENABLE |
| Alignment | BYTE cả RAM và ngoại vi | BYTE cả RAM và ngoại vi |
| Mode | NORMAL | CIRCULAR |
| Priority | LOW | LOW |

`PeriphInc = DISABLE` vì mỗi byte đều đi qua cùng thanh ghi dữ liệu USART1. `MemInc = ENABLE` vì byte tiếp theo nằm ở địa chỉ RAM tiếp theo. BYTE phù hợp khung 8 bit đang dùng.

`__HAL_LINKDMA(uartHandle, hdmatx/hdmarx, ...)` nối cấu trúc UART với DMA. Nhờ đó HAL biết DMA nào phục vụ UART, và từ handle DMA truy được UART cha để gọi callback đúng đối tượng.

USART1, DMA Channel 4 và Channel 5 đang có ưu tiên NVIC 0. SysTick có ưu tiên thấp hơn theo cấu hình project. Ngắt UART/DMA kéo dài có thể làm trễ main và tick; tránh đưa thao tác in/ghi file/chờ dài vào callback.

`HAL_UART_MspDeInit` là đường tháo cấu hình: tắt clock USART1, trả chân GPIO, deinit DMA, tắt ngắt USART1. Luồng chạy bình thường hiện không gọi đường tháo này.

## 4. main làm gì trong từng mode?

| Mode | Trước while | Trong while |
| --- | --- | --- |
| Polling | Bắt đầu đo idle; gọi truyền chặn, hàm tự gửi DWT; main gửi IDL1 | Bài thử đã xong, không chạy bước nền cho lượt đó |
| IT | Bắt đầu đo idle; gọi khởi động IT | Kiểm tra lỗi; chưa xong thì chạy `CPULoad_IdleStep`; xong thì chốt idle và gửi báo cáo một lần |
| DMA | Bắt đầu đo idle; gọi khởi động DMA | Giống IT, dùng các cờ/bộ đếm của DMA |
| RX | Gọi `UART_RX_DMA_Start` | Gọi `UART_RX_DMA_Process` liên tục; đủ dữ liệu thì gửi RESULT một lần |

TX tự bắt đầu sau reset, không đợi PC gửi lệnh START. Vì vậy PC phải mở cổng và sẵn sàng nhận trước khi reset STM32 ở bài TX. Bài RX thì STM32 phải sẵn sàng nhận trước khi PC gửi.

## 5. Các hàm phụ trong main.c

### `UART_Test_IdleStart()`

Hàm nội bộ cho các bài TX. Nó xóa `idle_counter`, `idle_result`, `idle_elapsed_ms`, `idle_measurement_done`; đặt PC13 thấp và ghi `idle_start_ms = HAL_GetTick()`.

Đây là bắt đầu cửa sổ đếm việc nền, chưa phải phép hiệu chuẩn. Hàm không gọi `CPULoad_Calibrate`.

### `UART_Test_IdleStop()`

Nếu chưa chốt, lấy chênh lệch tick vào `idle_elapsed_ms`, sao chép `idle_counter` sang `idle_result`, đặt cờ done. Gọi nhiều lần cũng chỉ chốt lần đầu. Ở RX hàm không thực hiện phép đo này.

Polling gọi trước khi gửi DWT. IT/DMA gọi từ main sau khi cờ truyền xong đã được đặt và IRQ cuối đã trả về. Khi ấy bộ đếm DWT của IRQ cuối cũng đã cộng xong.

### `UART_Test_SendIdleResult()`

Tạo 8 byte `IDL1 + uint32 counter`, số nguyên little-endian, rồi gửi bằng `HAL_UART_Transmit`. Giá trị gửi là `idle_result`, **không gửi `idle_elapsed_ms`**. Báo cáo nằm ngoài cửa sổ đo.

### `HAL_UART_TxCpltCallback(huart)`

Callback chung do HAL gọi. Nó chuyển đến `UART_Interrup_TxCpltCallback` hoặc `UART_DMA_TxCpltCallback` theo TEST. Các mode còn lại không xử lý TX tại callback này.

### `HAL_UART_ErrorCallback(huart)`

Chỉ quan tâm USART1. Mode IT đặt `truyen_loi_it`, DMA đặt `truyen_loi_dma`; main nhìn cờ để gọi `Error_Handler`. Nhánh RX hiện chưa đặt cờ lỗi riêng, chưa phục hồi hoặc khởi động lại nhận ở callback này.

### `Error_Handler()`

Tắt ngắt rồi lặp vô hạn. Nó không gửi lỗi về PC, không nháy LED báo lỗi và không tự phục hồi. PC thường chỉ thấy thiếu dữ liệu/timeout. Khi debug, dừng CPU để xem có đang nằm tại đây không.

`assert_failed` chỉ có khi bật `USE_FULL_ASSERT`, hiện là chỗ trống cho người dùng thêm xử lý; không phải cơ chế báo lỗi đo UART chính.

## 6. Ngắt đi qua những hàm nào?

### TX IT

```text
USART1_IRQHandler                    [stm32f1xx_it.c]
 → UART_Test_USART_IRQHandler        [main.c]
 → UART_Interrup_IRQHandler           [interrup.c, bắt đầu đo DWT]
 → HAL_UART_IRQHandler               [HAL, phục vụ TXE/TC]
    → HAL_UART_TxCpltCallback         [main.c, chỉ khi hoàn tất khối]
       → UART_Interrup_TxCpltCallback [tính CRC/nối khối/đánh dấu xong]
 → cộng DWT rồi trở về main
```

Ngắt nạp byte không đồng nghĩa mỗi lần ngắt đều gọi callback hoàn tất khối. Callback ứng dụng xuất hiện sau khi khối đã phát hết.

### TX DMA normal

```text
DMA1_Channel4_IRQHandler → UART_Test_DMA_IRQHandler
 → UART_DMA_IRQHandler → HAL_DMA_IRQHandler
 → HAL xử lý HT/TC; khi TC bật ngắt UART TC

USART1_IRQHandler → UART_Test_USART_IRQHandler
 → UART_DMA_USART_IRQHandler → HAL_UART_IRQHandler
 → UART TC → HAL_UART_TxCpltCallback → UART_DMA_TxCpltCallback
```

**DMA TC** nghĩa là DMA chuyển xong byte từ RAM sang ngoại vi. **UART TC** nghĩa là UART phát xong cả byte cuối trên dây. HAL đang dùng chờ UART TC rồi mới báo hoàn tất TX normal cho ứng dụng. Vì vậy TX DMA vẫn cần ngắt USART1.

### RX DMA circular + IDLE

```text
DMA1_Channel5_IRQHandler → HAL_DMA_IRQHandler → HT/TC callback của HAL
                                              → HAL_UARTEx_RxEventCallback

USART1_IRQHandler → UART_Test_USART_IRQHandler → HAL_UART_IRQHandler
                                              → IDLE → HAL_UARTEx_RxEventCallback

main → UART_RX_DMA_Process → xử lý dữ liệu đã được báo
```

Ngắt chỉ báo vị trí cho RX; parser và tính CRC chạy trong main. Xem cách xác định phần mới và giới hạn của cơ chế này ở tài liệu 05.

`SysTick_Handler` gọi `HAL_IncTick` để tăng tick. Các handler NMI/HardFault/MemManage/BusFault/UsageFault dừng trong vòng lặp; SVC, DebugMon, PendSV không triển khai tác vụ ứng dụng ở project này.
