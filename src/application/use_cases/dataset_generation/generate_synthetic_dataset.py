import numpy as np

from src.application.use_cases.simulation.simulate_fermentation import SimulateFermentation
from src.domain.entities.fermentation_profile import FermentationProfile
from src.domain.entities.kinetic_parameters import KineticParameters, YPS_MAXIMO_TEORICO


class GenerateSyntheticDataset:
    """
    Use case: genera un dataset sintético de N fermentaciones usando
    el simulador, variando parámetros, agregando ruido instrumental
    e inyectando anomalías.

    Responsabilidad única: producir registros de entrenamiento desde
    el simulador. No entrena modelos, no hace feature engineering.
    """

    ANOMALY_RATE = 0.10

    def __init__(self, seed: int = 42, simulator: SimulateFermentation | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._simulator = simulator or SimulateFermentation()

    def execute(self, n: int) -> list[dict]:
        records = []
        for _ in range(n):
            params = self._sample_parameters()
            profile = self._simulator.execute(params, model="logistic")
            profile = self._add_sensor_noise(profile)

            is_anomaly = self._rng.random() < self.ANOMALY_RATE
            anomaly_type = None
            if is_anomaly:
                profile, anomaly_type = self._inject_anomaly(profile)

            for row in profile.to_records():
                row["is_anomaly"] = is_anomaly
                row["anomaly_type"] = anomaly_type
                row["final_efficiency_percent"] = profile.final_efficiency_percent
                row["source"] = "synthetic"
                records.append(row)

        return records

    def _sample_parameters(self) -> KineticParameters:
        base = KineticParameters.calibrado_sacharomyces()
        rng = self._rng

        def vary(value: float, pct: float = 0.15) -> float:
            return float(value * (1 + rng.normal(0, pct)))

        yps = min(vary(base.Yps, 0.05), YPS_MAXIMO_TEORICO - 1e-4)
        xm = max(vary(base.Xm, 0.20), 5.0)
        x0 = min(vary(base.X0, 0.20), xm - 0.1)

        return KineticParameters(
            mu_max=max(vary(base.mu_max, 0.15), 0.01),
            Xm=xm,
            Yxs=max(vary(base.Yxs, 0.15), 0.05),
            Yps=yps,
            S0=max(vary(base.S0, 0.10), 10.0),
            X0=max(x0, 0.1),
            tf=max(vary(base.tf, 0.10), 24.0),
        )

    def _add_sensor_noise(self, profile: FermentationProfile) -> FermentationProfile:
        rng = self._rng
        n = len(profile.time_hours)
        t_norm = profile.time_hours / profile.time_hours[-1]

        def drift(scale: float) -> np.ndarray:
            return t_norm * rng.uniform(-scale, scale)

        return FermentationProfile(
            parameters=profile.parameters,
            time_hours=profile.time_hours,
            biomass=profile.biomass,
            sugar=profile.sugar,
            ethanol=profile.ethanol,
            id=profile.id,
            ph=profile.ph + rng.normal(0, 0.05, n) + drift(0.05),
            temperature_celsius=profile.temperature_celsius + rng.normal(0, 0.2, n) + drift(0.3),
            turbidity=np.maximum(profile.turbidity + rng.normal(0, 0.15, n) + drift(0.1), 0.0),
            conductivity=np.maximum(profile.conductivity + rng.normal(0, 30, n) + drift(20), 0.0),
            alcohol_percent=np.maximum(profile.alcohol_percent + rng.normal(0, 0.3, n) + drift(0.2), 0.0),
        )

    def _inject_anomaly(self, profile: FermentationProfile) -> tuple[FermentationProfile, str]:
        anomaly_types = ["stuck_ph", "temp_spike", "conductivity_jump", "stuck_alcohol"]
        anomaly_type = self._rng.choice(anomaly_types)

        n = len(profile.time_hours)
        start = int(n * 0.5) + self._rng.integers(0, int(n * 0.3))
        duration = self._rng.integers(int(n * 0.05), int(n * 0.15))
        end = min(start + duration, n)

        ph = profile.ph.copy()
        temperature = profile.temperature_celsius.copy()
        conductivity = profile.conductivity.copy()
        alcohol = profile.alcohol_percent.copy()

        if anomaly_type == "stuck_ph":
            ph[start:end] = ph[start]
        elif anomaly_type == "temp_spike":
            spike = self._rng.uniform(4, 8)
            temperature[start:end] += spike
            if end < n:
                recovery = np.exp(-np.arange(0, n - end) * 0.1)
                temperature[end:] += spike * recovery
        elif anomaly_type == "conductivity_jump":
            conductivity[start:end] += self._rng.uniform(150, 300)
        elif anomaly_type == "stuck_alcohol":
            alcohol[start:] = alcohol[start]

        modified = FermentationProfile(
            parameters=profile.parameters,
            time_hours=profile.time_hours,
            biomass=profile.biomass,
            sugar=profile.sugar,
            ethanol=profile.ethanol,
            id=profile.id,
            ph=ph,
            temperature_celsius=temperature,
            turbidity=profile.turbidity,
            conductivity=conductivity,
            alcohol_percent=alcohol,
        )
        return modified, anomaly_type