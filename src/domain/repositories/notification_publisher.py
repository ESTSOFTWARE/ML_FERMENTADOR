from abc import ABC, abstractmethod

from src.domain.dtos.anomaly_result_dto import AnomalyResultDTO
from src.domain.dtos.efficiency_result_dto import EfficiencyResultDTO


class NotificationPublisher(ABC):
    """
    Puerto para publicar resultados de predicción/anomalía hacia el
    canal de notificaciones en tiempo real. La implementación real
    reenvía esto al backend para que lo distribuya por WebSocket al
    frontend (no es este microservicio quien mantiene la conexión WS
    con el cliente final).
    """

    @abstractmethod
    def publish_efficiency_result(self, result: EfficiencyResultDTO) -> None:
        """Publica una predicción de eficiencia en tiempo real."""
        raise NotImplementedError

    @abstractmethod
    def publish_anomaly_result(self, result: AnomalyResultDTO) -> None:
        """Publica un resultado de detección de anomalía. Se llama SIEMPRE,
        incluso cuando is_anomaly=False, para mantener el frontend informado
        del estado de salud del proceso."""
        raise NotImplementedError