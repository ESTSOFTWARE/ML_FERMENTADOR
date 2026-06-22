from abc import ABC, abstractmethod
from typing import Any


class ModelRepository(ABC):
    """
    Puerto para guardar y cargar modelos entrenados (y sus scalers),
    sin importar el mecanismo de serialización real (joblib, pickle, etc).
    """

    @abstractmethod
    def save(self, artifact: Any, filename: str) -> str:
        """Guarda un modelo o scaler entrenado."""
        raise NotImplementedError

    @abstractmethod
    def load(self, filename: str) -> Any:
        """Carga un modelo o scaler previamente entrenado."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Indica si un artefacto ya fue entrenado y guardado."""
        raise NotImplementedError