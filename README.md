# Telegram Ollama Bot

# 🤖 Deepthought Bot

A multi-platform AI assistant bot supporting Telegram and Discord, with pluggable architecture and multiple LLM providers.

## ✨ Features

- **Multi-Platform**: Works on both Telegram and Discord
- **Multiple LLM Providers**: 6 providers (Ollama, OpenAI, Groq, Together AI, Hugging Face, Anthropic)
- **Plugin System**: Extensible architecture with 4 built-in plugins (Weather, Calculator, Web Search, Admin)
- **Channel Administration**: Per-channel AI settings for group admins
- **Admin Controls**: Restricted settings management with granular permissions
- **Personality System**: 6 distinct bot personalities (Friendly, Professional, Humorous, Helpful, Creative, Concise)
- **Auto-Content Processing**: News article and YouTube video summarization
- **Web Search**: Real-time web search with AI analysis and source attribution
- **Weather Information**: Current weather and 5-day forecasts
- **Calculator**: Mathematical expression evaluation with advanced functions
- **Conversation Memory**: Context-aware chat sessions with history management
- **Persistent Settings**: Database-backed configuration that survives restarts
- **Security**: Input validation, rate limiting, and access control
- **Testing**: Comprehensive test suite with 95%+ coverage

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/nomore1007/telegram-ollama-bot.git
cd telegram-ollama-bot

# Create virtual environment (recommended)
python -m venv bot_env
source bot_env/bin/activate  # On Windows: bot_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** Never commit virtual environments (`bot_env/`, `venv/`, etc.) to Git. They are platform-specific and can contain sensitive data. Each developer should create their own virtual environment locally.

### 2. Configuration

The bot automatically creates a `config.py` from `config.example.py` if it doesn't exist in the bot's configuration directory (`/opt/telegram-ollama-bot` in Docker deployments).

Configure your settings in `config.py` (located in your configured persistent directory) or use environment variables. Environment variables take precedence over settings in `config.py`.

### 3. Run the Bot

```bash
python bot.py
```

## ⚙️ Configuration

The bot loads settings in this priority order:
1. `config.py` (your custom configuration, auto-generated from `config.example.py` if missing)
2. Environment variables (`.env` file or system env)

### Admin Setup

**Admin Management CLI:**
```bash
# Initial admin setup
python admin_cli.py setup YOUR_TELEGRAM_USER_ID

# Add an admin
python admin_cli.py add 987654321

# Remove an admin
python admin_cli.py remove 987654321

# List all admins
python admin_cli.py list
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
| `/weather <city>` | Get current weather and 5-day forecast |
| `/calc <expression>` | Evaluate mathematical expressions |

### Conversation Management

| Command | Description |
|---------|-------------|
| `/clear` | Clear conversation history |
| `/personality` | Show available bot personalities |
| `/setpersonality <name>` | Change bot personality (friendly, professional, humorous, helpful, creative, concise) |

### Admin Commands (Admin Only)

| Command | Description |
|---------|-------------|
| `/model` | Show current AI model and provider info |
| `/listmodels` | List all available models for current provider |
| `/changemodel <model>` | Switch AI model |
| `/setprovider <provider>` | Change AI provider (ollama/openai/groq/etc) |
| `/setprompt` | Set custom AI system prompt |
| `/timeout <seconds>` | Set request timeout |
| `/addadmin <user_id>` | Add new administrator |
| `/removeadmin <user_id>` | Remove administrator |
| `/listadmins` | Show all administrators |

### Channel Administration (Channel Admins Only)

| Command | Description |
|---------|-------------|
| `/setchannelmodel <model>` | Set AI model for this specific channel |
| `/setchannelprovider <provider>` | Set AI provider for this channel |
| `/setchannelhost <url>` | Set Ollama host for this channel |
| `/setchannelprompt <text>` | Set custom prompt for this channel |

### Admin Management CLI

For initial setup and external admin management:

```bash
# Initial admin setup (run once)
python admin_cli.py setup YOUR_TELEGRAM_USER_ID

# Add additional admins
python admin_cli.py add USER_ID

