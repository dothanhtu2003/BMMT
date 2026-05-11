"""
send_to_m2_sftp.py  —  Gửi NHIỀU file/thư mục từ Máy 1 sang Máy 2 (SFTP)
══════════════════════════════════════════════════════════════════════
Logic:
  1. Nhập thông tin kết nối (IP, Username, Password) của Máy 2.
  2. Chọn NHIỀU file hoặc thư mục cùng lúc (Hỗ trợ upload cả thư mục lớn).
  3. Kết nối SFTP, tự động tạo cấu trúc và đẩy dữ liệu sang Máy 2.
"""

import os
import sys
import paramiko # pip install paramiko
from pathlib import Path

W = 70

# ── CẤU HÌNH MÁY 2 (Có thể nhập sẵn ở đây hoặc nhập khi chạy) ──
M2_IP       = "192.168.x.x"  # Thay bằng IP Máy 2
M2_USER     = "hostname"     # Thay bằng Username của Máy 2
M2_PASS     = "password"     # Thay bằng Mật khẩu của Máy 2
M2_REMOTE_DIR = "/tmp"       # Thư mục đích trên Máy 2 (Vd: /tmp hoặc C:/Users/Admin/Desktop)

# ── TRÌNH DUYỆT ĐA CHỌN (MULTI-SELECT BROWSER) ────────────────

def _fmt(size):
    if size < 1024: return f"{size} B"
    elif size < 1<<20: return f"{size/1024:.1f} KB"
    else: return f"{size/1<<20:.1f} MB"

def _ls(path):
    try:
        ent = os.listdir(path)
    except PermissionError:
        return [], []
    dirs  = sorted([e for e in ent if os.path.isdir(os.path.join(path,e)) and not e.startswith('.')], key=str.lower)
    files = sorted([e for e in ent if os.path.isfile(os.path.join(path,e)) and not e.startswith('.')], key=str.lower)
    return dirs, files

def browse_multiple(title, start=None):
    cur = os.path.abspath(start or os.getcwd())
    selected_items = set() # Lưu các đường dẫn tuyệt đối đã chọn
    
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("+" + "─"*(W-2) + "+")
        print(f"|  {title:<{W-4}}|")
        print("+" + "─"*(W-2) + "+")
        disp = cur if len(cur) <= W-18 else "..." + cur[-(W-21):]
        print(f"|  Thư mục : {disp:<{W-15}}|")
        print(f"|  Đã chọn : {len(selected_items):<3} mục (Gõ 'ok' để gửi) {'':<{W-39}}|")
        print("+" + "─"*(W-2) + "+")

        dirs, files = _ls(cur)
        items = []
        p = os.path.dirname(cur)
        
        # Thư mục cha (luôn ở đầu, không cho phép chọn)
        if p != cur:
            items.append(("[DIR]  .. (Lên thư mục cha)", p, True))
            
        for d in dirs:
            items.append((f"[DIR]  {d}/", os.path.join(cur, d), True))
        for fn in files:
            items.append((f"[FILE] {fn} ({_fmt(os.path.getsize(os.path.join(cur, fn)))})", os.path.join(cur, fn), False))

        if not items:
            print(f"|  {'(Thư mục trống)':<{W-4}}|")
        else:
            for i, (lbl, fp, _) in enumerate(items, 1):
                # Hiển thị dấu [x] nếu mục này nằm trong danh sách đã chọn
                mark = "[x]" if fp in selected_items else "[ ]"
                if fp == p: mark = "   " # Không hiển thị ô vuông cho thư mục cha
                
                line = f"  {i:>3}. {mark} {lbl}"
                if len(line) > W-3: line = line[:W-6] + "..."
                print(f"|{line:<{W-3}}|")

        print("+" + "─"*(W-2) + "+")
        print(f"|  [Số] = Đi vào thư mục      |  [s Số] = Chọn/Bỏ chọn mục    |")
        print(f"|  [ok] = XÁC NHẬN GỬI        |  [q] = Hủy bỏ                 |")
        print("+" + "─"*(W-2) + "+")
        
        c = input("\n  >>> Lệnh: ").strip().lower()
        if c == "q": 
            return None
        if c == "ok": 
            if not selected_items:
                input("  [!] Bạn chưa chọn mục nào! Nhấn Enter để tiếp tục...")
                continue
            return list(selected_items)
            
        # Xử lý lệnh chọn/bỏ chọn (vd: s 2, s 1 3 4)
        if c.startswith("s "):
            parts = c.split()[1:]
            for p_num in parts:
                if p_num.isdigit():
                    idx = int(p_num)
                    if 1 <= idx <= len(items):
                        _, fp, _ = items[idx-1]
                        if fp != p: # Không cho phép đánh dấu thư mục cha ".."
                            if fp in selected_items:
                                selected_items.remove(fp)
                            else:
                                selected_items.add(fp)
            continue
            
        # Xử lý lệnh đi vào thư mục (vd: 1, 2)
        if c.isdigit():
            idx = int(c)
            if 1 <= idx <= len(items):
                _, fp, is_d = items[idx-1]
                if is_d: 
                    cur = fp
                else:
                    input("  [!] Đây là file, không thể đi vào. Hãy dùng lệnh 's' để chọn. Enter...")
        else:
            input("  [!] Lệnh không hợp lệ. Nhấn Enter để tiếp tục...")

