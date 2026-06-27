from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    data_dir: Path = Path("data/generated")
    real_data_dir: Path = Path("data/real")
    models_dir: Path = Path("models")
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "nicka_ml"
    db_user: str = "nicka"
    db_password: str = "nicka"

    n_fermentations: int = 1000
    random_seed: int = 42

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"

    rabbitmq_url: str = "amqp://guest:guest@localhost/"
    rabbitmq_queue: str = "sensor.readings"

    backend_base_url: str = "http://nicka-backend:8080"
    backend_reports_endpoint: str = "/api/fermentation-reports"
    backend_sensors_endpoint: str = "/api/sensor-readings"
    backend_notifications_endpoint: str = "/api/notifications/ml-results"
    backend_api_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()