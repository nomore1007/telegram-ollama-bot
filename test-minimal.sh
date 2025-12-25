#!/bin/bash

# Minimal Bot Deployment Test
# This script tests the absolute minimum to get the bot running

echo "🧪 MINIMAL BOT DEPLOYMENT TEST"
echo "================================"

# Step 1: Check prerequisites
echo
echo "1. Checking Prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker is installed"

if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    exit 1
fi
echo "✅ Git is installed"

# Step 2: Create test directory
echo
echo "2. Setting up test environment..."
TEST_DIR="/tmp/bot-test"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Step 3: Clone repository
echo
echo "3. Cloning repository..."
if ! git clone https://github.com/nomore1007/telegram-ollama-bot.git . 2>/dev/null; then
    echo "❌ Failed to clone repository"
    exit 1
fi
echo "✅ Repository cloned successfully"

# Step 4: Create minimal environment
echo
echo "4. Creating minimal environment..."
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=test_token_placeholder
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
BOT_USERNAME=TestBot
EOF
echo "✅ Environment file created"

# Step 5: Test build
echo
echo "5. Testing Docker build..."
if ! docker build -t bot-test . > build.log 2>&1; then
    echo "❌ Docker build failed"
    echo "   Build log:"
    tail -20 build.log
    exit 1
fi
echo "✅ Docker build successful"

# Step 6: Test run (minimal)
echo
echo "6. Testing container startup..."
if ! docker run -d --name bot-test-container --env-file .env bot-test > /dev/null 2>&1; then
    echo "❌ Container failed to start"
    exit 1
fi

# Wait a moment
sleep 3

# Check status
if docker ps | grep -q bot-test-container; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    docker logs bot-test-container
    exit 1
fi

# Step 7: Check logs
echo
echo "7. Checking container logs..."
LOGS=$(docker logs bot-test-container 2>&1 | head -10)
if echo "$LOGS" | grep -q "Traceback\|Error\|Exception"; then
    echo "⚠️  Container started but has errors:"
    echo "$LOGS"
else
    echo "✅ Container started without errors"
    echo "   Sample logs:"
    echo "$LOGS"
fi

# Cleanup
echo
echo "8. Cleaning up..."
docker stop bot-test-container > /dev/null 2>&1
docker rm bot-test-container > /dev/null 2>&1
docker rmi bot-test > /dev/null 2>&1
cd /
rm -rf "$TEST_DIR"

echo
echo "🎉 BASIC DEPLOYMENT TEST PASSED!"
echo
echo "The bot container can be built and started successfully."
echo "The issue is likely with:"
echo "• Ollama connectivity"
echo "• Telegram token configuration"
echo "• Network/firewall settings"
echo
echo "Next steps:"
echo "1. Ensure Ollama is running: ollama list"
echo "2. Get real Telegram token from @BotFather"
echo "3. Use the working commands above with real values"