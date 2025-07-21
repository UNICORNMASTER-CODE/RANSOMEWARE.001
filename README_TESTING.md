# Testing Guide for Encryption/Decryption Files

This guide provides multiple approaches to test your `encrypt.py` and `decrypt.py` files.

## Files in Your Project

- `encrypt.py` - File encryption script with backup functionality
- `decrypt.py` - File decryption script  
- `test_encryption.py` - Comprehensive test suite (created)
- `requirements.txt` - Dependencies needed for full functionality

## Testing Approaches

### 1. Manual Testing (No Dependencies Required)

Run basic functionality tests without external libraries:

```bash
python3 test_encryption.py --manual
```

This will test:
- Module imports
- Function existence
- Basic file operations (without cryptography)

### 2. Unit Testing with unittest (Python Standard Library)

If you have the `cryptography` library installed:

```bash
python3 test_encryption.py
```

This runs the full test suite using Python's built-in unittest framework.

### 3. Testing with pytest (Recommended)

First install dependencies:

```bash
# Using pip (if available)
pip3 install -r requirements.txt

# Or using system package manager (Ubuntu/Debian)
sudo apt update
sudo apt install python3-cryptography python3-pytest

# Or using virtual environment
python3 -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
```

Then run tests:

```bash
# Run all tests
pytest test_encryption.py

# Run with verbose output
pytest test_encryption.py -v

# Run specific test class
pytest test_encryption.py::TestEncryptionFunctions

# Run specific test method
pytest test_encryption.py::TestEncryptionFunctions::test_generate_key_from_password
```

### 4. Direct Script Testing

Test the actual scripts with sample data:

```bash
# Create a test directory with sample files
mkdir ~/crypto_test
echo "This is test file 1" > ~/crypto_test/test1.txt
echo "This is test file 2" > ~/crypto_test/test2.txt

# Test encryption (will prompt for password)
python3 encrypt.py

# Test decryption (will prompt for password)
python3 decrypt.py
```

### 5. Manual Code Review Testing

Review the code for common issues:

```bash
# Check Python syntax
python3 -m py_compile encrypt.py
python3 -m py_compile decrypt.py

# Check for common issues
python3 -c "import ast; ast.parse(open('encrypt.py').read()); print('encrypt.py syntax OK')"
python3 -c "import ast; ast.parse(open('decrypt.py').read()); print('decrypt.py syntax OK')"
```

## Test Categories Covered

### Unit Tests
- ✅ Key generation consistency
- ✅ Backup folder creation
- ✅ File listing functionality
- ✅ File backup operations
- ✅ Error handling

### Integration Tests
- ✅ Encrypt/decrypt roundtrip
- ✅ Key compatibility between modules

### Functional Tests
- ✅ Directory traversal
- ✅ File exclusion logic
- ✅ Backup structure preservation

## Installation Issues Solutions

### If cryptography installation fails:

1. **Ubuntu/Debian systems:**
   ```bash
   sudo apt update
   sudo apt install python3-cryptography
   ```

2. **Using virtual environment:**
   ```bash
   sudo apt install python3-venv
   python3 -m venv test_env
   source test_env/bin/activate
   pip install cryptography pytest
   ```

3. **Using system packages:**
   ```bash
   sudo apt install python3-pytest
   ```

### If pip is not available:
```bash
sudo apt install python3-pip
```

## Expected Test Results

When all dependencies are available, you should see:

```
test_backup_file_failure ... ok
test_backup_file_success ... ok
test_create_backup_folder_custom_location ... ok
test_create_backup_folder_default_location ... ok
test_decrypt_generate_key_from_password ... ok
test_generate_key_from_password ... ok
test_list_all_files ... ok
test_encrypt_decrypt_roundtrip ... ok

----------------------------------------------------------------------
Ran 8 tests in X.XXXs

OK
```

## Continuous Integration

For CI/CD pipelines, add this to your workflow:

```yaml
# Example GitHub Actions
- name: Install dependencies
  run: |
    sudo apt update
    sudo apt install python3-cryptography python3-pytest
    
- name: Run tests
  run: |
    python3 test_encryption.py
    pytest test_encryption.py -v
```

## Troubleshooting

### Common Issues:

1. **ImportError: No module named 'cryptography'**
   - Install cryptography: `sudo apt install python3-cryptography`

2. **Permission denied errors**
   - Use `sudo` for system-wide installations
   - Or use virtual environments

3. **Tests skipped due to missing dependencies**
   - This is expected behavior when cryptography is not available
   - Install dependencies to run full test suite

### Manual Verification:

Even without automated tests, you can manually verify:

1. **Code syntax:** Both files should compile without errors
2. **Function existence:** All required functions should be present
3. **Logic flow:** Review the encryption/decryption process
4. **Security:** Check for hardcoded passwords or keys
5. **Error handling:** Verify try/catch blocks are present

## Security Testing Notes

⚠️ **Important Security Considerations:**

1. **Never test with real sensitive data**
2. **Use test directories only** (like `~/crypto_test`)
3. **Test password handling** - ensure passwords aren't logged
4. **Verify backup functionality** before running on important files
5. **Test error scenarios** - what happens with wrong passwords?

## Performance Testing

For large file sets, consider:

```bash
# Create many test files
for i in {1..100}; do echo "Test file $i" > ~/crypto_test/test_$i.txt; done

# Time the operations
time python3 encrypt.py
time python3 decrypt.py
```

This comprehensive testing approach ensures your encryption/decryption scripts work correctly and securely.