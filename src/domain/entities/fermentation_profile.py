from dataclasses import dataclass, field
from uuid import UUID, uuid4

import numpy as np

from src.domain.entities.kinetic_parameters import KineticParameters, YPS_MAXIMO_TEORICO


@dataclass
class FermentationProfile:
    """
    Resultado completo de UNA fermentación (simulada o reconstruida
    de datos reales). Una instancia = una fermentación de principio a fin.
    """

    parameters: KineticParameters
    time_hours: np.ndarray
    biomass: np.ndarray
    sugar: np.ndarray
    ethanol: np.ndarray
    ph: np.ndarray
    temperature_celsius: np.ndarray
    turbidity: np.ndarray
    conductivity: np.ndarray
    alcohol_percent: np.ndarray
    id: UUID = field(default_factory=uuid4)

    @property
    def sugar_consumed(self) -> np.ndarray:
        return self.sugar[0] - self.sugar

    @property
    def yield_percent(self) -> np.ndarray:
        """Rendimiento por timestamp (%). Equivale a 'efficiency' en fermentation_reports."""
        consumed = self.sugar_consumed
        result = np.zeros_like(consumed)
        mask = consumed > 1e-9
        result[mask] = self.ethanol[mask] / consumed[mask] / YPS_MAXIMO_TEORICO * 100.0
        return result

    @property
    def final_efficiency_percent(self) -> float:
        """Target del modelo de predicción de eficiencia."""
        return float(self.yield_percent[-1])

    def first_half(self) -> "FermentationProfile":
        """Recorta al primer 50% del tiempo (lo que el modelo 've' para predecir)."""
        mid = len(self.time_hours) // 2
        return FermentationProfile(
            parameters=self.parameters,
            time_hours=self.time_hours[:mid],
            biomass=self.biomass[:mid],
            sugar=self.sugar[:mid],
            ethanol=self.ethanol[:mid],
            ph=self.ph[:mid],
            temperature_celsius=self.temperature_celsius[:mid],
            turbidity=self.turbidity[:mid],
            conductivity=self.conductivity[:mid],
            alcohol_percent=self.alcohol_percent[:mid],
            id=self.id,
        )

    def to_records(self) -> list[dict]:
        """Convierte el perfil en lista de dicts, uno por timestamp."""
        return [
            {
                "fermentation_id": str(self.id),
                "time_hours": float(self.time_hours[i]),
                "biomass_g_l": float(self.biomass[i]),
                "sugar_g_l": float(self.sugar[i]),
                "ethanol_g_l": float(self.ethanol[i]),
                "ph": float(self.ph[i]),
                "temperature_c": float(self.temperature_celsius[i]),
                "turbidity_od": float(self.turbidity[i]),
                "conductivity_us_cm": float(self.conductivity[i]),
                "alcohol_percent": float(self.alcohol_percent[i]),
                "yield_percent": float(self.yield_percent[i]),
            }
            for i in range(len(self.time_hours))
        ]