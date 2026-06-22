import numpy as np

from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO


class ExtractAnomalyFeatures:
    """
    Use case: extrae ~10 features compactos de la lectura actual +
    historial de 2 horas, usados como input del Isolation Forest.

    Responsabilidad única: feature engineering para anomalías.
    No sabe nada de predicción de eficiencia, no entrena nada.
    Debe ser rápido (objetivo: <5ms), por eso son pocos features.
    """

    def execute(self, request: AnomalyRequestDTO) -> np.ndarray:
        t = np.array(request.history_hours)
        ph_hist = np.array([h.ph for h in request.history])
        turbidity_hist = np.array([h.turbidity for h in request.history])
        alcohol_hist = np.array([h.alcohol_percent for h in request.history])
        conductivity_hist = np.array([h.conductivity for h in request.history])

        return np.array([
            request.current.ph,
            request.current.turbidity,
            request.current.conductivity,
            request.current.alcohol_percent,
            request.current.temperature_c,
            self._slope(t, ph_hist),
            self._slope(t, turbidity_hist),
            self._slope(t, alcohol_hist),
            float(np.std(ph_hist)),
            float(np.std(conductivity_hist)),
        ], dtype=np.float64)

    @staticmethod
    def _slope(t: np.ndarray, signal: np.ndarray) -> float:
        if len(signal) < 2:
            return 0.0
        return float(np.polyfit(t, signal, 1)[0])