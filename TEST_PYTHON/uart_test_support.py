"""Dùng chung luồng nhận TX, đo thời gian, CRC và lưu báo cáo UART."""

import csv
import math
import struct
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

# Vai trò: module dùng chung cho các script TX Polling, IT và DMA.
# "TX" nhìn từ STM32: STM32 phát, còn chương trình Python nhận trên PC.
# Luồng hiện tại: payload N byte -> CRC 4 byte -> DWT2 20 byte -> IDL2 24 byte.
# Payload là dữ liệu cần kiểm tra; các gói sau payload là CRC và số liệu đo.
# Không có bước dò lại đầu khung: từng lần đọc phải đúng thứ tự và số byte.
# Các hàm nhận cùng cập nhật một TestResult để phần báo cáo dùng lại kết quả.
# Ba nguồn thời gian độc lập: perf_counter() trên PC, DWT và tick trên STM32.
# Các phép đo hoàn tất trước khi tính CRC trên PC hoặc xuất báo cáo.
# <     : các số nhiều byte dùng thứ tự little-endian.
# 4s    : một chuỗi bythoặc DWT2.es dài 4 byte, thường là magic như DWT1 
# Mỗi I : một số nguyên không dấu 32-bit, tương ứng uint32_t trong C.
# DWT (Data Watchpoint and Trace) cung cấp số chu kỳ CPU do firmware đo.
# DWT1, 16 byte: magic, mã chế độ, tổng chu kỳ CPU, tần số CPU (Hz).
DWT_FRAME = struct.Struct("<4sIII")
# Firmware hiện tại gửi DWT2; DWT1 được giữ để đọc firmware đời trước.
# DWT_FRAME.size vẫn dùng cho bước đọc 16 byte đầu của cả DWT1 lẫn DWT2.
# Kích thước khung là số byte, không phải số trường trong định dạng struct.
# DWT2, 20 byte: thêm chu kỳ CRC trước trường tần số để tách chi phí UART/CRC.
DWT_SPLIT_FRAME = struct.Struct("<4sIIII")
# Bố cục DWT2 theo offset byte (đều là uint32 trừ magic):
#   0..3: b"DWT2"; 4..7: mode; 8..11: tổng chu kỳ CPU;
#   12..15: chu kỳ CRC32_Update(); 16..19: tần số CPU tính bằng Hz.
# Timeout đọc báo cáo, tính bằng giây; tách khỏi timeout nhận payload.
DWT_TIMEOUT = 1
# IDL1, 8 byte: magic và số vòng lặp CPU rảnh (idle).
IDLE_FRAME = struct.Struct("<4sI")
# Sửa idle v2: count, elapsed_ms, max_count/s, payload_bytes, payload_ms.
IDLE_V2_FRAME = struct.Struct("<4sIIIII")
# Bố cục IDL2: magic, số vòng idle, thời lượng đo (ms), chuẩn idle (vòng/s),
# số byte payload đã phát và thời lượng phát payload (ms).
# idle_max_count là tốc độ hiệu chuẩn khi rảnh, không phải giới hạn kiểu số.


# danh sách tên cột trong file csv
# Thứ tự này phải khớp row trong save_csv và header của CSV hiện có.
RESULT_FIELDS = (
    # Nhóm cấu hình và kết quả nhận tại PC; thời điểm được lưu theo ISO 8601.
    "thoi_diem",
    "phuong_phap",
    "baud_rate",
    "so_byte_payload_yeu_cau",
    "so_byte_nhan",
    "thoi_gian_nhan_payload_pc_s",
    "hieu_suat_nhan_pc_phan_tram",
    # Chu kỳ từ DWT và tải CPU từ idle là hai loại chỉ số độc lập.
    "chu_ky_cpu_uart",
    "chu_ky_cpu_crc",
    "tong_chu_ky_cpu",
    "tai_cpu_uoc_tinh_phan_tram",
    "so_vong_lap_idle",
    "idle_elapsed_ms",
    "idle_max_count",
    # Nhóm thống kê phát do firmware gửi; không dùng thời gian PC để thay thế.
    "so_byte_payload_stm32",
    "thoi_gian_payload_stm32_s",
    "toc_do_payload_stm32_byte_s",
    "tan_so_cpu_hz",
    # Trạng thái đi kèm giúp phân biệt số liệu thiếu/sai với dữ liệu đo hợp lệ.
    "trang_thai_dwt",
    "trang_thai_do_idle",
    "trang_thai_crc",
    "ket_qua",
)
# Mã trạng thái dùng cho xử lý/CSV; nhãn tiếng Việt dùng khi hiển thị.
DWT_STATUS_LABELS = {
    "NOT_RECEIVED": "Chưa nhận",
    "MISSING": "Không có gói DWT (firmware cũ hoặc chưa gửi báo cáo)",
    "INVALID": "Gói DWT không hợp lệ",
    "MODE_MISMATCH": "Chế độ STM32 không khớp script Python",
    "WRAP_RISK": "Có thể tràn bộ đếm DWT 32 bit",
    "OK": "Hợp lệ",
}



