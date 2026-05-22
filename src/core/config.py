import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "Dresscode"
    debug: bool = True
    db_name: str = os.getenv("DB_NAME")

    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "e56c462f114c564ae096f1f04208f0bc033bd30fb445e3db465593745e7aee9f",
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_exp_minutes: int = int(os.getenv("JWT_ACCESS_EXP_MINUTES", "30"))
    jwt_refresh_exp_days: int = int(os.getenv("JWT_REFRESH_EXP_DAYS", "7"))

    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "uploads"))
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    allowed_image_mimes: frozenset[str] = frozenset(
        {"image/jpeg", "image/png", "image/webp"}
    )

    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    gemma_model_id: str = os.getenv("GEMMA_MODEL_ID", "gemma-4-26b-a4b-it")
    ai_auto_analyze_on_upload: bool = (
        os.getenv("AI_AUTO_ANALYZE_ON_UPLOAD", "true").lower() == "true"
    )

    @property
    def db_url(self):
        return f"sqlite+aiosqlite:///./{self.db_name}"


config = Config()
