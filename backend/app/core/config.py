from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Sika Family Vault API"
    database_url: str = "sqlite:///./test.db"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"

settings = Settings()
