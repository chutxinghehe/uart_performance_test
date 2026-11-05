#ifndef UART_DWT_H
#define UART_DWT_H

#include "main.h"

#define UART_DWT_MODE_POLLING 1U
#define UART_DWT_MODE_INTERRUPT 2U
#define UART_DWT_MODE_DMA 3U

/**
 * @brief Đóng gói và gửi báo cáo chu kỳ CPU qua UART.
 * @param huart UART dùng để gửi báo cáo.
 * @param cpu_cycles Tổng chu kỳ CPU trong phạm vi đo, đã gồm CRC.
 * @param crc_cycles Chu kỳ CRC32_Update(), đã nằm trong cpu_cycles.
 * @param mode Chế độ đo: 1 = polling, 2 = IT, 3 = DMA.
 * @return Trạng thái trả về từ HAL_UART_Transmit().
 * @note Gói 20 byte gồm "DWT2", mode, tổng chu kỳ, chu kỳ CRC và HCLK; số nguyên little-endian.
 * @note Gọi sau khi truyền xong dữ liệu và CRC, ngoài khoảng đo DWT.
 */
static inline HAL_StatusTypeDef UART_SendDWTResult(UART_HandleTypeDef *huart,
                                                  uint32_t cpu_cycles,
                                                  uint32_t crc_cycles,
                                                  uint32_t mode)
{
    uint8_t frame[20] = {'D', 'W', 'T', '2'};
    uint32_t values[4] = {mode, cpu_cycles, crc_cycles, HAL_RCC_GetHCLKFreq()};
    for (uint32_t word = 0; word < 4U; word++)
    {
        for (uint32_t byte = 0; byte < 4U; byte++)
        {
            frame[4U + word * 4U + byte] = (uint8_t)(values[word] >> (byte * 8U));
        }
    }
    return HAL_UART_Transmit(huart, frame, sizeof(frame), 1000U);
}

#endif
