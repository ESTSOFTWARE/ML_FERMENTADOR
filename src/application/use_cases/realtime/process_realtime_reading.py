from src.application.use_cases.realtime.detect_anomaly import DetectAnomaly
from src.application.use_cases.realtime.predict_efficiency import PredictEfficiency
from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO
from src.domain.dtos.anomaly_result_dto import AnomalyResultDTO
from src.domain.dtos.efficiency_result_dto import EfficiencyResultDTO
from src.domain.dtos.realtime_reading_dto import RealtimeReadingDTO
from src.domain.dtos.sensor_window_dto import SensorWindowDTO
from src.domain.repositories.notification_publisher import NotificationPublisher

EFFICIENCY_PREDICTION_THRESHOLD_RATIO = 0.5


class ProcessRealtimeReading:
    """
    Use case orquestador: dado una lectura nueva de una sesión activa,
    corre detección de anomalías (siempre) y predicción de eficiencia
    (solo si ya se alcanzó el 50% del tiempo PLANEADO de la sesión),
    y publica ambos resultados al canal de notificaciones.

    Responsabilidad única: orquestación del flujo en tiempo real.
    No contiene lógica de modelos (delega a PredictEfficiency y
    DetectAnomaly), no sabe cómo se publica (delega a
    NotificationPublisher).
    """

    def __init__(
        self,
        predict_efficiency: PredictEfficiency,
        detect_anomaly: DetectAnomaly,
        notification_publisher: NotificationPublisher,
    ) -> None:
        self._predict_efficiency = predict_efficiency
        self._detect_anomaly = detect_anomaly
        self._publisher = notification_publisher

    def execute(self, reading: RealtimeReadingDTO) -> dict:
        anomaly_result = self._run_anomaly_detection(reading)
        self._publisher.publish_anomaly_result(anomaly_result)

        efficiency_result = None
        if self._should_predict_efficiency(reading):
            efficiency_result = self._run_efficiency_prediction(reading)
            self._publisher.publish_efficiency_result(efficiency_result)

        return {
            "session_id": reading.session_id,
            "anomaly_detected": anomaly_result.is_anomaly,
            "efficiency_predicted": efficiency_result is not None,
        }

    @staticmethod
    def _should_predict_efficiency(reading: RealtimeReadingDTO) -> bool:
        halfway_point = reading.planned_duration_hours * EFFICIENCY_PREDICTION_THRESHOLD_RATIO
        return reading.elapsed_hours >= halfway_point

    def _run_anomaly_detection(self, reading: RealtimeReadingDTO) -> AnomalyResultDTO:
        request = AnomalyRequestDTO(
            current=reading.current,
            history_hours=reading.history_hours,
            history=reading.history,
        )
        is_anomaly, score = self._detect_anomaly.execute(request)

        return AnomalyResultDTO(
            session_id=reading.session_id,
            circuit_id=reading.circuit_id,
            is_anomaly=is_anomaly,
            anomaly_score=score,
            detected_at=reading.timestamp,
        )

    def _run_efficiency_prediction(self, reading: RealtimeReadingDTO) -> EfficiencyResultDTO:
        window = SensorWindowDTO(
            time_hours=reading.history_hours + [reading.elapsed_hours],
            ph=[h.ph for h in reading.history] + [reading.current.ph],
            temperature_c=[h.temperature_c for h in reading.history] + [reading.current.temperature_c],
            turbidity=[h.turbidity for h in reading.history] + [reading.current.turbidity],
            conductivity=[h.conductivity for h in reading.history] + [reading.current.conductivity],
            alcohol_percent=[h.alcohol_percent for h in reading.history] + [reading.current.alcohol_percent],
        )
        predicted = self._predict_efficiency.execute(window)

        return EfficiencyResultDTO(
            session_id=reading.session_id,
            circuit_id=reading.circuit_id,
            predicted_efficiency_percent=predicted,
            predicted_at=reading.timestamp,
        )