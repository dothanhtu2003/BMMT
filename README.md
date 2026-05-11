# Ransomware Lab Simulation with Hybrid Encryption

## 1. Project Overview

This project is an educational cybersecurity lab that simulates the main stages of a ransomware attack in a controlled environment. The implementation demonstrates how a simple attacker-victim model can combine network communication, file transfer, AES file encryption, RSA key protection, and data recovery.

The project is intended for coursework and security awareness. It must only be executed in an isolated lab with test files. Do not run these scripts on real systems, personal files, production machines, or any system that you do not own or have explicit permission to test.

## 2. Project Metadata

**Topic:** Ransomware attack workflow simulation and hybrid encryption using AES-256-GCM and RSA.

**Course:** Introduction to Information Security

**Group members:**

| Student ID | Full name | Role |
|---|---|---|
| 52200248 | Lai Quoc Hung | Team leader, scenario design, source code implementation |
| 52200286 | Nguyen Thanh Phat | Lab setup, source code testing |
| 52200240 | Do Thanh Tu | Source code analysis, report writing |

**Repository:** Add your GitHub/GitLab link here.

## 3. Educational Objectives

The lab is designed to help students understand:

- How ransomware uses symmetric encryption to lock files.
- Why hybrid encryption combines AES and RSA.
- How a basic client-server connection can be used to send data between two machines.
- How file transfer can be performed through SSH/SFTP in a lab.
- Why backup, monitoring, firewall rules, and endpoint protection are important against ransomware.

## 4. System Architecture

The project uses two machines in the same isolated network:

| Machine | Role | Main responsibility |
|---|---|---|
| Machine 1 | Attacker | Runs the server, generates RSA keys, sends files, receives information |
| Machine 2 | Victim | Runs the client, stores test data, performs encryption/decryption demo |

General workflow:

1. The attacker starts `server.py` and waits for a connection.
2. The victim runs `client.py`, which sends simulated victim information to the attacker.
3. The attacker generates an RSA key pair using `generate_RSA.py`.
4. The attacker transfers encryption tools to the victim machine using `sent.py`.
5. The victim-side encryption script `en_AES.py` encrypts test files using AES-256-GCM.
6. The AES key is protected using RSA through `en_RSA.py`.
7. For recovery, `de_RSA.py` restores the AES key and `de_AES.py` decrypts the locked files.

## 5. Source Code Structure

| File | Description |
|---|---|
| `server.py` | TCP server running on the attacker machine. It receives text/file data from the victim and stores it under `received_files`. |
| `client.py` | Client script running on the victim machine. It sends predefined victim information to the attacker server. |
| `generate_RSA.py` | Generates an RSA private/public key pair in PEM format. |
| `en_AES.py` | Encrypts files in a selected directory using AES-256-GCM and creates `.locked` files. |
| `de_AES.py` | Decrypts `.locked` files using the recovered AES key. |
| `en_RSA.py` | Encrypts a selected file using hybrid RSA + AES-GCM. In the demo, it is used to protect the AES key file. |
| `de_RSA.py` | Decrypts an RSA-protected `.enc` file using the corresponding RSA private key. |
| `sent.py` | Sends one or more files/directories from the attacker machine to the victim machine using SSH/SFTP via Paramiko. |

## 6. Lab Environment

Recommended environment:

| Component | Recommended value |
|---|---|
| Operating system | Ubuntu 22.04 on both machines |
| Python | Python 3.10 or later |
| Network mode | Host-only, NAT Network, or isolated LAN |
| Attacker IP example | `192.168.127.138` |
| Victim IP example | `192.168.127.139` |
| TCP server port | `12345` |
| SSH/SFTP port | `22` |

Python dependencies:

```bash
pip install cryptography paramiko
```

On the victim machine, SSH must be enabled if `sent.py` is used:

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

Before running the demo, verify connectivity:

```bash
ping 192.168.127.138
ssh username@192.168.127.139
```

## 7. Cryptographic Design

The project uses hybrid encryption:

- **AES-256-GCM** encrypts the main file contents.
- **RSA** protects the AES key.
- **RSA-OAEP with SHA-256** is used as the RSA padding scheme.

AES is used for file encryption because it is fast and suitable for large data. RSA is used only to protect the AES key because RSA is slower and limited in the amount of data it can encrypt directly.

Encryption flow:

```text
Original files
    |
    | AES-256-GCM
    v
.locked files

AES key
    |
    | RSA public key
    v
aes_key.pem.enc
```

Recovery flow:

```text
aes_key.pem.enc
    |
    | RSA private key
    v
aes_key.pem

.locked files
    |
    | AES key
    v
Original files
```

## 8. Demonstration Walkthrough

Only use test files in a disposable directory for this demonstration.

### Step 1: Prepare the Lab

Create a test directory on the victim machine and place sample files inside it.

Example:

```bash
mkdir ~/important
echo "Sample document 1" > ~/important/file1.txt
echo "Sample document 2" > ~/important/file2.txt
```

Make sure both machines are on the same isolated network and can ping each other.

### Step 2: Start the Attacker Server

On the attacker machine, run:

```bash
python3 server.py
```

The server listens on:

```text
0.0.0.0:12345
```

This means it accepts incoming TCP connections on all network interfaces.