def calculate_crc32_stm32(data):
    """Trả về CRC STM32F1 của data theo các word little-endian.

    data là đối tượng dạng byte. Đệm byte 0 đến bội số 4 để giữ cách
    ghép word của phiên bản hiện tại; đây không phải CRC của zlib.
    """
    # Giá trị khởi tạo của CRC STM32; bytes() chuẩn hóa bộ đệm đầu vào.
    crc = 0xFFFFFFFF
    data = bytes(data)

    # Phần đệm chỉ phục vụ tính CRC, không thay đổi payload đã nhận trong data gốc.
    # Ví dụ 5 byte được tính như 8 byte, với 3 byte 0 ở cuối.
    # check nếu hàm chia chia hết cho 4 (thêm 0 vào cuối nếu chưa chia hết cho 4)
    if len(data) % 4:
        data += b"\x00" * (4 - len(data) % 4)

    # Ghép mỗi nhóm 4 byte thành word 32 bit đúng thứ tự firmware nạp CRC.
    for offset in range(0, len(data), 4):
        word = (
            # Byte đầu là 8 bit thấp: [0x01, 0x02, 0x03, 0x04] -> 0x04030201.
            data[offset]
            | (data[offset + 1] << 8)
            | (data[offset + 2] << 16)
            | (data[offset + 3] << 24)
        )
        # XOR word vào CRC rồi xử lý 32 bit, bắt đầu từ bit cao nhất.
        crc ^= word
        for _ in range(32):
            if crc & 0x80000000:
                # Đa thức CRC của STM32, bỏ hệ số x^32 được biểu diễn ngầm.
                crc = (crc << 1) ^ 0x04C11DB7
            else:
                crc <<= 1
            # Python không tự tràn số nguyên; mặt nạ mô phỏng thanh ghi 32 bit.
            crc &= 0xFFFFFFFF

    # Trả CRC thô sau xử lý, không đảo bit và không XOR 0xFFFFFFFF ở cuối.
    return crc


class ReceiveProgress:
    """Cập nhật một dòng terminal theo thời gian, không in mỗi byte/khối."""

    
    """
    - hàm cập nhật đo nhận in terminal
    - gọi init lúc đầu, finish lúc sau
    - hàm update để cập nhật tiến trình
    """
    def __init__(self, start_time, enabled=True, interval=1.0):
        # start_time lấy từ perf_counter(); interval tính bằng giây giữa hai lần in.
        # enabled=False bỏ qua hiển thị, giúp giảm chi phí I/O trong lúc đo.
        self.start_time = start_time
        self.enabled = enabled
        self.interval = interval
        # Lưu thời gian đã trôi qua ở lần in gần nhất; None cho phép in lần đầu.
        self.last_update = None

    def update(self, received, total):
        """In received/total khi đủ interval; không trả về giá trị."""
        if not self.enabled:
            return
        # Đồng hồ đo khoảng thời gian, không phụ thuộc việc chỉnh giờ hệ thống.
        elapsed = time.perf_counter() - self.start_time
        # Chỉ kiểm tra nhịp cập nhật, không sleep nên không chủ động dừng nhận UART.
        if self.last_update is not None and elapsed - self.last_update < self.interval:
            return
        self.last_update = elapsed
        # end="" giữ con trỏ trên cùng dòng cho các lần cập nhật tiếp theo.
        self._print(received, total, elapsed, end="")

    def finish(self, received, total, elapsed):
        """In dòng cuối với elapsed đã chốt để không kéo dài phép đo."""
        # Gọi sau khi chốt thời gian nhận để lần in cuối không nằm trong phép đo.
        if self.enabled:
            self._print(received, total, elapsed, end="\n")

    @staticmethod
    def _print(received, total, elapsed, end):
        # staticmethod vì thao tác định dạng không cần đọc trạng thái đối tượng.
        # total=0 cho phần trăm 0, tránh chia cho 0 trong riêng phần hiển thị.
        percent = received / total * 100 if total else 0
        # Căn cột theo tổng số byte; ký tự \r đưa con trỏ về đầu dòng hiện tại.
        width = len(f"{total:,}")
        print(f"\rNhận: {percent:6.2f}% | {received:>{width},}/{total:,} byte | {elapsed:8.1f} s",
              end=end, flush=True)
        # flush=True đẩy ngay nội dung ra terminal; chi phí này có thể ảnh hưởng phép đo.


