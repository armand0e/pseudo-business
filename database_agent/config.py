"""Configuration management for the Database Agent."""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    # Database connection
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/pseudo_business",
        description="Database URL for PostgreSQL connection"
    )
    
    # Connection pool settings
    pool_size: int = Field(default=20, description="Database connection pool size")
    max_overflow: int = Field(default=30, description="Maximum pool overflow")
    pool_timeout: int = Field(default=30, description="Pool connection timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    
    # Performance settings
    query_timeout: int = Field(default=30, description="Query timeout in seconds")
    statement_timeout: int = Field(default=60, description="Statement timeout in seconds")
    
    class Config:
        env_prefix = "DB_"


class SecurityConfig(BaseSettings):
    """Security configuration settings."""
    
    # JWT settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token generation"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )
    
    # Rate limiting
    rate_limit_requests: int = Field(
        default=100, description="Rate limit requests per minute"
    )
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )
    
    # Security headers
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    
    class Config:
        env_prefix = "SEC_"


class AppConfig(BaseSettings):
    """Application configuration settings."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8001, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Service information
    service_name: str = Field(default="database-agent", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Redis for rate limiting and caching
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching and rate limiting"
    )
    
    class Config:
        env_prefix = "APP_"


class Settings:
    """Combined application settings."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.security = SecurityConfig()
        self.app = AppConfig()


# Global settings instance
settings = Settings()