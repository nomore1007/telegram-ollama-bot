# AGENTS.md - Internal Development Guide

## Project Structure & Development Guidelines

### Architecture Overview

This Telegram Ollama Bot follows a modular architecture designed for maintainability and scalability:

```
telegram-ollama-bot/
├── bot.py              # Main application entry point
├── handlers.py         # Telegram command/callback handlers
├── summarizers.py      # Content processing (News/YouTube)
├── ollama_client.py    # AI model communication
├── conversation.py     # Chat context management
├── security.py         # Input validation & rate limiting
├── constants.py        # Configuration constants
└── tests/              # Test suite
```

### Development Guidelines

#### Code Style
- **Python 3.11+** compatible
- **Type hints** for all function parameters
- **Docstrings** for all public functions
- **Logging** for debugging and monitoring
- **Error handling** with appropriate exception types

#### Security
- **Environment variables** for all sensitive data
- **Input validation** for all user inputs
- **Rate limiting** to prevent abuse
- **URL sanitization** to prevent malicious links

#### Testing
- **Unit tests** for core functionality
- **Integration tests** for API interactions
- **Docker-based testing** for deployment validation

### Deployment

#### Docker Setup
- **Multi-stage builds** for optimization
- **Security hardening** with non-root user
- **Health checks** for service monitoring
- **Volume management** for data persistence

#### Production Considerations
- **SSL/TLS** for secure communication
- **Resource limits** to prevent abuse
- **Logging aggregation** for monitoring
- **Backup strategies** for data protection

### API Integrations

#### Telegram Bot API
- Commands: `/start`, `/help`, `/model`, `/setmodel`, `/timeout`
- Callbacks: Menu navigation and model selection
- Message types: Text, URLs (auto-detection)

#### Ollama API
- Model management: List, switch models
- Text generation: With retry logic and timeouts
- Error handling: Graceful degradation

#### External APIs
- **Newspaper3k**: Article extraction and parsing
- **YouTube Transcript API**: Video transcript retrieval
- **Pytube**: Video metadata extraction

### Monitoring & Debugging

#### Logging Levels
- **DEBUG**: Detailed development information
- **INFO**: General operational messages
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors requiring attention

#### Health Checks
- Container health via `/health` endpoints
- Service connectivity verification
- Resource usage monitoring

### Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Implement** changes with tests
4. **Update** documentation
5. **Submit** pull request

### Future Enhancements

- **Multi-language support** (i18n)
- **Plugin system** for extensibility
- **Database integration** for persistence
- **Webhook support** for real-time updates
- **Analytics** for usage tracking

---

*This document is for internal development reference and may be updated as the project evolves.*