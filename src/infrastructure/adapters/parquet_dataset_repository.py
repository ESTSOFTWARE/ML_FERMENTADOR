from pathlib import Path

import pandas as pd

from src.domain.repositories.dataset_repository import DatasetRepository


class ParquetDatasetRepository(DatasetRepository):
    """Implementación de DatasetRepository usando archivos Parquet en disco."""

    def __init__(self, data_dir: Path) -> None:
        self._dir = data_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, records: list[dict], filename: str) -> str:
        path = self._dir / filename
        pd.DataFrame(records).to_parquet(path, index=False)
        return str(path)

    def load(self, filename: str) -> pd.DataFrame:
        path = self._dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Dataset no encontrado: {path}")
        return pd.read_parquet(path)

    def append(self, records: list[dict], filename: str) -> str:
        path = self._dir / filename
        new_df = pd.DataFrame(records)

        if path.exists():
            existing_df = pd.read_parquet(path)
            combined = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined = new_df

        combined.to_parquet(path, index=False)
        return str(path)