#!/usr/bin/env python3
"""Nhận dữ liệu UART interrupt từ STM32, đo thời gian và lưu kết quả."""

import sys
from pathlib import Path

from uart_test_support import run_tx_test


# Cấu hình phải khớp nhung/interrup.c và Core/Src/usart.c.
SERIAL_PORT = "COM4"  # Đặt đúng cổng USB-UART.
#BAUD_RATE = 9600
#BAUD_RATE = 115200
#BAUD_RATE = 460800
#BAUD_RATE = 921600
#BAUD_RATE = 1500000
#BAUD_RATE = 2000000

FIRST_BYTE_TIMEOUT = 30
READ_TIMEOUT = 2  # Tối thiểu; tự tăng nếu một khối dữ liệu cần lâu hơn ở baud thấp.
TOTAL_BYTES = 1_000_000
READ_CHUNK_SIZE = 4096
SHOW_PROGRESS = True  # Đặt False khi cần đo hiệu năng với ít ảnh hưởng từ terminal.
PROGRESS_INTERVAL = 1.0  # Giây giữa các lần cập nhật tiến trình.
BITS_PER_BYTE = 10  # UART 8N1: 1 bit bắt đầu + 8 bit dữ liệu + 1 bit kết thúc.
# Sửa idle v2: file mới, không nối dữ liệu vào schema/kết quả cũ.
CSV_PATH = Path(__file__).resolve().with_name("uart_it_tx_v2_results.csv")
TEST_MODE_CODE = 2  # Phải khớp chế độ firmware STM32.
DWT_SCOPE = "IT: UART không tính CRC = tổng HAL khởi động/IRQ - CRC32_Update(); vẫn gồm đóng gói/gửi CRC, chưa gồm chi phí phần cứng vào/ra ngắt."


def main():
    """Chạy một lượt theo các hằng cấu hình phía trên và trả về bool."""
    return run_tx_test(
        method="Interrupt",
        serial_port=SERIAL_PORT,
        baud_rate=BAUD_RATE,
        total_bytes=TOTAL_BYTES,
        read_chunk_size=READ_CHUNK_SIZE,
        first_byte_timeout=FIRST_BYTE_TIMEOUT,
        read_timeout=READ_TIMEOUT,
        show_progress=SHOW_PROGRESS,
        progress_interval=PROGRESS_INTERVAL,
        bits_per_byte=BITS_PER_BYTE,
        csv_path=CSV_PATH,
        test_mode_code=TEST_MODE_CODE,
        dwt_scope=DWT_SCOPE,
    )


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
