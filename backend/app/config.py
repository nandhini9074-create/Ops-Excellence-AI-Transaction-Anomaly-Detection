from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

# Calculate the project root which is two levels up from this file's directory (backend/app/config.py)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(root_dir, ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Ops Excellence AI"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:pass%40123@localhost:5432/ops_excellence"
    
    D1_WORKER_URL: str = "http://localhost:8787"
    D1_WORKER_API_KEY: str = "local_dev_key"
    
    SLACK_WEBHOOK_URL: Optional[str] = None
    TEAMS_WEBHOOK_URL: Optional[str] = None
    
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    ANOMALY_INTERVAL_HOURS: int = 4
    BASELINE_HISTORY_DAYS: int = 90
    
    Z_SCORE_THRESHOLD: float = 3.0
    ISOLATION_FOREST_CONTAMINATION: float = 0.05
    FALSE_POSITIVE_THRESHOLD: float = 0.15
    
    ZSCORE_WEIGHT: float = 0.25
    ISOLATION_FOREST_WEIGHT: float = 0.30
    PROPHET_WEIGHT: float = 0.25
    CHANGE_POINT_WEIGHT: float = 0.20

    model_config = SettingsConfigDict(env_file=env_path, case_sensitive=True, extra="ignore")

settings = Settings()