def receive_dwt(ser, result, expected_mode):
    """Đọc DWT1/DWT2 từ ser (serial) và cập nhật result, không trả về giá trị.

    expected_mode là mã polling/IT/DMA cần khớp firmware. Gọi sau khi
    chốt thời gian Payload + CRC; dữ liệu DWT thiếu hoặc sai được ghi
    vào trạng thái riêng, không tự suy ra chu kỳ từ thời gian PC.
    """
    # ser là cổng pyserial đang mở; result được sửa trực tiếp, không tạo bản sao.
    # Hàm giả định con trỏ nhận đang ở đầu gói DWT, ngay sau CRC của payload.
    # timeout áp dụng cho mỗi ser.read(), không phải hạn chót chung cho cả hàm.
    ser.timeout = DWT_TIMEOUT
    # Đọc 16 byte chung trước để nhận diện DWT1 hoặc DWT2 qua magic.
    frame = ser.read(DWT_FRAME.size)
    result.dwt_bytes = len(frame)

    # Không nhận byte nào là MISSING; nhận một phần khung sẽ bị đánh INVALID.
    if not frame:
        result.dwt_status = "MISSING"
        result.dwt_detail = "Nạp firmware có gửi gói DWT sau CRC để có số liệu CPU."
        return
    split_crc = frame[:4] == b"DWT2"
    # Magic là 4 byte nhận dạng phiên bản, không phải dữ liệu CRC hay chu kỳ.
    result.dwt_frame_size = DWT_SPLIT_FRAME.size if split_crc else DWT_FRAME.size

    # DWT2 cần đọc thêm 4 byte để đủ khung 20 byte trước khi giải mã.
    if split_crc and len(frame) == DWT_FRAME.size:
        # Không đọc bù nếu khối 16 byte đầu đã thiếu; nhánh kiểm tra sau sẽ báo lỗi.
        frame += ser.read(DWT_SPLIT_FRAME.size - DWT_FRAME.size)
        result.dwt_bytes = len(frame)

    if len(frame) != result.dwt_frame_size:
        result.dwt_status = "INVALID"
        result.dwt_detail = f"Nhận {len(frame)}/{result.dwt_frame_size} byte DWT."
        return
    
    # Chỉ unpack khi đủ khung; DWT1 không cung cấp số chu kỳ CRC riêng.
    if split_crc:
        # unpack() chuyển bytes thành các số nguyên theo thứ tự trường trên dây.
        magic, mode, cycles, crc_cycles, cpu_hz = DWT_SPLIT_FRAME.unpack(frame)
    else:
        magic, mode, cycles, cpu_hz = DWT_FRAME.unpack(frame)
        crc_cycles = None

    # kiểm tra dữ liệu cơ bản + mode 
    if magic not in (b"DWT1", b"DWT2") or mode not in (1, 2, 3) or cpu_hz == 0:
        result.dwt_status = "INVALID"
        result.dwt_detail = "Sai dấu nhận dạng DWT, chế độ hoặc tần số CPU."
        return
    
    # Phát hiện firmware chạy khác phương pháp mà script đang kiểm tra.
    if mode != expected_mode:
        result.dwt_status = "MODE_MISMATCH"
        result.dwt_detail = f"STM32 báo mode={mode}, script cần mode={expected_mode} (1=polling, 2=interrupt, 3=DMA)."
        return
    result.dwt_cycles = cycles
    result.dwt_crc_cycles = crc_cycles
    result.core_clock_hz = cpu_hz
    # Giữ số liệu thô trước kiểm tra tràn để báo cáo vẫn cho xem giá trị nhận được.
    # Polling đo một khoảng liên tục, nên thời gian toàn lượt có thể làm phép trừ
    # CYCCNT mất một vòng. IT/DMA cộng hiệu CYCCNT của từng lời gọi HAL/IRQ ngắn;
    # DWT quay vòng giữa các IRQ không làm sai các hiệu uint32_t đó. Các đoạn đo
    # và tổng tích lũy IT/DMA vẫn phải nằm trong giới hạn 32 bit của firmware.
    # Chu kỳ quay vòng = 2^32 / cpu_hz; ở 72 MHz xấp xỉ 59,65 giây.
    # Thời gian PC chỉ dùng cảnh báo nguy cơ, không dùng để khôi phục số vòng tràn.
    if (mode == 1 and result.total_seconds is not None
            and result.total_seconds >= (1 << 32) / cpu_hz):
        result.dwt_status = "WRAP_RISK"
        result.dwt_detail = "Giữ giá trị chu kỳ thô; không đổi ra thời gian khi có nguy cơ tràn."
        return
    if crc_cycles is not None:
        # None nghĩa là không có trường CRC; giá trị 0 vẫn là số đo có thể sử dụng.
        if crc_cycles > cycles:
            result.dwt_status = "INVALID"
            result.dwt_detail = "Chu kỳ CRC vượt tổng chu kỳ CPU; không tính hiệu."
            return
        # UART = tổng chu kỳ - chu kỳ CRC; chia tần số Hz để đổi sang giây.
        # Phần còn lại có thể gồm sinh dữ liệu, chờ UART và gửi trailer CRC,
        # tùy phạm vi đo firmware; không đồng nghĩa chỉ có lệnh xử lý UART.
        result.dwt_uart_cycles = cycles - crc_cycles
        result.crc_busy_seconds = crc_cycles / cpu_hz
        result.uart_busy_seconds = result.dwt_uart_cycles / cpu_hz
    else:
        result.dwt_detail = "Firmware DWT1 chỉ báo tổng; chưa có số chu kỳ CRC để trừ."
    result.cpu_busy_seconds = cycles / cpu_hz
    result.dwt_status = "OK"


def receive_idle(ser, result):
    """Sửa idle v2: đọc thống kê STM32; IDL1 cũ chỉ có count, không suy ra % CPU."""
    # Được gọi sau receive_dwt(); firmware phải đặt IDL ngay sau báo cáo DWT.
    # Hàm chỉ kiểm tra/giải mã thống kê, không tự hiệu chuẩn idle trên PC.
    ser.timeout = DWT_TIMEOUT
    magic = ser.read(4)
    if not magic:
        # Không có báo cáo: giữ idle_status="MISSING" của TestResult mới tạo.
        return
    # Hỗ trợ khung cũ để ghi nhận count dù thiếu dữ liệu tính tải CPU.
    if magic == b"IDL1":
        frame = magic + ser.read(IDLE_FRAME.size - 4)
        if len(frame) == IDLE_FRAME.size:
            _, result.idle_count = IDLE_FRAME.unpack(frame)
            result.idle_status = "LEGACY"
        else:
            result.idle_status = "INVALID"
        return
    if magic != b"IDL2":
        result.idle_status = "INVALID"
        return
    # IDL2 có 24 byte: magic và 5 số uint32 little-endian.
    frame = magic + ser.read(IDLE_V2_FRAME.size - 4)
    if len(frame) != IDLE_V2_FRAME.size:
        result.idle_status = "INVALID"
        return
    (_, result.idle_count, result.idle_elapsed_ms, result.idle_max_count,
     result.stm32_payload_bytes, payload_ms) = IDLE_V2_FRAME.unpack(frame)
    # Dấu _ bỏ qua magic đã kiểm tra; các trường còn lại cập nhật thẳng vào result.
    # Firmware gửi mili giây; kết quả và báo cáo dùng đơn vị giây.
    result.stm32_payload_seconds = payload_ms / 1000
    result.idle_status = "OK"
    # Đặt OK trước vì cpu_load_percent() chỉ tính khi trạng thái đầu vào là OK.
    # Tách dữ liệu thiếu mẫu số khỏi dữ liệu có tỷ lệ idle ngoài miền hợp lệ.
    if result.idle_elapsed_ms == 0 or result.idle_max_count == 0:
        result.idle_status = "ZERO_DENOMINATOR"
    elif cpu_load_percent(result) is None:
        result.idle_status = "OUT_OF_RANGE"


def crc_status(result):
    """Trả về OK, SAI hoặc CHƯA KIỂM TRA theo CRC trong result."""
    # Chỉ so sánh khi đủ 4 byte CRC và cả hai phía đã có giá trị.
    if (result.crc_bytes != 4 or result.received_crc is None
            or result.stm32_crc is None):
        return "CHƯA KIỂM TRA"
    return "OK" if result.received_crc == result.stm32_crc else "SAI"


