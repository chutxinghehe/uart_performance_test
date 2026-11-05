#include "polling.h"
//------------------------- begin ---------------------------------------
#include "uart_crc.h"
#include "uart_data.h"
#include "uart_dwt.h"
//-------------------------- end -------------------------------------

#define total_byte 1000000U
#define buffer_size 256U


volatile uint32_t cpu_busy_cycles=0;
/** Chu kỳ chạy CRC32_Update(); đã nằm trong cpu_busy_cycles. */
volatile uint32_t cpu_crc_cycles = 0;
volatile uint32_t byte_sent = 0;
extern UART_HandleTypeDef huart1;


/**
 * @brief Truyền 1.000.000 byte và CRC bằng UART polling, sau đó gửi báo cáo DWT.
 * @return HAL_OK khi hoàn tất; mã lỗi HAL nếu truyền hoặc cập nhật CRC thất bại.
 * @note Dùng HAL_UART_Transmit() chặn; tác vụ nền chỉ chạy từ vòng lặp main của IT/DMA.
 * @note DWT gồm sinh dữ liệu, chờ UART và CRC, không gồm gửi báo cáo.
 */
HAL_StatusTypeDef UART_Polling_Transmit(void)
{
	//------------------------- begin ---------------------------------------
	byte_sent = 0;
	cpu_busy_cycles = 0;
	cpu_crc_cycles = 0;
	CRC32_Reset();
	//-------------------------- end -------------------------------------

	// tao mang du lieu truyen
	uint8_t tx_buffer[buffer_size];
	
	uint32_t state = 123355889U;
	
	/*	do dwt	*/
	CoreDebug ->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk; //bat dau dwt
	
	DWT->CYCCNT = 0;
	DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
	
	uint32_t start_cycle = DWT->CYCCNT; // bat dau do cpu truyen
	


	while (byte_sent < total_byte)
	{
		uint16_t chunk_size = buffer_size; // du lieu duoc lay ra tu tx_bufer trong 1 lan truyen 
		
		if((total_byte - byte_sent) < buffer_size)
		{
			chunk_size = total_byte - byte_sent;
		}
		
		//------------------------------------------------
		UART_GenerateData(tx_buffer, chunk_size, &state);
		//-----------------------------------------------
		
		/* Sua idle v2: bat dau ngay truoc khi phat payload dau tien. */
		if (byte_sent == 0U)
		{
			UART_Test_PayloadStart();
		}
		HAL_StatusTypeDef status =
			HAL_UART_Transmit(&huart1, tx_buffer, chunk_size, HAL_MAX_DELAY);
	
		if(status != HAL_OK)
		{
			uint32_t end_cycle = DWT->CYCCNT;

			cpu_busy_cycles = end_cycle - start_cycle; //tinh chu ky cpu sau moi lan gui
		
			return status;
		}

		/* HAL polling da cho TC: payload cuoi da phat xong, chua tinh CRC cuoi. */
		if (byte_sent + chunk_size == total_byte)
		{
			UART_Test_PayloadStop(byte_sent + chunk_size);
		}
		//------------------------- begin ---------------------------------------
		/** Đo riêng tính CRC; không cộng lại vào bộ đếm tổng. */
		uint32_t crc_start = DWT->CYCCNT;
		status = CRC32_Update(tx_buffer, chunk_size);
		cpu_crc_cycles += DWT->CYCCNT - crc_start;
		if(status != HAL_OK)
		{
			uint32_t end_cycle = DWT->CYCCNT;
			cpu_busy_cycles = end_cycle - start_cycle;
			return status;
		}
		//-------------------------- end -------------------------------------

		byte_sent += chunk_size;
	}

	//------------------------- begin ---------------------------------------
	uint32_t crc_value = CRC32_GetValue();
	uint8_t crc_bytes[4] = {
		(uint8_t)crc_value,
		(uint8_t)(crc_value >> 8),
		(uint8_t)(crc_value >> 16),
		(uint8_t)(crc_value >> 24)
	};
	HAL_StatusTypeDef status =
		HAL_UART_Transmit(&huart1, crc_bytes, sizeof(crc_bytes), HAL_MAX_DELAY);
	if(status != HAL_OK)
	{
		uint32_t end_cycle = DWT->CYCCNT;
		cpu_busy_cycles = end_cycle - start_cycle;
		return status;
	}
	//-------------------------- end -------------------------------------
	
	uint32_t end_cycle = DWT->CYCCNT;

	// tinh tong chu ky cpu ban:
	cpu_busy_cycles = end_cycle - start_cycle; // cap nhat chu ky cpu cuoi cung
	
	// Chốt DWT trước khi gửi báo cáo; thời gian gửi báo cáo không nằm trong phép đo.
	return UART_SendDWTResult(&huart1, cpu_busy_cycles, cpu_crc_cycles,
	                         UART_DWT_MODE_POLLING);
}
