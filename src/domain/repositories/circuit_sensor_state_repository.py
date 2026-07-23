from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.dtos.anomaly_request_dto import SensorSnapshotDTO


class CircuitSensorStateRepository(ABC):
    """
    Puerto que mantiene, por circuito, (a) el último valor conocido de
    cada sensor y (b) una ventana deslizante de snapshots completos ya
    armados.

    Necesario porque mqtt.sensor.data.queue publica UNA lectura de UN
    sensor por mensaje -- para tener un "snapshot" completo (los 5
    sensores que usa el modelo de anomalías) hay que ir combinando el
    último valor conocido de cada uno a medida que llegan mensajes
    independientes, sin esperar a que los 5 lleguen juntos.
    """

    @abstractmethod
    def update_latest(self, circuit_id: int, field: str, value: float) -> None:
        """Actualiza el último valor conocido de un sensor para un circuito."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_snapshot(
        self, circuit_id: int, required_fields: set[str]
    ) -> SensorSnapshotDTO | None:
        """
        Arma un snapshot combinando el último valor conocido de cada
        campo requerido. Devuelve None si todavía falta el primer valor
        de alguno de los sensores requeridos para ese circuito.
        """
        raise NotImplementedError

    @abstractmethod
    def add_snapshot(self, circuit_id: int, timestamp: datetime, snapshot: SensorSnapshotDTO) -> None:
        """Agrega un snapshot ya armado a la ventana histórica del circuito."""
        raise NotImplementedError

    @abstractmethod
    def get_recent_snapshots(
        self, circuit_id: int, window_hours: float
    ) -> list[tuple[datetime, SensorSnapshotDTO]]:
        """
        Devuelve los snapshots del circuito dentro de la ventana de
        tiempo indicada, ordenados de más antiguo a más reciente. La
        ventana se ancla al timestamp del snapshot más reciente
        disponible, no al reloj de pared del proceso.
        """
        raise NotImplementedError