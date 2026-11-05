#!/usr/bin/env python3
"""Tổng hợp các CSV UART vào một Excel; không mở cổng UART."""

import argparse
import csv
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from tempfile import NamedTemporaryFile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from uart_test_support import RESULT_FIELDS


DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent
# Sửa idle v2: báo cáo mới chỉ đọc TX v2, giữ nguyên CSV/Excel TX cũ.
EXCEL_FILENAME = "uart_summary_v2.xlsx"
CSV_PATTERN = "uart_*_v2_results.csv"
LOCAL_TIMEZONE = timezone(timedelta(hours=7))
SUCCESS = "THÀNH CÔNG"
FAILURE = "THẤT BẠI"
INTEGER_FORMAT = "#,##0"
DECIMAL_FORMAT = "#,##0.000"
PERCENT_FORMAT = '0.000"%"'
NUMBER_FIELDS = {
    "baud_rate": int,
    "so_byte_nhan": int,
    "so_byte_payload_yeu_cau": int,
    "thoi_gian_nhan_payload_pc_s": float,
    "hieu_suat_nhan_pc_phan_tram": float,
    "chu_ky_cpu_uart": int,
    "chu_ky_cpu_crc": int,
    "tong_chu_ky_cpu": int,
    "tai_cpu_uoc_tinh_phan_tram": float,
    "so_vong_lap_idle": int,
    "idle_elapsed_ms": int,
    "idle_max_count": int,
    "so_byte_payload_stm32": int,
    "thoi_gian_payload_stm32_s": float,
    "toc_do_payload_stm32_byte_s": float,
    "tan_so_cpu_hz": int,
}
RX_RESULT_FIELDS = (
    "thoi_diem", "cong_com", "baud_rate", "so_byte_yeu_cau", "so_byte_gui",
    "so_byte_nhan", "crc32_pc", "crc32_stm32", "thoi_gian_s", "ket_qua", "ghi_chu",
)


def read_rx_results(csv_path):
    """Trả về các dòng CSV RX đã kiểm tra, sắp theo baud và thời điểm.

    Giữ CRC dạng chuỗi để không mất số 0 ở đầu. Ô số trống giữ None
    vì lượt FAIL có thể chưa nhận được phản hồi hoặc chưa có phép đo.
    Lỗi schema/dữ liệu phát sinh ValueError trước khi thay Excel cũ.
    """
    results = []
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != list(RX_RESULT_FIELDS):
            raise ValueError("CSV thiếu cột bắt buộc của kết quả UART RX.")
        for raw in reader:
            if not any(raw.values()):
                continue
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"CSV dòng {reader.line_num}: số cột không khớp tiêu đề.")
            row = dict(raw)
            try:
                for key in ("baud_rate", "so_byte_yeu_cau", "so_byte_gui", "so_byte_nhan", "thoi_gian_s"):
                    value = raw[key].strip()
                    convert = float if key == "thoi_gian_s" else int
                    row[key] = convert(value) if value else None
                    if row[key] is not None and (not math.isfinite(row[key]) or row[key] < 0):
                        raise ValueError(f"{key} phải là số hữu hạn không âm")
                if row["baud_rate"] is None or row["baud_rate"] <= 0:
                    raise ValueError("baud_rate phải lớn hơn 0")
                if row["ket_qua"] not in ("PASS", "FAIL"):
                    raise ValueError("kết quả RX phải là PASS hoặc FAIL")
                recorded_at = datetime.fromisoformat(raw["thoi_diem"])
                if recorded_at.tzinfo is None:
                    recorded_at = recorded_at.replace(tzinfo=LOCAL_TIMEZONE)
                row["_timestamp"] = recorded_at.timestamp()
                row["_display_time"] = recorded_at.astimezone(LOCAL_TIMEZONE).replace(tzinfo=None)
            except (ValueError, OverflowError) as error:
                raise ValueError(f"CSV dòng {reader.line_num}: {error}") from error
            results.append(row)
    return sorted(results, key=lambda row: (row["baud_rate"], row["_timestamp"]))


