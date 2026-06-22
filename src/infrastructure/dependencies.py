from functools import lru_cache

from src.application.use_cases.feature_engineering.extract_anomaly_features import (
    ExtractAnomalyFeatures,
)
from src.application.use_cases.feature_engineering.extract_prediction_features import (
    ExtractPredictionFeatures,
)
from src.application.use_cases.realtime.detect_anomaly import DetectAnomaly
from src.application.use_cases.realtime.predict_efficiency import PredictEfficiency
from src.application.use_cases.realtime.process_realtime_reading import ProcessRealtimeReading
from src.application.use_cases.shared.readings_to_profile import ReadingsToProfile
from src.application.use_cases.training.retrain_with_real_report import RetrainWithRealReport
from src.infrastructure.adapters.http_fermentation_report_repository import (
    HttpFermentationReportRepository,
)
from src.infrastructure.adapters.http_sensor_reading_repository import HttpSensorReadingRepository
from src.infrastructure.adapters.joblib_model_repository import JoblibModelRepository
from src.infrastructure.adapters.websocket_notification_publisher import (
    WebsocketNotificationPublisher,
)
from src.infrastructure.config.settings import settings
from src.infrastructure.controllers.anomaly_controller import AnomalyController
from src.infrastructure.controllers.predict_controller import PredictController
from src.infrastructure.controllers.realtime_controller import RealtimeController
from src.infrastructure.controllers.training_controller import TrainingController


@lru_cache
def get_model_repository() -> JoblibModelRepository:
    return JoblibModelRepository(settings.models_dir)


@lru_cache
def get_fermentation_report_repository() -> HttpFermentationReportRepository:
    return HttpFermentationReportRepository(
        base_url=settings.backend_base_url,
        reports_endpoint=settings.backend_reports_endpoint,
        timeout_seconds=settings.backend_api_timeout_seconds,
    )


@lru_cache
def get_sensor_reading_repository() -> HttpSensorReadingRepository:
    return HttpSensorReadingRepository(
        base_url=settings.backend_base_url,
        sensors_endpoint=settings.backend_sensors_endpoint,
        timeout_seconds=settings.backend_api_timeout_seconds,
    )


@lru_cache
def get_notification_publisher() -> WebsocketNotificationPublisher:
    return WebsocketNotificationPublisher(
        base_url=settings.backend_base_url,
        notifications_endpoint=settings.backend_notifications_endpoint,
        timeout_seconds=settings.backend_api_timeout_seconds,
    )


def get_predict_controller() -> PredictController:
    use_case = PredictEfficiency(get_model_repository(), ExtractPredictionFeatures())
    return PredictController(use_case)


def get_anomaly_controller() -> AnomalyController:
    use_case = DetectAnomaly(get_model_repository(), ExtractAnomalyFeatures())
    return AnomalyController(use_case)


def get_realtime_controller() -> RealtimeController:
    predict_use_case = PredictEfficiency(get_model_repository(), ExtractPredictionFeatures())
    detect_use_case = DetectAnomaly(get_model_repository(), ExtractAnomalyFeatures())
    orchestrator = ProcessRealtimeReading(
        predict_efficiency=predict_use_case,
        detect_anomaly=detect_use_case,
        notification_publisher=get_notification_publisher(),
    )
    return RealtimeController(orchestrator)


def get_training_controller() -> TrainingController:
    use_case = RetrainWithRealReport(
        model_repository=get_model_repository(),
        reading_repository=get_sensor_reading_repository(),
        readings_to_profile=ReadingsToProfile(),
        feature_extractor=ExtractPredictionFeatures(),
    )
    return TrainingController(use_case)