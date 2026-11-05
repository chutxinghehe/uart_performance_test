#include "dwt.h"

void DWT_Init(void)
{
	  // cho phep su dung  DWT
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    DWT->CYCCNT = 0;
	
    // Bat bo dem CPU cycle 
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

uint32_t DWT_GetCycles(void)
{
	  uint32_t cycles;
    cycles =  DWT->CYCCNT;
	  return cycles;  
}


uint32_t DWT_CyclesToUs(uint32_t cycles)
{   
	  
    return cycles / (SystemCoreClock / 1000000U);
}