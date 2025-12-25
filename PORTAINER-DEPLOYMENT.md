# 🚀 Portainer Deployment Guide

## Prerequisites

1. **Portainer Installed**: Access your Portainer instance (typically at `http://your-server:9000` or `https://portainer.yourdomain.com`)

2. **GitHub Repository**: Your bot repository at `https://github.com/nomore1007/telegram-ollama-bot`

3. **Docker Environment**: Portainer connected to Docker engine with sufficient resources (4GB+ RAM recommended)

## Step 1: Access Portainer

1. Open your Portainer web interface
2. Log in with your credentials
3. Select your **Docker environment** (local or remote)

## Step 2: Create Environment Variables

### Method 1: Portainer Environment Variables
1. Go to **Settings** → **Environment Variables** (if available)
2. Add these variables:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=DeepthoughtBot
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama2
MAX_TOKENS=2000
TEMPERATURE=0.7
TIMEOUT=30
DEFAULT_PROMPT=You are a helpful AI assistant. Respond to the user's message like a dude bro, but informative and concise. Be helpful and accurate in your responses.
```

### Method 2: Create .env File in Portainer
1. Go to **Volumes** → **Add Volume**
2. Create a volume named `telegram-bot-env`
3. Use Portainer's file browser to create a `.env` file in the volume

## Step 3: Deploy the Stack

### Option A: Use Pre-built Image (Recommended)

1. Go to **Stacks** in Portainer sidebar
2. Click **Add Stack**
3. Configure:
   - **Name**: `telegram-ollama-bot`
   - **Repository URL**: Leave empty (we'll paste compose content)
   - **Compose path**: Leave empty

4. **Paste this in "Web editor"**:

```yaml
version: '3.8'

services:
  telegram-bot:
    image: ghcr.io/nomore1007/telegram-ollama-bot:latest
    container_name: deepthought-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - BOT_USERNAME=${BOT_USERNAME:-DeepthoughtBot}
      - OLLAMA_HOST=${OLLAMA_HOST:-http://ollama:11434}
      - OLLAMA_MODEL=${OLLAMA_MODEL:-llama2}
      - MAX_TOKENS=${MAX_TOKENS:-2000}
      - TEMPERATURE=${TEMPERATURE:-0.7}
      - TIMEOUT=${TIMEOUT:-30}
      - DEFAULT_PROMPT=${DEFAULT_PROMPT}
    depends_on:
      - ollama
    networks:
      - bot-network
    volumes:
      - bot_logs:/app/logs
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-server
    restart: unless-stopped
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - bot-network
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 5
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  ollama_data:
    driver: local
  bot_logs:
    driver: local

networks:
  bot-network:
    driver: bridge
```

5. Click **Deploy the stack**

### Option B: Build from Source

If you prefer to build from source (for customizations):

1. **Clone the repository** to your server or use Git in Portainer
2. **Use build context** in Portainer stack:
   - **Repository URL**: `https://github.com/nomore1007/telegram-ollama-bot.git`
   - **Compose path**: `docker-compose.yml`

## Step 4: Configure Environment Variables

### In Portainer Stack:
1. After creating the stack, click on it
2. Go to **Environment** tab
3. Add all required environment variables

### Using .env File:
If you created a volume with .env file:
1. Mount the volume in the telegram-bot service:
```yaml
volumes:
  - telegram-bot-env:/.env
```

## Step 5: Pull Ollama Models

After deployment, you need to download AI models:

1. Go to **Containers** in Portainer
2. Find `ollama-server` container
3. Click **Console** → **Connect**
4. Run: `ollama pull llama2`

## Step 6: Monitor Deployment

### Check Container Status:
1. Go to **Containers** section
2. Verify both containers are **running** (green status)
3. Check **logs** for any errors

### Health Checks:
- **telegram-bot**: Should show healthy status
- **ollama**: Should show healthy after model download

### View Logs:
1. Click on container → **Logs**
2. Monitor for successful startup messages

## Step 7: Test the Bot

1. **Message your bot** on Telegram
2. **Send a test message** like "Hello"
3. **Check Portainer logs** for bot activity

## Troubleshooting

### Bot Not Responding:
```
Portainer → telegram-bot container → Logs
```
Look for connection errors or missing environment variables.

### Ollama Issues:
```
Portainer → ollama-server container → Console
ollama list  # Check if models are downloaded
```

### Environment Variables:
```
Portainer → Stacks → telegram-ollama-bot → Environment
```
Verify all variables are set correctly.

## Management

### Update Deployment:
1. **Pull latest changes** from GitHub
2. **Rebuild stack** in Portainer
3. **Redeploy** with updated configuration

### Scale Services:
- **telegram-bot**: Can run multiple instances behind a load balancer
- **ollama**: Usually single instance, but can be scaled with shared volume

### Backup:
- **Ollama models**: Backup `ollama_data` volume
- **Bot logs**: Backup `bot_logs` volume
- **Configuration**: Export stack configuration

## Security Notes

- **Environment variables** contain sensitive data - keep secure
- **Network isolation** - services communicate internally only
- **Regular updates** - keep Docker images updated
- **Access control** - limit Portainer access appropriately

---

**🎉 Your Telegram Ollama Bot is now deployed via Portainer!**