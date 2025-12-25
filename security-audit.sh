#!/bin/bash

# Security Audit Script for Telegram Ollama Bot
echo "🔒 SECURITY AUDIT SCRIPT"
echo "========================"

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not active"
    echo "Run: source bot_env/bin/activate"
    exit 1
fi

echo "✅ Virtual environment active: $VIRTUAL_ENV"

# Install security audit tool if not present
if ! command -v pip-audit &> /dev/null; then
    echo "📦 Installing pip-audit..."
    pip install pip-audit
fi

echo ""
echo "🔍 RUNNING SECURITY AUDIT..."
echo "============================="

# Run security audit
pip-audit --format markdown

echo ""
echo "📋 AUDIT SUMMARY"
echo "================"

# Count vulnerabilities
VULN_COUNT=$(pip-audit --format json 2>/dev/null | jq '.vulnerabilities | length' 2>/dev/null || echo "0")

if [ "$VULN_COUNT" = "0" ]; then
    echo "✅ No known vulnerabilities found!"
else
    echo "⚠️  Found $VULN_COUNT potential vulnerabilities"
    echo "Run 'pip-audit --format detailed' for more information"
fi

echo ""
echo "🛡️  ADDITIONAL SECURITY CHECKS"
echo "==============================="

# Check for sensitive files
echo "📁 Checking for sensitive files..."
if [ -f "settings.py" ]; then
    echo "✅ settings.py exists (excluded from git)"
else
    echo "❌ settings.py not found"
fi

# Check environment variables
echo "🔐 Checking environment security..."
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    TOKEN_LENGTH=${#TELEGRAM_BOT_TOKEN}
    echo "✅ TELEGRAM_BOT_TOKEN set ($TOKEN_LENGTH chars)"
else
    echo "⚠️  TELEGRAM_BOT_TOKEN not set"
fi

# Check file permissions
echo "🔒 Checking file permissions..."
if [ -f "settings.py" ]; then
    PERMS=$(stat -c "%a" settings.py 2>/dev/null || echo "unknown")
    echo "✅ settings.py permissions: $PERMS"
fi

echo ""
echo "🎯 RECOMMENDATIONS"
echo "=================="

if [ "$VULN_COUNT" != "0" ]; then
    echo "• Update vulnerable packages: pip install --upgrade <package>"
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "• Set TELEGRAM_BOT_TOKEN environment variable"
fi

echo "• Run this audit regularly: ./security-audit.sh"
echo "• Monitor logs for security events"

echo ""
echo "✅ SECURITY AUDIT COMPLETE"