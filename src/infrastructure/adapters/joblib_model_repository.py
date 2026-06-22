from pathlib import Path
from typing import Any

import joblib

from src.domain.repositories.model_repository import ModelRepository


class JoblibModelRepository(ModelRepository):
    """Implementación de ModelRepository usando joblib para serializar."""

    def __init__(self, models_dir: Path) -> None:
        self._dir = models_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, artifact: Any, filename: str) -> str:
        path = self._dir / filename
        joblib.dump(artifact, path)
        return str(path)

    def load(self, filename: str) -> Any:
        path = self._dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Modelo no encontrado: {path}")
        return joblib.load(path)

    def exists(self, filename: str) -> bool:
        return (self._dir / filename).exists()