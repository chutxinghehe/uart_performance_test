#ifndef UART_DATA_H
#define UART_DATA_H

#include <stdint.h>

/**
 * @brief Sinh dữ liệu xorshift32 và giữ trạng thái giữa các khối.
 * @param[out] buffer Vùng đệm nhận length byte dữ liệu.
 * @param length Số byte cần sinh.
 * @param[in,out] state Seed ban đầu và trạng thái cho lần gọi tiếp theo.
 * @note Cùng seed cho cùng chuỗi; seed 0 được thay bằng 1.
 */
void UART_GenerateData(uint8_t *buffer, uint16_t length, uint32_t *state);

#endif
