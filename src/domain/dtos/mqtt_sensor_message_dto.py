from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MqttSensorMessageDTO(BaseModel):
    """
    Formato real de los mensajes en mqtt.sensor.data.queue: UNA lectura
    de UN sensor por mensaje (el bridge MQTT publica cada sensor por
    separado, no agrupados).
    """

    circuit_id: int
    sensor_type: str
    value: float
    active: bool = True
    session_id: int | None = None
    timestamp: datetime