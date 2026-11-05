#ifndef __kxt_checkcrc
#define __kxt_checkcrc


#include "main.h"

/**
 * @brief Bật clock và đặt lại CRC phần cứng về 0xFFFFFFFF.
 */
void CRC32_Reset(void);
/**
 * @brief Tích lũy CRC phần cứng cho khối dữ liệu.
 * @param data Dữ liệu đầu vào.
 * @param length Số byte dữ liệu, phải chia hết cho 4.
 * @return HAL_OK nếu thành công; HAL_ERROR nếu tham số không hợp lệ.
 */
HAL_StatusTypeDef CRC32_Update(const uint8_t *data, uint32_t length);
/**
 * @brief Đọc giá trị CRC phần cứng đang tích lũy.
 * @return CRC 32 bit hiện tại.
 */
uint32_t CRC32_GetValue(void);
/**
 * @brief Reset và tính CRC phần cứng cho một vùng dữ liệu.
 * @param data Dữ liệu đầu vào.
 * @param length Số byte dữ liệu, phải chia hết cho 4.
 * @param[out] result Nơi nhận CRC 32 bit.
 * @return HAL_OK nếu thành công; HAL_ERROR nếu tham số không hợp lệ.
 */
HAL_StatusTypeDef CRC32_Compute(const uint8_t *data, uint32_t length, uint32_t *result);

/**
 * @brief Cập nhật CRC phần mềm tương thích zlib cho một khối dữ liệu.
 * @param crc CRC tích lũy; dùng 0 khi bắt đầu.
 * @param data Dữ liệu đầu vào.
 * @param length Số byte dữ liệu, không cần chia hết cho 4.
 * @return CRC tích lũy mới.
 */
uint32_t CRC32_ZlibUpdate(uint32_t crc, const uint8_t *data, uint32_t length);




#endif
