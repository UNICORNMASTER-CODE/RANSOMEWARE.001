#!/usr/bin/env python3
"""
Test suite for encrypt.py and decrypt.py

This test file can be run in multiple ways:
1. Using unittest: python3 test_encryption.py
2. Using pytest: pytest test_encryption.py (if pytest is installed)
3. Direct execution: python3 test_encryption.py
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open
import sys

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the modules - if cryptography is not available, we'll skip those tests
try:
    import encrypt
    import decrypt
    CRYPTO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import encrypt/decrypt modules: {e}")
    CRYPTO_AVAILABLE = False

class TestEncryptionFunctions(unittest.TestCase):
    """Test cases for encryption and decryption functions"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_password = "test_password_123"
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library not available")
    def test_generate_key_from_password(self):
        """Test that key generation from password works consistently"""
        key1 = encrypt.generate_key_from_password(self.test_password)
        key2 = encrypt.generate_key_from_password(self.test_password)
        
        # Same password should generate same key
        self.assertEqual(key1, key2)
        
        # Different password should generate different key
        different_key = encrypt.generate_key_from_password("different_password")
        self.assertNotEqual(key1, different_key)
        
        # Key should be bytes
        self.assertIsInstance(key1, bytes)
    
    @unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library not available")
    def test_decrypt_generate_key_from_password(self):
        """Test that decrypt module generates same key as encrypt module"""
        encrypt_key = encrypt.generate_key_from_password(self.test_password)
        decrypt_key = decrypt.generate_key_from_password(self.test_password)
        
        # Both modules should generate identical keys
        self.assertEqual(encrypt_key, decrypt_key)
    
    def test_create_backup_folder_default_location(self):
        """Test backup folder creation in default location"""
        with patch('os.makedirs') as mock_makedirs:
            backup_folder = encrypt.create_backup_folder()
            
            # Should create directory
            mock_makedirs.assert_called_once()
            
            # Should have timestamp format
            self.assertTrue(backup_folder.startswith('backup_'))
            self.assertTrue(len(backup_folder) > 10)  # Should include timestamp
    
    def test_create_backup_folder_custom_location(self):
        """Test backup folder creation in custom location"""
        custom_location = "/tmp/custom_backup"
        
        with patch('os.makedirs') as mock_makedirs:
            backup_folder = encrypt.create_backup_folder(custom_location)
            
            # Should create directory
            mock_makedirs.assert_called_once()
            
            # Should be in custom location
            self.assertTrue(backup_folder.startswith(custom_location))
            self.assertTrue('backup_' in backup_folder)
    
    def test_list_all_files(self):
        """Test file listing functionality"""
        # Create test files
        test_file1 = os.path.join(self.test_dir, "test1.txt")
        test_file2 = os.path.join(self.test_dir, "test2.txt")
        excluded_file = os.path.join(self.test_dir, "encrypt.py")
        
        # Create subdirectory with file
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)
        test_file3 = os.path.join(subdir, "test3.txt")
        
        # Write test files
        for file_path in [test_file1, test_file2, excluded_file, test_file3]:
            with open(file_path, 'w') as f:
                f.write("test content")
        
        # Test encrypt module
        files = encrypt.list_all_files(self.test_dir)
        
        # Should include regular files but exclude encrypt.py
        self.assertIn(test_file1, files)
        self.assertIn(test_file2, files)
        self.assertIn(test_file3, files)
        self.assertNotIn(excluded_file, files)
        
        # Test decrypt module
        files = decrypt.list_all_files(self.test_dir)
        
        # Should have same behavior
        self.assertIn(test_file1, files)
        self.assertIn(test_file2, files)
        self.assertIn(test_file3, files)
        self.assertNotIn(excluded_file, files)
    
    def test_backup_file_success(self):
        """Test successful file backup"""
        # Create test file
        test_file = os.path.join(self.test_dir, "test.txt")
        test_content = "This is test content"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        # Create backup directory
        backup_dir = os.path.join(self.test_dir, "backup")
        os.makedirs(backup_dir)
        
        # Test backup
        result = encrypt.backup_file(test_file, backup_dir, self.test_dir)
        
        # Should return True for success
        self.assertTrue(result)
        
        # Backup file should exist and have same content
        backup_file = os.path.join(backup_dir, "test.txt")
        self.assertTrue(os.path.exists(backup_file))
        
        with open(backup_file, 'r') as f:
            backup_content = f.read()
        
        self.assertEqual(test_content, backup_content)
    
    def test_backup_file_failure(self):
        """Test backup file failure handling"""
        # Try to backup non-existent file
        non_existent_file = os.path.join(self.test_dir, "nonexistent.txt")
        backup_dir = os.path.join(self.test_dir, "backup")
        
        with patch('builtins.print'):  # Suppress error output
            result = encrypt.backup_file(non_existent_file, backup_dir, self.test_dir)
        
        # Should return False for failure
        self.assertFalse(result)

class TestIntegration(unittest.TestCase):
    """Integration tests for encrypt/decrypt workflow"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = tempfile.mkdtemp()
        self.test_password = "integration_test_password"
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography library not available")
    def test_encrypt_decrypt_roundtrip(self):
        """Test that data can be encrypted and then decrypted successfully"""
        try:
            from cryptography.fernet import Fernet
            
            # Create test data
            test_content = b"This is test data for encryption/decryption"
            
            # Generate key
            key = encrypt.generate_key_from_password(self.test_password)
            
            # Encrypt data
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(test_content)
            
            # Decrypt data
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Should match original
            self.assertEqual(test_content, decrypted_data)
            
        except ImportError:
            self.skipTest("cryptography.fernet not available")

def run_manual_tests():
    """Run basic manual tests without external dependencies"""
    print("Running manual tests for encryption/decryption modules...")
    print("=" * 50)
    
    # Test 1: Module imports
    try:
        import encrypt
        import decrypt
        print("✓ Successfully imported encrypt and decrypt modules")
    except ImportError as e:
        print(f"✗ Failed to import modules: {e}")
        return False
    
    # Test 2: Function existence
    required_functions = [
        (encrypt, 'generate_key_from_password'),
        (encrypt, 'create_backup_folder'),
        (encrypt, 'backup_file'),
        (encrypt, 'list_all_files'),
        (decrypt, 'generate_key_from_password'),
        (decrypt, 'list_all_files'),
    ]
    
    for module, func_name in required_functions:
        if hasattr(module, func_name):
            print(f"✓ {module.__name__}.{func_name} exists")
        else:
            print(f"✗ {module.__name__}.{func_name} missing")
    
    # Test 3: Basic functionality without cryptography
    try:
        # Test file listing
        current_dir = os.path.dirname(os.path.abspath(__file__))
        files = encrypt.list_all_files(current_dir)
        print(f"✓ list_all_files found {len(files)} files")
        
        # Test backup folder creation (mock)
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_folder = encrypt.create_backup_folder(temp_dir)
            if os.path.exists(backup_folder):
                print("✓ create_backup_folder works")
            else:
                print("✗ create_backup_folder failed")
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
    
    print("=" * 50)
    print("Manual tests completed!")
    return True

if __name__ == '__main__':
    print("Encryption/Decryption Test Suite")
    print("=" * 40)
    
    # Check if we're running with unittest or manually
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        run_manual_tests()
    else:
        # Run unittest suite
        unittest.main(verbosity=2)