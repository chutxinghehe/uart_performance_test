#ifndef INTERRUP_H
#define INTERRUP_H

#include "main.h"
extern volatile uint32_t byte_sent_it;
extern volatile uint8_t truyen_done_it;
extern volatile uint8_t truyen_loi_it;
extern volatile uint32_t cpu_busy_cycle_it;
extern volatile uint32_t cpu_crc_cycles_it;

/**
 * @brief Khởi động bài truyền UART bằng ngắt và đặt lại trạng thái đo.
 * @return HAL_OK nếu khởi động thành công; HAL_ERROR nếu thất bại.
 */
HAL_StatusTypeDef UART_Interrup_Transmit(void);
/**
 * @brief Xử lý khối truyền hoàn tất, nối dữ liệu và CRC cho bài test IT.
 * @param huart UART vừa hoàn tất truyền một khối.
 */
void UART_Interrup_TxCpltCallback(UART_HandleTypeDef *huart);
/**
 * @brief Xử lý ngắt USART1 và tích lũy chu kỳ CPU cho bài test IT.
 */
void UART_Interrup_IRQHandler(void);

#endif
