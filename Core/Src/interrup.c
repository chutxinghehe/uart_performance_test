#include "interrup.h"

extern UART_HandleTypeDef huart1;

#define total_byte 1000000U
#define buffer_size 256U

static uint8_t tx_buffer[buffer_size];
static uint32_t data_state;

//---------- cxing 01 ------------------
#include "uart_crc.h"
#include "uart_data.h"
static uint8_t crc_bytes[4];
static uint16_t pending_size;
static uint8_t crc_sending;
//--------------------------------------

volatile uint32_t byte_sent_it = 0;
volatile uint8_t truyen_done_it = 0;
volatile uint8_t truyen_loi_it = 0;
// Chu kỳ gọi HAL ban đầu + tổng chu kỳ HAL/callback trong các lần ngắt USART1.
volatile uint32_t cpu_busy_cycle_it = 0;
/** Chu kỳ chạy CRC32_Update() trong callback; đã nằm trong tổng IRQ. */
volatile uint32_t cpu_crc_cycles_it = 0;

/**
 * @brief Đặt lại trạng thái và khởi động khối truyền UART đầu tiên bằng ngắt.
 * @return HAL_OK nếu khởi động thành công; HAL_ERROR nếu không khởi động được.
 * @note Trả về sau khi khởi động; callback nối các khối dữ liệu và 4 byte CRC.
 */
HAL_StatusTypeDef UART_Interrup_Transmit(void)
{
    // khoi tao DWT
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;

    //---------- cxing 02 ------------------
    byte_sent_it = 0;
    truyen_done_it = 0;
    truyen_loi_it = 0;
    cpu_busy_cycle_it = 0;
    cpu_crc_cycles_it = 0;
    crc_sending = 0;
    data_state = 123456879U;
//	data_state = 946U;
    CRC32_Reset();
    //--------------------------------------

    /* Đo cả chi phí sinh khối dữ liệu đầu tiên. */
    uint32_t generate_start = DWT->CYCCNT;
    UART_GenerateData(tx_buffer, buffer_size, &data_state);
    cpu_busy_cycle_it += DWT->CYCCNT - generate_start;

    uint16_t chunk_size = buffer_size; // du lieu duoc lay trong moi lan truyen di

    //---------- cxing 03 ------------------
    pending_size = chunk_size;
    //--------------------------------------

    // Tạm chặn ngắt để IRQ không chen vào phép đo HAL ban đầu hoặc cập nhật bộ đếm.
    uint32_t saved_primask = __get_PRIMASK();
    __disable_irq();
    /* Sua idle v2: moc bat dau ngay truoc khoi payload dau tien. */
    UART_Test_PayloadStart();
    uint32_t start_cycle = DWT->CYCCNT;
    HAL_StatusTypeDef status = HAL_UART_Transmit_IT(&huart1, tx_buffer, chunk_size);
    cpu_busy_cycle_it += DWT->CYCCNT - start_cycle;

    // Cập nhật trước khi cho phép IRQ xử lý khối đầu tiên.
    if (status == HAL_OK)
    {
        byte_sent_it += chunk_size;
    }
    __set_PRIMASK(saved_primask);

    if (status != HAL_OK)
    {
        truyen_loi_it = 1;
        return HAL_ERROR;
    }
    return HAL_OK;
}




/**
 * @brief Truyền khối tiếp theo, gửi CRC và đặt cờ hoàn tất cho bài test IT.
 * @param huart UART vừa hoàn tất truyền một khối.
 * @note Chỉ xử lý USART1; gọi qua HAL_UART_TxCpltCallback() khi TEST == TXIT.
 */
void UART_Interrup_TxCpltCallback(UART_HandleTypeDef *huart)
{
    // con tro tro den dia chi uart su dung
    if (huart->Instance != USART1)
    {
        return;
    }

    //---------- cxing 04 ------------------
    if (crc_sending)
    {
        truyen_done_it = 1;
        return;
    }
    /* TC bao payload cuoi da phat xong; khong tinh CRC cuoi vao thoi gian. */
    if (byte_sent_it >= total_byte)
    {
        UART_Test_PayloadStop(byte_sent_it);
    }
    /** Đo riêng CRC, kể cả khi hàm cập nhật trả lỗi. */
    uint32_t crc_start = DWT->CYCCNT;
    HAL_StatusTypeDef crc_status = CRC32_Update(tx_buffer, pending_size);
    cpu_crc_cycles_it += DWT->CYCCNT - crc_start;
    if (crc_status != HAL_OK)
    {
        truyen_loi_it = 1;
        return;
    }
    //--------------------------------------

    if (byte_sent_it >= total_byte)
    {
        //---------- cxing 05 ------------------
        uint32_t crc = CRC32_GetValue();
        crc_bytes[0] = (uint8_t)crc;
        crc_bytes[1] = (uint8_t)(crc >> 8);
        crc_bytes[2] = (uint8_t)(crc >> 16);
        crc_bytes[3] = (uint8_t)(crc >> 24);

        if (HAL_UART_Transmit_IT(huart, crc_bytes, sizeof(crc_bytes)) == HAL_OK)
        {
            crc_sending = 1;
        }
        else
        {
            truyen_loi_it = 1;
        }
        //--------------------------------------
        return;
    }

    // tinh so byte truyen con lai
    uint32_t remaining = total_byte - byte_sent_it;
    uint16_t chunk_size;
    if (remaining > buffer_size)
    {
        chunk_size = buffer_size;
    }
    else
    {
        chunk_size = (uint16_t)remaining;
    }

    //---------- cxing 06 ------------------
    pending_size = chunk_size;
    //--------------------------------------

    UART_GenerateData(tx_buffer, chunk_size, &data_state);
    if (HAL_UART_Transmit_IT(huart, tx_buffer, chunk_size) == HAL_OK)
    {
        byte_sent_it += chunk_size;
    }
    else
    {
        truyen_loi_it = 1;
    }
}

/**
 * @brief Đo và cộng chu kỳ CPU xử lý ngắt USART1 cho bài test IT.
 * @note Gồm HAL, sinh khối tiếp theo và CRC trong callback; chưa gồm chi phí phần cứng vào/ra ngắt.
 * @note Gọi từ USART1_IRQHandler() thông qua bộ chọn TEST trong main.c.
 */
void UART_Interrup_IRQHandler(void)
{
    uint32_t start_cycle = DWT->CYCCNT;

    HAL_UART_IRQHandler(&huart1);
    cpu_busy_cycle_it += DWT->CYCCNT - start_cycle;
}
