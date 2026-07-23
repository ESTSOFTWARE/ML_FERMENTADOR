from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class MqttSensorMessageDTO(BaseModel):
    """
    Formato real de los mensajes en mqtt.sensor.data.queue: UNA lectura
    de UN sensor por mensaje (el bridge MQTT publica cada sensor por
    separado, no agrupados).

    circuit_id/sensor_type/value son obligatorios (sin ellos la lectura
    no es enrutable). timestamp es opcional: algunos sensores no lo
    incluyen, así que se usa la hora de llegada como fallback.
    """

    circuit_id: int
    sensor_type: str
    value: float
    active: bool = True
    session_id: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))