/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "crc.h"
#include "dma.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "polling.h"
#include "interrup.h"
#include "dma1.h"
#include "uart_dwt.h"
#include "uart_rx_dma.h"
#include "dwt.h"
#include "cpu_load.h"
#include <stdio.h>


/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

 // Test
 
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

#define TXPOLLING 1
#define TXIT      2
#define TXDMA     3
#define TEST_DMA_RX 4

// Chọn bài test tại đây, rồi build và nạp lại STM32.
#ifndef TEST

#define TEST TXPOLLING
//#define TEST TXIT
//#define TEST  TXDMA
//#define TEST TEST_DMA_RX

#endif

#if (TEST != TXPOLLING) && (TEST != TXIT) && (TEST != TXDMA) && (TEST != TEST_DMA_RX)
#error "TEST phai la TXPOLLING, TXIT, TXDMA hoac TEST_DMA_RX"
#endif


/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/*
 * Ý nghĩa các biến đo idle (có thể xem trong Keil Watch):
 * - idle_start_ms: mốc HAL_GetTick() ngay trước khi khởi động truyền payload đầu.
 * - idle_counter: số lần chạy CPULoad_IdleStep(); được reset khi bắt đầu payload
 *   và tăng trong vòng lặp main khi phép đo payload chưa kết thúc (IT/DMA).
 * - idle_result: giá trị idle_counter được chốt khi payload cuối phát xong.
 * - idle_elapsed_ms: thời gian từ idle_start_ms đến khi payload cuối phát xong,
 *   đơn vị ms; không gồm phần tính/gửi CRC cuối và gửi báo cáo.
 * - idle_measurement_done: 0 khi đang đo; 1 khi đã chốt kết quả, giúp chốt một
 *   lần và ngừng tăng bộ đếm idle trong main.
 * - idle_max_count: số vòng idle hiệu chuẩn trong 1 giây khi chưa truyền UART,
 *   do CPULoad_Calibrate() đo để làm mốc so sánh.
 * idle_counter và idle_max_count được định nghĩa trong cpu_load.c,
 * khai báo extern qua cpu_load.h; các biến còn lại được định nghĩa bên dưới.
 */
volatile uint32_t idle_result = 0;       /* So vong idle trong luot do. */
volatile uint32_t idle_elapsed_ms = 0;   /* Thoi luong do tren STM32 (ms). */
volatile uint8_t idle_measurement_done = 0;
volatile uint32_t payload_elapsed_ms = 0; /* Thoi gian phat payload, khong gom CRC. */
volatile uint32_t payload_bytes_sent = 0; /* So byte payload da phat xong. */

#if TEST != TEST_DMA_RX
static uint32_t idle_start_ms;
#endif

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

#if TEST != TEST_DMA_RX
static HAL_StatusTypeDef UART_Test_SendIdleResult(void);
#endif

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/**
 * @brief Sua idle v2: bat dau ngay truoc loi goi HAL phat payload dau tien.
 */
void UART_Test_PayloadStart(void)
{
#if TEST != TEST_DMA_RX
  idle_counter = 0;
  idle_result = 0;
  idle_elapsed_ms = 0;
  payload_elapsed_ms = 0;
  payload_bytes_sent = 0;
  idle_measurement_done = 0;
  HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET);
  idle_start_ms = HAL_GetTick();
#endif
}

#if TEST != TEST_DMA_RX
/**
 * @brief Gửi số vòng nền đã chốt về PC qua USART1.
 * @return Trạng thái trả về từ HAL_UART_Transmit().
 * @note Sua idle v2: IDL2 + 5 uint32 little-endian, ngoai cua so do.
 */
static HAL_StatusTypeDef UART_Test_SendIdleResult(void)
{
  uint8_t frame[24] = {'I', 'D', 'L', '2'};
  uint32_t values[5] = {idle_result, idle_elapsed_ms, idle_max_count,
                        payload_bytes_sent, payload_elapsed_ms};
  for (uint32_t word = 0; word < 5U; word++)
  {
    for (uint32_t byte = 0; byte < 4U; byte++)
    {
      frame[4U + word * 4U + byte] = (uint8_t)(values[word] >> (byte * 8U));
    }
  }
  return HAL_UART_Transmit(&huart1, frame, sizeof(frame), 1000U);
}
#endif

/**
 * @brief Sua idle v2: chot ngay khi payload cuoi phat xong, truoc CRC cuoi.
 * @note IT/DMA goi trong callback TC; polling goi sau HAL_UART_Transmit().
 * @note Không thực hiện phép đo khi TEST == TEST_DMA_RX.
 */
