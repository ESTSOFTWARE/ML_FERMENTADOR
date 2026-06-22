from src.application.use_cases.realtime.detect_anomaly import DetectAnomaly
from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO
from src.domain.dtos.anomaly_response_dto import AnomalyResponseDTO


class AnomalyController:
    """
    Controller: orquesta la petición HTTP de detección de anomalía
    hacia el use case correspondiente. No contiene lógica de negocio,
    solo traduce DTO de entrada -> use case -> DTO de salida.
    """

    def __init__(self, detect_anomaly: DetectAnomaly) -> None:
        self._detect_anomaly = detect_anomaly

    def handle(self, request: AnomalyRequestDTO) -> AnomalyResponseDTO:
        is_anomaly, score = self._detect_anomaly.execute(request)
        return AnomalyResponseDTO(is_anomaly=is_anomaly, anomaly_score=score)