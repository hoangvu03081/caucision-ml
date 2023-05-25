from pydantic import BaseSettings
from os import environ

environment = environ.get("FASTAPI_ENV")


class Settings(BaseSettings):
    class Config:
        # Order: prod > development > test
        env_file = ".env.test", ".env.development", ".env.production"
        case_sensitive = False

    app_name: str = "CaucisionML"

    DATABASE_URL: str
    SCYLLA_HOST: str
    SCYLLA_KEYSPACE: str = "caucision"
    REDIS_URL: str
    CELERY_BROKER_URL: str


settings = Settings()
