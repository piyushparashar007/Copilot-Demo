#!/usr/bin/env bash

set -e

VENV_DIR=".security-scan-env"

if [ ! -d "$VENV_DIR" ]; then
    echo "Security environment missing. Run install script first."
    exit 1
fi

source $VENV_DIR/bin/activate

echo "=============================="
echo "Python Dependency Vulnerability Scan"
echo "=============================="

if command -v pip-audit >/dev/null 2>&1; then
    if [ -f requirements.txt ]; then
        pip-audit -r requirements.txt
    else
        echo "requirements.txt not found. Auditing current environment."
        pip-audit
    fi
else
    echo "pip-audit not installed. Skipping Python dependency scan."
fi


echo ""
echo "=============================="
echo "Python Security Static Analysis"
echo "=============================="

if command -v bandit >/dev/null 2>&1; then
    bandit -r .
else
    echo "bandit not installed. Skipping code scan."
fi


echo ""
echo "=============================="
echo "Frontend Dependency Audit"
echo "=============================="

//traveses into frontend directory if it exists otherwise print current directory and run npm audit if package.json is found
if [ -d frontend ]; then
    echo "Entering frontend directory for audit..."
    cd frontend
else
    echo "No frontend directory found. Running audit in current directory: $(pwd)"
fi  


if [ -f package.json ]; then

    if [ ! -f package-lock.json ]; then
        echo "package-lock.json not found. Creating lockfile..."
        npm install --package-lock-only
    fi

    npm audit --audit-level=moderate

else
    echo "No frontend package.json detected. Skipping npm audit."
fi


echo ""
echo "=============================="
echo "Optional Static Security Scan"
echo "=============================="

if command -v semgrep >/dev/null 2>&1; then
    semgrep --config auto .
else
    echo "semgrep not installed. Skipping advanced scan."
fi


echo ""
echo "Security scan complete."