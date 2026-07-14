import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

from src.application.use_cases.shared.anomaly_window_builder import AnomalyWindowBuilder

MIN_NORMAL_SAMPLES = 1  # con 0 no hay absolutamente nada con qué entrenar


class TrainAnomalyModel:
    """
    Use case: entrena un IsolationForest desde cero usando un DataFrame
    con filas por timestamp (formato producido por GenerateSyntheticDataset
    o BuildDatasetFromCsv/LabFileToProfile).

    Responsabilidad única: entrenamiento completo del modelo de
    anomalías. Es no supervisado: se entrena SOLO con ventanas
    normales (is_anomaly=False); las anómalas se usan solo para evaluar.

    warm_start=True queda fijo en el modelo resultante para permitir
    reentrenamiento incremental posterior (ver RetrainAnomalyWithRealReport)
    sin tener que reconstruir el estimador desde configuración.
    """

    def __init__(self, window_builder: AnomalyWindowBuilder | None = None) -> None:
        self._window_builder = window_builder or AnomalyWindowBuilder()

    def execute(self, df: pd.DataFrame) -> tuple[IsolationForest, StandardScaler, dict]:
        X_normal, X_all, y_all = self._build_dataset(df)

        if len(X_normal) < MIN_NORMAL_SAMPLES:
            raise ValueError(
                "No se generó ninguna ventana de entrenamiento normal a partir de los "
                "archivos subidos. Verifica que cada fermentación tenga al menos 2 "
                "puntos de tiempo, y que no todas las filas estén marcadas is_anomaly=True."
            )

        scaler = StandardScaler()
        X_normal_s = scaler.fit_transform(X_normal)
        X_all_s = scaler.transform(X_all) if len(X_all) else X_normal_s

        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42, warm_start=True)
        model.fit(X_normal_s)

        metrics = self._evaluate(model, X_all_s, y_all) if len(X_all) else {
            "precision": 0.0, "recall": 0.0, "f1": 0.0,
        }
        metrics["n_windows"] = len(X_all)
        metrics["validated"] = len(X_all) >= 20
        if not metrics["validated"]:
            metrics["warning"] = (
                f"Entrenado con solo {len(X_all)} ventana(s). Este modelo NO está "
                f"evaluado de forma confiable -- agrega más fermentaciones antes de "
                f"usarlo para notificaciones en producción."
            )

        return model, scaler, metrics

    def _build_dataset(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        normal_rows, all_rows, all_labels = [], [], []

        for _, group in df.groupby("fermentation_id"):
            for feat, label in self._window_builder.build(group):
                all_rows.append(feat)
                all_labels.append(label)
                if not label:
                    normal_rows.append(feat)

        return np.array(normal_rows), np.array(all_rows), np.array(all_labels)

    @staticmethod
    def _evaluate(model: IsolationForest, X: np.ndarray, y_true: np.ndarray) -> dict:
        y_pred = (model.predict(X) == -1).astype(int)
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        return {
            "precision": report.get("1", {}).get("precision", 0.0),
            "recall": report.get("1", {}).get("recall", 0.0),
            "f1": report.get("1", {}).get("f1-score", 0.0),
        }