# ── CORE TRANSFER FUNCTION ─────────────────────────────

def sftp_mkdir_p(sftp, remote_directory):
    """Tạo đệ quy thư mục trên remote nếu chưa tồn tại"""
    if remote_directory == '/' or remote_directory == '':
        return
    try:
        sftp.stat(remote_directory)
    except IOError:
        parent = os.path.dirname(remote_directory)
        sftp_mkdir_p(sftp, parent)
        try:
            sftp.mkdir(remote_directory)
        except Exception:
            pass

def sftp_upload_recursive(sftp, local_path, remote_base_dir):
    """Đẩy đệ quy file/thư mục lên SFTP"""
    item_name = os.path.basename(local_path)
    remote_path = f"{remote_base_dir}/{item_name}".replace('//', '/')

    if os.path.isfile(local_path):
        print(f"    -> Đang đẩy File: {item_name}")
        sftp.put(local_path, remote_path)
    elif os.path.isdir(local_path):
        print(f"    -> Tạo Thư mục  : {item_name}/")
        try:
            sftp.mkdir(remote_path)
        except IOError:
            pass # Thư mục có thể đã tồn tại, không sao
            
        # Lặp qua các file/thư mục con và đệ quy
        for child in os.listdir(local_path):
            child_local_path = os.path.join(local_path, child)
            sftp_upload_recursive(sftp, child_local_path, remote_path)

def sftp_send(ip, user, password, local_paths, target_dir):
    try:
        print(f"\n[...] Đang kết nối tới {ip} qua SSH/SFTP...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password, timeout=10)
        
        sftp = ssh.open_sftp()
        
        # Đảm bảo thư mục đích gốc tồn tại
        print(f"[...] Đang kiểm tra thư mục đích: {target_dir}")
        sftp_mkdir_p(sftp, target_dir.replace('\\', '/'))
        
        print("\n[...] BẮT ĐẦU ĐẨY DỮ LIỆU:")
        for path in local_paths:
            sftp_upload_recursive(sftp, path, target_dir)
            
        print(f"\n[OK] CHUYỂN DỮ LIỆU THÀNH CÔNG!")
        sftp.close()
        ssh.close()
        return True
    except Exception as e:
        print(f"\n[X] Lỗi kết nối hoặc lỗi trong quá trình gửi: {e}")
        return False

# ── MAIN ─────────────────────────────────────

def main():
    try:
        sys.stdin.reconfigure(encoding='utf-8', errors='ignore')
    except:
        pass

    os.system("cls" if os.name == "nt" else "clear")
    print("="*W)
    print("      TRÌNH GỬI NHIỀU FILE / THƯ MỤC QUA MÁY 2 (SFTP)")
    print("="*W)
    
    ip = input(f"  IP Máy 2 [{M2_IP}]: ").strip() or M2_IP
    user = input(f"  Username [{M2_USER}]: ").strip() or M2_USER
    pwd = input(f"  Password: ").strip() or M2_PASS
    target_dir = input(f"  Thư mục đích trên M2 [{M2_REMOTE_DIR}]: ").strip() or M2_REMOTE_DIR

    print("\n[BUỚC 1] Chọn các file / thư mục cần gửi")
    input("  Nhấn Enter để mở trình duyệt...")
    
    selected_items = browse_multiple("CHỌN MỤC CẦN GỬI (Hỗ trợ chọn nhiều)")
    if not selected_items:
        print("\n[--] Đã hủy.")
        return

    os.system("cls" if os.name == "nt" else "clear")
    print("="*W)
    print("        THÔNG TIN XÁC NHẬN GỬI")
    print("="*W)
    print(f"  Máy nhận   : {user}@{ip}")
    print(f"  Thư mục đích: {target_dir}")
    print(f"  Tổng cộng  : {len(selected_items)} mục được chọn:")
    for item in selected_items[:5]:
        print(f"    - {os.path.basename(item)}")
    if len(selected_items) > 5:
        print(f"    ... và {len(selected_items) - 5} mục khác.")
    print("="*W)
    
    confirm = input("\n  Bắt đầu gửi dữ liệu? (y/n) [y]: ").strip().lower()
    if confirm == "n":
        print("[--] Đã hủy.")
        return

    # Gửi qua SFTP
    sftp_send(ip, user, pwd, selected_items, target_dir)
    
    print("\n" + "="*W)
    input("  Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()
