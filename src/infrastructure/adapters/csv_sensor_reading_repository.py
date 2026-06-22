from pathlib import Path

import pandas as pd

from src.domain.entities.sensor_reading import SensorReading, SensorType
from src.domain.repositories.sensor_reading_repository import SensorReadingRepository

# Mapea nombres de columnas esperados en el CSV a SensorType del dominio.
COLUMN_TO_SENSOR_TYPE = {
    "ph": SensorType.PH,
    "temperature_c": SensorType.TEMPERATURE,
    "turbidity": SensorType.TURBIDITY,
    "conductivity": SensorType.CONDUCTIVITY,
    "alcohol_percent": SensorType.ALCOHOL,
}


class CsvSensorReadingRepository(SensorReadingRepository):
    """
    Implementación de SensorReadingRepository para CSVs de laboratorio
    (formato ancho: una columna por sensor, una fila por timestamp),
    como el dataset calibrado de Sacharomyces.

    El CSV debe tener una columna 'time_hours' y al menos una de las
    columnas listadas en COLUMN_TO_SENSOR_TYPE.
    """

    def __init__(self, real_data_dir: Path) -> None:
        self._dir = real_data_dir

    def get_by_session_id(self, session_id: int) -> list[SensorReading]:
        raise NotImplementedError(
            "CsvSensorReadingRepository no tiene noción de session_id real. "
            "Usa get_by_source con el nombre del archivo."
        )

    def get_by_source(self, source_identifier: str) -> list[SensorReading]:
        path = self._dir / source_identifier
        if not path.exists():
            raise FileNotFoundError(f"CSV no encontrado: {path}")

        df = pd.read_csv(path)
        readings: list[SensorReading] = []

        for _, row in df.iterrows():
            for column, sensor_type in COLUMN_TO_SENSOR_TYPE.items():
                if column in df.columns and pd.notna(row[column]):
                    readings.append(
                        SensorReading(
                            circuit_id=0,  # Los CSVs históricos no tienen circuito real asociado.
                            session_id=None,
                            sensor_type=sensor_type,
                            value=float(row[column]),
                            timestamp=row["time_hours"],
                        )
                    )

        return readings