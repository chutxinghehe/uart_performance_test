# STM32 UART Performance Benchmark

### Performance Analysis of Polling, Interrupt, and DMA Communication

A bare-metal embedded systems project designed to evaluate and compare UART communication methods on the **STM32F103C8T6 (ARM Cortex-M3)**.

The project focuses on analyzing CPU execution overhead, transmission time, and processor availability when using **Polling, Interrupt, and Direct Memory Access (DMA)**.

## 1. Project Overview

UART is one of the most widely used communication peripherals in embedded systems. However, different transmission methods have different impacts on CPU utilization and system responsiveness.

This project implements a benchmarking framework to investigate three UART transmission approaches:

- **Polling:** Blocking transmission controlled by the CPU.
- **Interrupt:** Non-blocking transmission using UART interrupts and completion callbacks.
- **DMA:** Data transmission using the DMA controller with reduced CPU involvement.

The primary objective is to understand the trade-offs between these methods through firmware-level measurements rather than theoretical comparisons alone.

## 2. Hardware & Software

| Component | Specification |
|---|---|
| Microcontroller | STM32F103C8T6 |
| Processor | ARM Cortex-M3 |
| System Clock | 72 MHz |
| Programming Language | Embedded C |
| Firmware Library | STM32 HAL |
| Development Tools | Keil MDK-ARM, STM32CubeMX |
| Communication | USART1 |
| Performance Measurement | DWT Cycle Counter, HAL_GetTick |
| Data Integrity | Hardware CRC Peripheral |
| Testing | Python Host-Side Tools |

### UART Configuration

- USART1_TX: PA9
- USART1_RX: PA10
- DMA TX: DMA1 Channel 4
- DMA RX: DMA1 Channel 5
- Debug Interface: SWD

## 3. System Architecture

The firmware separates UART communication methods into dedicated modules to support consistent performance comparisons.

```text
              STM32F103C8T6
            +------------------+
            |  Test Selection  |
            |     main.c       |
            +--------+---------+
                     |
         +-----------+-----------+
         |           |           |
    +----v----+ +----v----+ +----v----+
    | Polling | |Interrupt| |   DMA   |
    |   TX    | |   TX    | |   TX    |
    +----+----+ +----+----+ +----+----+
         |           |           |
         +-----------+-----------+
                     |
                +----v----+
                | USART1  |
                +----+----+
                     |
                Serial Link
                     |
               Python Host
```

Additional firmware modules provide:

- DWT cycle measurements
- CPU idle-loop monitoring
- CRC processing
- UART transmission reporting
- DMA-based UART reception testing

## 4. Implementation

### 4.1. Polling Transmission

Polling uses blocking UART transmission.

The CPU remains occupied while the HAL transmission function executes, limiting its ability to perform other application tasks.

**Implementation:**
- Blocking UART transmission
- CPU cycle measurement
- Payload transmission timing
- CRC processing and reporting

### 4.2. Interrupt Transmission

Interrupt-driven UART transmission allows the CPU to return to the main application while UART transmission progresses.

Transmission completion is handled through UART interrupt callbacks.

**Implementation:**
- Non-blocking UART transmission
- Interrupt service routine handling
- Transmission completion callbacks
- CPU idle-loop monitoring
- DWT-based CPU overhead measurement

### 4.3. DMA Transmission

DMA enables data transfers between memory and the UART peripheral without requiring the CPU to handle every transmitted byte.

The CPU primarily participates in transfer initialization, completion handling, and associated processing.

**Implementation:**
- USART1 DMA transmission
- DMA interrupt handling
- Transmission completion callbacks
- CPU cycle measurement
- CPU idle-loop monitoring

### 4.4. DMA Reception

The project also includes a separate UART receive test using DMA.

**Implementation:**
- Circular DMA reception configuration
- Receive-data processing
- Payload byte counting
- CRC32 result reporting

## 5. Performance Measurement

The benchmarking framework examines three main performance characteristics.

### CPU Execution Overhead