def cpu_load_percent(result):
    """100 - % idle; thiếu/0/ngoài miền trả None, không dùng giờ PC."""
    values = (result.idle_count, result.idle_elapsed_ms, result.idle_max_count)
    # Kiểm tra None trước phép so sánh số; toán tử or dừng ngay khi điều kiện đúng.
    # Trả None để biểu thị không tính được, khác với tải hợp lệ bằng 0%.
    if (result.idle_status != "OK" or any(value is None for value in values)
            or result.idle_count < 0 or result.idle_elapsed_ms <= 0
            or result.idle_max_count <= 0):
        return None
    # Chuẩn vòng/s × thời lượng STM32 (s) = số vòng idle tối đa trong lượt đo.
    # Ví dụ chuẩn 100.000 vòng/s, đo 500 ms, có 20.000 vòng: idle=40%, tải=60%.
    idle_pct = result.idle_count / (result.idle_max_count * result.idle_elapsed_ms / 1000) * 100
    if not math.isfinite(idle_pct) or not 0 <= idle_pct <= 100:
        # Không ép tỷ lệ về 0..100 vì sẽ che khuất dữ liệu đo/hiệu chuẩn bất hợp lệ.
        return None
    # Phần thời gian không rảnh được dùng làm ước tính tải CPU.
    return 100 - idle_pct


def stm32_payload_rate(result):
    """Tốc độ phát payload trên STM32, byte/s; không lấy thời gian PC."""
    if (result.stm32_payload_bytes is None or result.stm32_payload_seconds is None
            or result.stm32_payload_seconds <= 0):
        return None
    # Chỉ dùng số byte và thời lượng do STM32 báo để tính tốc độ phát.
    return result.stm32_payload_bytes / result.stm32_payload_seconds


def append_result(csv_path, row):
    """Thêm row vào csv_path theo đúng cột TX, không trả về giá trị.

    Kiểm tra header trước khi nối để tránh trộn schema. Tệp mới được
    thay thế qua tệp tạm; lỗi cấu trúc hoặc I/O được chuyển cho hàm gọi.
    """
    csv_path = Path(csv_path)
    # row phải chứa đúng tên và thứ tự cột, không tự thêm cột hay đổi schema cũ.
    # dict giữ thứ tự chèn khóa, nên danh sách này cũng xác định thứ tự cột.
    fields = list(row)
    if fields != list(RESULT_FIELDS):
        raise ValueError("Dòng kết quả không khớp schema CSV UART.")
    if csv_path.exists() and csv_path.stat().st_size:
        # utf-8-sig đọc được header có BOM; newline="" để csv xử lý xuống dòng.
        with csv_path.open(newline="", encoding="utf-8-sig") as source:
            reader = csv.DictReader(source)
            old_fields = reader.fieldnames or []
            # Từ chối header trống, tên cột lặp hoặc tên rỗng trước khi ghi nối.
            if not old_fields or len(old_fields) != len(set(old_fields)) or not all(old_fields):
                raise ValueError("Header CSV không hợp lệ.")
            if old_fields != fields:
                raise ValueError("Header CSV không khớp schema mới; hãy chuyển đổi CSV trước khi ghi tiếp.")
        # Khi nối dòng, dùng UTF-8 thường để không chèn thêm BOM giữa tệp.
        with csv_path.open("a", newline="", encoding="utf-8") as output:
            csv.DictWriter(output, fieldnames=fields).writerow(row)
        return
    temporary_path = None
    # Tệp chưa có hoặc đang rỗng đều được tạo lại với header và dòng kết quả đầu.
    try:
        # Ghi đủ header và dữ liệu vào tệp tạm cùng thư mục trước khi thay đích.
        with NamedTemporaryFile(mode="w", dir=csv_path.parent, prefix=".uart_csv_",
                                suffix=".tmp", delete=False, newline="", encoding="utf-8-sig") as output:
            temporary_path = Path(output.name)
            writer = csv.DictWriter(output, fieldnames=fields)
            # utf-8-sig thêm BOM ở đầu tệp mới để hỗ trợ đọc tiếng Việt trong Excel.
            writer.writeheader()
            writer.writerow(row)
        # Đóng tệp tạm trước replace để tương thích cơ chế khóa tệp trên Windows.
        temporary_path.replace(csv_path)
    finally:
        # Dọn tệp tạm khi ghi lỗi; missing_ok xử lý trường hợp đã replace xong.
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


