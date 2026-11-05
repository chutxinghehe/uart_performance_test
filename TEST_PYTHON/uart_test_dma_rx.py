#!/usr/bin/env python3
"""Gửi Length + Payload đến TEST_DMA_RX và đối chiếu RESULT với zlib.crc32()."""

import argparse
import csv
import os
import struct
import sys
import time
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import serial

CSV_PATH = Path(__file__).resolve().with_name("uart_dma_rx_results.csv")
CSV_FIELDS = (
    "thoi_diem", "cong_com", "baud_rate", "so_byte_yeu_cau", "so_byte_gui",
    "so_byte_nhan", "crc32_pc", "crc32_stm32", "thoi_gian_s", "ket_qua", "ghi_chu",
)


def save_result(result):
    """Thêm result vào CSV_PATH theo CSV_FIELDS, không trả về giá trị.

    Chỉ ghi header khi tệp trống để giữ lịch sử các lượt RX. Lỗi I/O
    được chuyển cho hàm gọi; schema RX được giữ riêng với schema TX.
    """
    with CSV_PATH.open("a", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
        if output.tell() == 0:
            writer.writeheader()
        writer.writerow(result)


def main():
    """Gửi khung theo tham số dòng lệnh và trả về 0 khi RESULT hợp lệ.

    Đối chiếu số byte và CRC32 với Payload gửi đi. Luôn lưu kết quả
    trong finally; lỗi cổng, timeout hoặc phản hồi sai được chuyển ra
    ngoài để điểm vào chương trình in FAIL và trả mã thoát 1.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default="COM4")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--length", type=int, default=1_000_000)
    parser.add_argument("--repeat", type=int, default=1, choices=(1,),
                        help="Mỗi lần khởi động lại STM32 chỉ gửi một khung dữ liệu")
    parser.add_argument("--truncate-to", type=int, help="Gửi thiếu Payload để kiểm tra hết thời gian chờ/FAIL")
    args = parser.parse_args()
    if not 0 <= args.length <= 0xFFFFFFFF or args.baud <= 0 or args.repeat < 1:
        parser.error("length phải nằm trong khoảng 0 đến 4294967295; baud và repeat phải lớn hơn 0")
    if args.truncate_to is not None and not 0 <= args.truncate_to < args.length:
        parser.error("truncate-to phải lớn hơn hoặc bằng 0 và nhỏ hơn length")

    header = struct.pack("<I", args.length)
    send_length = args.length if args.truncate_to is None else args.truncate_to
    write_timeout = max(5.0, (send_length + len(header)) * 10 / args.baud + 5)
    result = {
        "thoi_diem": datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds"),
        "cong_com": args.port,
        "baud_rate": args.baud,
        "so_byte_yeu_cau": args.length,
        "so_byte_gui": 0,
        "so_byte_nhan": "",
        "crc32_pc": "",
        "crc32_stm32": "",
        "thoi_gian_s": "",
        "ket_qua": "FAIL",
        "ghi_chu": "",
    }
    started = time.perf_counter()
    try:
        with serial.Serial(args.port, args.baud, timeout=4, write_timeout=write_timeout,
                           bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
                           stopbits=serial.STOPBITS_ONE, xonxoff=False,
                           rtscts=False, dsrdtr=False) as port:
            port.reset_input_buffer()
            for session in range(1, args.repeat + 1):
                # CRC của toàn bộ Payload phát hiện cả trường hợp cố ý gửi thiếu.
                payload = os.urandom(args.length)
                expected_crc = zlib.crc32(payload)
                sent = payload if args.truncate_to is None else payload[:args.truncate_to]
                processed_crc = zlib.crc32(sent)
                result["crc32_pc"] = f"{expected_crc:08X}"
                print(f"TEST_DMA_RX: {args.port}, {args.baud} baud, Số byte={args.length}, CRC={expected_crc:08X}")
                print("STM32 phải chạy TEST_DMA_RX. Khởi động lại STM32 trước mỗi lượt kiểm tra (mỗi lần một khung).")
                started = time.perf_counter()
                frame = header + sent
                written = port.write(frame)
                result["so_byte_gui"] = max(0, written - len(header))
                if written != len(frame):
                    raise RuntimeError("Chưa gửi đủ dữ liệu qua cổng UART")
                port.flush()
                response = port.read_until(b"\n", 64)
                try:
                    line = response.decode("ascii").strip()
                except UnicodeDecodeError:
                    raise RuntimeError("Gói RESULT chứa ký tự không hợp lệ; kiểm tra baud và kết nối UART") from None
                elapsed = time.perf_counter() - started
                result["thoi_gian_s"] = round(elapsed, 6)
                print(f"{session}/{args.repeat}: {line or '(chưa nhận được RESULT)'} | {elapsed:.3f} s")
                if not response.endswith(b"\n"):
                    raise RuntimeError("Hết thời gian chờ hoặc chưa nhận đủ gói RESULT")
                fields = line.split(",")
                if len(fields) != 4 or fields[0] != "RESULT":
                    raise RuntimeError("Thiếu hoặc sai định dạng gói RESULT; kiểm tra firmware, baud và dây UART")
                try:
                    status, count, actual_crc = fields[1], int(fields[2]), int(fields[3], 16)
                except ValueError:
                    raise RuntimeError("Số byte hoặc CRC32 trong gói RESULT không phải giá trị số hợp lệ") from None
                result["so_byte_nhan"] = count
                result["crc32_stm32"] = f"{actual_crc:08X}"
                if (status != "DONE" or count != len(sent) or count != args.length
                        or actual_crc != expected_crc):
                    raise RuntimeError(
                        f"Kết quả không khớp. Cần RESULT,DONE,{args.length},{expected_crc:08X}; "
                        f"đã gửi {len(sent)} byte dữ liệu (CRC={processed_crc:08X})"
                    )
                result["ket_qua"] = "PASS"
                print(f"PASS: Nhận đúng {count} byte, CRC32={actual_crc:08X}")
    except (serial.SerialException, OSError, ValueError, RuntimeError) as error:
        result["ghi_chu"] = str(error)
        raise
    finally:
        if result["thoi_gian_s"] == "":
            result["thoi_gian_s"] = round(time.perf_counter() - started, 6)
        save_result(result)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (serial.SerialException, OSError, ValueError, RuntimeError) as error:
        print(f"FAIL: {error}. Hãy khởi động lại STM32 trước khi thử lại.", file=sys.stderr)
        sys.exit(1)
