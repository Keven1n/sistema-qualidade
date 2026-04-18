from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./dados_inspecoes.db"
    
    # Security
    secret_key: str = "troque-em-producao-use-valor-longo-aleatorio"
    encryption_key: Optional[str] = None
    hash_admin: str = ""
    
    # Session
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    
    # Upload
    max_size_mb: int = 5
    img_dir: str = "./fotos"
    
    # Business Rules
    items_per_page_inspecao: int = 20
    items_per_page_auditoria: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

settings = Settings()
