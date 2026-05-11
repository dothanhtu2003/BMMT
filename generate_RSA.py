"""
generate_RSA.py
Sinh cặp khóa RSA → private_key.pem + public_key.pem
Dùng cho hệ thống Hybrid Encryption (AES + RSA)
"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os
import getpass


def generate_rsa_keypair(key_size: int = 2048):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )
    return private_key, private_key.public_key()


def save_private_key(private_key, filepath: str, password: bytes = None):
    encryption = (
        serialization.BestAvailableEncryption(password)
        if password else serialization.NoEncryption()
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )
    with open(filepath, "wb") as f:
        f.write(pem)


def save_public_key(public_key, filepath: str):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(filepath, "wb") as f:
        f.write(pem)


def main():
    print("=" * 50)
    print("       SINH CAP KHOA RSA (KEY PAIR)")
    print("=" * 50)

    # Chọn kích thước key
    print("\nChon kich thuoc key:")
    print("  1. 2048 bits  (mac dinh, khuyen nghi)")
    print("  2. 3072 bits")
    print("  3. 4096 bits")
    choice = input("\nNhap lua chon (1/2/3) [mac dinh: 1]: ").strip() or "1"
    key_size = {"1": 2048, "2": 3072, "3": 4096}.get(choice, 2048)

    # Tên file output
    name = input("\nNhap ten bo key (khong can duoi .pem) [mac dinh: rsa_key]: ").strip() or "rsa_key"
    private_path = f"{name}_private.pem"
    public_path  = f"{name}_public.pem"

    # Password bảo vệ private key
    use_pwd = input("\nBao ve private key bang password? (y/n) [mac dinh: n]: ").strip().lower()
    password = None
    if use_pwd == "y":
        pwd1 = getpass.getpass("  Nhap password: ")
        pwd2 = getpass.getpass("  Xac nhan password: ")
        if pwd1 != pwd2:
            print("[X] Password khong khop. Thoat.")
            return
        if len(pwd1) < 6:
            print("[X] Password qua ngan (toi thieu 6 ky tu).")
            return
        password = pwd1.encode("utf-8")

    # Sinh key
    print(f"\n[...] Dang sinh RSA-{key_size} key pair...")
    private_key, public_key = generate_rsa_keypair(key_size)

    # Lưu
    save_private_key(private_key, private_path, password)
    save_public_key(public_key, public_path)

    # Hiển thị kết quả
    print()
    print("+" + "-" * 48 + "+")
    print(f"|  {'KET QUA:':<47}|")
    print("+" + "-" * 48 + "+")
    print(f"|  Private Key : {private_path:<32}|")
    print(f"|  Public  Key : {public_path:<32}|")
    print(f"|  Key Size    : RSA-{key_size:<27}|")
    if password:
        print(f"|  Bao ve      : {'Co password (giu kin!)':<32}|")
    else:
        print(f"|  Bao ve      : {'Khong co password':<32}|")
    print("+" + "-" * 48 + "+")
    print()
    print("  [!] PUBLIC KEY  -> Dung cho ma hoa (encrypt_AES.py)")
    print("  [!] PRIVATE KEY -> Dung cho giai ma (decrypt_AES.py)")
    if password:
        print("  [!] Mat password = KHONG the giai ma duoc!")
    print()
    print("[OK] Hoan tat!")
    print("=" * 50)


if __name__ == "__main__":
    main()
