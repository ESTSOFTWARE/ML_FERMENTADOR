import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.application.use_cases.shared.anomaly_window_builder import AnomalyWindowBuilder
from src.application.use_cases.shared.readings_to_profile import ReadingsToProfile
from src.domain.dtos.fermentation_report_dto import FermentationReportDTO
from src.domain.repositories.model_repository import ModelRepository
from src.domain.repositories.sensor_reading_repository import SensorReadingRepository

ANOMALY_MODEL_FILENAME = "iforest_anomaly.pkl"
ANOMALY_SCALER_FILENAME = "scaler_anomaly.pkl"
WARM_START_TREES_INCREMENT = 10


class RetrainAnomalyWithRealReport:
    """
    Use case: reentrena incrementalmente el IsolationForest con UNA
    fermentación real recién completada, agregando árboles nuevos
    (warm_start=True + n_estimators incrementado) en vez de
    reentrenar desde cero. Simétrico a RetrainWithRealReport, pero
    para el modelo de anomalías.

    Importante -- a diferencia del reentrenamiento de eficiencia, aquí
    NO se usa ningún campo de 'report' como target: todas las ventanas
    generadas se etiquetan como normales (is_anomaly=False), asumiendo
    que una fermentación que llegó a 'completed' es un proceso sano.
    El reporte solo se usa para saber QUÉ session_id ya terminó y
    poder pedir su serie de tiempo real. Si en el futuro el backend
    expone qué timestamps fueron anómalos dentro de una sesión
    completada, ese dato debería incorporarse aquí en vez de asumir
    todo normal.

    El escalador NO se reajusta (no se hace fit_transform de nuevo):
    se reutiliza el scaler ya entrenado para mantener la misma
    distribución de referencia entre reentrenamientos incrementales.
    """

    def __init__(
        self,
        model_repository: ModelRepository,
        reading_repository: SensorReadingRepository,
        readings_to_profile: ReadingsToProfile | None = None,
        window_builder: AnomalyWindowBuilder | None = None,
    ) -> None:
        self._model_repository = model_repository
        self._reading_repository = reading_repository
        self._converter = readings_to_profile or ReadingsToProfile()
        self._window_builder = window_builder or AnomalyWindowBuilder()

    def execute(self, report: FermentationReportDTO) -> dict:
        if not self._model_repository.exists(ANOMALY_MODEL_FILENAME):
            raise FileNotFoundError(
                "No existe un modelo de anomalías base entrenado. Ejecuta el "
                "entrenamiento inicial (/training/anomaly/upload) antes de "
                "reentrenar incrementalmente."
            )

        readings = self._reading_repository.get_by_session_id(report.session_id)
        profile = self._converter.execute(readings, fermentation_id=f"session-{report.session_id}")

        df = pd.DataFrame(profile.to_records())
        windows = self._window_builder.build(df)

        if not windows:
            raise ValueError(
                f"session_id={report.session_id} no tiene suficientes lecturas para "
                f"generar ventanas de anomalía (mínimo 2 puntos de tiempo)."
            )

        X = np.array([feat for feat, _ in windows])

        model: IsolationForest = self._model_repository.load(ANOMALY_MODEL_FILENAME)
        scaler = self._model_repository.load(ANOMALY_SCALER_FILENAME)
        X_scaled = scaler.transform(X)

        model.set_params(warm_start=True, n_estimators=model.n_estimators + WARM_START_TREES_INCREMENT)
        model.fit(X_scaled)

        self._model_repository.save(model, ANOMALY_MODEL_FILENAME)

        return {
            "session_id": report.session_id,
            "n_windows_used": len(windows),
            "n_estimators_total": model.n_estimators,
            "status": "model_updated",
        }