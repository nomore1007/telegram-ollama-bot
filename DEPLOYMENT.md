# 🚀 Telegram Ollama Bot - Deployment Guide

## Quick Start (3 minutes)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd deepthought-bot
cp .env.example .env

# 2. Configure your bot token
# Edit .env file and add your TELEGRAM_BOT_TOKEN

# 3. Deploy
make build && make up

# 4. Check it's working
make logs
```

## 📋 Prerequisites

- **Docker & Docker Compose** installed
- **4GB+ RAM** recommended for Ollama models
- **Telegram Bot Token** from [@BotFather](https://t.me/botfather)

## 🛠️ Complete Setup Guide

### Step 1: Get Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the API token (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Step 2: Clone Repository

```bash
git clone <your-repository-url>
cd deepthought-bot
```

### Step 3: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

**Required settings in .env:**
```bash
TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
```

**Optional settings (with defaults):**
```bash
BOT_USERNAME=DeepthoughtBot
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama2
TIMEOUT=30
```

### Step 4: Deploy with Docker

```bash
# Build containers (first time only)
make build

# Start services
make up

# Check status
make health
```

### Step 5: Verify Deployment

```bash
# Check logs
make logs

# Test bot functionality
# Send a message to your bot on Telegram
```

## 📊 Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  telegram-bot   │    │     ollama      │
│                 │◄──►│                 │
│ • Python 3.11   │    │ • llama2        │
│ • Telegram API  │    │ • mistral       │
│ • AI features   │    │ • codellama     │
│ • Security      │    │                 │
└─────────────────┘    └─────────────────┘
```

## 🛠️ Management Commands

### Basic Operations
```bash
make up          # Start all services
make down        # Stop all services
make restart     # Restart services
make logs        # View all logs
```

### Development
```bash
make dev         # Development mode (live reload)
make shell       # Access bot container
make test        # Run tests
```

### Maintenance
```bash
make build       # Rebuild containers
make clean       # Remove containers & volumes
make health      # Check service status
make pull        # Update Ollama image
```

## 🔧 Manual Docker Commands

```bash
# Build and run
docker-compose build
docker-compose up -d

# View specific logs
docker-compose logs -f telegram-bot
docker-compose logs -f ollama

# Stop and cleanup
docker-compose down
docker-compose down -v  # Remove data volumes
```

## 🌐 Network Configuration

- **Bot Container**: Accessible via Telegram API
- **Ollama Container**: Internal network only (port 11434)
- **Default Network**: `bot-network` (Docker bridge)

## 💾 Data Persistence

- **Ollama Models**: Stored in `ollama_data` volume
- **Bot Logs**: Mounted to `./logs/` directory
- **Configuration**: Environment variables (no persistent state)

## 🚨 Troubleshooting

### Bot Not Responding
```bash
# Check logs
make logs-bot

# Verify token
docker-compose exec telegram-bot env | grep TELEGRAM

# Test connectivity
docker-compose exec telegram-bot python -c "import telegram; print('OK')"
```

### Ollama Issues
```bash
# Check Ollama status
make logs-ollama

# List available models
docker-compose exec ollama ollama list

# Pull a model manually
docker-compose exec ollama ollama pull llama2
```

### Common Issues

**"Invalid token" error:**
- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Ensure no extra spaces or quotes

**"Connection refused" to Ollama:**
- Wait for Ollama to fully start (check logs)
- Verify `OLLAMA_HOST` is set to `http://ollama:11434`

**Out of memory:**
- Increase Docker memory limit to 4GB+
- Use smaller models (llama2:7b instead of 13b)

## 🔒 Security Considerations

- **Environment Variables**: Never commit `.env` file
- **Network Isolation**: Services communicate internally only
- **Non-root User**: Bot runs as unprivileged user
- **Input Validation**: Built-in security against malicious inputs
- **Rate Limiting**: Automatic abuse prevention

## 📈 Monitoring & Logs

```bash
# Real-time logs
make logs

# Bot-specific logs
docker-compose logs -f telegram-bot

# System resource usage
docker stats

# Container health
docker-compose ps
```

## 🚀 Production Deployment

For production environments:

### 1. SSL/TLS Setup
```bash
# Use reverse proxy (nginx/caddy)
# Configure SSL certificates
# Set up domain name
```

### 2. Resource Limits
```yaml
# Add to docker-compose.yml
services:
  telegram-bot:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
```

### 3. Backup Strategy
```bash
# Backup Ollama models
docker run --rm -v ollama_data:/source -v $(pwd)/backup:/backup \
  alpine tar czf /backup/ollama-models-$(date +%Y%m%d).tar.gz -C /source .
```

### 4. High Availability
- Run multiple bot instances behind load balancer
- Use Redis for session storage (available in dev mode)
- Implement health checks and auto-healing

## 📞 Support

**Logs to check:**
- `make logs` - All service logs
- `docker-compose ps` - Container status
- `docker system df` - Disk usage

**Common commands:**
```bash
# Full reset
make clean && make build && make up

# Update deployment
git pull && make build && make restart

# Debug mode
make shell  # Access container directly
```

## 📝 File Reference

| File | Purpose | Required |
|------|---------|----------|
| `Dockerfile` | Bot container definition | ✅ |
| `docker-compose.yml` | Service orchestration | ✅ |
| `.env` | Environment configuration | ✅ |
| `Makefile` | Command shortcuts | ✅ |
| `requirements.txt` | Python dependencies | ✅ |
| `.dockerignore` | Build optimization | ✅ |

---

**🎉 Happy deploying! Your AI-powered Telegram bot is ready to chat, summarize news, and analyze YouTube videos.**