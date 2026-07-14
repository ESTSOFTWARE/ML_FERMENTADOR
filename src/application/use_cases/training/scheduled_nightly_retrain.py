import logging
from datetime import datetime, timedelta

from src.application.use_cases.training.retrain_anomaly_with_real_report import (
    RetrainAnomalyWithRealReport,
)
from src.application.use_cases.training.retrain_with_real_report import RetrainWithRealReport
from src.domain.repositories.fermentation_report_repository import FermentationReportRepository

logger = logging.getLogger(__name__)


class ScheduledNightlyRetrain:
    """
    Reentrenamiento batch nocturno: obtiene todos los reportes de
    fermentación completados en las últimas 24 horas y reentrena
    incrementalmente AMBOS modelos (eficiencia y anomalías) con cada
    uno. Se ejecuta todos los días a las 2:00 AM (ver main.py,
    CronTrigger(hour=2, minute=0)).

    Los dos reentrenamientos son independientes entre sí: si uno
    falla para un reporte dado (ej. porque su modelo base todavía no
    existe), el otro sigue intentándose igual. Un fallo en un reporte
    no detiene el procesamiento de los demás reportes de la noche.
    """

    def __init__(
        self,
        retrain_efficiency: RetrainWithRealReport,
        retrain_anomaly: RetrainAnomalyWithRealReport,
        report_repository: FermentationReportRepository,
    ) -> None:
        self._retrain_efficiency = retrain_efficiency
        self._retrain_anomaly = retrain_anomaly
        self._report_repository = report_repository

    def execute(self) -> None:
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        reports = self._report_repository.get_all_completed(since=since)

        if not reports:
            logger.info("Reentrenamiento nocturno: sin reportes nuevos en las últimas 24h.")
            return

        logger.info("Reentrenamiento nocturno: %d reportes encontrados.", len(reports))

        for report in reports:
            self._retrain_efficiency_safe(report)
            self._retrain_anomaly_safe(report)

    def _retrain_efficiency_safe(self, report) -> None:
        try:
            result = self._retrain_efficiency.execute(report)
            logger.info(
                "Eficiencia reentrenada: session_id=%s, efficiency=%.2f%%",
                result["session_id"],
                result["retrained_with_efficiency"],
            )
        except (ValueError, FileNotFoundError) as e:
            logger.warning("Eficiencia: saltando session_id=%s: %s", report.session_id, e)

    def _retrain_anomaly_safe(self, report) -> None:
        try:
            result = self._retrain_anomaly.execute(report)
            logger.info(
                "Anomalía reentrenada: session_id=%s, ventanas=%d, n_estimators=%d",
                result["session_id"],
                result["n_windows_used"],
                result["n_estimators_total"],
            )
        except (ValueError, FileNotFoundError) as e:
            logger.warning("Anomalía: saltando session_id=%s: %s", report.session_id, e)