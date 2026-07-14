from pathlib import Path

from src.application.use_cases.shared.lab_file_to_profile import LabFileToProfile
from src.application.use_cases.training.train_efficiency_model import TrainEfficiencyModel
from src.domain.repositories.model_repository import ModelRepository
from src.infrastructure.parsers.lab_file_reader import LabFileReader

EFFICIENCY_MODEL_FILENAME = "xgboost_efficiency.pkl"
EFFICIENCY_SCALER_FILENAME = "scaler_efficiency.pkl"
MIN_FERMENTATIONS = 5


class TrainEfficiencyFromFiles:
    """
    Entrena el modelo de eficiencia DESDE CERO con N archivos subidos
    (uno por fermentación). Archivos "kinetic" calculan su target
    automáticamente (azúcar/etanol reales). Archivos "wide" requieren
    un efficiency_override explícito, porque no traen esa información.
    """

    def __init__(self, model_repository: ModelRepository) -> None:
        self._model_repository = model_repository
        self._reader = LabFileReader()
        self._converter = LabFileToProfile()
        self._trainer = TrainEfficiencyModel()

    def execute(self, sources: list[tuple[Path, str, float | None]]) -> dict:
        if len(sources) < MIN_FERMENTATIONS:
            raise ValueError(
                f"Se necesitan al menos {MIN_FERMENTATIONS} fermentaciones para entrenar "
                f"desde cero (llegaron {len(sources)})."
            )

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