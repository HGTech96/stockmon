from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolved relative to this file (api/src/stockmon/config.py -> api/.env),
# not the process's working directory, so `stockmon` behaves the same
# whether launched from api/, the repo root, or an IDE run config.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str
    ui_origin: str = "http://localhost:5173"
    # Drives the session cookie's Secure flag only (see routes/auth.py) --
    # local dev runs over http, production runs behind HTTPS on Render.
    environment: Literal["local", "production"] = "local"


settings = Settings()
