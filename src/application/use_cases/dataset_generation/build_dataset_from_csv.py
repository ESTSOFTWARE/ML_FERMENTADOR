from src.application.use_cases.shared.readings_to_profile import ReadingsToProfile
from src.domain.entities.kinetic_parameters import YPS_MAXIMO_TEORICO
from src.domain.repositories.sensor_reading_repository import SensorReadingRepository


class BuildDatasetFromCsv:
    """
    Use case: construye registros de entrenamiento a partir de un CSV
    real de laboratorio (ej. fermentaciones tipo Sacharomyces.xlsx).

    Responsabilidad única: orquestar lectura de CSV + conversión a
    perfil + serialización a registros. La conversión de lecturas
    crudas a perfil se delega a ReadingsToProfile (compartida con
    el flujo de reentrenamiento con datos reales).
    """

    def __init__(
        self,
        reading_repository: SensorReadingRepository,
        readings_to_profile: ReadingsToProfile | None = None,
    ) -> None:
        self._repository = reading_repository
        self._converter = readings_to_profile or ReadingsToProfile()

    def execute(self, source_identifier: str, fermentation_id: str) -> list[dict]:
        readings = self._repository.get_by_source(source_identifier)
        profile = self._converter.execute(readings, fermentation_id)

        records = profile.to_records()
        for row in records:
            row["final_efficiency_percent"] = profile.final_efficiency_percent
            row["is_anomaly"] = False
            row["anomaly_type"] = None
            row["source"] = "csv_real"

        return records