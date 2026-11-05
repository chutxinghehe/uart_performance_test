#ifndef UART_RX_DMA_H
#define UART_RX_DMA_H

#include "main.h"

#define RX_BUF_SIZE 1024U

extern uint8_t rx_buf[RX_BUF_SIZE];

/* One Length + Payload frame per reset; CRC excludes the Length bytes. */
extern uint32_t rx_payload_bytes;
extern uint32_t rx_crc32;
extern uint8_t rx_done;

void UART_RX_DMA_Start(void);
void UART_RX_DMA_Process(void);

#endif
