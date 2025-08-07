"""Application configuration settings"""

from pydantic import BaseModel
from functools import lru_cache

class Settings(BaseModel):
    app_name: str = "Event Management API"
    # SQLite configuration for development
    database_url: str = "sqlite:///./event_management.db"
    
    # PostgreSQL configuration (uncomment for production)
    # database_username: str = "event_user"
    # database_password: str = "event_password"
    # database_hostname: str = "localhost"
    # database_port: str = "5433"
    # database_name: str = "event_management_db"
    # database_url: str = f"postgresql://{database_username}:{database_password}@{database_hostname}:{database_port}/{database_name}"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
