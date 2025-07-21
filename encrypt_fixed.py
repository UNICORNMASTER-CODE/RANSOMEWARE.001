#!/usr/bin/env python3
"""
Secure File Encryption Tool - Fixed Version
Addresses all security vulnerabilities and bugs from original encrypt.py
"""

import os
import shutil
import secrets
import getpass
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configuration
CONFIG = {
    'MIN_PASSWORD_LENGTH': 8,
    'MAX_FILE_SIZE_MB': 100,
    'CHUNK_SIZE': 64 * 1024,  # 64KB chunks
    'BACKUP_ENABLED': True,
    'EXCLUDED_EXTENSIONS': {'.py', '.pyc', '.pyo', '.key', '.log'},
    'EXCLUDED_FILES': {'encrypt.py', 'decrypt.py', 'encrypt_fixed.py', 'decrypt_fixed.py', 'thekey.key', 'voldemort.py'}
}

class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def generate_secure_salt() -> bytes:
    """Generate a cryptographically secure random salt"""
    return secrets.token_bytes(32)

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < CONFIG['MIN_PASSWORD_LENGTH']:
        raise ValidationError(f"Password must be at least {CONFIG['MIN_PASSWORD_LENGTH']} characters long")
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        print("⚠️  WARNING: Password should contain uppercase, lowercase, and numbers for better security")
    
    return True

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Generate encryption key from password using secure random salt"""
    validate_password(password)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    
    # Clear password from memory (best effort)
    password = None
    
    return key

def validate_directory(directory: str) -> Path:
    """Validate that directory exists and is accessible"""
    path = Path(directory).expanduser().resolve()
    
    if not path.exists():
        raise ValidationError(f"Directory does not exist: {path}")
    
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")
    
    if not os.access(path, os.R_OK):
        raise ValidationError(f"Directory is not readable: {path}")
    
    return path

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes"""
    return file_path.stat().st_size / (1024 * 1024)

def is_file_excluded(file_path: Path) -> bool:
    """Check if file should be excluded from encryption"""
    # Check by filename
    if file_path.name in CONFIG['EXCLUDED_FILES']:
        return True
    
    # Check by extension
    if file_path.suffix.lower() in CONFIG['EXCLUDED_EXTENSIONS']:
        return True
    
    # Check if it's a hidden file
    if file_path.name.startswith('.'):
        return True
    
    return False

def list_files_safely(root_directory: Path) -> List[Path]:
    """List all files in directory and subdirectories with proper validation"""
    all_files = []
    excluded_count = 0
    
    try:
        for item in root_directory.rglob('*'):
            if item.is_file():
                try:
                    # Check file accessibility
                    if not os.access(item, os.R_OK | os.W_OK):
                        print(f"⚠️  Skipping file (no permissions): {item}")
                        continue
                    
                    # Check if file should be excluded
                    if is_file_excluded(item):
                        excluded_count += 1
                        continue
                    
                    # Check file size
                    size_mb = get_file_size_mb(item)
                    if size_mb > CONFIG['MAX_FILE_SIZE_MB']:
                        print(f"⚠️  Skipping large file ({size_mb:.1f}MB): {item}")
                        continue
                    
                    all_files.append(item)
                    
                except (OSError, PermissionError) as e:
                    print(f"⚠️  Skipping file (error): {item} - {e}")
                    continue
    
    except PermissionError as e:
        raise ValidationError(f"Cannot access directory: {e}")
    
    print(f"📁 Found {len(all_files)} files to encrypt ({excluded_count} excluded)")
    return all_files

