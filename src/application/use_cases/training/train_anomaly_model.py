import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

from src.domain.dtos.anomaly_request_dto import AnomalyRequestDTO, SensorSnapshotDTO
from src.application.use_cases.feature_engineering.extract_anomaly_features import (
    ExtractAnomalyFeatures,
)

WINDOW_SIZE = 10
SENSOR_COLUMN_MAP = {
    "temperature_c": "temperature_c",
    "turbidity_od": "turbidity",
    "conductivity_us_cm": "conductivity",
}


class TrainAnomalyModel:
    """
    Use case: entrena un IsolationForest desde cero usando un DataFrame
    con filas por timestamp (formato producido por GenerateSyntheticDataset
    o BuildDatasetFromCsv).

    Responsabilidad única: entrenamiento completo del modelo de
    anomalías. Es no supervisado: se entrena SOLO con ventanas
    normales (is_anomaly=False); las anómalas se usan solo para evaluar.
    """

    def __init__(self) -> None:
        self._extractor = ExtractAnomalyFeatures()

    def execute(self, df: pd.DataFrame) -> tuple[IsolationForest, StandardScaler, dict]:
        X_normal, X_all, y_all = self._build_dataset(df)

        scaler = StandardScaler()
        X_normal_s = scaler.fit_transform(X_normal)
        X_all_s = scaler.transform(X_all)

        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        model.fit(X_normal_s)

        metrics = self._evaluate(model, X_all_s, y_all)
        return model, scaler, metrics

    def _build_dataset(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        normal_rows, all_rows, all_labels = [], [], []

        for _, group in df.groupby("fermentation_id"):
            group = group.sort_values("time_hours").reset_index(drop=True)

            for i in range(WINDOW_SIZE, len(group)):
                window = group.iloc[i - WINDOW_SIZE: i]
                request = self._build_request(group, window, i)

                feat = self._extractor.execute(request)
                is_anomaly = int(group.loc[i, "is_anomaly"])

                all_rows.append(feat)
                all_labels.append(is_anomaly)
                if not is_anomaly:
                    normal_rows.append(feat)

        return np.array(normal_rows), np.array(all_rows), np.array(all_labels)

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

    @staticmethod
    def _evaluate(model: IsolationForest, X: np.ndarray, y_true: np.ndarray) -> dict:
        y_pred = (model.predict(X) == -1).astype(int)
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        return {
            "precision": report.get("1", {}).get("precision", 0.0),
            "recall": report.get("1", {}).get("recall", 0.0),
            "f1": report.get("1", {}).get("f1-score", 0.0),
        }