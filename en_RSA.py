"""
encrypt_RSA.py  —  Ma hoa file don le (RSA Hybrid)
═══════════════════════════════════════════════════════
Logic:
  1. Chon file RSA Public Key (.pem)
  2. Chon file can ma hoa (Vi du: aes_key.pem)
  3. Ma hoa file do thanh dinh dang .enc 
  4. Hoi xoa file goc
"""

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import os, sys

W = 61

# ── FILE BROWSER ─────────────────────────────

def _fmt(size):
    if size<1024: return f"{size} B"
    elif size<1<<20: return f"{size/1024:.1f} KB"
    else: return f"{size/1<<20:.1f} MB"

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
        for d in dirs:
            full=os.path.join(cur,d)
            n=len(os.listdir(full)) if os.access(full,os.R_OK) else 0
            items.append((f"[DIR]  {d}/",full,True))
        for fn in files:
            full=os.path.join(cur,fn)
            items.append((f"[FILE] {fn}  ({_fmt(os.path.getsize(full))})",full,False))
        if not items:
            print(f"|  {'(Trong hoac khong co file phu hop)':<{W-2}}|")
        else:
            for i,(lbl,_,_) in enumerate(items,1):
                line=f"  {i:>3}.  {lbl}"
                if len(line)>W: line=line[:W-3]+"..."
                print(f"|{line:<{W}}|")
        print("+"+"─"*W+"+")
        print(f"|  {'Nhap so=chon | q=huy':<{W-2}}|")
        print("+"+"─"*W+"+")
        c=input("\n  >>> ").strip().lower()
        if c=="q": return None
        if c.isdigit():
            idx=int(c)
            if 1<=idx<=len(items):
                _,fp,is_d=items[idx-1]
                if is_d: cur=fp
                else:
                    fn=os.path.basename(fp)
                    if input(f"\n  [?] Chon '{fn}'? (y/n) [y]: ").strip().lower() in ("","y"): return fp
            else: input(f"  [!] So khong hop le. Enter...")
        else: input("  [!] Nhap sai. Enter...")

# ── CORE FUNCTIONS ─────────────────────────────

def load_public_key(path):
    with open(path,"rb") as f: data=f.read()
    try: return serialization.load_pem_public_key(data)
    except Exception as e: raise ValueError(f"Khong doc duoc Public Key: {e}")

def encrypt_file(public_key, in_path, out_path):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import struct
    aes_key = os.urandom(32)
    nonce   = os.urandom(12)
    with open(in_path,"rb") as f: pt=f.read()
    aesgcm = AESGCM(aes_key)
    ct_tag = aesgcm.encrypt(nonce,pt,None)
    enc_key = public_key.encrypt(aes_key,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=None))
    with open(out_path,"wb") as f:
        f.write(struct.pack(">I",len(enc_key))+enc_key+nonce+ct_tag)

# ── MAIN ─────────────────────────────────────

def main():
    os.system("cls" if os.name=="nt" else "clear")
    print("="*W)
    print("       BUOC 2: MA HOA FILE AES KEY BANG RSA")
    print("="*W)

    print("\n[1] Chon file RSA Public Key (.pem)")
    input("  Nhan Enter de mo trinh duyet file...")
    pem_file = browse_file("CHON FILE RSA PUBLIC KEY (*_public.pem)", ext=[".pem"])
    if not pem_file: return
    pub_key = load_public_key(pem_file)

    print("\n[2] Chon file can ma hoa (Thuong la aes_key.pem)")
    input("  Nhan Enter de mo trinh duyet file...")
    in_file = browse_file("CHON FILE CAN MA HOA", start=os.path.dirname(pem_file))
    if not in_file: return

    out_file = in_file + ".enc"
    try:
        encrypt_file(pub_key, in_file, out_file)
        print(f"\n[OK] Ma hoa thanh cong!")
        print(f"     File ma hoa duoc luu tai: {out_file}")
    except Exception as e:
        print(f"\n[X] Ma hoa that bai: {e}")
        return

    if input("\n  [?] Xoa file goc de hoan tat mo phong Ransomware? (y/n) [n]: ").strip().lower() == "y":
        os.remove(in_file)
        print(f"  [OK] Da xoa file goc: {os.path.basename(in_file)}")

if __name__ == "__main__":
    main()
