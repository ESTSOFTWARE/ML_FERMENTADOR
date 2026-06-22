from abc import ABC, abstractmethod

from src.domain.entities.sensor_reading import SensorReading


class SensorReadingRepository(ABC):
    """
    Puerto para obtener lecturas crudas de sensores de una sesión.
    Puede implementarse leyendo un CSV de laboratorio (datos históricos
    tipo Sacharomyces.xlsx) o consultando al backend por HTTP (datos
    reales de sesiones IoT).
    """

    @abstractmethod
    def get_by_session_id(self, session_id: int) -> list[SensorReading]:
        """Obtiene todas las lecturas de una sesión, ordenadas por timestamp."""
        raise NotImplementedError

    @abstractmethod
    def get_by_source(self, source_identifier: str) -> list[SensorReading]:
        """
        Obtiene lecturas desde una fuente identificada por nombre/ruta
        (ej. un archivo CSV específico), no necesariamente ligada a una
        sesión real del sistema.
        """
        raise NotImplementedError