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

## 🚨 Troubleshooting

*   **Bot Not Responding:**
    *   Check `TELEGRAM_BOT_TOKEN` in your `.env` file (or Portainer environment variables).
    *   View container logs for errors.
*   **Network Connectivity Issues / "Connection refused" to Ollama / `telegram.error.TimedOut`:**
    *   **Is Ollama running?** Verify your Ollama instance is actually running and accessible at the specified `OLLAMA_HOST`.
    *   **Check `OLLAMA_HOST`:** Ensure `OLLAMA_HOST` in your `.env` (or Portainer environment variables) correctly points to your running Ollama instance.
    *   **Debug from inside the container:** If the bot keeps restarting due to network errors, you might need to temporarily run a shell in the container for debugging.
        1.  Stop the `deepthought-bot` container in Portainer.
        2.  Edit the stack in Portainer, changing the `command` for the `telegram-bot` service to `/bin/bash` (e.g., `command: /bin/bash`). Redeploy.
        3.  Access the container's console via Portainer.
        4.  Run network diagnostics:
            *   `ping -c 3 8.8.8.8` (Test external IP connectivity)
            *   `ping -c 3 google.com` (Test DNS resolution)
            *   `curl -v https://api.telegram.org` (Test HTTPS connectivity to Telegram API)
            *   `cat /etc/resolv.conf` (Check DNS server configuration)
        5.  **Important:** After debugging, revert the `command: /bin/bash` change and redeploy the stack.
*   **`config.py` not created or accessible:**
    *   Check the bot container logs (`docker-compose logs -f`) for output from the `docker-entrypoint.sh` script. Look for messages confirming the copy operation or any reported errors.
    *   **Crucially, ensure the host directory `/opt/telegram-ollama-bot` exists and is writable by the non-root Docker user (app, UID 1000, GID 1000).** The entrypoint script will copy `config.example.py` and then set its ownership and permissions for the `app` user, but it cannot make the *directory itself* writable if the host permissions prevent it).

## 💾 Data Persistence

*   **Bot Logs:** Stored in `bot_logs` volume.
*   **Configuration & Database:** Stored in the host directory `/opt/telegram-ollama-bot`. This includes `config.py` and `deepthought_bot.db`.

## 🔒 Security Considerations

*   **Environment Variables**: Never commit your `.env` file to version control.
*   **Network Isolation**: Docker Compose creates isolated networks by default.
*   **Non-root User**: The bot runs as an unprivileged user within its container.

---

**🎉 Happy deploying! Your AI-powered Telegram bot is ready to chat.**