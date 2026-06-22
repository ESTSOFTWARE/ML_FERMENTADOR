import numpy as np
import pandas as pd

from src.domain.entities.fermentation_profile import FermentationProfile
from src.domain.entities.kinetic_parameters import KineticParameters
from src.domain.entities.sensor_reading import SensorReading


class ReadingsToProfile:
    """
    Use case: convierte una lista de SensorReading (lecturas crudas,
    sin importar si vienen de un CSV o de las tablas reales de
    sensores del backend) en un FermentationProfile utilizable por
    ExtractPredictionFeatures.

    Responsabilidad única: pivotear lecturas dispersas (una fila por
    lectura, por tipo de sensor) a series de tiempo alineadas (una
    fila por timestamp, una columna por sensor), e interpolar huecos.

    No conoce el origen de las lecturas (CSV, HTTP, etc) — eso es
    responsabilidad del repositorio que las entrega.
    """

    def execute(self, readings: list[SensorReading], fermentation_id: str) -> FermentationProfile:
        if not readings:
            raise ValueError("No se puede construir un perfil sin lecturas.")

        df = self._to_wide_dataframe(readings)
        df = self._interpolate_gaps(df)

        time_hours = df["time_hours"].values
        zeros = np.zeros_like(time_hours)

        # KineticParameters es requerido por FermentationProfile, pero
        # para datos reales no se conocen los parámetros cinéticos
        # "verdaderos" -> se usan los calibrados como placeholder,
        # ya que no se usan en el cálculo de features (solo las
        # series de sensores importan para ExtractPredictionFeatures).
        placeholder_params = KineticParameters.calibrado_sacharomyces()

        return FermentationProfile(
            parameters=placeholder_params,
            time_hours=time_hours,
            biomass=zeros,
            sugar=zeros,
            ethanol=df.get("alcohol", pd.Series(zeros)).values,
            ph=df["ph"].values,
            temperature_celsius=df["temperature"].values,
            turbidity=df["turbidity"].values,
            conductivity=df["conductivity"].values,
            alcohol_percent=df["alcohol"].values,
        )

    @staticmethod
    def _to_wide_dataframe(readings: list[SensorReading]) -> pd.DataFrame:
        rows = [
            {
                "time_hours": r.timestamp,
                "sensor_type": r.sensor_type.value,
                "value": r.value,
            }
            for r in readings
        ]
        long_df = pd.DataFrame(rows)
        wide = long_df.pivot_table(index="time_hours", columns="sensor_type", values="value")
        return wide.reset_index().sort_values("time_hours")

    @staticmethod
    def _interpolate_gaps(df: pd.DataFrame) -> pd.DataFrame:
        expected_columns = ["ph", "temperature", "turbidity", "conductivity", "alcohol"]
        for col in expected_columns:
            if col not in df.columns:
                df[col] = np.nan
        return df.interpolate(method="linear").bfill().ffill()