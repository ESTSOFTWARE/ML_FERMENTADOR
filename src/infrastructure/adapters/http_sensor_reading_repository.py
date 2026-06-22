import httpx

from src.domain.entities.sensor_reading import SensorReading, SensorType
from src.domain.repositories.sensor_reading_repository import SensorReadingRepository


class HttpSensorReadingRepository(SensorReadingRepository):
    """
    Implementación de SensorReadingRepository que consulta al backend
    principal por HTTP. Usada para reconstruir la serie de tiempo real
    de una sesión completada (reentrenamiento incremental).
    """

    def __init__(self, base_url: str, sensors_endpoint: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._endpoint = sensors_endpoint
        self._timeout = timeout_seconds

    def get_by_session_id(self, session_id: int) -> list[SensorReading]:
        url = f"{self._base_url}{self._endpoint}"
        params = {"session_id": session_id}

        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return [self._to_entity(item) for item in response.json()]

    def get_by_source(self, source_identifier: str) -> list[SensorReading]:
        raise NotImplementedError(
            "HttpSensorReadingRepository no soporta lectura por fuente arbitraria. "
            "Usa CsvSensorReadingRepository para CSVs de laboratorio."
        )

    @staticmethod
    def _to_entity(item: dict) -> SensorReading:
        return SensorReading(
            circuit_id=item["circuit_id"],
            session_id=item.get("session_id"),
            sensor_type=SensorType(item["sensor_type"]),
            value=item["value"],
            timestamp=item["timestamp"],
        )