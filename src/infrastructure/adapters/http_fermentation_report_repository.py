import httpx

from src.domain.dtos.fermentation_report_dto import FermentationReportDTO
from src.domain.repositories.fermentation_report_repository import FermentationReportRepository


class HttpFermentationReportRepository(FermentationReportRepository):
    """
    Implementación de FermentationReportRepository que consulta al
    backend principal por HTTP. Este microservicio no posee la base
    de datos de reportes -- esa vive en el backend.
    """

    def __init__(self, base_url: str, reports_endpoint: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._endpoint = reports_endpoint
        self._timeout = timeout_seconds

    def get_by_session_id(self, session_id: int) -> FermentationReportDTO:
        url = f"{self._base_url}{self._endpoint}/{session_id}"
        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url)
            response.raise_for_status()
            return FermentationReportDTO(**response.json())

    def get_all_completed(self, since: str | None = None) -> list[FermentationReportDTO]:
        url = f"{self._base_url}{self._endpoint}"
        params = {"status": "completed"}
        if since:
            params["since"] = since

        with httpx.Client(timeout=self._timeout) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return [FermentationReportDTO(**item) for item in response.json()]