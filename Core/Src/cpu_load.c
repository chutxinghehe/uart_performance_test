
#include "cpu_load.h"

/* So lan vong lap nen chay trong lan do hien tai */
volatile uint32_t idle_counter = 0;

/* Sua idle v2: idle_max_count = so vong idle hieu chuan moi giay. */
volatile uint32_t idle_max_count = 0;


/*
 * Ham: CPULoad_Calibrate()
 *
 * Muc dich:
 * - Do so lan vong lap nen chay trong 1 giay khi UART chua truyen.
 * - Luu ket qua vao idle_max_count lam moc chuan.
 *
 * Cach dung:
 * - Goi mot lan sau khi khoi tao GPIO va UART.
 * - Chua bat dau truyen UART trong luc hieu chuan.
 *
 * GPIO:
 * - PC13 toggle moi vong lap de Logic Analyzer quan sat.
 */
void CPULoad_Calibrate(void)
{
    uint32_t start_tick;

    /* Xoa bo dem truoc khi hieu chuan */
    idle_counter = 0;

    /* Luu thoi diem bat dau */
    start_tick = HAL_GetTick();

    /* Dem trong khoang thoi gian 1 giay */
    while ((HAL_GetTick() - start_tick) < 1000U)
    {
        /* Sua idle v2: dung cung buoc idle nhu khi dang truyen. */
        CPULoad_IdleStep();
    }

    /* Luu so dem lam moc chuan */
    idle_max_count = idle_counter;

    /* Xoa bo dem de chuan bi cho lan do UART */
    idle_counter = 0;
}


/*
 * Ham: CPULoad_IdleStep()
 *
 * Muc dich:
 * - Mo phong mot buoc cong viec nen don gian.
 * - Tang idle_counter moi khi ham duoc goi.
 * - Toggle PC13 de quan sat tren Logic Analyzer.
 *
 * Cach dung:
 * - Goi lien tuc trong vong cho UART Interrupt/DMA hoan tat.
 *
 * Luu y:
 * - Khong goi ham nay trong khi UART Polling dang blocking,
 *   vi CPU khong the quay lai vong cho trong thoi gian do.
 */
void CPULoad_IdleStep(void)
{
    idle_counter++;

    /* Dao muc logic PC13 */
    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
}