def read_results(csv_path):
    """Trả về các dòng CSV TX đã kiểm tra, sắp theo baud và thời điểm.

    csv_path trỏ đến CSV đúng schema RESULT_FIELDS. Ô số trống giữ None;
    dòng sai phát sinh ValueError kèm số dòng để tránh xuất báo cáo sai.
    """
    results = []
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != list(RESULT_FIELDS):
            raise ValueError("CSV thiếu cột bắt buộc của kết quả UART.")
        for raw in reader:
            if not any(raw.values()):
                continue
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"CSV dòng {reader.line_num}: số cột không khớp tiêu đề.")
            row = dict(raw)
            try:
                for key, convert in NUMBER_FIELDS.items():
                    value = raw.get(key, "").strip()
                    row[key] = convert(value) if value else None
                    if row[key] is not None and not math.isfinite(row[key]):
                        raise ValueError(f"{key} không phải số hữu hạn")
                if row["baud_rate"] is None or row["baud_rate"] <= 0:
                    raise ValueError("baud_rate phải lớn hơn 0")
                if row["so_byte_nhan"] is None or row["so_byte_nhan"] < 0:
                    raise ValueError("so_byte_nhan phải lớn hơn hoặc bằng 0")
                for key in NUMBER_FIELDS:
                    if row[key] is not None and row[key] < 0:
                        raise ValueError(f"{key} không được âm")
                if row["so_byte_payload_yeu_cau"] is None:
                    raise ValueError("Thiếu kích thước payload")
                if not row["phuong_phap"].strip():
                    raise ValueError("phuong_phap không được để trống")
                if row["trang_thai_crc"] not in ("OK", "SAI", "CHƯA KIỂM TRA"):
                    raise ValueError("trạng thái CRC không hợp lệ")
                if row["ket_qua"] not in (SUCCESS, FAILURE):
                    raise ValueError("kết quả không hợp lệ")
                if (row["tai_cpu_uoc_tinh_phan_tram"] is not None
                        and row["tai_cpu_uoc_tinh_phan_tram"] < 0):
                    raise ValueError("tai_cpu_uoc_tinh_phan_tram không được âm")
                for key in ("chu_ky_cpu_uart", "chu_ky_cpu_crc", "tong_chu_ky_cpu"):
                    if row[key] is not None and row[key] < 0:
                        raise ValueError(f"{key} không được âm")
                recorded_at = datetime.fromisoformat(raw["thoi_diem"])
                if recorded_at.tzinfo is None:
                    recorded_at = recorded_at.replace(tzinfo=LOCAL_TIMEZONE)
                row["_timestamp"] = recorded_at.timestamp()
                # Excel không lưu datetime có múi giờ; hiển thị giờ Việt Nam.
                row["_display_time"] = recorded_at.astimezone(LOCAL_TIMEZONE).replace(tzinfo=None)
            except (ValueError, OverflowError) as error:
                raise ValueError(f"CSV dòng {reader.line_num}: {error}") from error
            results.append(row)
    return sorted(results, key=lambda row: (row["baud_rate"], row["so_byte_payload_yeu_cau"],
                                           row["_timestamp"]))


