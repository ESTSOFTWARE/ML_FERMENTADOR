import httpx

from src.domain.dtos.anomaly_result_dto import AnomalyResultDTO
from src.domain.dtos.efficiency_result_dto import EfficiencyResultDTO
from src.domain.repositories.notification_publisher import NotificationPublisher


class WebsocketNotificationPublisher(NotificationPublisher):
    """
    Implementación de NotificationPublisher. Este microservicio NO
    mantiene la conexión WebSocket directamente con el frontend -- le
    hace POST al backend, que es quien reenvía el resultado por su
    propio canal WS ya establecido con el cliente.
    """

    def __init__(self, base_url: str, notifications_endpoint: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._endpoint = notifications_endpoint
        self._timeout = timeout_seconds

    def publish_efficiency_result(self, result: EfficiencyResultDTO) -> None:
        self._post("efficiency", result.model_dump(mode="json"))

    def publish_anomaly_result(self, result: AnomalyResultDTO) -> None:
        self._post("anomaly", result.model_dump(mode="json"))

    def _post(self, result_type: str, payload: dict) -> None:
        url = f"{self._base_url}{self._endpoint}"
        payload_with_type = {"type": result_type, **payload}

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(url, json=payload_with_type)
            response.raise_for_status()