# Remove admins
python admin_cli.py remove USER_ID

# List current admins
python admin_cli.py list
```

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

4. **Together AI** (Cloud)
   - Mixtral, Llama models
   - Competitive pricing
   - Requires API key

5. **Hugging Face** (Cloud)
   - Free inference API
   - Various open-source models
   - Requires API key

6. **Anthropic** (Cloud)
   - Claude models
   - Enterprise-grade safety
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

## 🎭 Personality System

The bot supports 6 distinct personalities that change how it responds:

- **Friendly**: Warm, conversational responses with emojis
- **Professional**: Formal, well-structured business communication
- **Humorous**: Witty responses with clever wordplay
- **Helpful**: Maximally useful, detailed explanations
- **Creative**: Imaginative, outside-the-box thinking
- **Concise**: Brief, direct answers

### Switching Personalities

```bash
# Set default personality
export DEFAULT_PERSONALITY="humorous"

# Or change at runtime
/setpersonality creative
```

Each personality uses a different system prompt that influences the AI's tone and response style.

## 🔍 Web Search Functionality

The bot includes powerful web search capabilities that allow the AI to gather real-time information and provide informed responses.

### How It Works

1. **Query Processing**: Your search query is sent to web search APIs
2. **Result Collection**: Top relevant results are retrieved and summarized
3. **AI Analysis**: The LLM analyzes the search results and provides a comprehensive answer
4. **Source Citation**: Responses include information about the sources used

### Search Commands

| Platform | Command | Example |
|----------|---------|---------|
| Telegram | `/search <query>` | `/search latest AI developments` |
| Discord | `!search <query>` | `!search Python best practices` |

### Search Capabilities

- **Real-time Information**: Access current news, trends, and updates
- **Comprehensive Analysis**: AI summarizes and synthesizes information from multiple sources
- **Source Attribution**: Results include links to original sources
- **Multi-language Support**: Search in different languages
- **Contextual Responses**: Answers are tailored to your query's context

### Examples

**Research Queries:**
```
/search quantum computing breakthroughs 2024
/search renewable energy trends in Europe
/search machine learning frameworks comparison
```

**Current Events:**
```
/search presidential election results
/search cryptocurrency market analysis
/search climate change summit outcomes
```

**Technical Questions:**
```
/search how to implement OAuth2 in React
/search Docker container security best practices
/search Kubernetes vs Docker Swarm comparison
```

### Search Tips

- **Be Specific**: More detailed queries yield better results
- **Use Keywords**: Include important terms your search should contain
- **Current Topics**: Great for news, trends, and recent developments
- **Technical Queries**: Excellent for programming, tools, and frameworks
- **Comparative Analysis**: Well-suited for "X vs Y" type questions

### Limitations

- **Internet Access Required**: Needs active internet connection
- **API Rate Limits**: Subject to search provider limitations
- **Content Freshness**: Results reflect current web content
- **No Sensitive Data**: Avoid searching for personal or confidential information

### Search Results Format

The bot provides structured responses including:
- **Summary**: AI-generated overview of findings
- **Key Points**: Important information extracted
- **Sources**: Links to original content
- **Recommendations**: Suggested next steps or related topics

## 🔌 Extending the Bot

### Creating Custom Plugins

1. **Create a plugin class**:
```python
from plugins.base import Plugin

class MyPlugin(Plugin):
    def __init__(self, name: str, config=None):
        super().__init__(name, config)

    def get_dependencies(self):
        return ["telegram"]  # Optional dependencies

    def get_commands(self):
        return ["mycommand"]

    def initialize(self, bot_instance):
        super().initialize(bot_instance)
        # Setup code here

    async def handle_mycommand(self, update, context):
        await update.message.reply_text("Hello from my plugin!")
