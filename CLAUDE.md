# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot project that integrates LLM (Large Language Model) capabilities with PostgreSQL database functionality. The project follows a comprehensive implementation plan outlined in "Telegram Bot Local LLM Markdown.md" - a detailed guide for building a modern, scalable Telegram bot with OpenRouter API integration.

## Architecture Blueprint

Based on the implementation plan, the project will follow this architecture:

**Technology Stack:**
- **aiogram 3.x** - Modern async Telegram Bot API framework
- **OpenRouter API** - Unified access to various LLM models
- **Poetry** - Modern Python dependency management
- **Docker & Kubernetes** - Containerization and orchestration
- **Redis** - Caching and state management
- **PostgreSQL** - Dialog data storage
- **Prometheus/Grafana** - Monitoring and metrics

**Planned Structure:**
```
src/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration with Pydantic
│   ├── handlers/            # Command handlers (commands.py, messages.py, callbacks.py)
│   ├── middlewares/         # Auth, logging, throttling
│   ├── services/           # Business logic (openrouter.py, context.py, llm.py)
│   ├── database/           # SQLAlchemy models, repositories
│   ├── keyboards/          # Inline and reply keyboards
│   ├── utils/              # Formatting, security, monitoring
│   └── filters/            # Custom filters
└── monitoring/
    ├── health.py           # Health checks
    └── metrics.py          # Prometheus metrics
```

## Development Setup Commands

**Initial Setup:**
```bash
# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Initialize project with Poetry
poetry init
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your tokens and configuration
```

**Development Commands:**
```bash
# Install dependencies
poetry install

# Run the bot in development mode
poetry run python -m bot.main

# Code formatting and linting
poetry run black src/
poetry run flake8 src/
poetry run mypy src/

# Run tests
poetry run pytest

# Docker development environment
docker-compose up -d
docker-compose logs -f bot
```

**Docker Commands:**
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f bot

# Restart services
docker-compose restart bot

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

## Key Configuration Files

**Environment Variables (.env):**
- `TELEGRAM_BOT_TOKEN` - Telegram bot token from BotFather
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM access
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Application secret key
- `ALLOWED_USER_IDS` - Comma-separated list of allowed user IDs

**Dependencies (pyproject.toml):**
Key dependencies include aiogram 3.21.0+, aiohttp, redis, sqlalchemy 2.0+, pydantic 2.7+, loguru, prometheus-client.

## Architecture Principles

**Async/Await Pattern:** All I/O operations use async/await for better performance
**Middleware Stack:** Authentication, rate limiting, and logging are handled via middleware
**Service Layer:** Business logic is separated into service classes (OpenRouter client, context management, LLM services)
**Repository Pattern:** Database operations are abstracted through repository classes
**Configuration Management:** Environment-specific settings managed through Pydantic settings
**Error Handling:** Comprehensive error handling with retry mechanisms and logging
**Security:** Input validation, rate limiting, and secure secret management

## Development Workflow

1. **Start with Docker Compose** for local development with Redis and PostgreSQL
2. **Follow the implementation plan** in "Telegram Bot Local LLM Markdown.md" for feature development
3. **Use Poetry** for dependency management and virtual environment
4. **Implement tests** for all new functionality
5. **Monitor metrics** via Prometheus endpoints during development
6. **Use pre-commit hooks** for code quality

## Testing Strategy

- Unit tests for service layer components
- Integration tests for database operations
- Mock testing for external API calls (Telegram, OpenRouter)
- Health check endpoints for monitoring

## Deployment

The project is designed for containerized deployment with:
- Multi-stage Docker builds for optimization
- Health checks and monitoring endpoints
- CI/CD pipeline with GitHub Actions
- Production-ready docker-compose configuration
- Systemd service configuration for server deployment