# dataclass tự tạo __init__ từ các trường bên dưới; mỗi lượt đo có một đối tượng.
# Kiểu "float | None" cho phép số thực hoặc chưa có số liệu; annotation không
# tự kiểm tra kiểu khi chạy. Giá trị 0 và None có ý nghĩa khác nhau trong báo cáo.
@dataclass
class TestResult:
    """Lưu dữ liệu và phép đo của một lượt TX; None biểu thị chưa đo được."""

    # Số byte nhận thực tế: payload và CRC được theo dõi riêng.
    received_bytes: int = 0
    crc_bytes: int = 0
    # Thời lượng tại PC: payload, payload + CRC, hoặc đến lúc dừng vì lỗi.
    payload_seconds: float | None = None
    # total_seconds chỉ được chốt khi nhận đủ cả payload và 4 byte CRC.
    total_seconds: float | None = None
    observed_seconds: float | None = None
    # observed_seconds phục vụ chẩn đoán khi dừng/timeout, không thay payload_seconds.
    # received_crc do PC tính; stm32_crc được giải mã từ 4 byte firmware gửi.
    received_crc: int | None = None
    stm32_crc: int | None = None
    # Kích thước khung DWT nhận được và số chu kỳ CPU do firmware báo.
    dwt_bytes: int = 0
    dwt_frame_size: int = DWT_SPLIT_FRAME.size
    # Ban đầu kỳ vọng DWT2 (20 byte); receive_dwt đổi thành 16 nếu nhận khung cũ.
    dwt_cycles: int | None = None
    dwt_crc_cycles: int | None = None
    dwt_uart_cycles: int | None = None
    # core_clock_hz do firmware báo, không suy từ baud rate hoặc cấu hình máy PC.
    core_clock_hz: int | None = None
    # Thời gian CPU quy đổi từ DWT; không phải thời gian truyền trên đường UART.
    cpu_busy_seconds: float | None = None
    crc_busy_seconds: float | None = None
    uart_busy_seconds: float | None = None
    # Trạng thái báo cáo độc lập với kết quả kiểm tra dữ liệu/CRC.
    dwt_status: str = "NOT_RECEIVED"
    dwt_detail: str = ""
    idle_count: int | None = None
    # Count đếm số lần firmware chạy bước idle trong cửa sổ đo, không phải chu kỳ CPU.
    # Sửa idle v2: số vòng idle, thời lượng STM32 và số vòng chuẩn mỗi giây.
    idle_elapsed_ms: int | None = None
    idle_max_count: int | None = None
    idle_status: str = "MISSING"
    # Các trạng thái khác: LEGACY, INVALID, ZERO_DENOMINATOR, OUT_OF_RANGE, OK.
    # Payload do STM32 thống kê, dùng đối chiếu số byte và tính tốc độ phát.
    stm32_payload_bytes: int | None = None
    stm32_payload_seconds: float | None = None
    # Cấu hình yêu cầu, kết luận và thông báo chung của lượt kiểm tra.
    requested_payload_bytes: int = 0
    passed: bool = False
    detail: str = ""


def receive_data(ser, result, *, baud_rate, total_bytes, read_chunk_size,
                 first_byte_timeout, read_timeout, show_progress,
                 progress_interval, bits_per_byte):
    """Nhận Payload và CRC, trả về bytearray và cập nhật result.

    ser là cổng đã mở; các tham số chỉ định kích thước, baud, timeout và
    tiến trình. Chốt thời gian trước khi đọc DWT hoặc tính CRC trên PC
    để các bước báo cáo không kéo dài khoảng đo dữ liệu.
    """
    # Các tham số sau * phải truyền theo tên, tránh nhầm các cấu hình cùng kiểu số.
    # total_bytes: số byte payload mong đợi, không gồm CRC/DWT/idle.
    # read_chunk_size: số byte tối đa yêu cầu mỗi lần đọc payload.
    # first_byte_timeout: thời gian chờ khởi động; read_timeout: mức chờ tối thiểu
    # cho mỗi khối. show_progress/progress_interval điều khiển hiển thị terminal.
    # bits_per_byte: số bit trên dây cho mỗi byte dữ liệu, dùng tính timeout.
    # bytearray cho phép nối nhiều khối; trả cả dữ liệu nhận dở khi gặp timeout.
    data = bytearray()
    # Thời gian chờ người dùng khởi động STM32 không được cộng vào phép đo.
    ser.timeout = first_byte_timeout
    first_byte = ser.read(1)
    # Mốc PC bắt đầu ngay sau lệnh đọc byte đầu, không gồm thời gian chờ byte đó.
    start_time = time.perf_counter()
    if not first_byte:
        result.detail = f"Không nhận được byte đầu trong {first_byte_timeout} giây."
        return data

    progress = ReceiveProgress(start_time, show_progress, progress_interval)
    try:
        data.extend(first_byte)
        result.received_bytes = len(data)
        progress.update(result.received_bytes, total_bytes)
        # Chừa thời gian nhận cả khối ở baud thấp, vẫn giới hạn mỗi lần đọc.
        # Thời gian lý thuyết một khối = số byte × bit/byte ÷ baud (bit/s).
        # Hệ số 2 chừa biên chờ; max() không để timeout thấp hơn cấu hình ban đầu.
        ser.timeout = max(
            read_timeout, read_chunk_size * bits_per_byte / baud_rate * 2
        )
        payload_finished = start_time
        # Nếu payload chỉ có 1 byte, vòng while không chạy và thời lượng là 0.
        while len(data) < total_bytes:
            # Giới hạn theo payload còn thiếu để không đọc lấn sang CRC/báo cáo.
            requested = min(total_bytes - len(data), read_chunk_size)
            chunk = ser.read(requested)
            # pyserial có thể trả ít byte hơn requested khi hết timeout,
            # kể cả b""; không giả định mỗi read() luôn nhận trọn một khối.
            # Chốt mốc cuối ngay khi đọc đủ payload, trước xử lý bộ đệm và in.
            if len(data) + len(chunk) == total_bytes:
                payload_finished = time.perf_counter()
            data.extend(chunk)
            result.received_bytes = len(data)
            if len(data) < total_bytes:
                progress.update(result.received_bytes, total_bytes)
            # read() trả thiếu số byte yêu cầu được xem là hết thời gian chờ.
            if len(chunk) < requested:
                result.detail = (
                    "Hết thời gian chờ nhận dữ liệu: "
                    f"đã nhận {len(data)}/{total_bytes} byte."
                )
                return data

        result.payload_seconds = payload_finished - start_time
        # Đây là thời gian nhận quan sát ở PC, có ảnh hưởng bộ đệm USB-UART/HĐH.
        # CRC là trailer 4 byte ngay sau payload, không tính vào payload_seconds.
        crc_trailer = ser.read(4)
        crc_finished = time.perf_counter()
        result.crc_bytes = len(crc_trailer)
        if len(crc_trailer) != 4:
            result.detail = (
                "Hết thời gian chờ nhận CRC từ STM32: "
                f"đã nhận {len(crc_trailer)}/4 byte CRC."
            )
            return data

        result.total_seconds = crc_finished - start_time
        # Không gán total_seconds khi CRC thiếu; hàm gọi sẽ bỏ đọc DWT/idle.
        # Thứ tự byte phải trùng uint32 little-endian mà firmware truyền.
        result.stm32_crc = int.from_bytes(crc_trailer, byteorder="little")
        return data
    finally:
        # Khi lỗi, đây là thời gian đến lúc phát hiện lỗi, gồm cả chờ timeout.
        result.observed_seconds = (
            result.total_seconds
            if result.total_seconds is not None
            else time.perf_counter() - start_time
        )
        progress.finish(result.received_bytes, total_bytes, result.observed_seconds)
        # finally cũng chạy khi return data trong try; không chạy nếu thiếu byte đầu
        # vì trường hợp đó thoát trước khi tạo progress và đi vào try.


