from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SensorType(str, Enum):
    """Coincide exactamente con el CHECK constraint de sensor_events.sensor_type."""
    ALCOHOL = "alcohol"
    DENSITY = "density"
    CONDUCTIVITY = "conductivity"
    PH = "ph"
    TEMPERATURE = "temperature"
    TURBIDITY = "turbidity"
    RPM = "rpm"


@dataclass(frozen=True)
class SensorReading:
    """
    Una lectura puntual de UN sensor, equivalente a una fila de
    alcohol_sensor / ph_sensor / temperature_sensor / etc.

    circuit_id y session_id son nullable en la BD (un circuito puede
    leer sin una sesión activa), por eso session_id es Optional aquí.
    """

    circuit_id: int
    sensor_type: SensorType
    value: float
    timestamp: datetime
    session_id: int | None = None

    def __post_init__(self) -> None:
        if self.circuit_id <= 0:
            raise ValueError(f"circuit_id debe ser > 0, recibido: {self.circuit_id}")