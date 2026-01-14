from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Supabase
    supabase_url: str
    supabase_key: str  # anon/public key
    supabase_service_role_key: str  # service role/secret key
    
    # VLM
    vlm_provider: str = "openrouter"
    vlm_api_key: str = ""
    vlm_model: str = "qwen/qwen2.5-vl-7b-instruct"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
