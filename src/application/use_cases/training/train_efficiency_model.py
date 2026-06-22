import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from src.application.use_cases.feature_engineering.extract_prediction_features import (
    ExtractPredictionFeatures,
)
from src.domain.entities.fermentation_profile import FermentationProfile


class TrainEfficiencyModel:
    """
    Use case: entrena un XGBRegressor desde cero usando una lista de
    FermentationProfile (sin importar si vienen del simulador, de un
    CSV real o se reconstruyeron de reportes).

    Responsabilidad única: entrenamiento completo (train/val/test split,
    fit, evaluación). No genera datos, no hace feature engineering
    propio (delega a ExtractPredictionFeatures), no persiste nada
    (eso es responsabilidad del adapter que reciba el resultado).
    """

    def __init__(self) -> None:
        self._extractor = ExtractPredictionFeatures()

    def execute(
        self, profiles: list[FermentationProfile]
    ) -> tuple[XGBRegressor, StandardScaler, dict]:
        X, y = self._build_dataset(profiles)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_val_s = scaler.transform(X_val)
        X_test_s = scaler.transform(X_test)

        model = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            early_stopping_rounds=20,
            random_state=42,
            verbosity=0,
        )
        model.fit(X_train_s, y_train, eval_set=[(X_val_s, y_val)], verbose=False)

        metrics = self._evaluate(model, X_test_s, y_test)
        return model, scaler, metrics

    def _build_dataset(self, profiles: list[FermentationProfile]) -> tuple[np.ndarray, np.ndarray]:
        rows, targets = [], []
        for profile in profiles:
            rows.append(self._extractor.execute(profile))
            targets.append(profile.final_efficiency_percent)
        return pd.DataFrame(rows).values, np.array(targets)

    @staticmethod
    def _evaluate(model: XGBRegressor, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        y_pred = model.predict(X_test)
        return {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
        }