### Step 3: Run the Victim Client

On the victim machine, update the attacker IP in `client.py`:

```python
SERVER_IP = '192.168.127.138'
SERVER_PORT = 12345
```

Then run:

```bash
python3 client.py
```

Expected result:

- The attacker server receives a connection.
- A text file is saved under `received_files`.
- The attacker can see the simulated victim information.

### Step 4: Generate RSA Keys

On the attacker machine, run:

```bash
python3 generate_RSA.py
```

Recommended option:

```text
RSA-2048
```

Expected output:

```text
rsa_key_private.pem
rsa_key_public.pem
```

The public key is used during encryption. The private key is required for recovery.

### Step 5: Transfer Required Files

Use `sent.py` on the attacker machine to transfer required files to the victim machine through SFTP.

Files typically transferred for the encryption phase:

- `en_AES.py`
- `en_RSA.py`
- `rsa_key_public.pem`

Files typically transferred for the recovery phase:

- `de_RSA.py`
- `de_AES.py`
- `rsa_key_private.pem`

Run:

```bash
python3 sent.py
```

Then enter the victim IP, username, password, and destination directory.

### Step 6: Encrypt Test Files with AES

On the victim machine, run:

```bash
python3 en_AES.py
```

Select the test directory, for example:

```text
~/important
```

The script asks for confirmation before encryption. Type:

```text
ENCRYPT
```

Expected result:

- Original test files are replaced by `.locked` files.
- `aes_key.pem` is created.
- `RANSOM_NOTE.txt` is created.

Example result:

```text
file1.txt.locked
file2.txt.locked
aes_key.pem
RANSOM_NOTE.txt
```

### Step 7: Protect the AES Key with RSA

On the victim machine, run:

```bash
python3 en_RSA.py
```

Select:

1. The RSA public key file, for example `rsa_key_public.pem`.
2. The AES key file, for example `aes_key.pem`.

Expected result:

```text
aes_key.pem.enc
```

In the demo, deleting the original AES key demonstrates why the victim cannot recover files without the private key. Only perform this step with test data.

### Step 8: Recover the AES Key

On the victim machine, run:

```bash
python3 de_RSA.py
```

Select:

1. The RSA private key file, for example `rsa_key_private.pem`.
2. The encrypted AES key file, for example `aes_key.pem.enc`.

Expected result:

```text
aes_key.pem
```

### Step 9: Decrypt the Locked Files

On the victim machine, run:

```bash
python3 de_AES.py
```

Select:

1. The recovered `aes_key.pem`.
2. The folder containing `.locked` files.

Type the confirmation:

```text
DECRYPT
```

Expected result:

- `.locked` files are decrypted.
- Original files are restored.
- Optional cleanup removes `RANSOM_NOTE.txt` and the AES key file.

## 9. Important Code Concepts

### TCP Server Binding

`server.py` listens for victim connections:

```python
HOST = '0.0.0.0'
PORT = 12345
server_sock.bind((HOST, PORT))
server_sock.listen(1)
```

`0.0.0.0` allows the server to receive connections from other machines in the lab network.

### AES-GCM Encryption

`en_AES.py` encrypts file data:

```python
aes_key = AESGCM.generate_key(bit_length=256)
nonce = os.urandom(12)
ct_tag = AESGCM(aes_key).encrypt(nonce, plaintext, None)
```

AES-GCM provides confidentiality and integrity. If the ciphertext is modified, decryption fails.

### RSA-OAEP Key Protection

`en_RSA.py` protects the AES key:

```python
enc_key = public_key.encrypt(
    aes_key,
    padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
```

RSA-OAEP with SHA-256 is used instead of older RSA padding methods because it provides stronger protection against cryptographic attacks.

## 10. Defensive Discussion

This project shows why ransomware is dangerous and why defense must be layered.

Recommended defenses:

- Maintain offline or immutable backups.
- Do not execute unknown email attachments or scripts.
- Restrict write permissions on important directories.
- Monitor abnormal file-renaming patterns such as mass creation of `.locked` files.
- Use endpoint detection and response tools.
- Block unnecessary outbound connections.
- Monitor unusual SSH/SFTP activity.
- Keep audit logs for process execution and file modifications.
- Segment networks so one infected machine cannot easily reach others.

## 11. Limitations

Current limitations of the lab:

- The model is simplified and does not include persistence, privilege escalation, or antivirus evasion.
- IP addresses and ports are configured manually.
- The client-server communication is not authenticated.
- The socket communication is not encrypted.
- The encryption is only demonstrated on a selected folder.
- The project is designed for education, not for production security tooling.

## 12. Safety Notice

This repository contains code that can encrypt and delete test files. Use it only in a controlled lab environment. The authors are not responsible for data loss or misuse. Always run the project on disposable test files and virtual machines.

## 13. References

- Python socket documentation: https://docs.python.org/3/library/socket.html
- Python pathlib documentation: https://docs.python.org/3/library/pathlib.html
- Cryptography library documentation: https://cryptography.io/
- AES-GCM documentation in `cryptography`: https://cryptography.io/en/latest/hazmat/primitives/aead/
- RSA documentation in `cryptography`: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/
- Paramiko documentation: https://docs.paramiko.org/
