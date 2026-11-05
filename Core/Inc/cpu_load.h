
#ifndef CPU_LOAD_H
#define CPU_LOAD_H

#include "main.h"

/*
 * idle_counter:
 * So lan vong lap nen da chay trong lan do hien tai.
 * Gia tri cang lon trong cung mot khoang thoi gian
 * thi CPU cang co nhieu thoi gian xu ly cong viec nen.
 */
extern volatile uint32_t idle_counter;

/*
 * idle_max_count:
 * Sua idle v2: idle_max_count = so vong idle hieu chuan moi giay.
 * So lan vong lap idle chay duoc trong 1 giay
 * khi chua truyen UART.
 * Day la moc chuan de tham khao khi so sanh.
 */
extern volatile uint32_t idle_max_count;

/*
 * CPULoad_Calibrate():
 * Hieu chuan bo dem khi UART chua truyen.
 * Goi mot lan sau khi khoi tao GPIO va UART.
 */
void CPULoad_Calibrate(void);

/*
 * CPULoad_IdleStep():
 * Tang bo dem idle va toggle GPIO PC13; dung ca khi hieu chuan.
 * Goi lien tuc trong vong cho khi do Interrupt/DMA.
 */
void CPULoad_IdleStep(void);

#endif
