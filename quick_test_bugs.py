#!/usr/bin/env python3
"""
Quick test to demonstrate bugs in encrypt.py and decrypt.py
"""

import os
import sys

def test_directory_bug():
    """Test what happens when target directory doesn't exist"""
    print("Testing directory validation bug...")
    
    # Simulate what happens in the original code
    non_existent_dir = os.path.expanduser('~/NonExistentDirectory')
    print(f"Testing with directory: {non_existent_dir}")
    print(f"Directory exists: {os.path.exists(non_existent_dir)}")
    
    # This would be the behavior in the original code
    try:
        # This simulates list_all_files() from the original
        for dirpath, dirnames, filenames in os.walk(non_existent_dir):
            print(f"Found: {filenames}")
        print("✓ No error (but also no files found)")
    except Exception as e:
        print(f"✗ Error: {e}")

def test_salt_issue():
    """Demonstrate the hardcoded salt security issue"""
    print("\nTesting hardcoded salt issue...")
    
    # Show that the salt is always the same
    salt1 = b'salt_1234567890'  # From encrypt.py
    salt2 = b'salt_1234567890'  # From decrypt.py
    
    print(f"Salt in encrypt.py: {salt1}")
    print(f"Salt in decrypt.py: {salt2}")
    print(f"Salts are identical: {salt1 == salt2}")
    print("🔴 SECURITY ISSUE: Same salt used for all users/sessions!")

def test_memory_issue():
    """Demonstrate password in memory issue"""
    print("\nTesting password memory issue...")
    
    # Simulate password handling
    password = "test_password_123"
    print(f"Password stored as string: '{password}'")
    print(f"Password in memory at: {id(password)}")
    print("🟠 SECURITY ISSUE: Password remains in memory as plain text!")

def test_excluded_files():
    """Test the excluded files logic"""
    print("\nTesting excluded files logic...")
    
    excluded_files = {"voldemort.py", "encrypt.py", "decrypt.py", "thekey.key"}
    
    test_files = [
        "document.txt",
        "encrypt.py",  # Should be excluded
        "my_script.py",  # NOT excluded but probably should be
        "config.json",
        "backup.py",  # NOT excluded but probably should be
        "thekey.key"  # Should be excluded
    ]
    
    for file in test_files:
        if file in excluded_files:
            print(f"✓ {file} - Excluded")
        else:
            print(f"? {file} - NOT excluded (potential issue)")

def test_error_handling():
    """Test error handling specificity"""
    print("\nTesting error handling...")
    
    try:
        # Simulate opening a non-existent file
        with open("/nonexistent/file.txt", "rb") as f:
            content = f.read()
    except Exception as e:
        print(f"Generic exception caught: {type(e).__name__}: {e}")
        print("🟡 ISSUE: Generic exception handling masks specific errors")

if __name__ == "__main__":
    print("=" * 50)
    print("BUG DEMONSTRATION SCRIPT")
    print("=" * 50)
    
    test_directory_bug()
    test_salt_issue()
    test_memory_issue()
    test_excluded_files()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("- Directory validation missing")
    print("- Hardcoded salt security vulnerability")
    print("- Password stored in plain text memory")
    print("- Incomplete file exclusion list")
    print("- Generic error handling")
    print("=" * 50)