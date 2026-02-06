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

The bot uses environment variables and/or a `config.py` file for configuration. It's recommended to manage `config.py` within a persistent host directory for Docker deployments, or the current working directory for local runs.

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

**Optional Environment Variables for Configuration Directories:**

*   `BOT_CONFIG_DIR`: This variable controls where `config.py` and the `deepthought_bot.db` database file are stored.
    *   **Inside Docker:** This is automatically set by `docker-compose.yml` to `/app/data`.
    *   **Outside Docker:** If not set, it defaults to the directory where the bot is run. You can explicitly set it if you want to store config/DB in a different location (e.g., `export BOT_CONFIG_DIR=/path/to/my/config`).
*   `BOT_APP_SOURCE_DIR`: This variable controls where the application expects to find its source code and `config.example.py`.
    *   **Inside Docker:** This is automatically set by `docker-compose.yml` to `/app`.
    *   **Outside Docker:** If not set, it defaults to the directory where the `settings_manager.py` script is located. You generally won't need to change this.

## 🔒 Security Considerations

*   **Environment Variables**: Never commit your `.env` file to version control.
*   **Host Network Mode**: The container shares the network stack of the host. This can expose container ports to the host's network interfaces directly and bypass network isolation. Ensure you understand the implications of this.
*   **Non-root User**: The bot runs as an unprivileged user within its container.

---

**🎉 Happy deploying! Your AI-powered Telegram bot is ready to chat.**