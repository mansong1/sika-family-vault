from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Sika Bank API"
    DEBUG: bool = False
    SECRET_KEY: str = "sika-dev-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Supabase
    SUPABASE_URL: str = "https://localhost.supabase.co"
    SUPABASE_KEY: str = "local"
    
    # Mobile Money (mock)
    MOMO_API_URL: str = "https://mock.momo.api"
    MOMO_API_KEY: str = "mock-key"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
