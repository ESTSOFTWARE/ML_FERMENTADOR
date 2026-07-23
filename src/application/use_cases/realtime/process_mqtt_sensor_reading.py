from __future__ import annotations

import logging
from datetime import datetime

from src.application.use_cases.realtime.detect_anomaly import DetectAnomaly
from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO
from src.domain.dtos.anomaly_result_dto import AnomalyResultDTO
from src.domain.repositories.circuit_sensor_state_repository import (
    CircuitSensorStateRepository,
)
from src.domain.repositories.notification_publisher import NotificationPublisher

logger = logging.getLogger(__name__)

MIN_HISTORY_POINTS = 2
HISTORY_WINDOW_HOURS = 2.0

# Campos que necesita SensorSnapshotDTO / ExtractAnomalyFeatures. Mientras
# no se conozca al menos un valor de CADA uno para un circuito, no se
# puede armar un snapshot completo y se omite la detección.
REQUIRED_SNAPSHOT_FIELDS = {"ph", "temperature_c", "turbidity", "conductivity", "alcohol_percent"}


class ProcessMqttSensorReading:
    """
    Use case: procesa UNA lectura cruda de UN sensor proveniente de
    mqtt.sensor.data.queue (un mensaje = un sensor_type + value). Combina
    esa lectura con el último valor conocido de los otros sensores del
    mismo circuito para armar un snapshot completo, lo agrega a la
    ventana histórica del circuito y, si ya hay suficiente historial de
    las últimas 2 horas, corre detección de anomalías y publica el
    resultado.

    Reemplaza, solo para el caso de anomalías, la dependencia de que el
    backend arme el RealtimeReadingDTO completo: la lectura llega directo
    desde el bridge MQTT -> RabbitMQ, por lo que la detección reacciona a
    cada lectura real de sensor. Es independiente del flujo de predicción
    de eficiencia (ProcessRealtimeReading), que sigue igual.
    """

    def __init__(
        self,
        state_repository: CircuitSensorStateRepository,
        detect_anomaly: DetectAnomaly,
        notification_publisher: NotificationPublisher,
        history_window_hours: float = HISTORY_WINDOW_HOURS,
    ) -> None:
        self._state_repository = state_repository
        self._detect_anomaly = detect_anomaly
        self._publisher = notification_publisher
        self._history_window_hours = history_window_hours

    def execute(
        self,
        circuit_id: int,
        session_id: int | None,
        timestamp: datetime,
        field: str,
        value: float,
    ) -> None:
        self._state_repository.update_latest(circuit_id, field, value)

        snapshot = self._state_repository.get_latest_snapshot(circuit_id, REQUIRED_SNAPSHOT_FIELDS)
        if snapshot is None:
            logger.debug(
                "circuit_id=%s: todavía no se conoce un valor de cada sensor, se omite detección.",
                circuit_id,
            )
            return

        self._state_repository.add_snapshot(circuit_id, timestamp, snapshot)
        points = self._state_repository.get_recent_snapshots(circuit_id, self._history_window_hours)

        if len(points) < MIN_HISTORY_POINTS:
            logger.debug(
                "circuit_id=%s: historial insuficiente (%d punto(s)), se omite detección.",
                circuit_id,
                len(points),
            )
            return

        *history_points, (current_ts, current_snapshot) = points
        request = AnomalyRequestDTO(
            current=current_snapshot,
            history_hours=[self._hours_ago(ts, current_ts) for ts, _ in history_points],
            history=[snap for _, snap in history_points],
        )

        is_anomaly, score = self._detect_anomaly.execute(
            request,
            session_id=session_id,
            circuit_id=circuit_id,
            timestamp=current_ts,
        )

        # AnomalyResultDTO.session_id no es opcional -- si el circuito no
        # tiene una sesión activa, igual queda la inferencia guardada en
        # el historial (DetectAnomaly ya la persiste), pero no tiene
        # sentido "notificar" un resultado sin sesión a la que asociarlo.
        if session_id is None:
            return

        result = AnomalyResultDTO(
            session_id=session_id,
            circuit_id=circuit_id,
            is_anomaly=is_anomaly,
            anomaly_score=score,
            detected_at=current_ts,
        )
        self._publisher.publish_anomaly_result(result)

    @staticmethod
    def _hours_ago(past: datetime, reference: datetime) -> float:
        return max((reference - past).total_seconds() / 3600.0, 0.0)