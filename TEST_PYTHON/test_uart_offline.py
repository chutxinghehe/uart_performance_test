"""Kiểm tra UART bằng dữ liệu giả lập; không mở cổng serial thật."""

import csv
import importlib
import io
import itertools
import struct
import sys
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

import serial
from openpyxl import load_workbook

import uart_excel_report as report
import uart_test_dma_rx as rx
import uart_test_support as support


TX_FIELDS = (
    "thoi_diem", "phuong_phap", "baud_rate", "so_byte_payload_yeu_cau",
    "so_byte_nhan", "thoi_gian_nhan_payload_pc_s", "hieu_suat_nhan_pc_phan_tram",
    "chu_ky_cpu_uart", "chu_ky_cpu_crc", "tong_chu_ky_cpu", "tai_cpu_uoc_tinh_phan_tram",
    "so_vong_lap_idle", "idle_elapsed_ms", "idle_max_count", "so_byte_payload_stm32",
    "thoi_gian_payload_stm32_s", "toc_do_payload_stm32_byte_s", "tan_so_cpu_hz",
    "trang_thai_dwt", "trang_thai_do_idle", "trang_thai_crc", "ket_qua",
)
RX_FIELDS = (
    "thoi_diem", "cong_com", "baud_rate", "so_byte_yeu_cau", "so_byte_gui",
    "so_byte_nhan", "crc32_pc", "crc32_stm32", "thoi_gian_s", "ket_qua", "ghi_chu",
)


def tx_row(**overrides):
    """Dòng v2 mẫu có thời gian PC khác thời gian STM32."""
    row = dict(zip(TX_FIELDS, ["2026-10-17T10:00:00+07:00", "DMA", 921600, 16,
                              16, 2, 50, 648, 72, 720, 25, 1500, 2000, 1000, 16,
                              1.5, 16 / 1.5, 72000000, "OK", "OK", "OK", "THÀNH CÔNG"]))
    row.update(overrides)
    return row


def serial_stream(data):
    """Trả về cổng giả đọc tuần tự data, hỗ trợ with như pyserial."""
    port = MagicMock()
    port.__enter__.return_value = port
    port.read.side_effect = io.BytesIO(data).read
    return port