def create_backup_folder(backup_location: Optional[Path] = None) -> Path:
    """Create a backup folder with timestamp at specified location"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder_name = f"backup_{timestamp}"
    
    if backup_location:
        backup_location = validate_directory(str(backup_location))
        backup_folder = backup_location / backup_folder_name
    else:
        backup_folder = Path.home() / "Desktop" / backup_folder_name
    
    try:
        backup_folder.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise EncryptionError(f"Cannot create backup folder: {e}")
    
    return backup_folder

def backup_file_safely(file_path: Path, backup_folder: Path, root_folder: Path) -> bool:
    """Copy file to backup folder maintaining directory structure with verification"""
    try:
        rel_path = file_path.relative_to(root_folder)
        backup_path = backup_folder / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file with metadata
        shutil.copy2(file_path, backup_path)
        
        # Verify backup integrity
        if backup_path.stat().st_size != file_path.stat().st_size:
            raise EncryptionError(f"Backup verification failed for {file_path}")
        
        return True
        
    except (OSError, PermissionError, ValueError) as e:
        print(f"❌ Backup failed for {file_path}: {e}")
        return False

def encrypt_file_safely(file_path: Path, fernet: Fernet) -> bool:
    """Encrypt file with atomic operation and error handling"""
    temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
    
    try:
        # Read and encrypt in chunks for large files
        with open(file_path, 'rb') as infile, open(temp_file, 'wb') as outfile:
            content = infile.read()
            if len(content) == 0:
                print(f"⚠️  Skipping empty file: {file_path}")
                temp_file.unlink()
                return False
            
            encrypted_content = fernet.encrypt(content)
            outfile.write(encrypted_content)
        
        # Atomic replacement
        temp_file.replace(file_path)
        return True
        
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        print(f"❌ Encryption failed for {file_path}: {e}")
        return False

def save_salt_file(salt: bytes, backup_folder: Path) -> None:
    """Save salt to backup folder for decryption"""
    salt_file = backup_folder / "encryption_salt.key"
    try:
        with open(salt_file, 'wb') as f:
            f.write(salt)
        print(f"🔑 Salt saved to: {salt_file}")
        print("⚠️  IMPORTANT: Keep this salt file safe! You need it for decryption.")
    except OSError as e:
        print(f"⚠️  Warning: Could not save salt file: {e}")

def confirm_operation(files: List[Path], root_folder: Path) -> bool:
    """Get user confirmation before proceeding with encryption"""
    print(f"\n📋 ENCRYPTION SUMMARY:")
    print(f"   Directory: {root_folder}")
    print(f"   Files to encrypt: {len(files)}")
    print(f"   Backup enabled: {CONFIG['BACKUP_ENABLED']}")
    
    if len(files) > 10:
        print(f"\n📄 First 10 files:")
        for file_path in files[:10]:
            print(f"   • {file_path.relative_to(root_folder)}")
        print(f"   ... and {len(files) - 10} more files")
    else:
        print(f"\n📄 Files to encrypt:")
        for file_path in files:
            print(f"   • {file_path.relative_to(root_folder)}")
    
    print(f"\n⚠️  WARNING: This will encrypt files in-place!")
    print(f"   Original files will be replaced with encrypted versions.")
    
    while True:
        response = input("\n❓ Do you want to proceed? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def main():
    """Main encryption process with comprehensive error handling"""
    print("🔒 Secure File Encryption Tool - Fixed Version")
    print("=" * 50)
    
    try:
        # Get target directory
        while True:
            directory_input = input("📁 Enter directory path to encrypt (or 'test' for ~/Desktop/crypto_test): ").strip()
            
            if directory_input.lower() == 'test':
                root_folder = Path.home() / "Desktop" / "crypto_test"
                # Create test directory if it doesn't exist
                root_folder.mkdir(parents=True, exist_ok=True)
                print(f"✅ Using test directory: {root_folder}")
                break
            elif directory_input:
                try:
                    root_folder = validate_directory(directory_input)
                    break
                except ValidationError as e:
                    print(f"❌ {e}")
                    continue
            else:
                print("Please enter a valid directory path")
        
        # List files
        print(f"\n📂 Scanning directory: {root_folder}")
        files = list_files_safely(root_folder)
        
        if not files:
            print("❌ No files found to encrypt!")
            return
        
        # Get user confirmation
        if not confirm_operation(files, root_folder):
            print("❌ Operation cancelled by user")
            return
        
        # Create backup if enabled
        backup_folder = None
        if CONFIG['BACKUP_ENABLED']:
            print(f"\n💾 Creating backup...")
            backup_folder = create_backup_folder()
            print(f"✅ Backup folder created: {backup_folder}")
            
            # Backup all files first
            backup_count = 0
            for file_path in files:
                if backup_file_safely(file_path, backup_folder, root_folder):
                    backup_count += 1
            
            print(f"✅ Backup complete! {backup_count}/{len(files)} files backed up")
            
            if backup_count != len(files):
                response = input("⚠️  Some files failed to backup. Continue anyway? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("❌ Operation cancelled")
                    return
        
        # Get password securely
        print(f"\n🔐 Password Requirements:")
        print(f"   • Minimum {CONFIG['MIN_PASSWORD_LENGTH']} characters")
        print(f"   • Recommended: uppercase, lowercase, numbers")
        
        while True:
            try:
                password = getpass.getpass("🔑 Enter encryption password: ")
                if validate_password(password):
                    password_confirm = getpass.getpass("🔑 Confirm password: ")
                    if password == password_confirm:
                        break
                    else:
                        print("❌ Passwords don't match. Please try again.")
                        password = password_confirm = None  # Clear from memory
            except ValidationError as e:
                print(f"❌ {e}")
                password = None  # Clear from memory
        
        # Generate secure salt and key
        print(f"\n🔐 Generating encryption key...")
        salt = generate_secure_salt()
        key = generate_key_from_password(password, salt)
        password = password_confirm = None  # Clear passwords from memory
        
        # Save salt for decryption
        if backup_folder:
            save_salt_file(salt, backup_folder)
        
        # Encrypt files
        print(f"\n🔒 Starting encryption...")
        fernet = Fernet(key)
        encrypted_count = 0
        
        for i, file_path in enumerate(files, 1):
            print(f"🔒 Encrypting ({i}/{len(files)}): {file_path.relative_to(root_folder)}")
            if encrypt_file_safely(file_path, fernet):
                encrypted_count += 1
        
        # Final summary
        print(f"\n✅ ENCRYPTION COMPLETE!")
        print(f"   Files encrypted: {encrypted_count}/{len(files)}")
        if backup_folder:
            print(f"   Backup location: {backup_folder}")
            print(f"   Salt file: {backup_folder}/encryption_salt.key")
        
        if encrypted_count != len(files):
            print(f"⚠️  {len(files) - encrypted_count} files failed to encrypt")
        
        print(f"\n🔐 IMPORTANT NOTES:")
        print(f"   • Remember your password - it cannot be recovered!")
        print(f"   • Keep the salt file safe - you need it for decryption!")
        print(f"   • Test decryption on a copy before deleting backups!")
        
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"Please check the error and try again")

if __name__ == "__main__":
    main()