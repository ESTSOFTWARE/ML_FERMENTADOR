from pathlib import Path

from src.application.use_cases.training.retrain_with_real_report import RetrainWithRealReport
from src.application.use_cases.training.train_anomaly_from_files import TrainAnomalyFromFiles
from src.application.use_cases.training.train_efficiency_from_files import TrainEfficiencyFromFiles
from src.domain.dtos.fermentation_report_dto import FermentationReportDTO


class TrainingController:
    def __init__(
        self,
        retrain_with_real_report: RetrainWithRealReport,
        train_efficiency_from_files: TrainEfficiencyFromFiles,
        train_anomaly_from_files: TrainAnomalyFromFiles,
    ) -> None:
        self._retrain = retrain_with_real_report
        self._train_efficiency = train_efficiency_from_files
        self._train_anomaly = train_anomaly_from_files

    def handle_report_completed(self, report: FermentationReportDTO) -> dict:
        return self._retrain.execute(report)

    def handle_efficiency_upload(self, sources: list[tuple[Path, str, float | None]]) -> dict:
        return self._train_efficiency.execute(sources)

    def handle_anomaly_upload(self, sources: list[tuple[Path, str]]) -> dict:
        return self._train_anomaly.execute(sources)