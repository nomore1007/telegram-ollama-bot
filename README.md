# Telegram Ollama Bot

A Python bot that interfaces Telegram with a hosted Ollama LLM.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables or copy `settings.example.py` to `settings.py`:
- Get a Telegram bot token from @BotFather
- Set your Ollama host URL
- Choose your preferred model

### Environment Variables
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2
BOT_USERNAME=YourBotName
TIMEOUT=30
DEFAULT_PROMPT=Your custom prompt
```

4. Run the bot:
```bash
python bot.py
```

## Commands

- `/start` - Start the bot
- `/help` - Show help message  
- `/model` - Display current AI model info

## Security

Configuration uses environment variables. The `settings.py` file is excluded from version control. Never commit actual credentials.

### Security Features
- **Input Validation**: Sanitizes user inputs to prevent injection attacks
- **Rate Limiting**: Prevents abuse with configurable request limits per user
- **URL Validation**: Blocks dangerous URLs and localhost access
- **Content Sanitization**: Prevents markdown and HTML abuse

## Architecture

The bot is organized into modular components:
- `bot.py`: Main application and message routing
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