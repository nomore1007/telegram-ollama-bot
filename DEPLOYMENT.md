# 🚀 Telegram Ollama Bot - Deployment Guide

This guide provides instructions for deploying the Deepthought Bot using Docker and Docker Compose. This deployment assumes you have an **existing Ollama AI service** running elsewhere and you want the bot to connect to it.

## 📋 Prerequisites

-   **Docker & Docker Compose** installed
-   **An existing Ollama AI Service** running and accessible from where the bot will be deployed.
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

The bot uses environment variables and/or a `settings.py` file for configuration. It's recommended to manage `settings.py` within a persistent host directory for easier updates and portability.

Create a `.env` file in the project root to store your primary environment variables.

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

**Required Settings in `.env`:**

*   `TELEGRAM_BOT_TOKEN=your_actual_bot_token_here` (Replace with the token you got from @BotFather)
*   `OLLAMA_HOST=http://your_ollama_ip:11434` (This **must** be set to the address of your existing Ollama instance.)

**Important: Initializing `settings.py` within the persistent host directory**

For advanced configuration (e.g., plugin settings, complex personality prompts) or if you prefer file-based configuration over environment variables, you'll need a `settings.py` file. This file should be placed within the host directory `/opt/telegram-ollama-bot`.

If `settings.py` doesn't exist in this directory, the bot will use `settings.example.py` for defaults. To create your custom `settings.py`:

1.  **Ensure the host directory exists:**
    ```bash
    sudo mkdir -p /opt/telegram-ollama-bot
    sudo chown -R $USER:$USER /opt/telegram-ollama-bot # Adjust ownership as needed
    ```
2.  **Copy `settings.example.py` to the host directory:**
    ```bash
    cp settings.example.py /opt/telegram-ollama-bot/settings.py
    ```
3.  **Edit `settings.py` directly on your host machine:**
    ```bash
    nano /opt/telegram-ollama-bot/settings.py # or your preferred editor
    ```

**Other Optional Settings (with defaults):**

```bash
BOT_USERNAME=DeepthoughtBot
OLLAMA_MODEL=llama2
TIMEOUT=30
```

## Step 4: Deploy the Bot

This will deploy the bot as a standalone service, connecting to your specified external Ollama instance.

```bash
# Build bot container (first time or after code changes)
docker-compose build

# Start bot service
docker-compose up -d
```

## Step 5: Verify Deployment

*   **Check container status:**
    ```bash
    docker-compose ps
    ```
    Ensure your `telegram-bot` container is in the `Up` state.

*   **View logs:**
    ```bash
    docker-compose logs -f
    ```
    Look for messages indicating successful startup and bot activity.

*   **Test bot functionality:** Send a message to your bot on Telegram.

## 🛠️ Management Commands

You can use `docker-compose` commands directly.

### Basic `docker-compose` Operations
```bash
docker-compose up -d   # Start bot service
docker-compose down    # Stop bot service
docker-compose restart # Restart bot service
docker-compose logs -f # View bot logs
```

## 🚨 Troubleshooting

*   **Bot Not Responding:**
    *   Check `TELEGRAM_BOT_TOKEN` in your `.env` file (or Portainer environment variables).
    *   View container logs for errors.
*   **"Connection refused" to Ollama:**
    *   Verify `OLLAMA_HOST` in your `.env` (or Portainer environment variables) correctly points to a running Ollama instance, and that network connectivity is allowed from the bot container.
    *   Ensure your Ollama instance is actually running and accessible at the specified host and port.

## 💾 Data Persistence

*   **Bot Logs:** Stored in `bot_logs` volume.
*   **Configuration & Database:** Stored in the host directory `/opt/telegram-ollama-bot`. This includes `settings.py` and `deepthought_bot.db`.

## 🔒 Security Considerations

*   **Environment Variables**: Never commit your `.env` file to version control.
*   **Network Isolation**: Docker Compose creates isolated networks by default.
*   **Non-root User**: The bot runs as an unprivileged user within its container.

---

**🎉 Happy deploying! Your AI-powered Telegram bot is ready to chat.**