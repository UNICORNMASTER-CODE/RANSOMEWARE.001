import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertScriptConfigurationSchema } from "@shared/schema";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  
  // Generate and download encrypt script
  app.post("/api/scripts/encrypt", async (req, res) => {
    try {
      const config = insertScriptConfigurationSchema.parse(req.body);
      
      const backupLocation = config.backupLocation === "custom" ? config.customBackupPath : config.backupLocation;
      
      const encryptScript = generateEncryptScript(config.targetLocation, backupLocation);
      
      res.setHeader('Content-Type', 'text/x-python');
      res.setHeader('Content-Disposition', 'attachment; filename="encrypt.py"');
      res.send(encryptScript);
    } catch (error) {
      res.status(400).json({ message: "Invalid configuration data" });
    }
  });

  // Generate and download decrypt script
  app.post("/api/scripts/decrypt", async (req, res) => {
    try {
      const config = insertScriptConfigurationSchema.parse(req.body);
      
      const decryptScript = generateDecryptScript(config.targetLocation);
      
      res.setHeader('Content-Type', 'text/x-python');
      res.setHeader('Content-Disposition', 'attachment; filename="decrypt.py"');
      res.send(decryptScript);
    } catch (error) {
      res.status(400).json({ message: "Invalid configuration data" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}

function generateEncryptScript(targetLocation: string, backupLocation: string): string {
  return `import os
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
    root_folder = os.path.expanduser('${targetLocation}')
    
    files = list_all_files(root_folder)
    print(f"Found {len(files)} files to encrypt")
    
    backup_location = os.path.expanduser('${backupLocation}')
    
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
`;
}

function generateDecryptScript(targetLocation: string): string {
  return `import os
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
    
    root_folder = os.path.expanduser('${targetLocation}')
    
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
`;
}
