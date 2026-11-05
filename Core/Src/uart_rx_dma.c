#include "uart_rx_dma.h"
#include "dwt.h"
#include "uart_crc.h"
extern UART_HandleTypeDef huart1;

uint8_t rx_buf[RX_BUF_SIZE];

volatile uint16_t last_size = 0;

volatile uint32_t callback_count = 0;
volatile uint32_t total_received = 0;

volatile uint16_t process_pos = 0;
volatile uint16_t dma_pos = 0;

volatile uint8_t new_data_ready = 0;

volatile uint32_t cpu_cycles_A = 0;
volatile uint32_t cpu_cycles_B = 0;

volatile uint32_t cpu_time_us_A = 0;
volatile uint32_t cpu_time_us_B = 0;

//-----------------------------------------------------------------------
/* One frame per reset; CRC starts at zero to match zlib.crc32(). */
uint32_t rx_payload_bytes = 0;
uint32_t rx_crc32 = 0;
uint8_t rx_done = 0;
static uint32_t rx_length = 0;
static uint8_t rx_length_bytes = 0;

/* Called only from the existing read loops in UART_RX_DMA_Process(). */
static void UART_RX_ProcessByte(uint8_t data)
{
    if (rx_done)
        return;
    if (rx_length_bytes < 4U)
    {
        rx_length |= (uint32_t)data << (8U * rx_length_bytes++);
    }
    else
    {
        rx_crc32 = CRC32_ZlibUpdate(rx_crc32, &data, 1U);
        rx_payload_bytes++;
    }
    if (rx_length_bytes == 4U && rx_payload_bytes == rx_length)
        rx_done = 1;
}
//-----------------------------------------------------------------------

void UART_RX_DMA_Start(void) {
    if (HAL_UARTEx_ReceiveToIdle_DMA(&huart1,rx_buf,RX_BUF_SIZE) != HAL_OK)
    {
        Error_Handler();
    }
}

void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart,uint16_t Size){
    if (huart->Instance != USART1)
        return;

    callback_count++;

    if (Size >= last_size)
    {
        total_received += (Size - last_size);
    }
    else
    {
        total_received += (RX_BUF_SIZE - last_size);
        total_received += Size;
    }

    dma_pos = Size;
    new_data_ready = 1;
    last_size = Size;
}


   //H�m xu l� du li�u moi 
void UART_RX_DMA_Process(void){
	 uint16_t pos;
	
	if(!new_data_ready)
		return;
	
	new_data_ready = 0;
	pos = dma_pos; 
  
	if(pos == process_pos)
		return;
	
  // TH1 CHUA QUAY  (chua circuler )
  if (pos > process_pos)
    {
			// Buffer A 
        if (process_pos < RX_BUF_SIZE/2)
        {
            uint16_t end_A;

            if (pos < RX_BUF_SIZE/2)
                end_A = pos;
            else
                end_A = RX_BUF_SIZE/2;

            uint32_t start = DWT_GetCycles();

            for (uint16_t i = process_pos; i < end_A; i++)
            {
                volatile uint8_t data = rx_buf[i];
                //--------------------------
                UART_RX_ProcessByte(data);
                //--------------------------
            }
            uint32_t end = DWT_GetCycles();

            cpu_cycles_A = end - start;
            cpu_time_us_A = DWT_CyclesToUs(cpu_cycles_A);
        }
				
          // Buffer B 
        if (pos > RX_BUF_SIZE/2)
        {
            uint16_t start_B;

            if (process_pos < RX_BUF_SIZE/2)
                start_B = RX_BUF_SIZE/2;
            else
                start_B = process_pos;

            uint32_t start = DWT_GetCycles();

            for (uint16_t i = start_B; i < pos; i++)
            {
                volatile uint8_t data = rx_buf[i];
                UART_RX_ProcessByte(data);
            }

            uint32_t end = DWT_GetCycles();

            cpu_cycles_B = end - start;
            cpu_time_us_B = DWT_CyclesToUs(cpu_cycles_B);
        }
    }
    
    // TH2 DA QUAY LAI BUF[0]		
    else
    {    
			  // Tai buf B 
        uint32_t start_B = DWT_GetCycles();

        for (uint16_t i = process_pos; i < RX_BUF_SIZE; i++)
        {
            volatile uint8_t data = rx_buf[i];
            UART_RX_ProcessByte(data);
        }

        uint32_t end_B = DWT_GetCycles();

        cpu_cycles_B = end_B - start_B;
        cpu_time_us_B = DWT_CyclesToUs(cpu_cycles_B);

        // Tai buf A 
        if (pos > 0)
        {
            uint32_t start_A = DWT_GetCycles();

            for (uint16_t i = 0; i < pos; i++)
            {
                volatile uint8_t data = rx_buf[i];
                UART_RX_ProcessByte(data);
            }

            uint32_t end_A = DWT_GetCycles();

            cpu_cycles_A = end_A - start_A;
            cpu_time_us_A = DWT_CyclesToUs(cpu_cycles_A);
        }
    }
		
    process_pos = pos;
}





