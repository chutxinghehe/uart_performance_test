#include "dma1.h"
#include "stm32f1xx.h"
#include "uart_crc.h"
#include "uart_data.h"
extern UART_HandleTypeDef huart1;

#define total_byte 1000000U
#define buffer_size 256U

/** Buffer dùng lại cho các khối truyền DMA. */
static uint8_t tx_buffer[buffer_size];
static uint32_t data_state;
static uint8_t crc_bytes[4];
static uint16_t pending_size;
static uint8_t crc_sending;

/** Số byte đã yêu cầu truyền và trạng thái của bài test. */
 volatile uint32_t byte_sent_dma = 0;
 volatile uint8_t truyen_done_dma = 0;
 volatile uint8_t truyen_loi_dma = 0;

/** Tổng chu kỳ khởi động DMA và xử lý HAL trong ngắt DMA/USART. */
 volatile uint32_t cpu_busy_cycle_dma = 0;
/** Chu kỳ CRC32_Update() trong callback; đã nằm trong bộ đếm tổng. */
volatile uint32_t cpu_crc_cycles_dma = 0;

//-------------------------------------------------------------------------------------------
/**
 * @brief Đặt lại trạng thái và khởi động khối truyền UART đầu tiên bằng DMA.
 * @return HAL_OK nếu khởi động thành công; HAL_ERROR nếu không khởi động được.
 * @note DWT tại đây chỉ đo lời gọi HAL, chưa tính sinh khối dữ liệu đầu tiên.
 */
HAL_StatusTypeDef UART_DMA_Transmit(void)
{
	/** Bật bộ đếm chu kỳ DWT và đặt lại kết quả đo CPU. */
	CoreDebug ->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
	DWT ->CYCCNT = 0;
	DWT -> CTRL |= DWT_CTRL_CYCCNTENA_Msk;
	
	byte_sent_dma = 0;
	truyen_done_dma = 0;
	truyen_loi_dma = 0;
	cpu_busy_cycle_dma = 0;
	cpu_crc_cycles_dma = 0;
	crc_sending = 0;
	data_state = 123246789U;
	CRC32_Reset();


	/* Đo cả chi phí sinh khối dữ liệu đầu tiên. */
	uint32_t generate_start = DWT->CYCCNT;
	/* Sinh khối đầu trước khi đo lời gọi HAL. */
	UART_GenerateData(tx_buffer, buffer_size, &data_state);
	cpu_busy_cycle_dma += DWT->CYCCNT - generate_start;


	pending_size = buffer_size;


	/** Chặn IRQ đến khi đã đo HAL và cập nhật trạng thái khối đầu, giống IT. */
	uint32_t saved_primask = __get_PRIMASK();
	__disable_irq();
	/* Sua idle v2: moc bat dau ngay truoc khoi payload dau tien. */
	UART_Test_PayloadStart();
	uint32_t start_cycle = DWT->CYCCNT;
	HAL_StatusTypeDef status = HAL_UART_Transmit_DMA(&huart1, tx_buffer, pending_size);
	
	cpu_busy_cycle_dma += DWT->CYCCNT - start_cycle;


	if (status == HAL_OK)
	{
		byte_sent_dma += pending_size;
	}
	__set_PRIMASK(saved_primask);


	if (status != HAL_OK)
	{
		truyen_loi_dma = 1;
		return HAL_ERROR;
	}
	return HAL_OK;
}



//-------------------------------------------------------------------------------------------
/**
 * @brief Truyền khối DMA tiếp theo, gửi CRC và đặt cờ hoàn tất sau khi CRC phát hết.
 * @param huart UART vừa hoàn tất truyền một khối.
 * @note DMA NORMAL: gọi qua callback HAL trong main.c khi USART1 báo phát xong khối.
 */
void UART_DMA_TxCpltCallback(UART_HandleTypeDef *huart)
{
	if (huart->Instance != USART1)
	{
		return;
	}
	if (crc_sending)
	{
		truyen_done_dma = 1;
		return;
	}
	/* TC bao payload cuoi da ra het UART; chot truoc tinh/gui CRC. */
	if (byte_sent_dma >= total_byte)
	{
		UART_Test_PayloadStop(byte_sent_dma);
	}

	/** Tính CRC đúng kích thước khối vừa truyền; đo riêng chi phí cập nhật. */
	uint32_t crc_start = DWT->CYCCNT;
	HAL_StatusTypeDef crc_status = CRC32_Update(tx_buffer, pending_size);
	cpu_crc_cycles_dma += DWT->CYCCNT - crc_start;
	if (crc_status != HAL_OK)
	{
		truyen_loi_dma = 1;
		return;
	}

	if (byte_sent_dma >= total_byte)
	{
		/** Dữ liệu đã xong; gửi CRC little-endian bằng buffer tồn tại suốt DMA. */
		uint32_t crc = CRC32_GetValue();
		crc_bytes[0] = (uint8_t)crc;
		crc_bytes[1] = (uint8_t)(crc >> 8);
		crc_bytes[2] = (uint8_t)(crc >> 16);
		crc_bytes[3] = (uint8_t)(crc >> 24);
		if (HAL_UART_Transmit_DMA(huart, crc_bytes, sizeof(crc_bytes)) == HAL_OK)
		{
			crc_sending = 1;
		}
		else
		{
			truyen_loi_dma = 1;
		}
		return;
	}

	uint32_t remaining = total_byte - byte_sent_dma;
	uint16_t chunk_size = (remaining > buffer_size) ? buffer_size : (uint16_t)remaining;
	pending_size = chunk_size;
	UART_GenerateData(tx_buffer, chunk_size, &data_state);
	if (HAL_UART_Transmit_DMA(huart, tx_buffer, chunk_size) == HAL_OK)
	{
		byte_sent_dma += chunk_size;
	}
	else
	{
		truyen_loi_dma = 1;
	}
}


//-------------------------------------------------------------------------------------------
/**
 * @brief Xử lý ngắt DMA TX và cộng chu kỳ CPU chạy HAL_DMA_IRQHandler().
 * @note Gọi từ DMA1_Channel4_IRQHandler(); chưa tính chi phí phần cứng vào/ra ngắt.
 */
void UART_DMA_IRQHandler(void)
{
    uint32_t start_cycle;
    uint32_t end_cycle;

    start_cycle = DWT->CYCCNT;

    HAL_DMA_IRQHandler(huart1.hdmatx);

    end_cycle = DWT->CYCCNT;

    cpu_busy_cycle_dma += end_cycle - start_cycle;
}

/**
 * @brief Đo và cộng chu kỳ CPU xử lý ngắt USART1 cho bài test DMA.
 * @note Gồm callback cập nhật CRC và chuẩn bị khối tiếp theo; chưa gồm phần cứng vào/ra ngắt.
 */
void UART_DMA_USART_IRQHandler(void)
{
    uint32_t start_cycle = DWT->CYCCNT;
    HAL_UART_IRQHandler(&huart1);
    cpu_busy_cycle_dma += DWT->CYCCNT - start_cycle;
}

/**
 * @brief Đọc cờ hoàn tất truyền của bài test DMA.
 * @return 1 khi đã phát xong dữ liệu và 4 byte CRC; 0 nếu chưa hoàn tất.
 */
uint8_t UART_DMA_IsDone(void)
{
    return truyen_done_dma;
}
