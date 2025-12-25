#!/bin/bash

# Docker Setup Test Script
# This script validates the Docker configuration without requiring Docker

echo "🐳 Testing Docker Configuration"
echo "================================="

# Check required files exist
required_files=("Dockerfile" "docker-compose.yml" ".dockerignore" "requirements.txt")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file: Found"
    else
        echo "❌ $file: Missing"
        exit 1
    fi
done

# Check optional files
optional_files=(".env.example" "docker-compose.dev.yml" "Makefile")
for file in "${optional_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file: Found (optional)"
    else
        echo "⚠️  $file: Missing (optional)"
    fi
done

# Test YAML syntax
echo
echo "📄 Testing YAML syntax..."
python3 -c "
import yaml
files = ['docker-compose.yml']
try:
    files.append('docker-compose.dev.yml')
except:
    pass

for f in files:
    try:
        with open(f, 'r') as file:
            yaml.safe_load(file)
        print(f'✅ {f}: Valid YAML')
    except Exception as e:
        print(f'❌ {f}: YAML error - {e}')
"

# Test environment template
echo
echo "🔧 Testing environment template..."
if [ -f ".env.example" ]; then
    required_vars=("TELEGRAM_BOT_TOKEN" "OLLAMA_HOST" "OLLAMA_MODEL")
    missing_vars=()

    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env.example; then
            echo "✅ $var: Defined in template"
        else
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "❌ Missing required variables in .env.example:"
        printf '  - %s\n' "${missing_vars[@]}"
    fi
else
    echo "❌ .env.example: Missing"
fi

# Test Makefile syntax
echo
echo "🔨 Testing Makefile..."
if [ -f "Makefile" ]; then
    # Check for basic targets
    targets=("help" "build" "up" "down")
    for target in "${targets[@]}"; do
        if grep -q "^${target}:" Makefile; then
            echo "✅ make $target: Available"
        else
            echo "⚠️  make $target: Missing"
        fi
    done
else
    echo "❌ Makefile: Missing"
fi

# Check .dockerignore
echo
echo "🚫 Testing .dockerignore..."
if [ -f ".dockerignore" ]; then
    important_excludes=("__pycache__" "*.pyc" ".env" ".git")
    for exclude in "${important_excludes[@]}"; do
        if grep -q "$exclude" .dockerignore; then
            echo "✅ Excluding: $exclude"
        else
            echo "⚠️  Not excluding: $exclude"
        fi
    done
else
    echo "❌ .dockerignore: Missing"
fi

echo
echo "🎉 Docker configuration validation complete!"
echo
echo "📋 Next steps:"
echo "1. Copy .env.example to .env and configure your tokens"
echo "2. Run: make build"
echo "3. Run: make up"
echo "4. Check logs: make logs"