import os
from typing import List, Optional
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Конфигурация приложения с валидацией"""
    
    # Telegram
    telegram_bot_token: SecretStr
    telegram_webhook_url: Optional[str] = None
    telegram_webhook_secret: Optional[str] = None
    
    # OpenRouter API
    openrouter_api_key: SecretStr
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-4o-mini"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: SecretStr
    allowed_user_ids: str = ""
    rate_limit_messages: int = 10
    rate_limit_window: int = 60
    
    # Monitoring
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None
    metrics_port: int = 8000
    
    # External Services
    rag_service_url: Optional[str] = None
    rag_service_api_key: Optional[SecretStr] = None
    external_services_timeout: int = 30
    
    # Development
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @field_validator('allowed_user_ids')
    @classmethod
    def parse_allowed_users(cls, v):
        if not v:
            return []
        return [int(user_id.strip()) for user_id in v.split(',')]
    
    @field_validator('telegram_bot_token', 'openrouter_api_key', 'secret_key')
    @classmethod
    def validate_secrets(cls, v):
        if not v or len(v.get_secret_value()) < 10:
            raise ValueError('Secret is too short or empty')
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

# Глобальный экземпляр настроек
settings = Settings()