void UART_Test_PayloadStop(uint32_t payload_bytes)
{
#if TEST != TEST_DMA_RX
  if (!idle_measurement_done)
  {
    idle_elapsed_ms = HAL_GetTick() - idle_start_ms;
    idle_result = idle_counter;
    payload_elapsed_ms = idle_elapsed_ms;
    payload_bytes_sent = payload_bytes;
    idle_measurement_done = 1;
  }
#else
  (void)payload_bytes;
#endif
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */
#if (TEST == TXIT) || (TEST == TXDMA)
  uint8_t dwt_report_sent = 0;
#elif TEST == TEST_DMA_RX
  uint8_t rx_result_sent = 0;
#endif
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
	DWT_Init();
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_CRC_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */


  //------------------------- begin ---------------------------------------
#if TEST != TEST_DMA_RX
  /* Sua idle v2: hieu chuan 1 lan sau GPIO/UART, truoc cua so payload. */
  CPULoad_Calibrate();
#endif

#if TEST == TXPOLLING
  // Hàm polling tự đo DWT và gửi dữ liệu -> CRC -> báo cáo DWT trước khi trả về.
  if (UART_Polling_Transmit() != HAL_OK)
  {
    Error_Handler();
  }
  if (UART_Test_SendIdleResult() != HAL_OK)
  {
    Error_Handler();
  }
#elif TEST == TXIT
  // Khởi động truyền bằng ngắt; báo cáo DWT được gửi trong vòng lặp main.
  if (UART_Interrup_Transmit() != HAL_OK)
  {
    Error_Handler();
  }
#elif TEST == TXDMA
  if (UART_DMA_Transmit() != HAL_OK)
  {
    Error_Handler();
  }
#elif TEST == TEST_DMA_RX
  UART_RX_DMA_Start();
#endif





  //-------------------------- end -------------------------------------
	



  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  // Sua idle v2: idle tai main chi chay den khi payload cuoi phat xong.
  // Polling chặn trong USER CODE BEGIN 2 nên counter nền của lượt truyền bằng 0.
  while (1)
  {
#if TEST == TXPOLLING
    // Bài test polling đã hoàn tất và gửi DWT trong USER CODE BEGIN 2.
#elif TEST == TXIT
    if (truyen_loi_it)
    {
      Error_Handler();
    }

    // IRQ cuối đã trả về và cộng xong DWT; gửi báo cáo đúng một lần từ main.
    if (truyen_done_it && !dwt_report_sent)
    {
      if (UART_SendDWTResult(&huart1, cpu_busy_cycle_it, cpu_crc_cycles_it,
                             UART_DWT_MODE_INTERRUPT) != HAL_OK)
      {
        Error_Handler();
      }
      if (UART_Test_SendIdleResult() != HAL_OK)
      {
        Error_Handler();
      }
      dwt_report_sent = 1;
    }
    else if (!idle_measurement_done)
    {
      CPULoad_IdleStep();
    }
#elif TEST == TXDMA
    if (truyen_loi_dma)
    {
      Error_Handler();
    }

    // IRQ cuối đã cộng xong tổng/CRC; gửi báo cáo một lần sau dữ liệu + CRC.
    if (truyen_done_dma && !dwt_report_sent)
    {
      if (UART_SendDWTResult(&huart1, cpu_busy_cycle_dma, cpu_crc_cycles_dma,
                             UART_DWT_MODE_DMA) != HAL_OK)
      {
        Error_Handler();
      }
      if (UART_Test_SendIdleResult() != HAL_OK)
      {
        Error_Handler();
      }
      dwt_report_sent = 1;
    }
    else if (!idle_measurement_done)
    {
      CPULoad_IdleStep();
    }
#elif TEST == TEST_DMA_RX
    UART_RX_DMA_Process();
    if (rx_done == 1U && !rx_result_sent)
    {
      char reply[64];
      int size = snprintf(reply, sizeof(reply), "RESULT,DONE,%lu,%08lX\r\n",
                          (unsigned long)rx_payload_bytes,
                          (unsigned long)rx_crc32);
      if (size <= 0 || size >= (int)sizeof(reply))
      {
        Error_Handler();
      }
      if (HAL_UART_Transmit(&huart1, (uint8_t *)reply, (uint16_t)size, 100U) != HAL_OK)
      {
        Error_Handler();
      }
      rx_result_sent = 1;
    }
#endif

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/**
 * @brief Chuyển sự kiện hoàn tất khối truyền đến bài test IT hoặc DMA đang chọn.
 * @param huart UART vừa hoàn tất truyền một khối.
 * @note Callback của bài test xử lý CRC, gửi khối tiếp theo và đặt cờ hoàn tất.
 */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
#if TEST == TXIT
    UART_Interrup_TxCpltCallback(huart);
#elif TEST == TXDMA
    UART_DMA_TxCpltCallback(huart);
#else
    (void)huart;
#endif
}

/**
 * @brief Đặt cờ lỗi truyền UART/DMA cho bài test IT hoặc DMA đang chọn.
 * @param huart UART phát sinh lỗi.
 * @note Chỉ xử lý USART1; main kiểm tra cờ để gọi Error_Handler().
 */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance != USART1)
    {
      return;
    }
#if TEST == TXIT
    truyen_loi_it = 1;
#elif TEST == TXDMA
    truyen_loi_dma = 1;
#endif
}

/**
 * @brief Xử lý ngắt USART1 theo chế độ TEST.
 * @note IT/DMA đo chu kỳ CPU quanh xử lý HAL; chế độ còn lại gọi HAL trực tiếp.
 */
void UART_Test_USART_IRQHandler(void)
{
#if TEST == TXIT
    UART_Interrup_IRQHandler();
#elif TEST == TXDMA
    UART_DMA_USART_IRQHandler();
#else
    HAL_UART_IRQHandler(&huart1);
#endif
}

/**
 * @brief Xử lý ngắt DMA TX của USART1.
 * @note Chỉ cộng chu kỳ CPU khi TEST == TXDMA; chế độ khác gọi HAL trực tiếp.
 */
void UART_Test_DMA_IRQHandler(void)
{
#if TEST == TXDMA
    UART_DMA_IRQHandler();
#else
    HAL_DMA_IRQHandler(huart1.hdmatx);
#endif
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