def style_sheet(sheet, title, description, headers, widths, table_name):
    """Định dạng sheet tại chỗ theo tiêu đề, cột và độ rộng đã cho.

    table_name phải duy nhất trong workbook. Hàm không trả về giá trị;
    giữ chuỗi ở dạng text để dữ liệu CSV không trở thành công thức Excel.
    """
    last_column = get_column_letter(len(headers))
    title_end = get_column_letter(min(len(headers), 12))
    sheet.merge_cells(f"A1:{title_end}1")
    sheet["A1"] = title
    sheet["A1"].font = Font(name="Calibri", size=18, bold=True, color="FFFFFF")
    sheet["A1"].fill = PatternFill("solid", fgColor="17365D")
    sheet["A1"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 36
    sheet.merge_cells(f"A2:{title_end}3")
    sheet["A2"] = description
    sheet["A2"].font = Font(name="Calibri", size=11, color="526477")
    sheet["A2"].alignment = Alignment(wrap_text=True, vertical="center")
    sheet.row_dimensions[2].height = 24
    sheet.row_dimensions[3].height = 24

    for index, header in enumerate(headers, start=1):
        cell = sheet.cell(5, index, header)
        cell.font = Font(name="Calibri", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="24476A")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        sheet.column_dimensions[get_column_letter(index)].width = widths[index - 1]
    sheet.row_dimensions[5].height = 42

    for cells in sheet.iter_rows(min_row=6, max_col=len(headers)):
        sheet.row_dimensions[cells[0].row].height = 32
        for cell in cells:
            cell.font = Font(name="Calibri", size=11, color="243746")
            cell.fill = PatternFill("solid", fgColor="F0F5FA" if cell.row % 2 == 0 else "FFFFFF")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if isinstance(cell.value, str):
                cell.data_type = "s"

    sheet.sheet_view.showGridLines = False
    sheet.sheet_view.zoomScale = 85
    sheet.freeze_panes = "C6"
    sheet.print_title_rows = "1:5"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    if sheet.max_row >= 6:
        table = Table(displayName=table_name, ref=f"A5:{last_column}{sheet.max_row}")
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        sheet.add_table(table)
        sheet.auto_filter.ref = table.ref


def add_detail_sheet(workbook, results, feature, index):
    """Tạo và trả về sheet chi tiết cho results đã đọc của feature.

    index dùng đặt tên bảng duy nhất. Thứ tự cột bám RESULT_FIELDS để
    CSV và Excel luôn cùng schema; thời điểm hiển thị theo UTC+7.
    """
    sheet_name = re.sub(r'[\\/*?:\[\]]', " ", feature)[:31] or "Kết quả"
    if sheet_name.casefold() in {name.casefold() for name in workbook.sheetnames}:
        sheet_name = f"{sheet_name[:26]} {index}"
    detail = workbook.create_sheet(sheet_name)
    detail.sheet_properties.tabColor = "24476A"
    detail.append([])
    # Hàng 1–5 dành cho tiêu đề và hướng dẫn, dữ liệu bắt đầu từ hàng 6.
    for row_number, row in enumerate(results, start=6):
        values = [row["_display_time"]] + [row[field] for field in RESULT_FIELDS[1:]]
        for column, value in enumerate(values, start=1):
            detail.cell(row_number, column, value)
    style_sheet(
        detail, f"KẾT QUẢ KIỂM TRA UART {feature}",
        f"{len(results)} lần chạy • Sắp xếp baud tăng dần, sau đó thời điểm tăng dần.\n"
        "PC: thời gian nhận payload. STM32: thời gian phát payload, không gồm CRC/báo cáo. Tải CPU từ idle.",
        ["Thời điểm (UTC+7)", "Phương pháp", "Baud rate", "Payload yêu cầu (byte)",
         "Số byte nhận PC", "Thời gian nhận payload PC (s)", "Hiệu suất nhận PC (%)",
         "Chu kỳ CPU UART", "Chu kỳ CPU CRC", "Tổng chu kỳ CPU", "Tải CPU ước tính (%)",
         "Số vòng lặp idle", "Thời lượng idle STM32 (ms)", "Idle hiệu chuẩn (vòng/s)",
         "Payload đã phát STM32 (byte)", "Thời gian payload STM32 (s)", "Tốc độ payload STM32 (byte/s)",
         "Tần số CPU (Hz)", "Trạng thái DWT", "Trạng thái đo idle", "Trạng thái CRC", "Kết quả"],
        [23, 16, 16, 22, 18, 25, 22, 22, 21, 22, 22, 20, 25, 25, 25, 25, 28, 22, 22, 24, 20, 17],
        f"KetQuaUART{index}",
    )
    detail.freeze_panes = "D6"
    previous_baud = None
    for row_number, row in enumerate(results, start=6):
        detail.cell(row_number, 1).number_format = "dd/mm/yyyy hh:mm:ss"
        for field, convert in NUMBER_FIELDS.items():
            column = RESULT_FIELDS.index(field) + 1
            detail.cell(row_number, column).number_format = (
                INTEGER_FORMAT if convert is int else
                PERCENT_FORMAT if field.endswith("phan_tram") else "0.000000")
        passed = row["ket_qua"] == SUCCESS
        status = detail.cell(row_number, RESULT_FIELDS.index("ket_qua") + 1)
        status.fill = PatternFill("solid", fgColor="DCFCE7" if passed else "FEE2E2")
        status.font = Font(name="Calibri", bold=True, color="166534" if passed else "991B1B")
        crc_cell = detail.cell(row_number, RESULT_FIELDS.index("trang_thai_crc") + 1)
        crc_ok = row["trang_thai_crc"] == "OK"
        crc_cell.fill = PatternFill("solid", fgColor="DCFCE7" if crc_ok else "FEE2E2")
        if previous_baud is not None and row["baud_rate"] != previous_baud:
            for cell in detail[row_number]:
                cell.border = Border(top=Side(style="medium", color="8CA9C4"))
        previous_baud = row["baud_rate"]

    return detail


def add_rx_sheet(workbook, results):
    """Thêm sheet DMA RX với đúng 11 cột nguồn; không gộp vào thống kê TX.

    results là các dòng từ read_rx_results(). Hàm trả về sheet mới,
    giữ số liệu FAIL và ghi chú thay vì suy ra các chỉ số CPU của TX.
    """
    sheet = workbook.create_sheet("DMA RX")
    sheet.sheet_properties.tabColor = "168A73"
    for row_number, row in enumerate(results, start=6):
        values = [row["_display_time"]] + [row[field] for field in RX_RESULT_FIELDS[1:]]
        for column, value in enumerate(values, start=1):
            sheet.cell(row_number, column, value)
    style_sheet(
        sheet, "KẾT QUẢ KIỂM TRA UART DMA RX",
        f"{len(results)} lần chạy • Sắp xếp baud tăng dần, sau đó thời điểm tăng dần.\n"
        "Giữ riêng các cột RX; CRC ở dạng text, ô trống là chưa có số liệu.",
        ["Thời điểm (UTC+7)", "Cổng COM", "Baud rate", "Số byte yêu cầu", "Số byte gửi",
         "Số byte nhận", "CRC32 PC", "CRC32 STM32", "Thời gian (s)", "Kết quả", "Ghi chú"],
        [23, 16, 16, 20, 20, 20, 18, 18, 20, 16, 50], "KetQuaUARTRX",
    )
    sheet.freeze_panes = "D6"
    for row_number, row in enumerate(results, start=6):
        sheet.cell(row_number, 1).number_format = "dd/mm/yyyy hh:mm:ss"
        for column in (3, 4, 5, 6):
            sheet.cell(row_number, column).number_format = INTEGER_FORMAT
        sheet.cell(row_number, 9).number_format = "0.000000"
        status = sheet.cell(row_number, 10)
        passed = row["ket_qua"] == "PASS"
        status.fill = PatternFill("solid", fgColor="DCFCE7" if passed else "FEE2E2")
        status.font = Font(name="Calibri", bold=True, color="166534" if passed else "991B1B")
    return sheet


def build_workbook(feature_results):
    """Trả về Workbook chứa bảng tổng hợp và chi tiết của feature_results.

    Đầu vào ánh xạ tên tính năng tới các dòng từ read_results(). Chỉ
    lấy trung bình lượt thành công; đếm CRC hợp lệ độc lập kết quả lượt.
    """
    workbook = Workbook()
    summary = workbook.active
    summary.title = "Tổng hợp"
    summary.sheet_properties.tabColor = "168A73"
    groups = defaultdict(list)
    for index, (feature, results) in enumerate(sorted(feature_results.items()), start=1):
        add_detail_sheet(workbook, results, feature, index)
        for row in results:
            # Sửa idle v2: không gộp khác baud/payload/clock.
            groups[(feature, row["baud_rate"], row["so_byte_payload_yeu_cau"],
                    row["tan_so_cpu_hz"] or 0)].append(row)
    for row_number, ((feature, baud, payload, cpu_hz), runs) in enumerate(sorted(groups.items()), start=6):
        successful = [row for row in runs if row["ket_qua"] == SUCCESS]
        crc_valid_count = sum(row["trang_thai_crc"] == "OK" for row in runs)

        def average(key):
            values = [row[key] for row in successful if row[key] is not None
                      and (key not in ("chu_ky_cpu_uart", "chu_ky_cpu_crc", "tong_chu_ky_cpu")
                           or row["trang_thai_dwt"] == "OK")]
            return mean(values) if values else None

        values = [
            feature, baud, payload, cpu_hz or None,
            len(runs), len(successful), len(runs) - len(successful),
            len(successful) / len(runs) * 100,
            average("so_byte_nhan"), average("thoi_gian_nhan_payload_pc_s"),
            average("hieu_suat_nhan_pc_phan_tram"),
            average("thoi_gian_payload_stm32_s"), average("toc_do_payload_stm32_byte_s"),
            average("chu_ky_cpu_uart"),
            average("chu_ky_cpu_crc"), average("tong_chu_ky_cpu"),
            average("tai_cpu_uoc_tinh_phan_tram"), average("so_vong_lap_idle"), crc_valid_count,
        ]
        for column, value in enumerate(values, start=1):
            summary.cell(row_number, column, value)
    style_sheet(
        summary, "TỔNG HỢP HIỆU NĂNG UART",
        "Trung bình của các lần THÀNH CÔNG; số lượt CRC hợp lệ đếm riêng cả kết quả thất bại.\n"
        "Chỉ so sánh cùng baud, kích thước payload và clock; tải CPU từ idle.",
        ["Phương pháp", "Baud rate", "Payload yêu cầu (byte)", "Tần số CPU (Hz)",
         "Số lần chạy", "Thành công", "Thất bại",
         "Tỷ lệ thành công (%)", "Số byte nhận PC TB", "Thời gian nhận payload PC TB (s)",
         "Hiệu suất nhận PC TB (%)", "Thời gian payload STM32 TB (s)", "Tốc độ payload STM32 TB (byte/s)",
         "Chu kỳ CPU UART TB", "Chu kỳ CPU CRC TB", "Tổng chu kỳ CPU TB",
         "Tải CPU ước tính TB (%)", "Số vòng lặp idle TB", "CRC hợp lệ"],
        [20, 16, 23, 22, 15, 15, 15, 22, 20, 25, 25, 28, 30, 24, 23, 24, 25, 23, 15], "TongHopUART",
    )
    for cells in summary.iter_rows(min_row=6):
        for cell in cells:
            cell.number_format = (
                INTEGER_FORMAT if cell.column in (2, 3, 4, 5, 6, 7, 9, 14, 15, 16, 19)
                else PERCENT_FORMAT if cell.column in (8, 11, 17)
                else DECIMAL_FORMAT
            )
        cells[0].number_format = "General"
    return workbook


def discover_csv_files(source=None):
    """Trả về thư mục và danh sách CSV theo source, hoặc thư mục mặc định.

    source có thể là thư mục hoặc một CSV. Luôn quét cả thư mục dù chỉ
    định một tệp để giữ hành vi tổng hợp chung của các script TX.
    """
    source = Path(source) if source is not None else DEFAULT_RESULTS_DIR
    directory = source if source.is_dir() else source.parent
    csv_paths = set(directory.glob(CSV_PATTERN))
    # RX không đổi schema; vẫn có sheet riêng, không tham gia so sánh TX.
    rx_path = directory / "uart_dma_rx_results.csv"
    if rx_path.exists():
        csv_paths.add(rx_path)
    if not source.is_dir():
        if source.suffix.lower() != ".csv":
            raise ValueError("Nguồn phải là thư mục kết quả hoặc tệp .csv.")
        csv_paths.add(source)
    if not csv_paths:
        raise ValueError(f"Không tìm thấy CSV kết quả theo mẫu {CSV_PATTERN} trong {directory}.")
    return directory, sorted(csv_paths)


def feature_name(csv_path):
    """Trả về nhãn tính năng từ tên csv_path, với IT đổi thành INTERRUPT."""
    stem = csv_path.stem
    if stem.startswith("uart_") and stem.endswith("_results"):
        stem = stem[len("uart_"):-len("_results")]
    if stem.endswith("_v2"):
        stem = stem[:-3]
    return " ".join("INTERRUPT" if part.lower() == "it" else part.upper() for part in stem.split("_"))


def export_excel(csv_path=None, excel_path=None):
    """Xuất các CSV cùng thư mục và trả về đường dẫn báo cáo Excel.

    csv_path chọn nguồn; excel_path chọn đầu ra, hoặc dùng giá trị mặc
    định. Chỉ thay Excel cũ khi đọc và ghi thành công; lỗi được chuyển
    cho hàm gọi và tệp tạm luôn được dọn dẹp.
    """
    directory, csv_paths = discover_csv_files(csv_path)
    excel_path = Path(excel_path) if excel_path is not None else directory / EXCEL_FILENAME
    if excel_path.suffix.lower() != ".xlsx":
        raise ValueError("Tệp báo cáo phải có phần mở rộng .xlsx.")
    if excel_path.name.lower() == "uart_summary.xlsx":
        raise ValueError("Giữ báo cáo cũ; hãy dùng uart_summary_v2.xlsx hoặc tên mới.")
    feature_results = {}
    rx_results = None
    for source_path in csv_paths:
        feature = feature_name(source_path)
        if feature in feature_results or (feature == "DMA RX" and rx_results is not None):
            raise ValueError(f"Tên tính năng bị trùng: {feature} ({source_path.name}).")
        try:
            if feature == "DMA RX":
                rx_results = read_rx_results(source_path)
            else:
                feature_results[feature] = read_results(source_path)
        except (ValueError, csv.Error) as error:
            raise ValueError(f"{source_path.name}: {error}") from error
    workbook = build_workbook(feature_results)
    temporary_path = None
    try:
        if rx_results is not None:
            add_rx_sheet(workbook, rx_results)
        with NamedTemporaryFile(dir=excel_path.parent, prefix=".uart_report_", suffix=".tmp", delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
        workbook.save(temporary_path)
        temporary_path.replace(excel_path)
    finally:
        workbook.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return excel_path


def main():
    """Đọc tham số xuất báo cáo; trả về 0 khi thành công, 1 khi gặp lỗi."""
    parser = argparse.ArgumentParser(description="Tổng hợp các CSV UART vào một Excel, không chạy phép thử UART.")
    parser.add_argument("csv", nargs="?", type=Path, default=DEFAULT_RESULTS_DIR,
                        help="Thư mục hoặc CSV nguồn; đọc mọi uart_*_results.csv cùng thư mục")
    parser.add_argument("--output", type=Path, help="Đường dẫn Excel đầu ra (.xlsx)")
    args = parser.parse_args()
    try:
        print(f"Đã tạo báo cáo Excel: {export_excel(args.csv, args.output)}")
        return 0
    except (OSError, ValueError, csv.Error) as error:
        print(f"Không tạo được Excel: {error}. Nếu tệp đang mở trong Excel, hãy đóng rồi chạy lại.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
