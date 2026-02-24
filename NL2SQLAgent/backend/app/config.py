from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "智能数据分析助理"
    debug: bool = True

    dashscope_api_key: str = ""
    llm_model_name: str = "qwen3-max"

    app_db_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'app.db'}"
    sample_db_path: str = str(BASE_DIR / "data" / "sample.db")
    sample_db_uri: str = f"sqlite:///{BASE_DIR / 'data' / 'sample.db'}"

    sql_max_rows: int = 500
    sql_timeout: int = 10
    memory_window: int = 10

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

    model_config = {"env_file": str(BASE_DIR / ".env"), "extra": "ignore"}


settings = Settings()
