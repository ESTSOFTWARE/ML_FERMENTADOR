import logging
from datetime import datetime, timedelta

from src.application.use_cases.training.retrain_with_real_report import RetrainWithRealReport
from src.domain.repositories.fermentation_report_repository import FermentationReportRepository

logger = logging.getLogger(__name__)


class ScheduledNightlyRetrain:
    """
    Reentrenamiento batch nocturno: obtiene todos los reportes de
    fermentación completados en las últimas 24 horas y reentrena el
    modelo incrementalmente con cada uno.
    Se ejecuta todos los días a las 2:00 AM.
    """

    def __init__(
        self,
        retrain: RetrainWithRealReport,
        report_repository: FermentationReportRepository,
    ) -> None:
        self._retrain = retrain
        self._report_repository = report_repository

    def execute(self) -> None:
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        reports = self._report_repository.get_all_completed(since=since)

        if not reports:
            logger.info("Reentrenamiento nocturno: sin reportes nuevos en las últimas 24h.")
            return

        logger.info("Reentrenamiento nocturno: %d reportes encontrados.", len(reports))

        for report in reports:
            try:
                result = self._retrain.execute(report)
                logger.info(
                    "Reentrenado con session_id=%s, efficiency=%.2f%%",
                    result["session_id"],
                    result["retrained_with_efficiency"],
                )
            except (ValueError, FileNotFoundError) as e:
                logger.warning("Saltando session_id=%s: %s", report.session_id, e)
