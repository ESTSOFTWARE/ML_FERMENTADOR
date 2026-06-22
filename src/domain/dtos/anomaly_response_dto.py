from pydantic import BaseModel


class AnomalyResponseDTO(BaseModel):
    """Respuesta del endpoint POST /detect/anomaly (detección síncrona, fuera del flujo realtime)."""

    is_anomaly: bool
    anomaly_score: float