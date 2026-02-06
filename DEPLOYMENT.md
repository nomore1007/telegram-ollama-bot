# 🚀 Telegram Ollama Bot - Deployment Guide

This guide provides instructions for deploying the Deepthought Bot using Docker and Docker Compose. You have two main deployment options:

1.  **Full Stack Deployment:** Deploy both the bot and an Ollama AI service together.
2.  **Bot-Only Deployment:** Deploy only the bot and connect it to an existing, external Ollama AI service.

## 📋 Prerequisites

-   **Docker & Docker Compose** installed
-   **4GB+ RAM** recommended for Ollama models (for Full Stack deployment)
-   **Telegram Bot Token** from [@BotFather](https://t.me/botfather)

## Step 1: Get Telegram Bot Token

1.  Message [@BotFather](https://t.me/botfather) on Telegram.
2.  Send `/newbot`.
3.  Follow instructions to create your bot.
4.  Copy the API token (format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).

## Step 2: Clone Repository

```bash
git clone https://github.com/nomore1007/telegram-ollama-bot.git
cd telegram-ollama-bot
```

## Step 3: Configure Environment Variables

Create a `.env` file in the project root to store your configuration.

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

**Required Setting:**

*   `TELEGRAM_BOT_TOKEN=your_actual_bot_token_here` (Replace with the token you got from @BotFather)

**Important Optional Setting for Bot-Only Deployment:**

*   `OLLAMA_HOST=http://your_ollama_ip:11434` (Only set this if you are using Bot-Only Deployment and have an external Ollama instance. Otherwise, for Full Stack Deployment, you can omit this, and the bot will connect to the Ollama service within the same Docker Compose stack.)

**Other Optional Settings (with defaults):**

```bash
BOT_USERNAME=DeepthoughtBot
OLLAMA_MODEL=llama2
TIMEOUT=30
```

## Step 4: Choose and Deploy Your Stack

### Option 1: Full Stack Deployment (Bot + Ollama)

Use this option if you want Docker Compose to manage both your Telegram bot and its dedicated Ollama AI service.

```bash
# Build containers (first time or after code changes)
docker-compose -f docker-compose.yml build

# Start services
docker-compose -f docker-compose.yml up -d

# After starting, you may need to pull an Ollama model:
# docker-compose exec ollama ollama pull llama2
```

### Option 2: Bot-Only Deployment (Connect to External Ollama)

Use this option if you already have an Ollama AI service running elsewhere (e.g., on your host machine, another server, or a separate Docker container) and you want the bot to connect to it.

**Make sure you have configured `OLLAMA_HOST` in your `.env` file (Step 3).**

```bash
# Build bot container (first time or after code changes)
docker-compose -f docker-compose.bot-only.yml build

# Start bot service
docker-compose -f docker-compose.bot-only.yml up -d
```

## Step 5: Verify Deployment

*   **Check container status:**
    ```bash
    docker-compose ps
    # Or for bot-only:
    docker-compose -f docker-compose.bot-only.yml ps
    ```
    Ensure your `telegram-bot` container (and `ollama` if using full stack) is in the `Up` state.

*   **View logs:**
    ```bash
    docker-compose logs -f
    # Or for bot-only:
    docker-compose -f docker-compose.bot-only.yml logs -f
    ```
    Look for messages indicating successful startup and bot activity.

*   **Test bot functionality:** Send a message to your bot on Telegram.

## 🛠️ Management Commands

You can use `docker-compose` commands directly, or if a `Makefile` is present in the project, it may provide convenient `make` commands as shortcuts.

### Basic `docker-compose` Operations
```bash
# For Full Stack Deployment:
docker-compose -f docker-compose.yml up -d   # Start all services
docker-compose -f docker-compose.yml down    # Stop all services
docker-compose -f docker-compose.yml restart # Restart services
docker-compose -f docker-compose.yml logs -f # View all logs

# For Bot-Only Deployment:
docker-compose -f docker-compose.bot-only.yml up -d
docker-compose -f docker-compose.bot-only.yml down
docker-compose -f docker-compose.bot-only.yml restart
docker-compose -f docker-compose.bot-only.yml logs -f
```

## 🚨 Troubleshooting

*   **Bot Not Responding:**
    *   Check `TELEGRAM_BOT_TOKEN` in your `.env` file.
    *   View container logs for errors.
*   **"Connection refused" to Ollama:**
    *   **Full Stack:** Ensure the `ollama` service is running and healthy within the stack.
    *   **Bot-Only:** Verify `OLLAMA_HOST` in your `.env` correctly points to a running Ollama instance, and that network connectivity is allowed.
*   **Ollama Models:** If using full stack, ensure you have pulled the desired Ollama models (`docker-compose exec ollama ollama pull llama2`).

## 💾 Data Persistence

*   **Ollama Models (Full Stack):** Stored in `ollama_data` volume.
*   **Bot Logs:** Stored in `bot_logs` volume.
*   **Configuration:** Handled via environment variables.

## 🔒 Security Considerations

*   **Environment Variables**: Never commit your `.env` file to version control.
*   **Network Isolation**: Docker Compose creates isolated networks by default.
*   **Non-root User**: The bot runs as an unprivileged user within its container.

---

**🎉 Happy deploying! Your AI-powered Telegram bot is ready to chat.**