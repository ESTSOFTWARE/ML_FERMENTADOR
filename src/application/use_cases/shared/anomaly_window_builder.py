import numpy as np
import pandas as pd

from src.application.use_cases.feature_engineering.extract_anomaly_features import (
    ExtractAnomalyFeatures,
)
from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO, SensorSnapshotDTO

DEFAULT_WINDOW_SIZE = 10


class AnomalyWindowBuilder:
    """
    Construye ventanas deslizantes de features de anomalía a partir de
    un DataFrame de UNA fermentación (columnas esperadas: time_hours,
    ph, temperature_c, turbidity_od, conductivity_us_cm,
    alcohol_percent, e is_anomaly opcional).

    El tamaño de ventana se ADAPTA cuando la fermentación tiene pocos
    puntos de tiempo (ej. una sola fermentación real subida a mano,
    con 10 filas): en vez de exigir WINDOW_SIZE=10 fijo -- lo que
    generaría CERO muestras si el archivo tiene <=10 filas, porque
    range(10, 10) está vacío -- usa min(WINDOW_SIZE, n-1).

    Esto permite entrenar/reentrenar con muy pocos datos, a costa de
    calidad estadística: una sola ventana con historial corto no
    representa bien la dinámica normal de la fermentación. Es
    aceptable para pruebas de pipeline o para arrancar el modelo,
    pero se debe reentrenar con más fermentaciones reales antes de
    confiar en las predicciones para notificaciones en producción.
    """

    def __init__(
        self,
        window_size: int = DEFAULT_WINDOW_SIZE,
        extractor: ExtractAnomalyFeatures | None = None,
    ) -> None:
        self._window_size = window_size
        self._extractor = extractor or ExtractAnomalyFeatures()

    def build(self, group: pd.DataFrame) -> list[tuple[np.ndarray, int]]:
        group = group.sort_values("time_hours").reset_index(drop=True)
        n = len(group)
        if n < 2:
            return []

        effective_window = min(self._window_size, n - 1)
        rows: list[tuple[np.ndarray, int]] = []

        for i in range(effective_window, n):
            window = group.iloc[i - effective_window : i]
            request = self._build_request(group, window, i)
            feat = self._extractor.execute(request)
            label = int(group.loc[i, "is_anomaly"]) if "is_anomaly" in group.columns else 0
            rows.append((feat, label))

        return rows

    @staticmethod
    def _build_request(group: pd.DataFrame, window: pd.DataFrame, i: int) -> AnomalyRequestDTO:
        current = SensorSnapshotDTO(
            ph=group.loc[i, "ph"],
            temperature_c=group.loc[i, "temperature_c"],
            turbidity=group.loc[i, "turbidity_od"],
            conductivity=group.loc[i, "conductivity_us_cm"],
            alcohol_percent=group.loc[i, "alcohol_percent"],
        )
        history = [
            SensorSnapshotDTO(
                ph=row["ph"],
                temperature_c=row["temperature_c"],
                turbidity=row["turbidity_od"],
                conductivity=row["conductivity_us_cm"],
                alcohol_percent=row["alcohol_percent"],
            )
            for _, row in window.iterrows()
        ]
        return AnomalyRequestDTO(
            current=current,
            history_hours=window["time_hours"].tolist(),
            history=history,
        )