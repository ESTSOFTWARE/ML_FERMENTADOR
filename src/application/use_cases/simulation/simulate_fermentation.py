from abc import ABC, abstractmethod

import numpy as np
from scipy.integrate import odeint

from src.domain.entities.fermentation_profile import FermentationProfile
from src.domain.entities.kinetic_parameters import KineticParameters
from src.domain.entities.sensor_calibration import SensorCalibration

PUNTOS_DE_TIEMPO = 600


class SensorProfileMapper:
    """
    Convierte (X, S, E, t) en las 5 lecturas de sensores.
    Vive aquí porque es lógica de orquestación de la simulación,
    usada únicamente por SimulateFermentation.
    """

    def __init__(self, calibration: SensorCalibration) -> None:
        self._cal = calibration

    def map_all(
        self,
        time_hours: np.ndarray,
        biomass: np.ndarray,
        sugar: np.ndarray,
        ethanol: np.ndarray,
    ) -> dict[str, np.ndarray]:
        c = self._cal
        consumed = sugar[0] - sugar
        return {
            "ph": c.ph_inicial + c.ph_delta_max * (1 - np.exp(-c.ph_velocidad * time_hours)),
            "temperature_celsius": np.full_like(time_hours, fill_value=c.temperatura_base),
            "turbidity": c.od_por_biomasa * biomass,
            "conductivity": np.maximum(c.conductividad_inicial - c.conductividad_por_azucar * consumed, 0.0),
            "alcohol_percent": ethanol / c.alcohol_por_etanol,
        }


class _KineticModel(ABC):
    """Estrategia interna: resuelve las EDO según el modelo cinético elegido."""

    @abstractmethod
    def odes(self, state: list[float], t: float, parameters: KineticParameters) -> list[float]:
        raise NotImplementedError


class _LogisticModel(_KineticModel):
    """
    Modelo Logístico. Recomendado: calibrado con datos reales (R²=0.9955).
    mu = mu_max * (1 - X/Xm)
    """

    def odes(self, state: list[float], t: float, parameters: KineticParameters) -> list[float]:
        X, S, E = state
        X = max(X, 0.0)
        mu = max(parameters.mu_max * (1 - X / parameters.Xm), 0.0)
        dXdt = mu * X
        dSdt = -(1 / parameters.Yxs) * mu * X
        dEdt = parameters.Yps * (1 / parameters.Yxs) * mu * X
        return [dXdt, dSdt, dEdt]


class _MonodModel(_KineticModel):
    """Modelo de Monod. Disponible para comparación, no calibrado. Usa Xm como aproximación de Ks."""

    def odes(self, state: list[float], t: float, parameters: KineticParameters) -> list[float]:
        X, S, E = state
        S = max(S, 0.0)
        ks = parameters.Xm
        mu = parameters.mu_max * S / (ks + S)
        dXdt = mu * X
        dSdt = -(1 / parameters.Yxs) * mu * X
        dEdt = parameters.Yps * (1 / parameters.Yxs) * mu * X
        return [dXdt, dSdt, dEdt]


class SimulateFermentation:
    """
    Use case: corre el simulador matemático para UNA fermentación y
    devuelve un FermentationProfile completo.

    Responsabilidad única: dado unos parámetros cinéticos, producir
    un perfil de fermentación. No genera datasets, no agrega ruido,
    no entrena nada — eso vive en otros use cases.
    """

    _MODELS: dict[str, _KineticModel] = {
        "logistic": _LogisticModel(),
        "monod": _MonodModel(),
    }

    def __init__(self, sensor_mapper: SensorProfileMapper | None = None) -> None:
        self._mapper = sensor_mapper or SensorProfileMapper(SensorCalibration.calibrado_sacharomyces())

    def execute(
        self,
        parameters: KineticParameters,
        model: str = "logistic",
    ) -> FermentationProfile:
        if model not in self._MODELS:
            raise ValueError(f"Modelo '{model}' no soportado. Opciones: {list(self._MODELS)}")

        kinetic_model = self._MODELS[model]
        time_hours = np.linspace(0, parameters.tf, PUNTOS_DE_TIEMPO)
        y0 = [parameters.X0, parameters.S0, 0.0]

        solution = odeint(kinetic_model.odes, y0, time_hours, args=(parameters,))

        biomass = np.maximum(solution[:, 0], 0.0)
        sugar = np.maximum(solution[:, 1], 0.0)
        ethanol = np.maximum(solution[:, 2], 0.0)

        sensors = self._mapper.map_all(time_hours, biomass, sugar, ethanol)

        return FermentationProfile(
            parameters=parameters,
            time_hours=time_hours,
            biomass=biomass,
            sugar=sugar,
            ethanol=ethanol,
            ph=sensors["ph"],
            temperature_celsius=sensors["temperature_celsius"],
            turbidity=sensors["turbidity"],
            conductivity=sensors["conductivity"],
            alcohol_percent=sensors["alcohol_percent"],
        )