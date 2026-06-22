# src/application/use_cases/training/retrain_with_real_report.py

import numpy as np
from xgboost import XGBRegressor

from src.application.use_cases.feature_engineering.extract_prediction_features import (
    ExtractPredictionFeatures,
)
from src.application.use_cases.shared.readings_to_profile import ReadingsToProfile
from src.domain.dtos.fermentation_report_dto import FermentationReportDTO
from src.domain.repositories.model_repository import ModelRepository
from src.domain.repositories.sensor_reading_repository import SensorReadingRepository

EFFICIENCY_MODEL_FILENAME = "xgboost_efficiency.pkl"
EFFICIENCY_SCALER_FILENAME = "scaler_efficiency.pkl"


class RetrainWithRealReport:
    """
    Use case: reentrena incrementalmente el modelo de eficiencia con
    UNA fermentación real recién completada, sin descartar el
    conocimiento ganado durante el entrenamiento sintético inicial.

    Responsabilidad única: dado un session_id ya completado, obtener
    su serie de tiempo REAL completa (vía SensorReadingRepository,
    consultando las 7 tablas de sensores del backend), reconstruir un
    FermentationProfile, extraer el MISMO espacio de 54 features que
    usa el modelo base, y hacer warm-start del XGBoost existente.

    El reporte (FermentationReportDTO) se usa solo para el target real
    (efficiency) y para validar que la sesión ya terminó -- la
    predicción usa las lecturas reales, no los campos resumen del
    reporte.
    """

    def __init__(
        self,
        model_repository: ModelRepository,
        reading_repository: SensorReadingRepository,
        readings_to_profile: ReadingsToProfile | None = None,
        feature_extractor: ExtractPredictionFeatures | None = None,
    ) -> None:
        self._model_repository = model_repository
        self._reading_repository = reading_repository
        self._converter = readings_to_profile or ReadingsToProfile()
        self._extractor = feature_extractor or ExtractPredictionFeatures()

    def execute(self, report: FermentationReportDTO) -> dict:
        if report.efficiency is None:
            raise ValueError(
                f"El reporte de session_id={report.session_id} no tiene "
                f"'efficiency' calculada todavía; no se puede reentrenar con él."
            )

        if not self._model_repository.exists(EFFICIENCY_MODEL_FILENAME):
            raise FileNotFoundError(
                "No existe un modelo base entrenado. Ejecuta el entrenamiento "
                "inicial con datos sintéticos antes de reentrenar incrementalmente."
            )

        readings = self._reading_repository.get_by_session_id(report.session_id)
        profile = self._converter.execute(readings, fermentation_id=f"session-{report.session_id}")

        features = self._extractor.execute(profile)
        X = np.array(list(features.values())).reshape(1, -1)
        y = np.array([report.efficiency])

        model: XGBRegressor = self._model_repository.load(EFFICIENCY_MODEL_FILENAME)
        scaler = self._model_repository.load(EFFICIENCY_SCALER_FILENAME)

        X_scaled = scaler.transform(X)

        # Warm start: agrega árboles incrementales al modelo existente
        # en vez de reentrenar desde cero.
        updated_model = XGBRegressor(
            n_estimators=10,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            verbosity=0,
        )
        updated_model.fit(X_scaled, y, xgb_model=model.get_booster())

        self._model_repository.save(updated_model, EFFICIENCY_MODEL_FILENAME)

        return {
            "session_id": report.session_id,
            "retrained_with_efficiency": report.efficiency,
            "n_readings_used": len(readings),
            "status": "model_updated",
        }