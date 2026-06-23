from datetime import datetime

from src.application.use_cases.feature_engineering.extract_anomaly_features import (
    ExtractAnomalyFeatures,
)
from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO
from src.domain.entities.anomaly_inference import AnomalyInference
from src.domain.repositories.inference_repository import InferenceRepository
from src.domain.repositories.model_repository import ModelRepository

ANOMALY_MODEL_FILENAME = "iforest_anomaly.pkl"
ANOMALY_SCALER_FILENAME = "scaler_anomaly.pkl"
MODEL_VERSION = "1.0.0"


class DetectAnomaly:
    """
    Use case: corre el Isolation Forest ya entrenado sobre la lectura
    actual + historial de 2 horas, persiste la inferencia en la BD
    local, y devuelve si es anómala + score.

    Responsabilidad única: detección + persistencia de inferencia.
    No entrena, no publica notificaciones.
    """

    def __init__(
        self,
        model_repository: ModelRepository,
        inference_repository: InferenceRepository,
        feature_extractor: ExtractAnomalyFeatures | None = None,
    ) -> None:
        self._model_repository = model_repository
        self._inference_repository = inference_repository
        self._extractor = feature_extractor or ExtractAnomalyFeatures()

    def execute(
        self,
        request: AnomalyRequestDTO,
        session_id: int | None = None,
        circuit_id: int | None = None,
        timestamp: datetime | None = None,
    ) -> tuple[bool, float]:
        if not self._model_repository.exists(ANOMALY_MODEL_FILENAME):
            raise FileNotFoundError("Modelo de anomalías no entrenado todavía.")

        model = self._model_repository.load(ANOMALY_MODEL_FILENAME)
        scaler = self._model_repository.load(ANOMALY_SCALER_FILENAME)

        features = self._extractor.execute(request)
        X = features.reshape(1, -1)
        X_scaled = scaler.transform(X)

        prediction = model.predict(X_scaled)[0]
        score = float(-model.score_samples(X_scaled)[0])
        is_anomaly = bool(prediction == -1)

        self._persist(request, is_anomaly, score, session_id, circuit_id, timestamp)

        return is_anomaly, round(score, 4)

    def _persist(
        self,
        request: AnomalyRequestDTO,
        is_anomaly: bool,
        score: float,
        session_id: int | None,
        circuit_id: int | None,
        timestamp: datetime | None,
    ) -> None:
        inference = AnomalyInference(
            session_id=session_id,
            circuit_id=circuit_id,
            timestamp=timestamp or datetime.utcnow(),
            ph=request.current.ph,
            temperature_c=request.current.temperature_c,
            turbidity=request.current.turbidity,
            conductivity=request.current.conductivity,
            alcohol_percent=request.current.alcohol_percent,
            history_length=len(request.history),
            is_anomaly=is_anomaly,
            anomaly_score=score,
            model_version=MODEL_VERSION,
        )
        self._inference_repository.save(inference)