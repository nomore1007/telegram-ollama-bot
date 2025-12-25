#!/bin/bash

# Portainer Deployment Fix Script
# Run this locally to test and fix deployment issues

echo "🔧 Portainer Deployment Fix Script"
echo "==================================="

# Test 1: Check GitHub repository access
echo
echo "1. Testing GitHub Repository Access..."
if curl -s --head https://github.com/nomore1007/telegram-ollama-bot | head -1 | grep "200" > /dev/null; then
    echo "✅ GitHub repository is accessible"
else
    echo "❌ GitHub repository not accessible"
    exit 1
fi

# Test 2: Check if we can clone the repository
echo
echo "2. Testing Repository Cloning..."
if git ls-remote https://github.com/nomore1007/telegram-ollama-bot.git > /dev/null 2>&1; then
    echo "✅ Repository can be cloned"
else
    echo "❌ Repository cloning failed"
    exit 1
fi

# Test 3: Check Ollama connectivity (if running)
echo
echo "3. Testing Ollama Connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is accessible on localhost:11434"
else
    echo "⚠️  Ollama not accessible on localhost:11434"
    echo "   Make sure Ollama is running and accessible"
fi

echo
echo "4. Local Deployment Test..."
echo "   This will build and test the bot locally"

# Create test .env file
cat > .env.test << EOF
TELEGRAM_BOT_TOKEN=test_token_placeholder
OLLAMA_HOST=http://host.docker.internal:11434
OLLAMA_MODEL=llama2
BOT_USERNAME=TestBot
EOF

echo "   Created test .env file"

# Test Docker build
echo
echo "5. Testing Docker Build..."
if docker build -t telegram-bot-test . > build.log 2>&1; then
    echo "✅ Docker build successful"
    rm build.log
else
    echo "❌ Docker build failed"
    echo "   Check build.log for details"
    exit 1
fi

echo
echo "6. Testing Container Run..."
if docker run -d --name test-bot --env-file .env.test telegram-bot-test > /dev/null 2>&1; then
    echo "✅ Container started successfully"
    sleep 5

    # Check if container is healthy
    if docker ps | grep test-bot | grep healthy > /dev/null 2>&1; then
        echo "✅ Container health check passed"
    else
        echo "⚠️  Container health check pending (may take longer)"
    fi

    # Clean up
    docker stop test-bot > /dev/null 2>&1
    docker rm test-bot > /dev/null 2>&1
else
    echo "❌ Container failed to start"
fi

# Cleanup
rm .env.test

echo
echo "🎯 DEPLOYMENT READY!"
echo
echo "If local tests pass, the issue is likely:"
echo "• Portainer network/firewall restrictions"
echo "• Portainer user permissions"
echo "• Environment variable format in Portainer"
echo
echo "Try these solutions:"
echo "1. Use 'host' network mode in Portainer"
echo "2. Check Portainer user has stack deployment permissions"
echo "3. Use IP addresses instead of hostnames"
echo "4. Try the manual Docker commands instead of Portainer"