def print_summary(result, *, method, serial_port, baud_rate, total_bytes,
                  bits_per_byte, dwt_scope):
    """In kết quả theo cấu hình TX; giữ ô chưa đo dưới dạng thông báo.

    result chứa dữ liệu đã chốt; hàm chỉ hiển thị và không trả về giá trị.
    """
    # dwt_scope do script từng chế độ cung cấp để giải thích phạm vi chu kỳ đã đo.
    # Các điều kiện "is not None" vẫn cho phép hiển thị giá trị đo hợp lệ bằng 0.
    print("\n" + "=" * 60)
    print(f"KẾT QUẢ KIỂM TRA UART {method.upper()} TX")
    print(f"Cổng: {serial_port} | Tốc độ baud: {baud_rate} | Cấu hình: 8N1")
    print(f"Dữ liệu đã nhận: {result.received_bytes}/{total_bytes} byte")
    print(f"CRC đã nhận: {result.crc_bytes}/4 byte")
    # bits_per_byte gồm cả start/stop/parity theo cấu hình; 8N1 là 10 bit/byte.
    theoretical_seconds = total_bytes * bits_per_byte / baud_rate
    print(f"Thời gian dữ liệu lý thuyết: {theoretical_seconds:.6f} giây")
    if result.payload_seconds is not None:
        elapsed = result.payload_seconds
        print(f"Thời gian nhận payload tại PC: {elapsed:.6f} giây ({elapsed * 1000:.3f} ms)")
        if elapsed > 0:
            # byte/s dùng byte thực nhận; KiB/s = byte/s ÷ 1024.
            # Hiệu suất = thời gian lý thuyết ÷ thời gian PC × 100, không phải tải CPU.
            rate = result.received_bytes / elapsed
            print(f"Tốc độ nhận payload tại PC: {rate:.2f} byte/s | {rate / 1024:.2f} KiB/s")
            print(f"Hiệu suất nhận tại PC so với UART lý thuyết: {theoretical_seconds / elapsed * 100:.2f}%")
    if result.total_seconds is not None:
        elapsed = result.total_seconds
        print(f"Thời gian nhận payload + CRC tại PC: {elapsed:.6f} giây ({elapsed * 1000:.3f} ms)")
    elif result.observed_seconds is not None:
        print(f"Thời gian đến khi dừng (gồm chờ lỗi): {result.observed_seconds:.6f} giây")

    # In CRC ở dạng hex 8 chữ số để đối chiếu trực tiếp giá trị 32 bit.
    for label, value in (
        ("CRC do PC tính từ dữ liệu nhận được", result.received_crc),
        ("CRC do STM32 gửi", result.stm32_crc),
    ):
        print(f"{label}: " + (f"0x{value:08X}" if value is not None else "chưa có"))
    if result.stm32_crc is not None and result.received_crc is not None:
        print("CRC STM32 / PC: " + (
            "KHỚP" if result.stm32_crc == result.received_crc else "KHÔNG KHỚP"
        ))
    print(f"DWT đã nhận: {result.dwt_bytes}/{result.dwt_frame_size} byte | {DWT_STATUS_LABELS[result.dwt_status]}")
    # Vẫn hiển thị chu kỳ thô khi có; thời gian CPU chỉ in nếu đã quy đổi hợp lệ.
    if result.dwt_cycles is not None:
        print(f"DWT CPU tổng (gồm CRC): {result.dwt_cycles:,} chu kỳ")
        print(f"Tần số CPU do STM32 báo: {result.core_clock_hz:,} Hz")
    if result.cpu_busy_seconds is not None:
        print(f"Thời gian CPU theo DWT: {result.cpu_busy_seconds:.6f} giây ({result.cpu_busy_seconds * 1000:.3f} ms)")
    else:
        print("Thời gian CPU theo DWT: chưa có số liệu hợp lệ.")
    if result.dwt_uart_cycles is not None:
        print(f"DWT tính CRC32_Update: {result.dwt_crc_cycles:,} chu kỳ")
        print(f"DWT CPU UART không tính CRC32_Update: {result.dwt_uart_cycles:,} chu kỳ")
        print(f"Thời gian CPU tính CRC: {result.crc_busy_seconds:.6f} giây")
        print(f"Thời gian CPU UART không tính CRC: {result.uart_busy_seconds:.6f} giây")
    else:
        print("CPU UART không tính CRC: chưa có số liệu hợp lệ.")
    if result.dwt_detail:
        print(result.dwt_detail)
    print("Số vòng lặp idle: " + (f"{result.idle_count:,}" if result.idle_count is not None else "chưa nhận"))
    print(f"Đo idle: {result.idle_status} | thời lượng STM32: {result.idle_elapsed_ms} ms | chuẩn: {result.idle_max_count} vòng/s")
    # Tải CPU lấy từ idle; DWT được dùng riêng để báo chi phí xử lý UART/CRC.
    load = cpu_load_percent(result)
    print("Tải CPU ước tính từ idle: " + (f"{load:.3f}%" if load is not None else "chưa có số liệu hợp lệ"))
    if result.stm32_payload_bytes is not None:
        print(f"Payload đã phát trên STM32: {result.stm32_payload_bytes} byte | thời gian: {result.stm32_payload_seconds:.6f} s")
    stm32_rate = stm32_payload_rate(result)
    if stm32_rate is not None:
        print(f"Tốc độ phát payload trên STM32: {stm32_rate:.2f} byte/s")
    print(dwt_scope)
    print(("THÀNH CÔNG: " if result.passed else "THẤT BẠI: ") + result.detail)
    print("Thời gian nhận PC chịu ảnh hưởng USB-UART/HĐH; thời gian phát STM32 lấy từ HAL_GetTick().")
    print("=" * 60)


