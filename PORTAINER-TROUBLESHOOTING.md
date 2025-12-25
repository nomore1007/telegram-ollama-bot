# 🚀 Alternative Portainer Deployment Methods

## Method 1: Build from Source (Recommended)

Since the pre-built image doesn't exist yet, build directly from the GitHub repository:

### In Portainer:

1. **Stacks** → **Add Stack**
2. **Name:** `telegram-bot`
3. **Repository URL:** `https://github.com/nomore1007/telegram-ollama-bot.git`
4. **Compose path:** `docker-compose.bot-only.yml`
5. **Environment variables:**
   - `TELEGRAM_BOT_TOKEN=your_token_here`
   - `OLLAMA_HOST=http://host.docker.internal:11434` (adjust as needed)
6. **Deploy the stack**

This will build the image from source in Portainer.

## Method 2: Local Build First

### Build locally and push to your registry:

```bash
# Clone the repository
git clone https://github.com/nomore1007/telegram-ollama-bot.git
cd telegram-ollama-bot

# Build the image
docker build -t telegram-ollama-bot:latest .

# Tag for your registry (if you have one)
# docker tag telegram-ollama-bot:latest your-registry.com/telegram-ollama-bot:latest

# Push to registry
# docker push your-registry.com/telegram-ollama-bot:latest

# Then use in Portainer: your-registry.com/telegram-ollama-bot:latest
```

## Method 3: Direct Docker Run (For Testing)

### Test the bot directly with Docker:

```bash
# Run the bot container directly
docker run -d \
  --name telegram-bot \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama2 \
  -v bot_logs:/app/logs \
  --network bridge \
  telegram-ollama-bot:latest
```

## Method 4: Simplified Compose for Portainer

If the above doesn't work, use this minimal compose:

```yaml
version: '3.8'

services:
  telegram-bot:
    build:
      context: https://github.com/nomore1007/telegram-ollama-bot.git
      dockerfile: Dockerfile
    container_name: deepthought-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OLLAMA_HOST=${OLLAMA_HOST}
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

## Troubleshooting Steps

### 1. Check Portainer Logs
- Go to **Stacks** → Click on your stack → **Logs**
- Look for build errors or deployment failures

### 2. Verify GitHub Access
```bash
# Test if GitHub repo is accessible
curl -s https://api.github.com/repos/nomore1007/telegram-ollama-bot | head -5
```

### 3. Check Environment Variables
- Ensure `TELEGRAM_BOT_TOKEN` is set correctly
- Verify `OLLAMA_HOST` points to your Ollama instance

### 4. Network Connectivity
```bash
# Test Ollama connection from your machine
curl http://localhost:11434/api/tags
```

### 5. Portainer Permissions
- Ensure your Portainer user has permissions to deploy stacks
- Check if Docker socket is properly mounted in Portainer

## Alternative: Manual Docker Commands

If Portainer continues to fail, deploy manually:

```bash
# 1. Clone repository
git clone https://github.com/nomore1007/telegram-ollama-bot.git
cd telegram-ollama-bot

# 2. Create .env file
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env
echo "OLLAMA_HOST=http://host.docker.internal:11434" >> .env

# 3. Build and run
docker-compose -f docker-compose.bot-only.yml --env-file .env up -d

# 4. Check status
docker ps
docker logs deepthought-bot
```

## Quick Fix Options

### Option A: Use Docker Hub Image
If you build and push to Docker Hub, use:
```yaml
image: your-dockerhub-username/telegram-ollama-bot:latest
```

### Option B: Build Context in Portainer
Use the **Web editor** with build context:
```yaml
services:
  telegram-bot:
    build:
      context: https://github.com/nomore1007/telegram-ollama-bot.git
    # ... rest of config
```

### Option C: Pre-built Alternative
Use a similar bot image or build locally first.

---

**Try Method 1 first** - building from source in Portainer should work since the repository and Dockerfile are accessible.