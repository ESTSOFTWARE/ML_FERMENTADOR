from datetime import datetime

from pydantic import BaseModel, model_validator

from src.domain.dtos.anomaly_request_dto import SensorSnapshotDTO


class RealtimeReadingDTO(BaseModel):
    """
    Input del endpoint POST /realtime/reading.
    El backend lo envía cada vez que llega una lectura nueva de
    sensores para una sesión con status='running'.
    """

    session_id: int
    circuit_id: int
    timestamp: datetime
    current: SensorSnapshotDTO
    history_hours: list[float]
    history: list[SensorSnapshotDTO]

    elapsed_hours: float
    """Horas transcurridas desde actual_start."""

    planned_duration_hours: float
    """
    Duración total planeada de la fermentación, en horas.
    Se calcula en el backend como
    (scheduled_end - scheduled_start) en horas, desde
    fermentation_sessions. Se usa para saber si ya se alcanzó el 50%
    del tiempo planeado y conviene predecir eficiencia.
    """

    @model_validator(mode="after")
    def validar_planned_duration(self) -> "RealtimeReadingDTO":
        if self.planned_duration_hours <= 0:
            raise ValueError("planned_duration_hours debe ser > 0.")
        if len(self.history_hours) != len(self.history):
            raise ValueError("history_hours y history deben tener la misma longitud.")
        return self