The ARM Cortex-M DWT cycle counter is used to measure CPU execution cycles associated with UART processing.

This allows CPU overhead to be examined at a finer resolution than millisecond-based timing.

### Transmission Duration

The firmware uses `HAL_GetTick()` to record the elapsed time between the beginning and completion of payload transmission.

The measurement excludes the final CRC and performance-report transmission.

### CPU Idle Activity

An idle-loop counter tracks how often the CPU executes background processing while UART transmission is in progress.

A calibration step establishes a reference idle-loop count before transmission.

This provides a comparative indicator of CPU availability under different UART transmission methods.

**Measurement note:** Idle-loop counts are an indirect indicator of processor availability, not a hardware-measured CPU utilization percentage. Measurement overhead and interrupt behavior should be considered when interpreting results.

## 6. Benchmark Comparison

The project is designed to collect the following metrics for each transmission method:

| Metric | Polling | Interrupt | DMA |
|---|---|---|---|
| Transmission duration | Measured | Measured | Measured |
| CPU execution cycles | Measured | Measured | Measured |
| CPU idle-loop activity | Measured | Measured | Measured |
| CRC processing | Supported | Supported | Supported |

Actual benchmark values should be collected from hardware under consistent test conditions.

The results can be used to evaluate:

- CPU overhead of each communication method
- Processor availability during transmission
- Trade-offs between blocking and non-blocking communication
- The impact of interrupt and DMA handling

## 7. How to Run

### Requirements

- STM32F103C8T6 development board
- ST-Link programmer/debugger
- UART-to-USB adapter
- Keil MDK-ARM
- STM32CubeMX
- Python environment for host-side testing

### Step 1: Clone the Repository

```bash
git clone https://github.com/chutxinghehe/uart_performance_test.git
cd uart_performance_test
```

### Step 2: Open the Firmware Project

Open the project in the `MDK-ARM` directory using Keil uVision.

The STM32CubeMX configuration is available in:

`Test_hieu_nang_UART.ioc`

### Step 3: Select the UART Test

Open:

`Core/Src/main.c`

Locate the test selection macros:

```c
#define TXPOLLING   1
#define TXIT        2
#define TXDMA       3
#define TEST_DMA_RX 4
```

Select the desired test by defining `TEST`:

```c
#define TEST TXPOLLING
```

Change it to `TXIT`, `TXDMA`, or `TEST_DMA_RX` as required.

Only one test mode is compiled at a time.

### Step 4: Build and Flash

1. Build the firmware in Keil.
2. Connect the ST-Link debugger.
3. Flash the firmware to the STM32.
4. Connect USART1 to the host computer through a UART-to-USB adapter.
5. Run the appropriate host-side test or capture tool.

### Step 5: Analyze the Output

Capture UART reports and examine:

- CPU cycle measurements
- Payload transmission duration
- Idle-loop counts
- Transmitted data volume
- CRC verification results

Repeat the measurements under consistent conditions for meaningful comparisons.

## 8. Technical Highlights

This project demonstrates practical experience in:

- STM32 peripheral configuration and programming
- Embedded C firmware development
- UART communication protocols
- Interrupt-driven embedded programming
- DMA controller integration
- ARM Cortex-M DWT performance profiling
- CPU overhead and execution-time analysis
- Hardware CRC-based data integrity verification
- Embedded debugging and hardware-software testing

## 9. Key Engineering Takeaways

The project explores an important embedded software engineering question:

**How can UART data transmission be handled efficiently while preserving CPU processing capacity for other tasks?**

Polling provides a straightforward blocking implementation, while Interrupt and DMA approaches allow transmission to progress with less continuous CPU involvement.

The benchmarking framework helps evaluate these approaches based on measured execution overhead and processor availability.

## 10. Future Improvements

Potential extensions include:

- Automated benchmark result collection
- Performance visualization using Python
- Repeated test runs with statistical analysis
- Benchmarking different UART baud rates
- Evaluating multiple payload sizes
- Measuring the effects of interrupt priorities
