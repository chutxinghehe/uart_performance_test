"""Chạy C polling/IT/DMA thật với HAL giả để kiểm tra mốc payload, không cần bo mạch."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


FAKE_HAL = r"""
#ifndef FAKE_HAL_H
#define FAKE_HAL_H
#define __MAIN_H
#include <stdint.h>
typedef enum { HAL_OK, HAL_ERROR } HAL_StatusTypeDef;
typedef struct { void *Instance; void *hdmatx; } UART_HandleTypeDef;
typedef struct { uint32_t DEMCR; } DebugRegisters;
typedef struct { uint32_t CTRL, CYCCNT; } DwtRegisters;
extern DebugRegisters debug_registers;
extern DwtRegisters dwt_registers;
#define CoreDebug (&debug_registers)
#define DWT (&dwt_registers)
#define CoreDebug_DEMCR_TRCENA_Msk 1U
#define DWT_CTRL_CYCCNTENA_Msk 1U
#define USART1 ((void *)1)
#define GPIOC ((void *)2)
#define GPIO_PIN_13 8192U
#define HAL_MAX_DELAY 0xFFFFFFFFU
static inline uint32_t __get_PRIMASK(void) { return 0; }
static inline void __disable_irq(void) {}
static inline void __set_PRIMASK(uint32_t x) { (void)x; }
uint32_t HAL_GetTick(void);
uint32_t HAL_RCC_GetHCLKFreq(void);
void HAL_GPIO_TogglePin(void *port, uint32_t pin);
void HAL_DMA_IRQHandler(void *dma);
void HAL_UART_IRQHandler(UART_HandleTypeDef *uart);
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *, const uint8_t *, uint16_t, uint32_t);
HAL_StatusTypeDef HAL_UART_Transmit_IT(UART_HandleTypeDef *, const uint8_t *, uint16_t);
HAL_StatusTypeDef HAL_UART_Transmit_DMA(UART_HandleTypeDef *, const uint8_t *, uint16_t);
void UART_Test_PayloadStart(void);
void UART_Test_PayloadStop(uint32_t bytes);
#endif
"""

HARNESS = r"""
#include "fake_hal.h"
#include "cpu_load.h"
#include "polling.h"
#include "interrup.h"
#include "dma1.h"
#include <assert.h>
#include <stdio.h>

DebugRegisters debug_registers;
DwtRegisters dwt_registers;
UART_HandleTypeDef huart1 = {USART1, 0};
static uint32_t tick, tick_step, toggles, starts, stops, payload, crc_bytes, crc_calls;
static uint32_t start_tick, elapsed, saved_idle;
static uint16_t pending;

