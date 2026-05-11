"""
decrypt_RSA.py  —  Giai ma file don le bang RSA Private Key
═══════════════════════════════════════════════════════
Logic:
  1. Chon RSA Private Key (.pem) 
  2. Chon file .enc can giai ma (Vi du: aes_key.pem.enc)
  3. Khoi phuc lai file goc
"""

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import os, sys, getpass

W = 61

# ── FILE BROWSER ─────────────────────────────
# (Giống y hệt encrypt_RSA.py, giữ nguyên hàm browse_file)
def _fmt(size): return f"{size} B" if size<1024 else f"{size/1024:.1f} KB" if size<1<<20 else f"{size/1<<20:.1f} MB"
def _ls(path, ext=None):
    try: ent = os.listdir(path)
    except PermissionError: return [],[]
    dirs  = sorted([e for e in ent if os.path.isdir(os.path.join(path,e))  and not e.startswith('.')],key=str.lower)
    files = sorted([e for e in ent if os.path.isfile(os.path.join(path,e)) and not e.startswith('.')],key=str.lower)
    if ext: files=[f for f in files if os.path.splitext(f)[1].lower() in ext]
    return dirs,files

def browse_file(title, start=None, ext=None):
    cur = os.path.abspath(start or os.getcwd())
    while True:
        os.system("cls" if os.name=="nt" else "clear")
        print("+"+"─"*W+"+")
        print(f"|  {title:<{W-2}}|")
        print("+"+"─"*W+"+")
        disp = cur if len(cur)<=W-12 else "..."+cur[-(W-15):]
        print(f"|  Thu muc : {disp:<{W-12}}|")
        print(f"|  Loc     : {(' '.join(ext) if ext else 'Tat ca file'):<{W-12}}|")
        print("+"+"─"*W+"+")
        dirs,files=_ls(cur,ext)
        items=[]
        p=os.path.dirname(cur)
        if p!=cur: items.append(("[DIR]  .. (len thu muc cha)",p,True))
        for d in dirs: items.append((f"[DIR]  {d}/",os.path.join(cur,d),True))
        for fn in files: items.append((f"[FILE] {fn}",os.path.join(cur,fn),False))
        if not items: print(f"|  {'(Trong hoac khong co file phu hop)':<{W-2}}|")
        else:
            for i,(lbl,_,_) in enumerate(items,1):
                line=f"  {i:>3}.  {lbl}"
                if len(line)>W: line=line[:W-3]+"..."
                print(f"|{line:<{W}}|")
        print("+"+"─"*W+"+")
        c=input("\n  >>> Nhap so de chon (q=huy): ").strip().lower()
        if c=="q": return None
        if c.isdigit() and 1<=int(c)<=len(items):
            _,fp,is_d=items[int(c)-1]
            if is_d: cur=fp
            else: return fp

# ── CORE FUNCTIONS ─────────────────────────────

def load_private_key(path, password=None):
    with open(path,"rb") as f: data=f.read()
    try: return serialization.load_pem_private_key(data, password=password)
    except TypeError:
        pwd = getpass.getpass("  [!] Private key co password — Nhap: ")
        return serialization.load_pem_private_key(data, password=pwd.encode("utf-8"))

def decrypt_file(private_key, in_path, out_path):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import struct
    with open(in_path,"rb") as f: data=f.read()
    enc_key_len = struct.unpack(">I", data[:4])[0]
    enc_key = data[4:4+enc_key_len]
    nonce   = data[4+enc_key_len:4+enc_key_len+12]
    ct_tag  = data[4+enc_key_len+12:]
    aes_key = private_key.decrypt(enc_key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    pt = AESGCM(aes_key).decrypt(nonce, ct_tag, None)
    with open(out_path,"wb") as f: f.write(pt)

# ── MAIN ─────────────────────────────────────

def main():
    os.system("cls" if os.name=="nt" else "clear")
    print("="*W)
    print("       BUOC 3: GIAI MA FILE (.enc) BANG RSA")
    print("="*W)

    print("\n[1] Chon duong dan file RSA Private Key (.pem)")
    input("  Nhan Enter de mo trinh duyet file...")
    pem_file = browse_file("CHON FILE RSA PRIVATE KEY (*_private.pem)", ext=[".pem"])
    if not pem_file: return
    priv_key = load_private_key(pem_file)

    print("\n[2] Chon file can giai ma (.enc)")
    input("  Nhan Enter de mo trinh duyet file...")
    in_file = browse_file("CHON FILE CAN GIAI MA (.enc)", start=os.path.dirname(pem_file), ext=[".enc"])
    if not in_file: return

    out_file = in_file[:-4] if in_file.endswith(".enc") else in_file+"_decrypted"
    try:
        decrypt_file(priv_key, in_file, out_file)
        print(f"\n[OK] Giai ma thanh cong!")
        print(f"     Da khoi phuc file goc tai: {out_file}")
    except Exception as e:
        print(f"\n[X] Giai ma that bai (Sai key hoac file hong): {e}")
        return

    if input("\n  [?] Xoa file .enc da giai ma? (y/n) [y]: ").strip().lower() in ("y", ""):
        os.remove(in_file)
        print(f"  [OK] Da xoa: {os.path.basename(in_file)}")

if __name__ == "__main__":
    main()
