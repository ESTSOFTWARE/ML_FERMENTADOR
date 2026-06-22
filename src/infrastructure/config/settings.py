from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Rutas locales
    data_dir: Path = Path("data/generated")
    real_data_dir: Path = Path("data/real")
    models_dir: Path = Path("models")

    # Generación de datos sintéticos
    n_fermentations: int = 1000
    random_seed: int = 42

    # API propia (este microservicio)
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    # Backend principal (Nich-Ká FERMENTADOR-BACK)
    backend_base_url: str = "http://nicka-backend:8080"
    backend_reports_endpoint: str = "/api/fermentation-reports"
    backend_sensors_endpoint: str = "/api/sensor-readings"
    backend_notifications_endpoint: str = "/api/notifications/ml-results"
    backend_api_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()