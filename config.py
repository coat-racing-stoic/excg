import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    fixedfloat_api_key: Optional[str] = os.getenv("FIXEDFLOAT_API_KEY")
    fixedfloat_api_secret: Optional[str] = os.getenv("FIXEDFLOAT_API_SECRET")
    
    # Server Configuration
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "12000"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "250"))
    rate_limit_create_order_weight: int = int(os.getenv("RATE_LIMIT_CREATE_ORDER_WEIGHT", "50"))
    rate_limit_default_weight: int = int(os.getenv("RATE_LIMIT_DEFAULT_WEIGHT", "1"))
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = os.getenv("LOG_DIR", "logs")
    log_api_requests: bool = os.getenv("LOG_API_REQUESTS", "True").lower() == "true"
    log_api_responses: bool = os.getenv("LOG_API_RESPONSES", "True").lower() == "true"
    log_fixedfloat_requests: bool = os.getenv("LOG_FIXEDFLOAT_REQUESTS", "True").lower() == "true"
    log_fixedfloat_responses: bool = os.getenv("LOG_FIXEDFLOAT_RESPONSES", "True").lower() == "true"
    log_request_data: bool = os.getenv("LOG_REQUEST_DATA", "True").lower() == "true"
    log_response_data: bool = os.getenv("LOG_RESPONSE_DATA", "False").lower() == "true"  # По умолчанию выключено для безопасности
    
    class Config:
        env_file = ".env"

settings = Settings()