from pathlib import Path

from src.application.use_cases.shared.lab_file_to_profile import LabFileToProfile
from src.application.use_cases.training.train_efficiency_model import TrainEfficiencyModel
from src.domain.repositories.model_repository import ModelRepository
from src.infrastructure.parsers.lab_file_reader import LabFileReader

EFFICIENCY_MODEL_FILENAME = "xgboost_efficiency.pkl"
EFFICIENCY_SCALER_FILENAME = "scaler_efficiency.pkl"


class TrainEfficiencyFromFiles:
    """
    Entrena el modelo de eficiencia DESDE CERO con N archivos subidos
    (uno por fermentación). Archivos "kinetic" calculan su target
    automáticamente (azúcar/etanol reales). Archivos "wide" requieren
    un efficiency_override explícito, porque no traen esa información.

    No exige un mínimo de fermentaciones: se puede entrenar con 1 sola
    mientras se acumulan más datos reales. TrainEfficiencyModel decide
    internamente si hay suficientes muestras para hacer split de
    validación/test (metrics["validated"] indica si el resultado está
    evaluado o no). Con pocas fermentaciones, el modelo resultante debe
    tratarse como provisional -- no lo uses para predicciones reales
    hasta acumular más datos.
    """

    def __init__(self, model_repository: ModelRepository) -> None:
        self._model_repository = model_repository
        self._reader = LabFileReader()
        self._converter = LabFileToProfile()
        self._trainer = TrainEfficiencyModel()

    def execute(self, sources: list[tuple[Path, str, float | None]]) -> dict:
        if not sources:
            raise ValueError("Debes subir al menos 1 archivo para entrenar.")

        profiles, targets = [], []
        for path, fermentation_id, efficiency_override in sources:
            df, fmt = self._reader.read(path)

            if fmt == "wide" and efficiency_override is None:
                raise ValueError(
                    f"'{path.name}' es formato ancho (solo lecturas de sensor) y no trae "
                    f"target de eficiencia. Debes enviar 'efficiencies' para este archivo."
                )

            profile = self._converter.execute(df, fmt, fermentation_id)
            profiles.append(profile)
            targets.append(efficiency_override)

        model, scaler, metrics = self._trainer.execute(profiles, targets=targets)

        self._model_repository.save(model, EFFICIENCY_MODEL_FILENAME)
        self._model_repository.save(scaler, EFFICIENCY_SCALER_FILENAME)

        return {"n_fermentations": len(profiles), "metrics": metrics, "status": "model_trained"}