#ifndef DWT_H
#define DWT_H

#include "main.h"

void DWT_Init(void);

uint32_t DWT_GetCycles(void);

uint32_t DWT_CyclesToUs(uint32_t cycles);

#endif