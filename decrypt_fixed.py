#!/usr/bin/env python3
"""
Secure File Decryption Tool - Fixed Version
Addresses all security vulnerabilities and bugs from original decrypt.py
"""

import os
import getpass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Configuration
CONFIG = {
    'MIN_PASSWORD_LENGTH': 8,
    'MAX_FILE_SIZE_MB': 100,
    'CHUNK_SIZE': 64 * 1024,  # 64KB chunks
    'EXCLUDED_EXTENSIONS': {'.py', '.pyc', '.pyo', '.key', '.log'},
    'EXCLUDED_FILES': {'encrypt.py', 'decrypt.py', 'encrypt_fixed.py', 'decrypt_fixed.py', 'thekey.key', 'voldemort.py'}
}

class DecryptionError(Exception):
    """Custom exception for decryption-related errors"""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Generate encryption key from password using provided salt"""
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

def load_salt_file(salt_file_path: str) -> bytes:
    """Load salt from file with validation"""
    salt_path = Path(salt_file_path).expanduser().resolve()
    
    if not salt_path.exists():
        raise ValidationError(f"Salt file does not exist: {salt_path}")
    
    if not salt_path.is_file():
        raise ValidationError(f"Salt path is not a file: {salt_path}")
    
    try:
        with open(salt_path, 'rb') as f:
            salt = f.read()
        
        if len(salt) != 32:
            raise ValidationError(f"Invalid salt file format (expected 32 bytes, got {len(salt)})")
        
        return salt
    
    except OSError as e:
        raise ValidationError(f"Cannot read salt file: {e}")

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes"""
    return file_path.stat().st_size / (1024 * 1024)

def is_file_excluded(file_path: Path) -> bool:
    """Check if file should be excluded from decryption"""
    # Check by filename
    if file_path.name in CONFIG['EXCLUDED_FILES']:
        return True
    
    # Check by extension
    if file_path.suffix.lower() in CONFIG['EXCLUDED_EXTENSIONS']:
        return True
    
    # Check if it's a hidden file
    if file_path.name.startswith('.'):
        return True
    
    # Skip salt files
    if file_path.name == 'encryption_salt.key':
        return True
    
    return False

def is_file_encrypted(file_path: Path) -> bool:
    """Check if file appears to be encrypted (basic heuristic)"""
    try:
        with open(file_path, 'rb') as f:
            # Read first few bytes to check for Fernet token format
            header = f.read(10)
            # Fernet tokens start with version byte and timestamp
            if len(header) >= 9 and header[0:1] in [b'\x80', b'\x81']:
                return True
    except (OSError, PermissionError):
        pass
    return False

def list_encrypted_files(root_directory: Path) -> List[Path]:
    """List all encrypted files in directory and subdirectories with proper validation"""
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
                    
                    # Only include files that appear to be encrypted
                    if is_file_encrypted(item):
                        all_files.append(item)
                    else:
                        print(f"⚠️  Skipping non-encrypted file: {item}")
                    
                except (OSError, PermissionError) as e:
                    print(f"⚠️  Skipping file (error): {item} - {e}")
                    continue
    
    except PermissionError as e:
        raise ValidationError(f"Cannot access directory: {e}")
    
    print(f"📁 Found {len(all_files)} encrypted files to decrypt ({excluded_count} excluded)")
    return all_files

def decrypt_file_safely(file_path: Path, fernet: Fernet) -> bool:
    """Decrypt file with atomic operation and error handling"""
    temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
    
    try:
        # Read and decrypt
        with open(file_path, 'rb') as infile:
            encrypted_content = infile.read()
            if len(encrypted_content) == 0:
                print(f"⚠️  Skipping empty file: {file_path}")
                return False
        
        # Decrypt content
        try:
            decrypted_content = fernet.decrypt(encrypted_content)
        except Exception as e:
            if "InvalidToken" in str(type(e).__name__):
                print(f"❌ Wrong password or corrupted file: {file_path}")
            else:
                print(f"❌ Decryption failed for {file_path}: {e}")
            return False
        
        # Write decrypted content to temp file
        with open(temp_file, 'wb') as outfile:
            outfile.write(decrypted_content)
        
        # Atomic replacement
        temp_file.replace(file_path)
        return True
        
    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        print(f"❌ Decryption failed for {file_path}: {e}")
        return False

