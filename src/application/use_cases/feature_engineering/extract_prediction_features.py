import numpy as np

from src.domain.entities.fermentation_profile import FermentationProfile

SENSOR_FIELDS = {
    "ph": "ph",
    "temperature_c": "temperature_celsius",
    "turbidity": "turbidity",
    "conductivity": "conductivity",
    "alcohol": "alcohol_percent",
}


class ExtractPredictionFeatures:
    """
    Use case: extrae ~50 features estadísticos y temporales del primer
    50% de una fermentación, usados como input del modelo XGBoost de
    predicción de eficiencia.

    Responsabilidad única: feature engineering para predicción.
    No sabe nada de anomalías, no entrena nada.
    """

    def execute(self, profile: FermentationProfile) -> dict[str, float]:
        half = profile.first_half()
        features: dict[str, float] = {}

        for short_name, attr_name in SENSOR_FIELDS.items():
            signal = getattr(half, attr_name)
            features.update(self._temporal_features(short_name, signal, half.time_hours))

        features.update(self._interaction_features(features))
        return features

    def _temporal_features(self, name: str, signal: np.ndarray, time: np.ndarray) -> dict[str, float]:
        slope = float(np.polyfit(time, signal, 1)[0])
        velocity = np.gradient(signal, time)
        accel = float(np.gradient(velocity, time)[-1])
        autocorr = float(np.corrcoef(signal[:-1], signal[1:])[0, 1]) if len(signal) > 1 else 0.0

        mask_1h = time >= (time[-1] - 1.0)
        range_1h = float(signal[mask_1h].max() - signal[mask_1h].min()) if mask_1h.any() else 0.0

        return {
            f"{name}_mean": float(np.mean(signal)),
            f"{name}_std": float(np.std(signal)),
            f"{name}_min": float(np.min(signal)),
            f"{name}_max": float(np.max(signal)),
            f"{name}_slope": slope,
            f"{name}_accel": accel,
            f"{name}_autocorr": autocorr,
            f"{name}_range_1h": range_1h,
            f"{name}_q25": float(np.quantile(signal, 0.25)),
            f"{name}_q75": float(np.quantile(signal, 0.75)),
        }

    @staticmethod
    def _interaction_features(f: dict[str, float]) -> dict[str, float]:
        od_growth = f.get("turbidity_slope", 1e-6)
        ph_drop = -f.get("ph_slope", 1e-6)
        return {
            "growth_efficiency_ratio": od_growth / (ph_drop + 1e-6),
            "alcohol_vs_growth": f.get("alcohol_slope", 0.0) / (od_growth + 1e-6),
            "conductivity_range": f.get("conductivity_q75", 0.0) - f.get("conductivity_min", 0.0),
            "temp_stability": 1.0 / (f.get("temperature_c_std", 1e-6) + 1e-6),
        }