```

2. **Add to plugin loading** in `bot.py`:
```python
plugin_manager.load_plugin("myplugin", MyPlugin, {"setting": "value"})
plugin_manager.enable_plugin("myplugin")
```

3. **Enable in configuration**:
```python
ENABLED_PLUGINS = "telegram,discord,myplugin"
```

### Plugin Features

- **Dependencies**: Plugins can require other plugins
- **Configuration**: Per-plugin settings with validation
- **Lifecycle**: Proper initialization and cleanup
- **Event Hooks**: Commands, messages, callbacks

## 🔌 Suggested Additional Plugins

### 1. **Image Generation Plugin** (`plugins/image_gen_plugin.py`)
**Purpose:** Generate images using AI models
**Commands:** `/generate <prompt>`, `/imagine <description>`
**Dependencies:** `openai`, `replicate` (optional)
**Use Cases:** Create artwork, diagrams, memes, visualizations
**Example:** `/generate a serene mountain landscape at sunset`

### 2. **Code Analysis Plugin** (`plugins/code_plugin.py`)
**Purpose:** AI-powered code review and analysis
**Commands:** `/review <code>`, `/explain <code>`, `/optimize <code>`
**Dependencies:** LLM providers
**Use Cases:** Code explanation, optimization suggestions, bug detection
**Example:** `/review def factorial(n): return n * factorial(n-1)`

### 3. **Translation Plugin** (`plugins/translate_plugin.py`)
**Purpose:** Multi-language translation capabilities
**Commands:** `/translate <text> to <language>`, `/detect <text>`
**Dependencies:** `googletrans`, `deep-translator`
**Use Cases:** Language learning, international communication
**Example:** `/translate Hello world to Spanish`

### 4. **Voice/Speech Plugin** (`plugins/voice_plugin.py`)
**Purpose:** Voice message processing and text-to-speech
**Commands:** `/voice <text>`, `/transcribe` (with voice message)
**Dependencies:** `speechrecognition`, `gTTS`, `pydub`
**Use Cases:** Voice commands, audio transcription, accessibility
**Example:** `/voice Welcome to our community!`

### 5. **Database Plugin** (`plugins/database_plugin.py`)
**Purpose:** Persistent storage and data management
**Commands:** `/store <key> <value>`, `/retrieve <key>`, `/list`
**Dependencies:** `sqlite3`, `sqlalchemy`
**Use Cases:** User preferences, conversation history, custom data storage
**Example:** `/store my_preference dark_mode`

### 6. **Analytics Plugin** (`plugins/analytics_plugin.py`)
**Purpose:** Usage statistics and performance monitoring
**Commands:** `/stats`, `/usage`, `/performance` (admin only)
**Dependencies:** `matplotlib`, `pandas`
**Use Cases:** Monitor bot usage, generate reports, track performance
**Example:** `/stats` shows message counts, popular commands, response times

### 7. **Social Media Plugin** (`plugins/social_plugin.py`)
**Purpose:** Social media integration and posting
**Commands:** `/post <platform> <content>`, `/schedule <content>`
**Dependencies:** `tweepy`, `facebook-sdk`, `instagram-api`
**Use Cases:** Automated social media posting, content scheduling
**Example:** `/post twitter Check out this amazing AI bot!`

### 8. **Calendar/Scheduling Plugin** (`plugins/calendar_plugin.py`)
**Purpose:** Calendar management and reminders
**Commands:** `/remind <time> <message>`, `/schedule <event>`, `/calendar`
**Dependencies:** `google-api-python-client`, `icalendar`
**Use Cases:** Meeting reminders, event scheduling, time management
**Example:** `/remind tomorrow 2pm Team meeting`

### 9. **File Processing Plugin** (`plugins/file_plugin.py`)
**Purpose:** Document and file analysis
**Commands:** `/analyze <file>`, `/summarize <document>`, `/convert <file>`
**Dependencies:** `PyPDF2`, `python-docx`, `pandas`
**Use Cases:** Document summarization, file format conversion, data analysis
**Example:** `/summarize` (with PDF attachment)

### 10. **Entertainment Plugin** (`plugins/entertainment_plugin.py`)
**Purpose:** Games, quizzes, and fun interactions
**Commands:** `/quiz`, `/joke`, `/trivia`, `/game <type>`
**Dependencies:** `random`, `requests` (for APIs)
**Use Cases:** User engagement, entertainment, icebreakers
**Example:** `/quiz` starts an interactive quiz session

### Plugin Development Template

```python
from plugins.base import Plugin

