# Telegram Ollama Bot

# 🤖 Deepthought Bot

A multi-platform AI assistant bot supporting Telegram and Discord, with pluggable architecture and multiple LLM providers.

## ✨ Features

- **Multi-Platform**: Works on both Telegram and Discord
- **Multiple LLM Providers**: Ollama, OpenAI, Groq, and more
- **Plugin System**: Extensible architecture for custom features
- **Admin Controls**: Restricted settings management
- **Auto-Content Processing**: News article and YouTube video summarization
- **Web Search**: AI-powered web search capabilities
- **Conversation Memory**: Context-aware chat sessions

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/nomore1007/telegram-ollama-bot.git
cd telegram-ollama-bot
pip install -r requirements.txt
```

### 2. Configuration

Copy and edit the settings file:
```bash
cp settings.example.py settings.py
```

Configure your preferred settings in `settings.py` or use environment variables.

### 3. Run the Bot

```bash
python bot.py
```

## ⚙️ Configuration

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather | `123456789:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |

### Optional Settings

| Setting | Description | Default | Example |
|---------|-------------|---------|---------|
| `LLM_PROVIDER` | AI provider: `ollama`, `openai`, `groq` | `ollama` | `openai` |
| `OLLAMA_MODEL` | Default Ollama model | `llama2` | `mistral` |
| `OPENAI_API_KEY` | OpenAI API key | - | `sk-...` |
| `GROQ_API_KEY` | Groq API key | - | `gsk_...` |
| `DISCORD_BOT_TOKEN` | Discord bot token | - | `MTIz...` |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | `[]` | `123456789,987654321` |
| `ENABLED_PLUGINS` | Active plugins | `telegram,web_search,discord` | `telegram,discord` |
| `TIMEOUT` | Request timeout (seconds) | `30` | `60` |
| `DEFAULT_PROMPT` | System prompt for AI | Custom prompt | - |

### Environment Variables

All settings can be configured via environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_token"
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="sk-..."
export ADMIN_USER_IDS="123456789"
```

## 🤖 Commands

### Public Commands (All Users)

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and available commands |
| `/help` | Display comprehensive help information |
| `/menu` | Show interactive menu |
| `/userid` | Display your Telegram user ID |

### AI Interaction

| Command | Description |
|---------|-------------|
| `/ask <message>` | Ask AI a question (Discord: `!ask <message>`) |
| `/search <query>` | Search the web and get AI-powered answer |

### Admin Commands (Admin Only)

| Command | Description |
|---------|-------------|
| `/model` | Show current AI model and provider info |
| `/listmodels` | List all available models for current provider |
| `/changemodel <model>` | Switch AI model |
| `/setprompt` | Set custom AI system prompt |
| `/timeout <seconds>` | Set request timeout |
| `/addadmin <user_id>` | Add new administrator |
| `/removeadmin <user_id>` | Remove administrator |
| `/listadmins` | Show all administrators |

### Discord Commands

| Command | Description |
|---------|-------------|
| `!ask <message>` | Ask AI a question |
| `!model` | Show current model info |
| `!search <query>` | Web search with AI analysis |

## 🔧 LLM Providers

### Supported Providers

1. **Ollama** (Local)
   - Free, local models
   - No API key required
   - Supports custom models

2. **OpenAI** (Cloud)
   - GPT-3.5 Turbo, GPT-4
   - Requires API key
   - Pay-per-use pricing

3. **Groq** (Cloud)
   - Fast inference with Mixtral, Llama models
   - Free tier available
   - Requires API key

### Switching Providers

```bash
# Via environment variable
export LLM_PROVIDER="openai"
export OPENAI_API_KEY="your_key"

# Via settings.py
LLM_PROVIDER = "groq"
GROQ_API_KEY = "your_key"
```

## 🛡️ Security Features

- **Input Validation**: Prevents injection attacks and malicious input
- **Rate Limiting**: Configurable request limits per user
- **URL Sanitization**: Blocks dangerous URLs and localhost access
- **Content Filtering**: Prevents markdown and HTML abuse
- **Admin Controls**: Restricted access to bot settings
- **Environment-Based Config**: Sensitive data stored securely

## 🏗️ Architecture

### Core Components

```
deepthought-bot/
├── bot.py                 # Main application orchestrator
├── llm_client.py          # Multi-provider LLM interface
├── admin.py               # Admin management system
├── plugins/               # Plugin system
│   ├── base.py           # Plugin base classes
│   ├── telegram_plugin.py # Telegram functionality
│   ├── discord_plugin.py  # Discord functionality
│   └── web_search_plugin.py # Web search capabilities
├── summarizers.py        # Content summarization
├── conversation.py       # Chat context management
├── constants.py          # Application constants
└── settings.example.py   # Configuration template
```

### Plugin System

The bot uses a modular plugin architecture:

- **Plugin Base Class**: Common interface for all plugins
- **Dynamic Loading**: Plugins loaded at runtime
- **Event Hooks**: Message processing, commands, callbacks
- **Configuration**: Per-plugin settings support

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d

# Or build manually
docker build -t deepthought-bot .
docker run -e TELEGRAM_BOT_TOKEN="your_token" deepthought-bot
```

