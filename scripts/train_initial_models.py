import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.application.use_cases.dataset_generation.generate_synthetic_dataset import (
    GenerateSyntheticDataset,
)
from src.application.use_cases.training.train_anomaly_model import TrainAnomalyModel
from src.application.use_cases.training.train_efficiency_model import TrainEfficiencyModel
from src.domain.entities.fermentation_profile import FermentationProfile
from src.domain.entities.kinetic_parameters import KineticParameters
from src.infrastructure.adapters.joblib_model_repository import JoblibModelRepository
from src.infrastructure.adapters.parquet_dataset_repository import ParquetDatasetRepository
from src.infrastructure.config.settings import settings


def _records_to_profiles(df: pd.DataFrame) -> list[FermentationProfile]:
    """Reconstruye FermentationProfile a partir de las filas planas del dataset."""
    profiles = []
    placeholder_params = KineticParameters.calibrado_sacharomyces()

    for _, group in df.groupby("fermentation_id"):
        group = group.sort_values("time_hours").reset_index(drop=True)
        profile = FermentationProfile(
            parameters=placeholder_params,
            time_hours=group["time_hours"].values,
            biomass=group["biomass_g_l"].values,
            sugar=group["sugar_g_l"].values,
            ethanol=group["ethanol_g_l"].values,
            ph=group["ph"].values,
            temperature_celsius=group["temperature_c"].values,
            turbidity=group["turbidity_od"].values,
            conductivity=group["conductivity_us_cm"].values,
            alcohol_percent=group["alcohol_percent"].values,
        )
        profiles.append(profile)

    return profiles


def main() -> None:
    dataset_repo = ParquetDatasetRepository(settings.data_dir)
    model_repo = JoblibModelRepository(settings.models_dir)

    print(f"[1/4] Generando {settings.n_fermentations} fermentaciones sintéticas...")
    generator = GenerateSyntheticDataset(seed=settings.random_seed)
    records = generator.execute(settings.n_fermentations)
    dataset_repo.save(records, "fermentations.parquet")
    print(f"      {len(records)} filas guardadas en data/generated/fermentations.parquet")

    df = dataset_repo.load("fermentations.parquet")
    profiles = _records_to_profiles(df)

    print("[2/4] Entrenando modelo de predicción de eficiencia (XGBoost)...")
    trainer_pred = TrainEfficiencyModel()
    model_pred, scaler_pred, metrics_pred = trainer_pred.execute(profiles)
    model_repo.save(model_pred, "xgboost_efficiency.pkl")
    model_repo.save(scaler_pred, "scaler_efficiency.pkl")
    print(
        f"      MAE: {metrics_pred['mae']:.2f}%  "
        f"RMSE: {metrics_pred['rmse']:.2f}%  "
        f"R²: {metrics_pred['r2']:.4f}"
    )

    print("[3/4] Entrenando modelo de detección de anomalías (Isolation Forest)...")
    trainer_anom = TrainAnomalyModel()
    model_anom, scaler_anom, metrics_anom = trainer_anom.execute(df)
    model_repo.save(model_anom, "iforest_anomaly.pkl")
    model_repo.save(scaler_anom, "scaler_anomaly.pkl")
    print(
        f"      Precision: {metrics_anom['precision']:.2f}  "
        f"Recall: {metrics_anom['recall']:.2f}  "
        f"F1: {metrics_anom['f1']:.2f}"
    )

    print("[4/4] Listo. Modelos guardados en models/:")
    for f in sorted(settings.models_dir.glob("*.pkl")):
        print(f"      {f.name}")


if __name__ == "__main__":
    main()