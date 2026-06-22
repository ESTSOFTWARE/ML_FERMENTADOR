from src.application.use_cases.feature_engineering.extract_anomaly_features import (
    ExtractAnomalyFeatures,
)
from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO
from src.domain.repositories.model_repository import ModelRepository

ANOMALY_MODEL_FILENAME = "iforest_anomaly.pkl"
ANOMALY_SCALER_FILENAME = "scaler_anomaly.pkl"


class DetectAnomaly:
    """
    Use case: corre el Isolation Forest ya entrenado sobre la lectura
    actual + historial de 2 horas, y devuelve si es anómala + score.

    Responsabilidad única: detección pura. No entrena, no publica
    notificaciones, no decide qué sensor causó la anomalía (eso podría
    vivir en un use case aparte si se necesita más adelante).
    """

    def __init__(
        self,
        model_repository: ModelRepository,
        feature_extractor: ExtractAnomalyFeatures | None = None,
    ) -> None:
        self._repository = model_repository
        self._extractor = feature_extractor or ExtractAnomalyFeatures()

    def execute(self, request: AnomalyRequestDTO) -> tuple[bool, float]:
        if not self._repository.exists(ANOMALY_MODEL_FILENAME):
            raise FileNotFoundError("Modelo de anomalías no entrenado todavía.")

        model = self._repository.load(ANOMALY_MODEL_FILENAME)
        scaler = self._repository.load(ANOMALY_SCALER_FILENAME)

        features = self._extractor.execute(request)
        X = features.reshape(1, -1)
        X_scaled = scaler.transform(X)

        # IsolationForest: -1 = anomalía, 1 = normal
        prediction = model.predict(X_scaled)[0]
        score = float(-model.score_samples(X_scaled)[0])  # mayor = más anómalo

        is_anomaly = bool(prediction == -1)
        return is_anomaly, round(score, 4)