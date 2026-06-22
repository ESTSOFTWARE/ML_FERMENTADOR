from src.application.use_cases.training.retrain_with_real_report import RetrainWithRealReport
from src.domain.dtos.fermentation_report_dto import FermentationReportDTO


class TrainingController:
    """
    Controller: orquesta el webhook que el backend dispara cuando una
    fermentación termina (fermentation_sessions.status = 'completed'),
    hacia el use case de reentrenamiento incremental.
    """

    def __init__(self, retrain_with_real_report: RetrainWithRealReport) -> None:
        self._retrain = retrain_with_real_report

    def handle_report_completed(self, report: FermentationReportDTO) -> dict:
        return self._retrain.execute(report)