def save_csv(result, started_at, *, csv_path, method, baud_rate, bits_per_byte):
    """Ghi result theo đúng thứ tự cột TX và trả về trạng thái lưu.

    Sửa idle v2: tách thời gian PC/STM32, tải CPU từ idle.
    started_at là thời điểm ISO. Lỗi ghi được báo và trả về False.
    """
    elapsed = result.payload_seconds
    # Chưa có thời lượng hợp lệ thì giữ None để CSV để trống chỉ số chưa đo.
    rate = result.received_bytes / elapsed if elapsed and elapsed > 0 else None
    # Hiệu suất PC = tốc độ nhận thực tế / tốc độ byte lý thuyết của UART.
    row = {
        # Giữ các giá trị dạng số/None; csv tự chuyển sang văn bản khi ghi dòng.
        "thoi_diem": started_at,
        "phuong_phap": method,
        "baud_rate": baud_rate,
        "so_byte_payload_yeu_cau": result.requested_payload_bytes,
        "so_byte_nhan": result.received_bytes,
        "thoi_gian_nhan_payload_pc_s": elapsed,
        "hieu_suat_nhan_pc_phan_tram": rate / (baud_rate / bits_per_byte) * 100 if rate is not None else None,
        "chu_ky_cpu_uart": result.dwt_uart_cycles,
        "chu_ky_cpu_crc": result.dwt_crc_cycles,
        "tong_chu_ky_cpu": result.dwt_cycles,
        "tai_cpu_uoc_tinh_phan_tram": cpu_load_percent(result),
        "so_vong_lap_idle": result.idle_count,
        "idle_elapsed_ms": result.idle_elapsed_ms,
        "idle_max_count": result.idle_max_count,
        "so_byte_payload_stm32": result.stm32_payload_bytes,
        "thoi_gian_payload_stm32_s": result.stm32_payload_seconds,
        "toc_do_payload_stm32_byte_s": stm32_payload_rate(result),
        "tan_so_cpu_hz": result.core_clock_hz,
        "trang_thai_dwt": result.dwt_status,
        "trang_thai_do_idle": result.idle_status,
        "trang_thai_crc": crc_status(result),
        "ket_qua": "THÀNH CÔNG" if result.passed else "THẤT BẠI",
    }
    try:
        append_result(csv_path, row)
        print(f"Đã lưu kết quả: {csv_path}")
        return True
    except (OSError, ValueError, csv.Error) as error:
        # Lưu báo cáo thất bại được trả riêng, không thay đổi result.passed của UART.
        print(f"Không lưu được CSV: {error}. Hãy kiểm tra quyền ghi hoặc đóng tệp trong Excel.")
        return False


def save_excel(csv_path):
    """Cập nhật Excel từ thư mục csv_path sau phép đo, không trả về giá trị.

    Import trễ để thiếu openpyxl không ngăn nhận UART và lưu CSV.
    Lỗi xuất báo cáo được thông báo; CSV đã lưu vẫn được giữ lại.
    """
    # csv_path được chuyển cho bộ xuất để đọc nguồn báo cáo; không nhận lại UART.
    try:
        # Chỉ nạp bộ xuất báo cáo khi cần, sau khi bước đo UART đã hoàn tất.
        from uart_excel_report import export_excel

        print(f"Đã cập nhật Excel: {export_excel(csv_path)}")
    except ImportError:
        print(
            "Chưa xuất được Excel vì thiếu thư viện. "
            f'Chạy: & "{sys.executable}" -m pip install -r TEST_PYTHON/requirements.txt'
        )
    except (OSError, ValueError, csv.Error) as error:
        print(
            f"Không cập nhật được Excel: {error}. CSV đã được lưu. "
            "Nếu tệp đang mở trong Excel, hãy đóng rồi chạy lại uart_excel_report.py."
        )


