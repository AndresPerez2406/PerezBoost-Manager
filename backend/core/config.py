import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv(".env")
if os.getenv("MODO_DESARROLLO") == "True":
    load_dotenv(".env.dev", override=True)

class Settings(BaseSettings):
    APP_NAME: str = "PerezBoost Pro API"
    APP_VERSION: str = os.getenv("APP_VERSION", "V14.0")
    API_V1_STR: str = "/api/v1"
    
    # Seguridad JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "perezboost_super_secret_jwt_key_2026_change_in_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    
    # Base de Datos (Si DATABASE_URL tiene postgres:// la convierte a postgresql:// para SQLAlchemy)
    raw_db_url: str = os.getenv("DATABASE_URL", "sqlite:///./perezboost.db")
    
    @property
    def DATABASE_URL(self) -> str:
        url = self.raw_db_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8501",
        "https://perezboost-manager.streamlit.app",
        "*"
    ]

    class Config:
        case_sensitive = True

settings = Settings()
