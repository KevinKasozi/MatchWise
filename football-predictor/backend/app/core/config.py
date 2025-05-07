from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Football Predictor"
    
    # BACKEND_CORS_ORIGINS is a comma-separated list of origins
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str
    DATABASE_TEST_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # OpenFootball Data Paths
    OPENFOOTBALL_DATA_DIR: str
    CLUBS_DATA_PATH: str
    PLAYERS_DATA_PATH: str

    # ML Configuration
    MODEL_PATH: str
    FEATURE_IMPORTANCE_PATH: str

    # Ingestion Script Configuration
    DATA_PATH: str = "data/raw"
    STATE_FILE_PATH: str = "data/state.json"
    TEAM_NAME_NORMALIZATION: str = "data/team_mapper.json"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 