#!/bin/bash

echo "======================================"
echo "   Testing encrypt.py and decrypt.py"
echo "======================================"
echo

# Test 1: Syntax validation
echo "1. Testing Python syntax..."
echo -n "   encrypt.py: "
if python3 -m py_compile encrypt.py 2>/dev/null; then
    echo "✓ OK"
else
    echo "✗ SYNTAX ERROR"
    exit 1
fi

echo -n "   decrypt.py: "
if python3 -m py_compile decrypt.py 2>/dev/null; then
    echo "✓ OK"
else
    echo "✗ SYNTAX ERROR"
    exit 1
fi

echo

# Test 2: AST parsing
echo "2. Testing code structure..."
echo -n "   encrypt.py AST: "
if python3 -c "import ast; ast.parse(open('encrypt.py').read())" 2>/dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

echo -n "   decrypt.py AST: "
if python3 -c "import ast; ast.parse(open('decrypt.py').read())" 2>/dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

echo

# Test 3: Function existence (without importing due to missing deps)
echo "3. Testing function definitions..."

# Check for required functions in encrypt.py
echo -n "   encrypt.py functions: "
if grep -q "def generate_key_from_password" encrypt.py && \
   grep -q "def create_backup_folder" encrypt.py && \
   grep -q "def backup_file" encrypt.py && \
   grep -q "def list_all_files" encrypt.py; then
    echo "✓ OK"
else
    echo "✗ Missing functions"
fi

# Check for required functions in decrypt.py
echo -n "   decrypt.py functions: "
if grep -q "def generate_key_from_password" decrypt.py && \
   grep -q "def list_all_files" decrypt.py; then
    echo "✓ OK"
else
    echo "✗ Missing functions"
fi

echo

# Test 4: Security checks
echo "4. Basic security checks..."

# Check for hardcoded passwords (excluding test data)
echo -n "   No hardcoded passwords: "
if ! grep -i "password.*=" encrypt.py decrypt.py | grep -v "input\|print\|#" > /dev/null; then
    echo "✓ OK"
else
    echo "⚠ WARNING: Possible hardcoded passwords found"
fi

# Check for proper error handling
echo -n "   Error handling present: "
if grep -q "try:" encrypt.py && grep -q "except" encrypt.py && \
   grep -q "try:" decrypt.py && grep -q "except" decrypt.py; then
    echo "✓ OK"
else
    echo "⚠ WARNING: Limited error handling"
fi

echo

# Test 5: Run manual tests if available
echo "5. Running manual tests..."
if [ -f "test_encryption.py" ]; then
    python3 test_encryption.py --manual
else
    echo "   test_encryption.py not found, skipping"
fi

echo
echo "======================================"
echo "Basic tests completed!"
echo "======================================"
echo
echo "To run full tests with cryptography:"
echo "1. Install dependencies: sudo apt install python3-cryptography python3-pytest"
echo "2. Run: python3 test_encryption.py"
echo "3. Or run: pytest test_encryption.py -v"
echo