### Cloud Deployment

- **Railway**: Easy one-click deployment
- **Fly.io**: Global deployment with Ollama support
- **Heroku**: Traditional cloud platform
- **AWS/GCP**: Scalable infrastructure

## 🔌 Extending the Bot

### Creating Custom Plugins

1. **Inherit from Plugin base class**:
```python
from plugins.base import Plugin

class MyPlugin(Plugin):
    def __init__(self, name: str, config: dict = None):
        super().__init__(name, config)

    def initialize(self, bot_instance):
        self.bot = bot_instance

    def get_commands(self):
        return ["mycommand"]

    async def handle_mycommand(self, update, context):
        await update.message.reply_text("Hello from my plugin!")
```

2. **Add to plugin loading in `bot.py`**:
```python
plugin_manager.load_plugin("myplugin", MyPlugin, {})
plugin_manager.enable_plugin("myplugin")
```

3. **Enable in configuration**:
```python
ENABLED_PLUGINS = "telegram,discord,myplugin"
```

## 📊 Monitoring & Analytics

- **Usage Statistics**: Command usage, response times
- **Performance Metrics**: LLM response times, error rates
- **User Analytics**: Active users, message counts
- **Plugin Metrics**: Feature usage tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integration
- [discord.py](https://github.com/Rapptz/discord.py) for Discord support
- [Ollama](https://ollama.ai/) for local AI models
- All contributors and the open-source community
- `handlers.py`: Telegram command and callback handlers
- `summarizers.py`: News and YouTube content processing
- `ollama_client.py`: AI model communication
- `conversation.py`: Chat history management
- `security.py`: Input validation and rate limiting
- `constants.py`: Configuration constants

### Docker Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   telegram-bot  │    │     ollama      │
│   (Python app)  │◄──►│  (AI models)    │
│                 │    │                 │
│ • Message       │    │ • llama2        │
│   handling      │    │ • mistral       │
│ • Content       │    │ • codellama     │
│   summarization │    │                 │
│ • Security      │    └─────────────────┘
│ • Conversation  │
│   context       │
└─────────────────┘
```

**Container Services:**
- **telegram-bot**: Main application container
- **ollama**: AI model server with automatic model downloading
- **redis** (dev): Optional caching and session storage

## Testing

Run tests with:
```bash
pytest
```

Run specific tests:
```bash
pytest tests/test_bot.py::TestNewsSummarizer::test_extract_urls_news_sites
```

## Docker Deployment

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd deepthought-bot
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram bot token and configuration
   ```

3. **Deploy with Docker Compose:**
   ```bash
   make setup    # Create .env file
   make build    # Build containers
   make up       # Start services
   ```

### Environment Configuration

Create a `.env` file with your configuration:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Optional (with defaults)
BOT_USERNAME=DeepthoughtBot
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama2
TIMEOUT=30
```

### Docker Commands

```bash
# Basic operations
make up          # Start all services
make down        # Stop all services
make logs        # View logs
make restart     # Restart services

# Development
make dev         # Start in development mode
make shell       # Access bot container shell
make test        # Run tests in container

# Maintenance
make build       # Rebuild containers
make clean       # Remove containers and volumes
make health      # Check service health
```

### Manual Docker Commands

```bash
# Build and run
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f telegram-bot
docker-compose logs -f ollama

# Stop and cleanup
docker-compose down
docker-compose down -v  # Remove volumes too
```

### Architecture

The Docker setup includes:

- **telegram-bot**: Main bot application
- **ollama**: AI model server (auto-downloads models)
- **redis** (dev): Optional caching layer

### Production Deployment

For production:

1. Use a reverse proxy (nginx/caddy) for SSL
2. Configure proper logging and monitoring
3. Set up automated backups
4. Use Docker secrets for sensitive data
5. Configure resource limits

### Troubleshooting

**Bot not responding:**
```bash
make logs-bot
# Check for connection errors or missing environment variables
```

**Ollama not working:**
```bash
make logs-ollama
# Check if models are downloaded: docker-compose exec ollama ollama list
```

**Permission issues:**
```bash
# Ensure .env file permissions are correct
chmod 600 .env
```

## Features

- 🤖 **AI Chat**: Conversational AI with conversation history and context
- 📰 **News Summarization**: Automatic detection and AI-powered summaries of news articles
- 🎬 **YouTube Summarization**: Video transcript extraction and summarization
- 🔒 **Security**: Input validation, rate limiting, and content sanitization
- 💬 **Context Awareness**: Maintains conversation history for better responses
- ⚙️ **Model Management**: Switch between different Ollama models
- 🎛️ **Interactive Menus**: User-friendly command interface