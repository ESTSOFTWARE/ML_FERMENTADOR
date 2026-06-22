from datetime import datetime

from pydantic import BaseModel

from src.domain.entities.sensor_reading import SensorType


class AnomalyResultDTO(BaseModel):
    """
    Resultado de detección de anomalía, listo para publicarse al
    WebSocket de notificaciones (vía notification_publisher).
    """

    session_id: int
    circuit_id: int
    is_anomaly: bool
    anomaly_score: float
    suspected_sensor: SensorType | None = None
    detected_at: datetime
    model_version: str = "1.0.0"