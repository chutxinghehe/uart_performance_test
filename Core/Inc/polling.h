#ifndef POLLING_H
#define POLLING_H

#include "main.h"

extern volatile uint32_t cpu_busy_cycles;
extern volatile uint32_t cpu_crc_cycles;
/**
 * @brief Truyền dữ liệu và CRC bằng polling, sau đó gửi báo cáo DWT.
 * @return HAL_OK khi hoàn tất; mã lỗi HAL nếu thất bại.
 * @note Hàm chặn đến khi truyền xong hoặc có lỗi.
 */
HAL_StatusTypeDef UART_Polling_Transmit(void);

#endif
