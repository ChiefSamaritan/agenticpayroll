# app/config/settings.py

import os
import json
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env first
load_dotenv()


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./payroll.db", alias="DATABASE_URL")
    api_keys: List[str] = Field(default_factory=lambda: ["supersecretkey"], alias="API_KEYS")

    # Validate database_url format
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        parsed = urlparse(v)
        if not parsed.hostname:
            raise ValueError(f"❌ DATABASE_URL is missing or invalid: {v}")
        return v

    @field_validator("api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v):
        if isinstance(v, str):
            return [key.strip() for key in v.split(",")]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# Instantiate once
settings = Settings()
DATABASE_URL = settings.database_url
API_KEYS = settings.api_keys


# Load country config from JSON
def load_country_config():
    config_path = os.path.join(os.path.dirname(__file__), "country_config.json")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


country_config = load_country_config()