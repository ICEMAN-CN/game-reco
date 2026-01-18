"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # Database
    database_url: str = "postgresql://iceman:iceman@localhost:5432/game_odyssey"
    
    # Game Data API (external data source - configure in .env)
    game_data_api_url: Optional[str] = None
    game_data_api_key: Optional[str] = None
    
    # Model Configuration
    embedding_model_provider: str = "local"
    embedding_model_name: str = "qwen3-embedding-4b"  # MLX本地模型
    embedding_base_url: str = "http://0.0.0.0:8000"  # 本地MLX服务地址
    embedding_api_key: Optional[str] = None
    
    # chat_model_provider: str = "openai"
    # chat_model_name: str = "gpt-4"
    # chat_base_url: str = "https://api.openai.com/v1"

    chat_model_provider: str = "local"
    chat_model_name: str = "qwen2.5:3b"
    chat_base_url: str = "http://localhost:11434"
    chat_api_key: Optional[str] = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

