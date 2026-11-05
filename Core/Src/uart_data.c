#include "uart_data.h"
#include <stddef.h>

/**
 * @brief Sinh chuỗi byte giả ngẫu nhiên bằng xorshift32 và cập nhật trạng thái.
 * @param[out] buffer Vùng đệm nhận dữ liệu, có ít nhất length byte.
 * @param length Số byte cần sinh.
 * @param[in,out] state Trạng thái được giữ lại để sinh tiếp ở lần gọi sau.
 * @note Cùng seed cho cùng chuỗi; seed 0 được thay bằng 1.
 * @note Không xử lý nếu con trỏ NULL hoặc length bằng 0.
 */
void UART_GenerateData(uint8_t *buffer, uint16_t length, uint32_t *state)
{
    if (buffer == NULL || state == NULL || length == 0U)
        return;

    uint32_t value = *state;
    if (value == 0U)
        value = 1U; /* xorshift32 cần trạng thái khác 0. */

    for (uint16_t i = 0; i < length; i++)
    {
       value ^= value << 13;
        value ^= value >> 17;
        value ^= value << 5;
        buffer[i] = (uint8_t)(value >> 24);
    } 

    *state = value; /* Giữ trạng thái để lần gọi sau sinh tiếp chuỗi dữ liệu. */
}
