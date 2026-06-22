from abc import ABC, abstractmethod

import pandas as pd


class DatasetRepository(ABC):
    """
    Puerto para guardar y leer datasets de entrenamiento, sin importar
    su origen (sintético, CSV, reportes reales) ni su formato de
    almacenamiento real (Parquet, CSV, base de datos, etc).
    """

    @abstractmethod
    def save(self, records: list[dict], filename: str) -> str:
        """Guarda una lista de registros y devuelve la ruta/identificador resultante."""
        raise NotImplementedError

    @abstractmethod
    def load(self, filename: str) -> pd.DataFrame:
        """Carga un dataset previamente guardado como DataFrame."""
        raise NotImplementedError

    @abstractmethod
    def append(self, records: list[dict], filename: str) -> str:
        """Agrega registros a un dataset existente (usado en reentrenamiento incremental)."""
        raise NotImplementedError