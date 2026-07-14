from pathlib import Path

import pandas as pd

from src.application.use_cases.shared.lab_file_to_profile import LabFileToProfile
from src.application.use_cases.training.train_anomaly_model import TrainAnomalyModel
from src.domain.repositories.model_repository import ModelRepository
from src.infrastructure.parsers.lab_file_reader import LabFileReader

ANOMALY_MODEL_FILENAME = "iforest_anomaly.pkl"
ANOMALY_SCALER_FILENAME = "scaler_anomaly.pkl"


class TrainAnomalyFromFiles:
    """
    Entrena el IsolationForest desde cero con N archivos subidos.
    Funciona con cualquiera de los dos formatos, porque el modelo de
    anomalías solo usa ph/temperatura/turbidez/conductividad/alcohol%,
    no azúcar/etanol/biomasa. Todas las filas se marcan is_anomaly=False
    (son datos normales de laboratorio, sin anomalías etiquetadas).

    Aviso: TrainAnomalyModel usa ventanas deslizantes de tamaño 10
    (WINDOW_SIZE). Un archivo con pocas filas (ej. tu Sacharomyces.xlsx
    con 11 puntos) genera muy pocas muestras de entrenamiento -- sube
    varios archivos o considera interpolar más puntos si el modelo
    sale con métricas pobres.
    """

    def __init__(self, model_repository: ModelRepository) -> None:
        self._model_repository = model_repository
        self._reader = LabFileReader()
        self._converter = LabFileToProfile()
        self._trainer = TrainAnomalyModel()

    def execute(self, sources: list[tuple[Path, str]]) -> dict:
        frames = []
        for path, fermentation_id in sources:
            df, fmt = self._reader.read(path)
            profile = self._converter.execute(df, fmt, fermentation_id)
            records = profile.to_records()
            for row in records:
                row["is_anomaly"] = False
            frames.append(pd.DataFrame(records))

        combined = pd.concat(frames, ignore_index=True)
        model, scaler, metrics = self._trainer.execute(combined)

        self._model_repository.save(model, ANOMALY_MODEL_FILENAME)
        self._model_repository.save(scaler, ANOMALY_SCALER_FILENAME)

        return {"n_fermentations": len(sources), "n_rows": len(combined), "metrics": metrics, "status": "model_trained"}