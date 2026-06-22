import numpy as np

from src.application.use_cases.feature_engineering.extract_prediction_features import (
    ExtractPredictionFeatures,
)
from src.domain.dtos.sensor_window_dto import SensorWindowDTO
from src.domain.entities.fermentation_profile import FermentationProfile
from src.domain.entities.kinetic_parameters import KineticParameters
from src.domain.repositories.model_repository import ModelRepository

EFFICIENCY_MODEL_FILENAME = "xgboost_efficiency.pkl"
EFFICIENCY_SCALER_FILENAME = "scaler_efficiency.pkl"


class PredictEfficiency:
    """
    Use case: corre el modelo XGBoost ya entrenado sobre una ventana
    de sensores y devuelve la eficiencia estimada.

    Responsabilidad única: predicción pura. No entrena, no publica
    notificaciones, no decide si es momento de predecir (eso lo
    decide ProcessRealtimeReading viendo elapsed_hours).
    """

    def __init__(
        self,
        model_repository: ModelRepository,
        feature_extractor: ExtractPredictionFeatures | None = None,
    ) -> None:
        self._repository = model_repository
        self._extractor = feature_extractor or ExtractPredictionFeatures()

    def execute(self, window: SensorWindowDTO) -> float:
        if not self._repository.exists(EFFICIENCY_MODEL_FILENAME):
            raise FileNotFoundError("Modelo de eficiencia no entrenado todavía.")

        model = self._repository.load(EFFICIENCY_MODEL_FILENAME)
        scaler = self._repository.load(EFFICIENCY_SCALER_FILENAME)

        profile = self._window_to_profile(window)
        features = self._extractor.execute(profile)

        X = np.array(list(features.values())).reshape(1, -1)
        X_scaled = scaler.transform(X)

        prediction = float(model.predict(X_scaled)[0])
        return round(prediction, 2)

    @staticmethod
    def _window_to_profile(window: SensorWindowDTO) -> FermentationProfile:
        """
        Envuelve la ventana de sensores en un FermentationProfile
        mínimo solo para reutilizar ExtractPredictionFeatures, que
        opera sobre esa entidad. Biomasa/azúcar/etanol no se conocen
        en tiempo real -> se rellenan en cero (no afectan las features
        de predicción, que solo usan los 5 sensores).
        """
        n = len(window.time_hours)
        zeros = np.zeros(n)
        placeholder_params = KineticParameters.calibrado_sacharomyces()

        return FermentationProfile(
            parameters=placeholder_params,
            time_hours=np.array(window.time_hours),
            biomass=zeros,
            sugar=zeros,
            ethanol=zeros,
            ph=np.array(window.ph),
            temperature_celsius=np.array(window.temperature_c),
            turbidity=np.array(window.turbidity),
            conductivity=np.array(window.conductivity),
            alcohol_percent=np.array(window.alcohol_percent),
        )