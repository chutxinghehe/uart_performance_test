#include "uart_crc.h"

/**
 * @brief Cập nhật CRC-32 phần mềm tương thích zlib.crc32() cho một khối dữ liệu.
 * @param crc CRC của các khối trước; dùng 0 cho khối đầu tiên.
 * @param data Dữ liệu cần cập nhật CRC.
 * @param length Số byte dữ liệu.
 * @return CRC sau khi ghép thêm khối dữ liệu.
 * @note Nhận mọi độ dài byte, không chèn byte đệm.
 */
uint32_t CRC32_ZlibUpdate(uint32_t crc, const uint8_t *data, uint32_t length)
{
    crc ^= 0xFFFFFFFFU;
    for (uint32_t i = 0; i < length; i++)
    {
        crc ^= data[i];
        for (uint32_t bit = 0; bit < 8U; bit++)
            crc = (crc >> 1) ^ ((crc & 1U) ? 0xEDB88320U : 0U);
    }
    return crc ^ 0xFFFFFFFFU;
}



//__________________________________________________________________________
/**
 * @brief Bật clock và đặt lại bộ CRC phần cứng STM32F1.
 * @note Giá trị khởi đầu là 0xFFFFFFFF; gọi trước khối đầu của phiên dữ liệu mới.
 */
void CRC32_Reset(void)
{
    // Bật clock CRC
    RCC->AHBENR |= RCC_AHBENR_CRCEN;

    // Reset CRC về giá trị khởi đầu của STM32F1: 0xFFFFFFFF.
    CRC->CR = CRC_CR_RESET;
}




//__________________________________________________________________________
/**
 * @brief Cập nhật CRC phần cứng bằng các word ghép từ 4 byte little-endian.
 * @param data Dữ liệu cần cập nhật CRC.
 * @param length Số byte dữ liệu, phải chia hết cho 4.
 * @return HAL_OK nếu thành công; HAL_ERROR nếu con trỏ hoặc độ dài không hợp lệ.
 * @note Reset trước khối đầu; các khối tiếp theo dùng tiếp CRC tích lũy.
 */
HAL_StatusTypeDef CRC32_Update(const uint8_t *data, uint32_t length)
{
    if ((data == NULL) || ((length % 4U) != 0U))
    {
        return HAL_ERROR;
    }

    for (uint32_t i = 0; i < length; i += 4U)
    {
        // Ghép 4 byte theo thứ tự little-endian thành một word.
        uint32_t word =
              (uint32_t)data[i]
            | ((uint32_t)data[i + 1U] << 8)
            | ((uint32_t)data[i + 2U] << 16)
            | ((uint32_t)data[i + 3U] << 24);

        // Mỗi lần ghi một word, CRC peripheral tự cập nhật CRC.
        CRC->DR = word;
    }

    return HAL_OK;
}



//__________________________________________________________________________
/**
 * @brief Đọc CRC tích lũy hiện tại từ thanh ghi CRC->DR.
 * @return Giá trị CRC phần cứng 32 bit.
 * @note Đọc kết quả không đặt lại bộ CRC.
 */
uint32_t CRC32_GetValue(void)
{
    return CRC->DR;
}


//__________________________________________________________________________
/**
 * @brief Tính CRC phần cứng cho một vùng dữ liệu từ trạng thái khởi đầu.
 * @param data Dữ liệu cần tính CRC.
 * @param length Số byte dữ liệu, phải chia hết cho 4.
 * @param[out] result Nơi nhận CRC 32 bit khi thành công.
 * @return HAL_OK nếu thành công; HAL_ERROR nếu con trỏ hoặc độ dài không hợp lệ.
 * @note Thực hiện lần lượt reset, cập nhật và đọc CRC.
 */
HAL_StatusTypeDef CRC32_Compute(const uint8_t *data, uint32_t length, uint32_t *result)
{
    if ((data == NULL) || (result == NULL) || ((length % 4U) != 0U))
    {
        return HAL_ERROR;
    }

    CRC32_Reset();

    HAL_StatusTypeDef status = CRC32_Update(data, length);
    if (status != HAL_OK)
    {
        return status;
    }

    *result = CRC32_GetValue();
    return HAL_OK;
}