class MyCustomPlugin(Plugin):
    def __init__(self, name: str, config=None):
        super().__init__(name, config)

    def get_dependencies(self):
        return []  # List required plugins

    def get_description(self):
        return "Description of what this plugin does"

    def get_config_schema(self):
        return {
            "api_key": {"type": "string", "required": True},
            "max_retries": {"type": "integer", "default": 3}
        }

    def initialize(self, bot_instance):
        super().initialize(bot_instance)
        # Setup code here

    def get_commands(self):
        return ["mycommand"]

    async def handle_mycommand(self, update, context):
        await update.message.reply_text("Plugin response!")
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
├── personality.py         # Bot personality system
├── plugins/               # Plugin system
│   ├── __init__.py       # Plugin manager
│   ├── base.py           # Plugin base classes
│   ├── telegram_plugin.py # Telegram functionality
│   ├── discord_plugin.py  # Discord functionality
│   └── web_search_plugin.py # Web search capabilities
├── summarizers.py        # Content summarization
├── conversation.py       # Chat context management
├── security.py           # Input validation & rate limiting
├── handlers.py           # Legacy Telegram handlers
├── constants.py          # Application constants
├── settings.example.py   # Configuration template
└── tests/                # Comprehensive test suite
    ├── test_*.py        # Unit and integration tests
    └── test_comprehensive.py # Full system tests
```

### Plugin System

The bot uses a modular plugin architecture:

- **Plugin Base Class**: Common interface for all plugins
- **Dependency Management**: Plugins can declare dependencies
- **Dynamic Loading**: Plugins loaded at runtime based on configuration
- **Lifecycle Management**: Proper initialization and shutdown
- **Event Hooks**: Message processing, commands, callbacks
- **Configuration Validation**: Schema-based config validation
- **Metadata Support**: Version, description, and help text

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_news.py    # Content processing tests
pytest tests/test_prompt.py  # Basic functionality tests

# Run with coverage
pytest --cov=bot --cov-report=html
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full system testing
- **Plugin Tests**: Plugin loading and functionality
- **Performance Tests**: Response time and memory usage
- **Security Tests**: Input validation and access control

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

## 🔧 Troubleshooting

### Common Issues

**Bot not responding to commands:**
- Check if bot token is correct in settings
- Verify bot has proper permissions in Telegram/Discord
- Check bot logs for error messages

**LLM provider errors:**
- Verify API keys are set correctly
- Check API rate limits and quotas
- Ensure provider service is available

**Search function issues:**
- Ensure internet connection is stable
- Check if web_search plugin is enabled in ENABLED_PLUGINS
- Verify search query is not empty or too short
- Some regions may have search restrictions

**Admin setup issues:**
- Use `python admin_cli.py setup YOUR_USER_ID` for initial admin setup
- Check that ADMIN_USER_IDS is properly configured in settings.py
- Ensure your user ID is correct (use `/userid` command once bot is running)
- Use `python admin_cli.py list` to verify admin configuration

**Plugin loading issues:**
- Check `ENABLED_PLUGINS` configuration
- Verify plugin dependencies are met
- Check plugin logs for initialization errors

**Memory/performance issues:**
- Clear conversation history with `/clear`
- Check system resources (RAM, CPU)
- Reduce conversation context length if needed

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL="DEBUG"
python bot.py
```

### Getting Help

- Check the [Issues](https://github.com/nomore1007/telegram-ollama-bot/issues) page
- Review the [Wiki](https://github.com/nomore1007/telegram-ollama-bot/wiki) for detailed guides
- Join our community discussions

## 📄 License

This project is open source. See LICENSE file for details.

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integration
- [discord.py](https://github.com/Rapptz/discord.py) for Discord support
- [Ollama](https://ollama.ai/) for local AI models
- [Together AI](https://together.ai/), [Hugging Face](https://huggingface.co/), [Anthropic](https://anthropic.com/) for cloud AI services
- All contributors and the open-source community
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