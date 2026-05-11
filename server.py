"""
server.py  —  Chạy trên Máy 1
Lắng nghe kết nối từ Máy 2, nhận thông tin dạng text và lưu thành file .txt
"""

import socket
import os
import datetime

# ── CẤU HÌNH ──────────────────────────────────────────
HOST = '0.0.0.0'   # Lắng nghe trên tất cả interface
PORT = 12345
SAVE_DIR = './received_files'
# ──────────────────────────────────────────────────────

os.makedirs(SAVE_DIR, exist_ok=True)

def get_local_ips():
    """Lấy danh sách IP local để hiển thị."""
    import subprocess
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return "Khong xac dinh duoc IP"

print("=" * 55)
print("         SERVER - MAY 1 (RECEIVING END)")
print("=" * 55)
print(f"\n[*] IP may nay : {get_local_ips()}")
print(f"[*] Lang nghe  : {HOST}:{PORT}")
print(f"[*] Luu file   : {os.path.abspath(SAVE_DIR)}")
print(f"\n[...] Dang cho ket noi tu May 2...")
print("-" * 55)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)

    while True:
        conn, addr = server_sock.accept()
        with conn:
            print(f"\n[+] Ket noi tu: {addr[0]}:{addr[1]}")

            # ── Nhận header (tên file + kích thước) ──
            header_raw = b""
            while b"\n---END_HEADER---\n" not in header_raw:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                header_raw += chunk

            if b"\n---END_HEADER---\n" not in header_raw:
                print("[-] Khong nhan duoc header hop le. Bo qua.")
                conn.sendall(b"ERR_HEADER")
                continue

            header_part, data_start = header_raw.split(b"\n---END_HEADER---\n", 1)
            header = {}
            for line in header_part.decode('utf-8', errors='ignore').splitlines():
                if '=' in line:
                    k, v = line.split('=', 1)
                    header[k.strip()] = v.strip()

            filename    = header.get('filename', 'unknown.txt')
            sender_name = header.get('sender', 'Unknown')
            file_size   = int(header.get('size', 0))

            print(f"[*] Nguoi gui  : {sender_name}")
            print(f"[*] Ten file   : {filename}")
            print(f"[*] Kich thuoc : {file_size} bytes")

            # Gửi ACK cho phép nhận data
            conn.sendall(b"ACK")

            # ── Nhận toàn bộ nội dung file ──
            data = data_start
            while len(data) < file_size:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk

            if len(data) < file_size:
                print(f"[-] Nhan thieu du lieu ({len(data)}/{file_size} bytes). Bo qua.")
                conn.sendall(b"ERR_INCOMPLETE")
                continue

            # Lưu file với timestamp để tránh ghi đè
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base, ext = os.path.splitext(filename)
            save_name = f"{base}_{timestamp}{ext}"
            save_path = os.path.join(SAVE_DIR, save_name)

            with open(save_path, 'wb') as f:
                f.write(data)

            conn.sendall(b"OK")

            print(f"\n[+] Da luu file tai: {save_path}")
            print("\n--- NOI DUNG FILE ---")
            print("-" * 40)
            try:
                print(data.decode('utf-8'))
            except UnicodeDecodeError:
                print("[Du lieu nhi phan - khong hien thi duoc]")
            print("-" * 40)
            print(f"\n[...] Tiep tuc cho ket noi moi...")
            print("-" * 55)
