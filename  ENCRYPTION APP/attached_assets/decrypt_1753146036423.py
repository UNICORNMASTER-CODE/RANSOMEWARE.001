import os
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

def list_all_files(root_directory):
    """Lists all files in directory and subdirectories safely"""
    all_files = []
    excluded_files = {"voldemort.py", "encrypt.py", "decrypt.py", "thekey.key"}
    
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename not in excluded_files:
                full_path = os.path.join(dirpath, filename)
                all_files.append(full_path)
    return all_files

user_phrase = input("Enter the password to decrypt your files: ")

try:
    secretkey = generate_key_from_password(user_phrase)
    
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
    print(f"Found {len(files)} files to decrypt")
    
    decrypted_count = 0
    for file_path in files:
        try:
            with open(file_path, "rb") as thefile:
                contents = thefile.read()
            contents_decrypted = Fernet(secretkey).decrypt(contents)
            with open(file_path, "wb") as thefile:
                thefile.write(contents_decrypted)
            decrypted_count += 1
            print(f"Decrypted: {file_path}")
        except Exception as e:
            print(f"Wrong password or couldn't decrypt {file_path}: {e}")
    
    print(f"Decryption complete! {decrypted_count} files decrypted.")
    
except Exception as e:
    print(f"Error (possibly wrong password): {e}")
