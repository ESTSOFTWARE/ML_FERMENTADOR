from src.domain.dtos.fermentation_report_dto import FermentationReportDTO
from src.domain.repositories.fermentation_report_repository import FermentationReportRepository


class BuildDatasetFromReports:
    """
    Use case: construye registros de entrenamiento a partir de reportes
    reales de fermentaciones completadas (fermentation_reports).

    Responsabilidad única: transformar FermentationReportDTO al formato
    de registro resumen usado en reentrenamiento. A diferencia de las
    otras dos fuentes, aquí NO hay serie de tiempo completa, solo
    valores inicial/final/última lectura por sensor.
    """

    def __init__(self, report_repository: FermentationReportRepository) -> None:
        self._repository = report_repository

    def execute_for_session(self, session_id: int) -> dict:
        report = self._repository.get_by_session_id(session_id)
        return self._to_record(report)

    def execute_all_completed(self, since: str | None = None) -> list[dict]:
        reports = self._repository.get_all_completed(since=since)
        return [self._to_record(r) for r in reports]

    @staticmethod
    def _to_record(report: FermentationReportDTO) -> dict:
        return {
            "fermentation_id": f"session-{report.session_id}",
            "group_id": report.group_id,
            "sugar_initial_g_l": report.initial_sugar,
            "sugar_final_g_l": report.final_sugar,
            "ethanol_detected_g_l": report.ethanol_detected,
            "theoretical_ethanol_g_l": report.theoretical_ethanol,
            "final_efficiency_percent": report.efficiency,
            "ph_initial": report.ph_initial,
            "ph_final": report.ph_final,
            "ph_last_reading": report.ph_last_reading,
            "temperature_initial": report.temperature_initial,
            "temperature_final": report.temperature_final,
            "temperature_last_reading": report.temperature_last_reading,
            "turbidity_initial": report.turbidity_initial,
            "turbidity_final": report.turbidity_final,
            "turbidity_last_reading": report.turbidity_last_reading,
            "conductivity_initial": report.conductivity_initial,
            "conductivity_final": report.conductivity_final,
            "conductivity_last_reading": report.conductivity_last_reading,
            "alcohol_initial": report.alcohol_initial,
            "alcohol_final": report.alcohol_final,
            "alcohol_last_reading": report.alcohol_last_reading,
            "source": "real_report",
        }