def run_tx_test(*, method, serial_port, baud_rate, total_bytes, read_chunk_size,
                first_byte_timeout, read_timeout, show_progress,
                progress_interval, bits_per_byte, csv_path, test_mode_code,
                dwt_scope):
    """Chạy một lượt TX theo cấu hình script và trả về True khi đạt.

    Các tham số giữ nguyên cấu hình polling/IT/DMA. Dữ liệu, CRC, DWT
    và counter được đọc theo thứ tự giao thức; báo cáo luôn chạy trong
    finally, kể cả timeout, lỗi cổng hoặc người dùng hủy.
    """
    # Bộ xuất Excel cũng import module này nhưng không cần cài pyserial.
    import serial

    # method là nhãn hiển thị; test_mode_code mới là số đối chiếu với firmware:
    # 1=Polling, 2=Interrupt, 3=DMA. Python không gửi lệnh chuyển chế độ cho STM32.
    # serial_port, baud_rate và các tham số nhận do script gọi hàm quyết định.
    result = TestResult(requested_payload_bytes=total_bytes)
    # Ghi thời điểm có múi giờ để phân biệt các lượt đo trong báo cáo.
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print("=" * 60)
    print(f"KIỂM TRA UART TRUYỀN BẰNG {method.upper()} — PC nhận dữ liệu từ STM32")
    print(f"Cổng: {serial_port} | Tốc độ baud: {baud_rate} | Dữ liệu: {total_bytes} byte")
    print("Giao thức: payload → CRC 4 byte → DWT2 20 byte → IDL2 24 byte (idle và thời gian STM32)")
    if method == "DMA":
        print("Firmware cần chọn #define TEST TXDMA, build/nạp lại và đặt baud khớp script.")
    print("Chạy chương trình này trước, sau đó reset/khởi động STM32 để truyền dữ liệu.")
    if show_progress:
        print(f"Tiến trình nhận cập nhật mỗi {progress_interval:g} giây, bắt đầu khi có dữ liệu.")
        print("In tiến trình có thể ảnh hưởng thời gian đo tại PC; đặt SHOW_PROGRESS = False khi đo hiệu năng.")
    else:
        print("Đã tắt tiến trình nhận để hạn chế ảnh hưởng đến phép đo tại PC.")
    print("=" * 60)

    try:
        # Context manager đóng cổng kể cả khi timeout, ngoại lệ hoặc Ctrl+C.
        with serial.Serial(
            # Cấu hình thực tế luôn là 8N1: 8 bit dữ liệu, không parity, 1 stop bit.
            # bits_per_byte phải phù hợp cấu hình này để chỉ số lý thuyết đúng.
            port=serial_port,
            baudrate=baud_rate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=first_byte_timeout,
        ) as ser:
            # Bỏ dữ liệu tồn từ lượt trước; STM32 cần bắt đầu truyền sau bước này.
            ser.reset_input_buffer()
            print(f"\nĐang chờ dữ liệu trên {serial_port}; hãy khởi động/reset STM32...")

            data = receive_data(
                # Bước 1: nhận payload + CRC và chốt thời lượng ở PC.
                ser, result, baud_rate=baud_rate, total_bytes=total_bytes,
                read_chunk_size=read_chunk_size, first_byte_timeout=first_byte_timeout,
                read_timeout=read_timeout, show_progress=show_progress,
                progress_interval=progress_interval, bits_per_byte=bits_per_byte,
            )
            if result.total_seconds is not None:
                # Bước 2: đọc DWT rồi idle đúng thứ tự firmware gửi.
                # Điều kiện này xác nhận đã nhận đủ payload + CRC, chưa xác nhận CRC khớp.
                # Thời gian dữ liệu + CRC đã được chốt; đọc DWT không kéo dài phép đo.
                receive_dwt(ser, result, test_mode_code)
                # Sửa idle v2: thống kê idle độc lập với giá trị chu kỳ DWT.
                receive_idle(ser, result)

        # Cổng đã đóng, phép đo đã kết thúc trước khi in, kiểm tra hay ghi CSV.
        if result.total_seconds is not None:
            print(
                f"\nPC đã nhận xong payload + CRC trong {result.total_seconds:.6f} giây "
                f"({result.total_seconds * 1000:.3f} ms)."
            )
        if result.received_bytes != total_bytes:
            return False

        # Kiểm tra payload thực nhận; không phụ thuộc mẫu dữ liệu hoặc seed.
        if result.total_seconds is None or result.crc_bytes != 4:
            return False
        print("Đang tính CRC từ dữ liệu nhận được trên PC...")
        result.received_crc = calculate_crc32_stm32(data)
        # Bước 3: tính CRC từ chính payload nhận được để so với CRC firmware.
        # Đạt khi CRC khớp, không lệch mode và số byte STM32 báo không mâu thuẫn.
        # Thiếu báo cáo DWT/idle không tự làm lượt kiểm tra dữ liệu thất bại.
        result.passed = (
            crc_status(result) == "OK"
            and result.dwt_status != "MODE_MISMATCH"
            and result.stm32_payload_bytes in (None, total_bytes)
        )
        # None chấp nhận firmware thiếu thống kê payload; có số thì phải đúng total_bytes.
        # Các trạng thái DWT MISSING/INVALID/WRAP_RISK không nằm trong điều kiện loại;
        # vì vậy UART có thể đạt dù chưa đủ số liệu để đánh giá hiệu năng CPU.
        if result.stm32_payload_bytes not in (None, total_bytes):
            result.detail = "Số byte payload STM32 báo không khớp kích thước yêu cầu."
        # Nếu đồng thời có nhiều lỗi, thông báo lệch mode được ưu tiên ở đây.
        if result.dwt_status == "MODE_MISMATCH":
            result.detail = result.dwt_detail
        if not result.detail:
            result.detail = (
                "Đã nhận đủ dữ liệu; CRC của PC và STM32 khớp."
                if result.passed
                else "CRC của dữ liệu nhận được không khớp CRC STM32 gửi."
            )
        return result.passed

    # Chuyển lỗi cổng/cấu hình và thao tác hủy thành kết quả thất bại có mô tả.
    except serial.SerialException as error:
        result.detail = (
            f"Lỗi cổng nối tiếp: {error}. "
            f"Kiểm tra cổng {serial_port} và chương trình khác đang sử dụng cổng."
        )
        result.passed = False
        return False
    except ValueError as error:
        result.detail = f"Cấu hình cổng nối tiếp không hợp lệ: {error}"
        result.passed = False
        return False
    except KeyboardInterrupt:
        result.detail = "Đã hủy kiểm tra."
        result.passed = False
        return False
    finally:
        # Bước 4: in và lưu cả lượt đạt lẫn thất bại sau khi đã vào try phía trên.
        # Giá trị bool trả về phản ánh bài kiểm tra UART; lỗi lưu báo cáo có thông báo riêng.
        # finally vẫn chạy khi return sớm; chỉ xuất Excel sau khi lưu CSV thành công.
        print_summary(
            result, method=method, serial_port=serial_port, baud_rate=baud_rate,
            total_bytes=total_bytes, bits_per_byte=bits_per_byte, dwt_scope=dwt_scope,
        )
        if save_csv(result, started_at, csv_path=csv_path, method=method,
                    baud_rate=baud_rate, bits_per_byte=bits_per_byte):
            save_excel(csv_path)