uint32_t HAL_GetTick(void) { uint32_t value = tick; tick += tick_step; return value; }
uint32_t HAL_RCC_GetHCLKFreq(void) { return 72000000U; }
void HAL_GPIO_TogglePin(void *port, uint32_t pin) {
    assert(port == GPIOC && pin == GPIO_PIN_13); toggles++;
}
void HAL_DMA_IRQHandler(void *dma) { (void)dma; }
void HAL_UART_IRQHandler(UART_HandleTypeDef *uart) { (void)uart; }
void CRC32_Reset(void) {}
uint32_t CRC32_GetValue(void) { return 123; }
HAL_StatusTypeDef CRC32_Update(const uint8_t *data, uint32_t length) {
    (void)data; assert(length % 4U == 0U);
    /* CRC của khối cuối chỉ chạy SAU khi phép đo payload đã chốt. */
    if (payload == 1000000U) assert(stops == 1U);
    crc_calls++; return HAL_OK;
}
void UART_Test_PayloadStart(void) {
    assert(starts == 0 && payload == 0 && crc_bytes == 0);
    starts++; idle_counter = 0; start_tick = tick;
}
void UART_Test_PayloadStop(uint32_t bytes) {
    assert(stops == 0 && bytes == 1000000U && payload == bytes);
    assert(crc_bytes == 0 && crc_calls == 3906U);
    stops++; elapsed = tick - start_tick; saved_idle = idle_counter;
}
static void complete(uint16_t size) {
    if (size >= 64U) { assert(starts == 1U); payload += size; tick += 3; }
    else if (size == 4U) { assert(stops == 1U); crc_bytes += size; tick++; }
    else { assert(size == 20U && stops == 1U); tick += 2; }
}
HAL_StatusTypeDef HAL_UART_Transmit(UART_HandleTypeDef *uart, const uint8_t *data,
                                   uint16_t size, uint32_t timeout) {
    (void)uart; (void)data; (void)timeout; complete(size); return HAL_OK;
}
HAL_StatusTypeDef HAL_UART_Transmit_IT(UART_HandleTypeDef *uart, const uint8_t *data, uint16_t size) {
    (void)uart; (void)data; assert(pending == 0); pending = size; return HAL_OK;
}
HAL_StatusTypeDef HAL_UART_Transmit_DMA(UART_HandleTypeDef *uart, const uint8_t *data, uint16_t size) {
    return HAL_UART_Transmit_IT(uart, data, size);
}
static void reset(void) {
    tick = tick_step = toggles = starts = stops = payload = crc_bytes = crc_calls = 0;
    elapsed = saved_idle = pending = 0; idle_counter = 0;
}
int main(void) {
    reset(); tick_step = 1;
    CPULoad_Calibrate();
    assert(idle_max_count > 0 && idle_max_count == toggles && idle_counter == 0);
    CPULoad_IdleStep();
    assert(idle_counter == 1 && toggles == idle_max_count + 1);
    reset();
    assert(UART_Polling_Transmit() == HAL_OK);
    assert(starts == 1 && stops == 1 && saved_idle == 0 && payload == 1000000U);
    assert(crc_bytes == 4 && elapsed == 3907U * 3U && tick > elapsed);
    for (int mode = 2; mode <= 3; mode++) {
        reset();
        assert((mode == 2 ? UART_Interrup_Transmit() : UART_DMA_Transmit()) == HAL_OK);
        while (pending) {
            uint16_t size = pending; pending = 0; complete(size);
            if (size >= 64U) CPULoad_IdleStep();
            if (mode == 2) UART_Interrup_TxCpltCallback(&huart1);
            else UART_DMA_TxCpltCallback(&huart1);
        }
        assert(starts == 1 && stops == 1 && payload == 1000000U && crc_bytes == 4);
        assert(saved_idle == 3907U && elapsed == 3907U * 3U && tick > elapsed);
        assert(mode == 2 ? truyen_done_it : truyen_done_dma);
    }
    puts("Calibration uses IdleStep; polling/IT/DMA stop at final payload before CRC: OK");
    return 0;
}
"""


class FirmwareIdleTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("gcc"), "Cần GCC host để chạy HAL giả")
    def test_calibration_and_payload_boundaries(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            header = folder / "fake_hal.h"
            header.write_text(FAKE_HAL, encoding="utf-8")
            (folder / "stm32f1xx.h").write_text('#include "fake_hal.h"\n', encoding="utf-8")
            harness = folder / "harness.c"
            harness.write_text(HARNESS, encoding="utf-8")
            output = folder / "firmware_idle_test.exe"
            sources = [root / name for name in ("Core/Src/cpu_load.c", "Core/Src/uart_data.c",
                                                "nhung/polling.c", "nhung/interrup.c", "nhung/dma1.c")]
            command = [shutil.which("gcc"), "-std=c99", "-O0", "-Wall", "-Wextra", "-Werror",
                       "-include", str(header), "-I" + str(folder), "-I" + str(root / "Core/Inc"),
                       "-I" + str(root / "nhung"), str(harness), *map(str, sources), "-o", str(output)]
            compiled = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            executed = subprocess.run([str(output)], capture_output=True, text=True, timeout=10)
            self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
            self.assertIn("before CRC: OK", executed.stdout)


if __name__ == "__main__":
    unittest.main()
