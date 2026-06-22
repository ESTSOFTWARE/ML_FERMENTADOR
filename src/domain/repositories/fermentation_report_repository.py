from abc import ABC, abstractmethod

from src.domain.dtos.fermentation_report_dto import FermentationReportDTO


class FermentationReportRepository(ABC):
    """
    Puerto para obtener reportes de fermentaciones completadas.
    La implementación real consulta al backend principal vía HTTP,
    ya que este microservicio no posee la base de datos de reportes.
    """

    @abstractmethod
    def get_by_session_id(self, session_id: int) -> FermentationReportDTO:
        """Obtiene el reporte completo de una sesión finalizada."""
        raise NotImplementedError

    @abstractmethod
    def get_all_completed(self, since: str | None = None) -> list[FermentationReportDTO]:
        """
        Obtiene todos los reportes completados, opcionalmente desde una
        fecha ISO 8601. Útil para construir un dataset desde reportes
        reales acumulados (build_dataset_from_reports.py).
        """
        raise NotImplementedError