def confirm_operation(files: List[Path], root_folder: Path) -> bool:
    """Get user confirmation before proceeding with decryption"""
    print(f"\n📋 DECRYPTION SUMMARY:")
    print(f"   Directory: {root_folder}")
    print(f"   Files to decrypt: {len(files)}")
    
    if len(files) > 10:
        print(f"\n📄 First 10 files:")
        for file_path in files[:10]:
            print(f"   • {file_path.relative_to(root_folder)}")
        print(f"   ... and {len(files) - 10} more files")
    else:
        print(f"\n📄 Files to decrypt:")
        for file_path in files:
            print(f"   • {file_path.relative_to(root_folder)}")
    
    print(f"\n⚠️  WARNING: This will decrypt files in-place!")
    print(f"   Encrypted files will be replaced with decrypted versions.")
    print(f"   Make sure you have backups of the encrypted files!")
    
    while True:
        response = input("\n❓ Do you want to proceed? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please enter 'yes' or 'no'")

def main():
    """Main decryption process with comprehensive error handling"""
    print("🔓 Secure File Decryption Tool - Fixed Version")
    print("=" * 50)
    
    try:
        # Get target directory
        while True:
            directory_input = input("📁 Enter directory path to decrypt (or 'test' for ~/Desktop/crypto_test): ").strip()
            
            if directory_input.lower() == 'test':
                root_folder = Path.home() / "Desktop" / "crypto_test"
                if not root_folder.exists():
                    print(f"❌ Test directory does not exist: {root_folder}")
                    print("Please create it first or use a different path.")
                    continue
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
        
        # Get salt file
        print(f"\n🔑 Salt File Required:")
        print(f"   The salt file was created during encryption.")
        print(f"   It's usually named 'encryption_salt.key' in the backup folder.")
        
        while True:
            salt_input = input("🔑 Enter salt file path (or 'auto' to search in directory): ").strip()
            
            if salt_input.lower() == 'auto':
                # Auto-search for salt file
                possible_salt_files = list(root_folder.rglob('encryption_salt.key'))
                if possible_salt_files:
                    salt_file_path = possible_salt_files[0]
                    print(f"✅ Found salt file: {salt_file_path}")
                    break
                else:
                    print("❌ No salt file found in directory. Please specify path manually.")
                    continue
            elif salt_input:
                try:
                    salt = load_salt_file(salt_input)
                    salt_file_path = salt_input
                    break
                except ValidationError as e:
                    print(f"❌ {e}")
                    continue
            else:
                print("Please enter a valid salt file path or 'auto'")
        
        # Load salt
        try:
            salt = load_salt_file(salt_file_path)
            print(f"✅ Salt loaded successfully")
        except ValidationError as e:
            print(f"❌ {e}")
            return
        
        # List encrypted files
        print(f"\n📂 Scanning directory for encrypted files: {root_folder}")
        files = list_encrypted_files(root_folder)
        
        if not files:
            print("❌ No encrypted files found to decrypt!")
            print("   Make sure you're in the right directory and files are actually encrypted.")
            return
        
        # Get user confirmation
        if not confirm_operation(files, root_folder):
            print("❌ Operation cancelled by user")
            return
        
        # Get password securely
        print(f"\n🔐 Password Required:")
        print(f"   Enter the same password used for encryption.")
        
        while True:
            password = getpass.getpass("🔑 Enter decryption password: ")
            if len(password) >= CONFIG['MIN_PASSWORD_LENGTH']:
                break
            else:
                print(f"❌ Password must be at least {CONFIG['MIN_PASSWORD_LENGTH']} characters")
                password = None  # Clear from memory
        
        # Generate key from password and salt
        print(f"\n🔐 Generating decryption key...")
        try:
            key = generate_key_from_password(password, salt)
            password = None  # Clear password from memory
        except Exception as e:
            print(f"❌ Key generation failed: {e}")
            return
        
        # Decrypt files
        print(f"\n🔓 Starting decryption...")
        fernet = Fernet(key)
        decrypted_count = 0
        
        for i, file_path in enumerate(files, 1):
            print(f"🔓 Decrypting ({i}/{len(files)}): {file_path.relative_to(root_folder)}")
            if decrypt_file_safely(file_path, fernet):
                decrypted_count += 1
        
        # Final summary
        print(f"\n✅ DECRYPTION COMPLETE!")
        print(f"   Files decrypted: {decrypted_count}/{len(files)}")
        
        if decrypted_count != len(files):
            failed_count = len(files) - decrypted_count
            print(f"⚠️  {failed_count} files failed to decrypt")
            print(f"   This might be due to wrong password or file corruption.")
        
        if decrypted_count > 0:
            print(f"\n✅ SUCCESS! Your files have been decrypted.")
            print(f"   Original encrypted files have been replaced with decrypted versions.")
        
    except KeyboardInterrupt:
        print(f"\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"Please check the error and try again")

if __name__ == "__main__":
    main()