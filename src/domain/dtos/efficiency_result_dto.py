from datetime import datetime

from pydantic import BaseModel


class EfficiencyResultDTO(BaseModel):
    """
    Resultado de predicción de eficiencia durante una fermentación
    en curso, listo para publicarse al WebSocket de notificaciones.
    """

    session_id: int
    circuit_id: int
    predicted_efficiency_percent: float
    predicted_at: datetime
    model_version: str = "1.0.0"