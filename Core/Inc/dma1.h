#ifndef DMA1_H
#define DMA1_H

#include "main.h"

/**
 * @brief Khởi động bài truyền UART bằng DMA và đặt lại trạng thái đo.
 * @return HAL_OK nếu khởi động thành công; HAL_ERROR nếu thất bại.
 */
HAL_StatusTypeDef UART_DMA_Transmit(void);
/**
 * @brief Đọc trạng thái hoàn tất truyền DMA.
 * @return 1 khi dữ liệu và CRC đã phát hết; 0 nếu chưa hoàn tất.
 */
uint8_t UART_DMA_IsDone(void);

/**
 * @brief Xử lý ngắt DMA TX và tích lũy chu kỳ chạy HAL.
 */
void UART_DMA_IRQHandler(void);
/**
 * @brief Xử lý ngắt USART1 và tích lũy chu kỳ CPU cho bài test DMA.
 */
void UART_DMA_USART_IRQHandler(void);
/**
 * @brief Xử lý khối DMA hoàn tất, nối dữ liệu và CRC đến khi truyền xong.
 * @param huart UART vừa hoàn tất truyền một khối.
 */
void UART_DMA_TxCpltCallback(UART_HandleTypeDef *huart);

extern volatile uint32_t byte_sent_dma;
extern volatile uint8_t truyen_done_dma;
extern volatile uint8_t truyen_loi_dma;
extern volatile uint32_t cpu_busy_cycle_dma;
extern volatile uint32_t cpu_crc_cycles_dma;
#endif
