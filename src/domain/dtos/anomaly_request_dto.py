from pydantic import BaseModel, Field


class SensorSnapshotDTO(BaseModel):
    """Una lectura puntual de los 5 sensores en un instante."""

    ph: float
    temperature_c: float
    turbidity: float
    conductivity: float
    alcohol_percent: float


class AnomalyRequestDTO(BaseModel):
    """
    Lectura actual + historial reciente, usado como input para
    detectar anomalías en tiempo real.
    """

    current: SensorSnapshotDTO
    history_hours: list[float] = Field(min_length=1)
    history: list[SensorSnapshotDTO] = Field(min_length=1)