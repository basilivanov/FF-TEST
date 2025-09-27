# Current Technology Stack

## Backend
- **Python 3.12** with type hints (`from __future__ import annotations`)
- **FastAPI** with prefix="/api/v1" 
- **SQLAlchemy** + Alembic for database
- **SQLite** for data storage
- **httpx** for async HTTP calls (connect=3s, read=10s timeouts)
- **tenacity** for retries with jitter
- **structlog** for JSON logging
- **pydantic-settings** for configuration

## Frontend
- **React** with TypeScript
- **Tailwind CSS** for styling
- **Modern React patterns** (hooks, functional components)

## Testing
- **pytest** for Python testing
- **TestClient** for API testing
- **Coverage** requirements ≥70% for critical paths

## Integrations
- **Telegram Bot API** for notifications
- **External APIs** (various providers)
- **LLM providers** (Anthropic, OpenAI, Gemini, Qwen)

## Development Standards
- **PEP8** compliance
- **Type annotations** mandatory
- **Async/await** patterns
- **Error handling** with proper exceptions
- **Transaction batching** for database operations
- **Secrets management** via environment variables