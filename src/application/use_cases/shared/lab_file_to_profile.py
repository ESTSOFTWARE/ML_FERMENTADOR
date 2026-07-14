"""
Convierte el DataFrame ya normalizado (por LabFileReader) en un
FermentationProfile, sin importar el formato de origen.

- "kinetic": azúcar y etanol son REALES (vienen del ensayo de
  laboratorio) -> biomasa se reconstruye por balance de masa
  (X(t) = X0 + Yxs * azúcar_consumida(t), consecuencia directa de
  las EDOs del modelo logístico, no una suposición). pH y
  Temperatura se usan tal cual, medidos. Turbidez/conductividad/
  alcohol% se derivan con SensorProfileMapper (las mismas fórmulas
  calibradas que usa el simulador), porque el archivo no las trae.
  El target de eficiencia queda BIEN calculado porque azúcar/etanol
  son reales.

- "wide": ya son lecturas de sensor -> se pivotea igual que
  ReadingsToProfile. Azúcar/etanol quedan en cero, por lo que
  final_efficiency_percent NO es confiable aquí; el llamador debe
  proveer el target por separado (ej. medido en laboratorio) si
  quiere entrenar el modelo de eficiencia con este archivo.
"""

import numpy as np
import pandas as pd

from src.application.use_cases.simulation.simulate_fermentation import SensorProfileMapper
from src.domain.entities.fermentation_profile import FermentationProfile
from src.domain.entities.kinetic_parameters import KineticParameters
from src.domain.entities.sensor_calibration import SensorCalibration
from infrastructure.parsers.lab_file_reader import FileFormat


class LabFileToProfile:
    def __init__(self, sensor_mapper: SensorProfileMapper | None = None) -> None:
        self._mapper = sensor_mapper or SensorProfileMapper(SensorCalibration.calibrado_sacharomyces())

    def execute(self, df: pd.DataFrame, file_format: FileFormat, fermentation_id: str) -> FermentationProfile:
        if file_format == "kinetic":
            return self._from_kinetic(df, fermentation_id)
        return self._from_wide(df, fermentation_id)

    def _from_kinetic(self, df: pd.DataFrame, fermentation_id: str) -> FermentationProfile:
        kp = KineticParameters.calibrado_sacharomyces()
        time_hours = df["time_hours"].to_numpy(dtype=float)

        sugar = df["azucares"].to_numpy(dtype=float) if "azucares" in df.columns else np.full_like(time_hours, kp.S0)
        ethanol = df["etanol"].to_numpy(dtype=float) if "etanol" in df.columns else np.zeros_like(time_hours)
        ethanol = np.nan_to_num(ethanol, nan=0.0)

        s0 = sugar[0]
        sugar_consumed = s0 - sugar
        biomass = kp.X0 + kp.Yxs * sugar_consumed  # balance de masa exacto del modelo logístico

        sensors = self._mapper.map_all(time_hours, biomass, sugar, ethanol)

        ph = df["ph"].to_numpy(dtype=float) if "ph" in df.columns else sensors["ph"]
        temperature = (
            df["temperatura"].to_numpy(dtype=float) if "temperatura" in df.columns else sensors["temperature_celsius"]
        )

        return FermentationProfile(
            parameters=kp,
            time_hours=time_hours,
            biomass=biomass,
            sugar=sugar,
            ethanol=ethanol,
            ph=np.nan_to_num(ph, nan=sensors["ph"]),
            temperature_celsius=np.nan_to_num(temperature, nan=sensors["temperature_celsius"]),
            turbidity=sensors["turbidity"],
            conductivity=sensors["conductivity"],
            alcohol_percent=sensors["alcohol_percent"],
            id=fermentation_id,  # ver nota abajo sobre el tipo de id
        )

    def _from_wide(self, df: pd.DataFrame, fermentation_id: str) -> FermentationProfile:
        time_hours = df["time_hours"].to_numpy(dtype=float)
        zeros = np.zeros_like(time_hours)
        kp = KineticParameters.calibrado_sacharomyces()

        def col(name: str) -> np.ndarray:
            if name not in df.columns:
                raise ValueError(f"Falta la columna '{name}' en el archivo de formato ancho.")
            return df[name].interpolate().bfill().ffill().to_numpy(dtype=float)

        return FermentationProfile(
            parameters=kp,
            time_hours=time_hours,
            biomass=zeros,
            sugar=zeros,
            ethanol=col("alcohol_percent") * SensorCalibration.calibrado_sacharomyces().alcohol_por_etanol
            if "alcohol_percent" in df.columns
            else zeros,
            ph=col("ph"),
            temperature_celsius=col("temperature_c"),
            turbidity=col("turbidity"),
            conductivity=col("conductivity"),
            alcohol_percent=col("alcohol_percent"),
            id=fermentation_id,
        )