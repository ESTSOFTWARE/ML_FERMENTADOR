from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Directorios
    data_dir: Path
    real_data_dir: Path
    models_dir: Path

    # Base de datos
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # Generación de datos
    n_fermentations: int
    random_seed: int

    # API
    api_host: str
    api_port: int
    api_prefix: str

    # RabbitMQ
    rabbitmq_url: str
    rabbitmq_queue: str

    # Backend
    backend_base_url: str
    backend_reports_endpoint: str
    backend_sensors_endpoint: str
    backend_notifications_endpoint: str
    backend_api_timeout_seconds: float

    # Debug
    debug: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()