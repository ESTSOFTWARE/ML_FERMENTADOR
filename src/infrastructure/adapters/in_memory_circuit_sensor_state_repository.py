from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

from src.domain.dtos.anomaly_request_dto import SensorSnapshotDTO
from src.domain.repositories.circuit_sensor_state_repository import (
    CircuitSensorStateRepository,
)

# Tope de puntos guardados por circuito, como salvaguarda de memoria ante
# un circuito que publique con una frecuencia inusualmente alta. A la
# cadencia normal de sensores (segundos/minutos), 2000 puntos cubre de
# sobra cualquier ventana de un par de horas.
DEFAULT_MAX_POINTS_PER_CIRCUIT = 2000


class InMemoryCircuitSensorStateRepository(CircuitSensorStateRepository):
    """
    Implementación en memoria del proceso. Suficiente para una sola
    instancia del servicio; si en el futuro se escala a múltiples
    réplicas, este estado debería migrarse a un almacenamiento
    compartido (ej. Redis) implementando el mismo puerto -- de lo
    contrario cada réplica vería solo una parte de las lecturas de un
    mismo circuito.
    """

    def __init__(self, max_points_per_circuit: int = DEFAULT_MAX_POINTS_PER_CIRCUIT) -> None:
        self._latest: dict[int, dict[str, float]] = defaultdict(dict)
        self._history: dict[int, deque[tuple[datetime, SensorSnapshotDTO]]] = defaultdict(
            lambda: deque(maxlen=max_points_per_circuit)
        )
        self._lock = threading.Lock()

    def update_latest(self, circuit_id: int, field: str, value: float) -> None:
        with self._lock:
            self._latest[circuit_id][field] = value

    def get_latest_snapshot(
        self, circuit_id: int, required_fields: set[str]
    ) -> SensorSnapshotDTO | None:
        with self._lock:
            known = dict(self._latest.get(circuit_id, {}))

        missing = required_fields - known.keys()
        if missing:
            return None

        return SensorSnapshotDTO(**{field: known[field] for field in required_fields})

    def add_snapshot(self, circuit_id: int, timestamp: datetime, snapshot: SensorSnapshotDTO) -> None:
        with self._lock:
            self._history[circuit_id].append((timestamp, snapshot))

    def get_recent_snapshots(
        self, circuit_id: int, window_hours: float
    ) -> list[tuple[datetime, SensorSnapshotDTO]]:
        with self._lock:
            points = list(self._history.get(circuit_id, ()))

        if not points:
            return []

        latest_timestamp = points[-1][0]
        cutoff = latest_timestamp - timedelta(hours=window_hours)
        return [point for point in points if point[0] >= cutoff]