from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # application
    APP_NAME: str = "Heart&Mind Recommender"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # database
    DATABASE_URL: str = "sqlite:///./heart_mind.db"
    
    # API Keys
    GEMINI_API_KEY: str = ""  # will be set from environment
    
    # recommendation engine
    MIN_INTERACTIONS_FOR_COLLABORATIVE: int = 3
    RECOMMENDATION_COUNT: int = 10
    SERENDIPITY_FACTOR: float = 0.05  # 5% wild cards
    
    # LLM explanation
    LLM_MODEL: str = "gemini-1.5-pro"
    LLM_MAX_TOKENS: int = 300
    EXPLANATION_TEMPERATURE: float = 0.7
    
    # server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()