class UartOfflineTests(unittest.TestCase):
    """Kiểm tra giao thức, nhánh lỗi và schema mà không cần phần cứng."""

    def test_crc_and_formulas(self):
        self.assertEqual(support.calculate_crc32_stm32(b""), 0xFFFFFFFF)
        self.assertEqual(support.calculate_crc32_stm32(bytes(4)), 0xC704DD7B)
        self.assertEqual(
            support.calculate_crc32_stm32(b"abc"),
            support.calculate_crc32_stm32(b"abc\x00"),
        )
        result = support.TestResult()
        self.assertEqual(support.crc_status(result), "CHƯA KIỂM TRA")
        self.assertIsNone(support.cpu_load_percent(result))
        result.crc_bytes = 4
        result.received_crc = result.stm32_crc = 123
        self.assertEqual(support.crc_status(result), "OK")
        result.stm32_crc += 1
        self.assertEqual(support.crc_status(result), "SAI")
        result.cpu_busy_seconds = 0.25
        result.total_seconds = 2
        # DWT và giờ PC không còn quyết định tải CPU.
        self.assertIsNone(support.cpu_load_percent(result))
        result.idle_count, result.idle_elapsed_ms, result.idle_max_count = 1500, 2000, 1000
        result.idle_status = "OK"
        self.assertEqual(support.cpu_load_percent(result), 25)
        result.total_seconds = 999
        result.cpu_busy_seconds = None
        self.assertEqual(support.cpu_load_percent(result), 25)
        result.idle_count = 0
        self.assertEqual(support.cpu_load_percent(result), 100)

    def test_dwt_and_idle_frames(self):
        cases = [
            (b"", 1, 1, "MISSING"),
            (b"DWT2", 1, 1, "INVALID"),
            (struct.pack("<4sIII", b"DWT1", 1, 720, 72000000), 1, 1, "OK"),
            (struct.pack("<4sIIII", b"DWT2", 1, 720, 72, 72000000), 1, 1, "OK"),
            (struct.pack("<4sIIII", b"DWT2", 2, 720, 72, 72000000), 1, 1, "MODE_MISMATCH"),
            (struct.pack("<4sIIII", b"DWT2", 1, 720, 721, 72000000), 1, 1, "INVALID"),
            (struct.pack("<4sIIII", b"DWT2", 1, 720, 72, 0), 1, 1, "INVALID"),
            (struct.pack("<4sIIII", b"DWT2", 1, 720, 72, 72000000), 1, 60, "WRAP_RISK"),
            (struct.pack("<4sIIII", b"DWT2", 2, 720, 72, 72000000), 2, 60, "OK"),
        ]
        for frame, mode, elapsed, expected in cases:
            with self.subTest(mode=mode, expected=expected, frame=frame):
                result = support.TestResult(total_seconds=elapsed)
                support.receive_dwt(serial_stream(frame), result, mode)
                self.assertEqual(result.dwt_status, expected)
                if expected == "WRAP_RISK":
                    self.assertIsNone(result.cpu_busy_seconds)
                if expected == "OK" and frame.startswith(b"DWT2"):
                    self.assertEqual(result.dwt_uart_cycles, 648)
        for frame, expected in [(b"", None), (b"IDL1", None),
                                (struct.pack("<4sI", b"BAD!", 4), None),
                                (struct.pack("<4sI", b"IDL1", 0), 0),
                                (struct.pack("<4sI", b"IDL1", 99), 99)]:
            with self.subTest(idle=frame):
                result = support.TestResult()
                support.receive_idle(serial_stream(frame), result)
                self.assertEqual(result.idle_count, expected)

    def test_receive_timeouts_and_timing(self):
        options = dict(baud_rate=9600, total_bytes=8, read_chunk_size=4,
                       first_byte_timeout=30, read_timeout=2, show_progress=False,
                       progress_interval=1, bits_per_byte=10)
        for data, count, crc_bytes in [(b"", 0, 0), (b"abc", 3, 0),
                                       (b"abcdefghXY", 8, 2),
                                       (b"abcdefgh" + bytes(4), 8, 4)]:
            with self.subTest(data=data):
                result = support.TestResult()
                clock = itertools.count()
                with patch.object(support.time, "perf_counter", side_effect=clock.__next__):
                    payload = support.receive_data(serial_stream(data), result, **options)
                self.assertEqual(len(payload), count)
                self.assertEqual(result.received_bytes, count)
                self.assertEqual(result.crc_bytes, crc_bytes)
                self.assertEqual(result.total_seconds is not None, crc_bytes == 4)
                if crc_bytes == 4:
                    self.assertEqual(result.payload_seconds, 1)
                    self.assertEqual(result.total_seconds, 2)

    def test_idle_v2_missing_zero_and_out_of_range(self):
        cases = [
            (b"", "MISSING", None),
            (b"IDL2\x00", "INVALID", None),
            (struct.pack("<4sI", b"IDL1", 42), "LEGACY", None),
            (struct.pack("<4sIIIII", b"IDL2", 1500, 2000, 1000, 16, 2000), "OK", 25),
            (struct.pack("<4sIIIII", b"IDL2", 0, 2000, 1000, 16, 2000), "OK", 100),
            (struct.pack("<4sIIIII", b"IDL2", 2000, 2000, 1000, 16, 2000), "OK", 0),
            (struct.pack("<4sIIIII", b"IDL2", 1, 0, 1000, 16, 0), "ZERO_DENOMINATOR", None),
            (struct.pack("<4sIIIII", b"IDL2", 1, 2000, 0, 16, 2000), "ZERO_DENOMINATOR", None),
            (struct.pack("<4sIIIII", b"IDL2", 2001, 2000, 1000, 16, 2000), "OUT_OF_RANGE", None),
        ]
        for frame, status, load in cases:
            with self.subTest(status=status, frame=frame):
                result = support.TestResult()
                support.receive_idle(serial_stream(frame), result)
                self.assertEqual(result.idle_status, status)
                self.assertEqual(support.cpu_load_percent(result), load)
                if result.stm32_payload_seconds == 0:
                    self.assertIsNone(support.stm32_payload_rate(result))

    def test_report_separates_baud_payload_clock_and_excludes_failed_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            path = folder / "uart_dma_tx_v2_results.csv"
            for row in [tx_row(), tx_row(thoi_gian_nhan_payload_pc_s=4, thoi_gian_payload_stm32_s=2.5),
                        tx_row(ket_qua="THẤT BẠI", thoi_gian_nhan_payload_pc_s=999,
                               thoi_gian_payload_stm32_s=999),
                        tx_row(baud_rate=115200), tx_row(so_byte_payload_yeu_cau=32),
                        tx_row(tan_so_cpu_hz=36000000)]:
                support.append_result(path, row)
            workbook = report.build_workbook({"DMA TX": report.read_results(path)})
            self.assertEqual(workbook["DMA TX"].max_row, 11)  # Giữ đủ 6 lượt.
            summary = workbook["Tổng hợp"]
            self.assertEqual(summary.max_row, 9)  # 4 nhóm độc lập.
            group = next(values for values in summary.iter_rows(min_row=6, values_only=True)
                         if values[:4] == ("DMA TX", 921600, 16, 72000000))
            self.assertEqual(group[4:7], (3, 2, 1))
            self.assertEqual(group[9], 3)  # PC: (2 + 4) / 2, không dùng 999.
            self.assertEqual(group[11], 2)  # STM32: (1.5 + 2.5) / 2.
            workbook.close()

    def test_legacy_results_are_not_rewritten_or_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            legacy = folder / "uart_dma_tx_results.csv"
            legacy_bytes = b'thoi_diem,so_tac_vu_nen\r\nold,42\r\n'
            legacy.write_bytes(legacy_bytes)
            legacy_excel = folder / "uart_summary.xlsx"
            legacy_excel.write_bytes(b'old workbook')
            new_path = folder / "uart_dma_tx_v2_results.csv"
            support.append_result(new_path, tx_row())
            with self.assertRaises(ValueError):
                support.append_result(legacy, tx_row())
            _, discovered = report.discover_csv_files(folder)
            self.assertEqual(discovered, [new_path])
            target = report.export_excel(folder)
            self.assertEqual(target.name, "uart_summary_v2.xlsx")
            with self.assertRaises(ValueError):
                report.export_excel(folder, legacy_excel)
            self.assertEqual(legacy.read_bytes(), legacy_bytes)
            self.assertEqual(legacy_excel.read_bytes(), b'old workbook')

    def test_tx_scripts_success_and_failures(self):
        payload = bytes(range(16))
        crc = support.calculate_crc32_stm32(payload).to_bytes(4, "little")
        for name, mode in [("polling", 1), ("it", 2), ("dma", 3)]:
            module = importlib.import_module(f"uart_test_{name}_tx")
            dwt = struct.pack("<4sIIII", b"DWT2", mode, 720, 72, 72000000)
            idle = struct.pack("<4sIIIII", b"IDL2", 1500, 2000, 1000, 16, 2000)
            cases = [(payload + crc + dwt + idle, True),
                     (payload + crc, True), (payload + bytes(4) + dwt, False),
                     (payload[:4], False), (payload + crc[:2], False),
                     (payload + crc + dwt + struct.pack("<4sIIIII", b"IDL2", 1500, 2000, 1000, 12, 2000), False)]
            for index, (frame, expected) in enumerate(cases):
                with self.subTest(script=name, case=index), tempfile.TemporaryDirectory() as directory:
                    csv_path = Path(directory) / "result.csv"
                    with patch.multiple(module, TOTAL_BYTES=16, READ_CHUNK_SIZE=4,
                                        CSV_PATH=csv_path, SHOW_PROGRESS=False), \
                            patch.object(serial, "Serial", return_value=serial_stream(frame)), \
                            patch.object(support, "save_excel") as export, \
                            redirect_stdout(io.StringIO()):
                        self.assertEqual(module.main(), expected)
                    export.assert_called_once_with(csv_path)
                    with csv_path.open(encoding="utf-8-sig", newline="") as source:
                        reader = csv.DictReader(source)
                        self.assertEqual(tuple(reader.fieldnames), TX_FIELDS)
                        row = next(reader)
                    self.assertEqual(row["ket_qua"], "THÀNH CÔNG" if expected else "THẤT BẠI")
                    if index == 0:
                        self.assertEqual(row["so_vong_lap_idle"], "1500")
                        self.assertEqual(float(row["tai_cpu_uoc_tinh_phan_tram"]), 25)
                        self.assertEqual(float(row["toc_do_payload_stm32_byte_s"]), 8)
                        self.assertEqual(row["so_byte_payload_stm32"], "16")
                    if index == 1:
                        self.assertEqual(row["tai_cpu_uoc_tinh_phan_tram"], "")
                        self.assertEqual(row["toc_do_payload_stm32_byte_s"], "")
        for error in [serial.SerialException("busy"), ValueError("baud"), KeyboardInterrupt()]:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as directory:
                module = importlib.import_module("uart_test_polling_tx")
                with patch.object(module, "CSV_PATH", Path(directory) / "error.csv"), \
                        patch.object(serial, "Serial", side_effect=error), \
                        patch.object(support, "save_excel"), redirect_stdout(io.StringIO()):
                    self.assertFalse(module.main())

    def test_rx_protocol_and_response_errors(self):
        payload = bytes(range(16))
        crc = zlib.crc32(payload)
        responses = [(f"RESULT,DONE,16,{crc:08X}\r\n".encode(), True),
                     (b"", False), (b"\xff\n", False), (b"WRONG\n", False),
                     (b"RESULT,DONE,no,XX\n", False), (b"RESULT,DONE,16,0\n", False)]
        for response, expected in responses:
            with self.subTest(response=response), tempfile.TemporaryDirectory() as directory:
                port = serial_stream(b"")
                port.write.side_effect = len
                port.read_until.return_value = response
                csv_path = Path(directory) / "rx.csv"
                with patch.object(rx, "CSV_PATH", csv_path), \
                        patch.object(sys, "argv", ["rx", "--length", "16", "--baud", "921600"]), \
                        patch.object(rx.os, "urandom", return_value=payload), \
                        patch.object(serial, "Serial", return_value=port), redirect_stdout(io.StringIO()):
                    if expected:
                        self.assertEqual(rx.main(), 0)
                    else:
                        with self.assertRaises(RuntimeError):
                            rx.main()
                port.write.assert_called_once_with(struct.pack("<I", 16) + payload)
                with csv_path.open(encoding="utf-8-sig", newline="") as source:
                    reader = csv.DictReader(source)
                    self.assertEqual(tuple(reader.fieldnames), RX_FIELDS)
                    self.assertEqual(next(reader)["ket_qua"], "PASS" if expected else "FAIL")

    def test_report_schema_and_atomic_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source = folder / "uart_dma_tx_v2_results.csv"
            row = tx_row()
            support.append_result(source, row)
            row.update(baud_rate=115200, ket_qua="THẤT BẠI")
            support.append_result(source, row)
            rows = report.read_results(source)
            self.assertEqual([item["baud_rate"] for item in rows], [115200, 921600])
            target = folder / "report.xlsx"
            report.export_excel(folder, target)
            workbook = load_workbook(target)
            self.assertEqual(workbook.sheetnames, ["Tổng hợp", "DMA TX"])
            detail = workbook["DMA TX"]
            self.assertEqual(detail.max_column, len(TX_FIELDS))
            self.assertEqual(workbook["Tổng hợp"].max_column, 19)
            self.assertEqual(detail.cell(6, 3).value, 115200)
            self.assertEqual(detail.cell(7, TX_FIELDS.index("so_vong_lap_idle") + 1).value, 1500)
            workbook.close()
            original = target.read_bytes()
            invalid = folder / "uart_dma_rx_results.csv"
            invalid.write_text("wrong,header\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "uart_dma_rx_results.csv"):
                report.export_excel(folder, target)
            self.assertEqual(target.read_bytes(), original)
            before = source.read_bytes()
            with self.assertRaises(ValueError):
                support.append_result(source, dict(reversed(list(row.items()))))
            self.assertEqual(source.read_bytes(), before)

    def test_report_accepts_rx_with_tx(self):
        self.assertEqual(report.RX_RESULT_FIELDS, rx.CSV_FIELDS)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            tx_path = folder / "uart_polling_tx_v2_results.csv"
            support.append_result(tx_path, tx_row(phuong_phap="Polling", so_vong_lap_idle=0,
                                                tai_cpu_uoc_tinh_phan_tram=100))
            target = folder / "report.xlsx"
            report.export_excel(folder, target)
            workbook = load_workbook(target)
            tx_values = {sheet.title: list(sheet.values) for sheet in workbook}
            workbook.close()
            rx_path = folder / "uart_dma_rx_results.csv"
            with rx_path.open("w", encoding="utf-8-sig", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=RX_FIELDS)
                writer.writeheader()
            # CSV chỉ có header cũng phải xuất được, như khi chưa chạy thử RX.
            report.export_excel(tx_path, target)
            workbook = load_workbook(target)
            self.assertEqual(workbook.sheetnames, ["Tổng hợp", "POLLING TX", "DMA RX"])
            self.assertEqual(workbook["DMA RX"].max_row, 5)
            self.assertEqual(workbook["DMA RX"].max_column, 11)
            for name, values in tx_values.items():
                self.assertEqual(list(workbook[name].values), values)
            workbook.close()
            rx_row = dict(zip(RX_FIELDS, ["2026-10-17T10:00:00+07:00", "COM13", 921600,
                                         16, 16, 16, "0000ABCD", "0000ABCD", 0.123456,
                                         "PASS", ""]))
            with rx_path.open("a", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=RX_FIELDS)
                writer.writerow(rx_row)
                rx_row.update(baud_rate=115200, so_byte_nhan="", crc32_stm32="",
                              ket_qua="FAIL", ghi_chu="=không phải công thức")
                writer.writerow(rx_row)
            report.export_excel(folder, target)
            workbook = load_workbook(target)
            sheet = workbook["DMA RX"]
            self.assertEqual(sheet.cell(6, 3).value, 115200)
            self.assertIsNone(sheet.cell(6, 6).value)
            self.assertEqual(sheet.cell(6, 10).value, "FAIL")
            self.assertEqual(sheet.cell(6, 11).data_type, "s")
            self.assertEqual(sheet.cell(7, 7).value, "0000ABCD")
            self.assertEqual(sheet.cell(7, 7).data_type, "s")
            self.assertEqual(sheet.cell(7, 9).value, 0.123456)
            for name, values in tx_values.items():
                self.assertEqual(list(workbook[name].values), values)
            workbook.close()
            original = target.read_bytes()
            # Giữ Excel đã có nếu CSV RX sai dữ liệu hoặc thiếu cột.
            for overrides in ({"thoi_gian_s": "nan"}, {"baud_rate": "0"},
                              {"so_byte_gui": "-1"}, {"ket_qua": "UNKNOWN"},
                              {"thoi_diem": "invalid"}):
                with self.subTest(overrides=overrides):
                    invalid_row = dict(rx_row, **overrides)
                    with rx_path.open("w", encoding="utf-8", newline="") as output:
                        writer = csv.DictWriter(output, fieldnames=RX_FIELDS)
                        writer.writeheader()
                        writer.writerow(invalid_row)
                    with self.assertRaisesRegex(ValueError, "uart_dma_rx_results.csv"):
                        report.export_excel(folder, target)
                    self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
