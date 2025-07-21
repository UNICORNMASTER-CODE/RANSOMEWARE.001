import os
import shutil
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

def generate_key_from_password(password):
    """Generate encryption key from password"""
    salt = b'salt_1234567890'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def create_backup_folder(custom_location=None):
    """Create a backup folder with timestamp at specified location"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder_name = f"backup_{timestamp}"
    
    if custom_location:
        backup_folder = os.path.join(custom_location, backup_folder_name)
    else:
        backup_folder = backup_folder_name
    
    os.makedirs(backup_folder, exist_ok=True)
    return backup_folder

def backup_file(file_path, backup_folder, root_folder):
    """Copy file to backup folder maintaining directory structure"""
    try:
        rel_path = os.path.relpath(file_path, root_folder)
        backup_path = os.path.join(backup_folder, rel_path)
        backup_dir = os.path.dirname(backup_path)
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return True
    except Exception as e:
        print(f"Backup failed for {file_path}: {e}")
        return False

def list_all_files(root_directory):
    """Lists all files in directory and subdirectories safely"""
    all_files = []
    excluded_files = {"encrypt.py", "decrypt.py", "thekey.key"}
    
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename not in excluded_files:
                full_path = os.path.join(dirpath, filename)
                all_files.append(full_path)
    return all_files

# Main encryption process
try:
    # Safe options:
    root_folder = os.path.expanduser('~/Desktop/crypto_test')  # Test folder
    # root_folder = os.path.expanduser('~/Documents')  # Documents folder only
    # root_folder = os.path.expanduser('~/Desktop')    # Desktop folder only
    # root_folder = os.path.expanduser('~/Downloads')  # Downloads folder only
    # root_folder = os.path.expanduser('~')            # Your home directory only
    
    # System-wide options:
    # root_folder = '/'  # Entire Mac filesystem
    # root_folder = 'C:\\'  # Entire Windows filesystem
    # root_folder = '/System'        # Mac system files
    # root_folder = '/usr'           # Unix system files
    # root_folder = '/Applications'  # All Mac apps
    # root_folder = '/Library'       # Mac system libraries
    # root_folder = 'C:\\Windows'    # Windows system files
    # root_folder = 'C:\\Program Files'  # Windows programs
    # root_folder = 'C:\\Program Files (x86)'  # 32-bit Windows programs
    
    files = list_all_files(root_folder)
    print(f"Found {len(files)} files to encrypt")
    
    # Choose backup location:
    backup_location = os.path.expanduser('~/Desktop')
    # backup_location = os.path.expanduser('~/Documents')
    # backup_location = '/Volumes/MyUSBDrive'
    # backup_location = '/Users/yourusername/SafeBackups'
    # backup_location = input("Enter backup location: ")
    
    backup_folder = create_backup_folder(backup_location)
    print(f"Created backup folder: {backup_folder}")
    
    print("Backing up files...")
    backup_count = 0
    for file_path in files:
        if backup_file(file_path, backup_folder, root_folder):
            backup_count += 1
            print(f"Backed up: {file_path}")
    
    print(f"Backup complete! {backup_count} files backed up.")
    
    password = input("Enter password for encryption: ")
    key = generate_key_from_password(password)
    
    print("Starting encryption...")
    encrypted_count = 0
    for file_path in files:
        try:
            with open(file_path, "rb") as thefile:
                contents = thefile.read()
            contents_encrypted = Fernet(key).encrypt(contents)
            with open(file_path, "wb") as thefile:
                thefile.write(contents_encrypted)
            encrypted_count += 1
            print(f"Encrypted: {file_path}")
        except Exception as e:
            print(f"Couldn't encrypt {file_path}: {e}")
    
    print(f"Encryption complete! {encrypted_count} files encrypted.")
    print(f"Original files are safely backed up in: {backup_folder}")
    
except Exception as e:
    print(f"Error: {e}")
