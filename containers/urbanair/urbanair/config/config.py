from fastapi import FastAPI
from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Urban Air API"
    admin_email: str = "ogiles@turing.ac.uk"
    database_secret_file: str = "db_secrets.json"


@lru_cache()
def get_settings():
    return Settings()
