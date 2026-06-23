from abc import ABC, abstractmethod

from src.domain.entities.anomaly_inference import AnomalyInference


class InferenceRepository(ABC):
    """
    Puerto para guardar y consultar inferencias de anomalía.
    La implementación real usa SQLite; si en el futuro se migra a
    PostgreSQL solo se cambia el adapter, nada más.
    """

    @abstractmethod
    def save(self, inference: AnomalyInference) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self, limit: int = 100) -> list[AnomalyInference]:
        raise NotImplementedError

    @abstractmethod
    def get_by_session_id(self, session_id: int) -> list[AnomalyInference]:
        raise NotImplementedError

    @abstractmethod
    def get_anomalies_only(self, limit: int = 100) -> list[AnomalyInference]:
        raise NotImplementedError