from src.domain.entities.anomaly_inference import AnomalyInference
from src.domain.repositories.inference_repository import InferenceRepository


class GetInferenceHistory:
    """
    Use case: consulta el historial de inferencias de anomalía
    almacenadas en la BD local, con filtros opcionales.

    Responsabilidad única: lectura del historial. No corre modelos,
    no persiste nada.
    """

    def __init__(self, inference_repository: InferenceRepository) -> None:
        self._repository = inference_repository

    def get_all(self, limit: int = 100) -> list[AnomalyInference]:
        return self._repository.get_all(limit=limit)

    def get_by_session(self, session_id: int) -> list[AnomalyInference]:
        return self._repository.get_by_session_id(session_id)

    def get_anomalies_only(self, limit: int = 100) -> list[AnomalyInference]:
        return self._repository.get_anomalies_only(limit=limit)