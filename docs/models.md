# Modelos de Machine Learning

[← Volver al README](../README.md)

El servicio utiliza dos modelos de Machine Learning en producción, más un simulador matemático (no un modelo de ML entrenado) que sirve como generador de datos sintéticos.

## 1. Predicción de eficiencia — `XGBRegressor`

| Aspecto | Detalle |
|---|---|
| **Algoritmo** | `XGBRegressor` (XGBoost), `sklearn.preprocessing.StandardScaler` para normalizar features |
| **Objetivo del modelo** | Predecir la **eficiencia final (%)** de una fermentación en curso, usando solo la información disponible hasta el 50 % del tiempo transcurrido, para poder alertar tempranamente si una fermentación va a rendir mal. |
| **Archivo del modelo** | `models/xgboost_efficiency.pkl` |
| **Archivo del scaler** | `models/scaler_efficiency.pkl` |
| **Entradas** | Serie de tiempo del **primer 50 %** de una fermentación: `time_hours`, `ph`, `temperature_c`, `turbidity`, `conductivity`, `alcohol_percent` (todas listas de igual longitud). |
| **Feature engineering** | `ExtractPredictionFeatures`: por cada uno de los 5 sensores calcula 10 features estadístico-temporales (`mean`, `std`, `min`, `max`, `slope`, `accel`, `autocorr`, `range_1h`, `q25`, `q75`) → 50 features, más 4 features de interacción (`growth_efficiency_ratio`, `alcohol_vs_growth`, `conductivity_range`, `temp_stability`) → **54 features totales**. |
| **Salida** | `efficiency_percent: float` — porcentaje de eficiencia estimado (redondeado a 2 decimales). |
| **Formato de datos esperado (entrada API)** | JSON `SensorWindowDTO`: listas paralelas de igual longitud (mínimo 2 puntos en `time_hours`). Ver [docs/api.md](api.md#post-apiv1predictefficiency). |
| **Target real (entrenamiento)** | `final_efficiency_percent` calculado por balance de masa: `etanol / azúcar_consumida / 0.511 * 100` (`YPS_MAXIMO_TEORICO`, límite estequiométrico Gay-Lussac), o `efficiency_override` provisto explícitamente para archivos formato `wide`. |
| **Entrenamiento** | `TrainEfficiencyModel`. Con ≥ 15 muestras: split train/val/test (64/16/20), `early_stopping_rounds=20`, métricas `mae`, `rmse`, `r2`. Con < 15 muestras: entrena con el 100 % de los datos sin evaluación, marca `validated: false` y devuelve advertencia — el modelo resultante debe considerarse **no validado**. |
| **Reentrenamiento incremental** | `RetrainWithRealReport`: warm-start (`xgb_model=model.get_booster()`) agregando 10 árboles nuevos por cada fermentación real completada, sin reajustar el scaler. |

## 2. Detección de anomalías — `IsolationForest`

| Aspecto | Detalle |
|---|---|
| **Algoritmo** | `IsolationForest` (no supervisado), `StandardScaler` |
| **Objetivo del modelo** | Detectar lecturas de sensor anómalas durante una fermentación en curso (p. ej. pH estancado, pico de temperatura, salto de conductividad, alcohol estancado), en tiempo real. |
| **Archivo del modelo** | `models/iforest_anomaly.pkl` |
| **Archivo del scaler** | `models/scaler_anomaly.pkl` |
| **Entradas** | Lectura actual de los 5 sensores + historial de las últimas ~2 horas (ventana deslizante). |
| **Feature engineering** | `ExtractAnomalyFeatures` (objetivo: <5ms): valores actuales de `ph`, `turbidity`, `conductivity`, `alcohol_percent`, `temperature_c`; pendientes (`slope`, regresión lineal) de `ph`, `turbidity`, `alcohol`; desviación estándar de `ph` y `conductivity` → **10 features**. |
| **Salida** | `is_anomaly: bool` (`True` si `model.predict()` devuelve `-1`) y `anomaly_score: float` (`-model.score_samples()`, redondeado a 4 decimales; a mayor score, más anómalo). |
| **Formato de datos esperado (entrada API)** | JSON `AnomalyRequestDTO`: `current` (snapshot de 5 sensores), `history_hours` (lista de timestamps) y `history` (lista de snapshots, misma longitud que `history_hours`). Ver [docs/api.md](api.md#post-apiv1detectanomaly). |
| **Entrenamiento** | `TrainAnomalyModel`: se entrena **solo con ventanas normales** (`is_anomaly=False`); las ventanas anómalas (si existen, ej. datos sintéticos con anomalías inyectadas) se usan únicamente para evaluar (`precision`, `recall`, `f1`). Con < 20 ventanas totales, el resultado se marca `validated: false`. `warm_start=True` queda fijo en el modelo para permitir reentrenamiento incremental posterior. |
| **Ventaneo** | `AnomalyWindowBuilder`, tamaño de ventana `10` (`DEFAULT_WINDOW_SIZE`), adaptativo (`min(window_size, n-1)`) cuando la fermentación tiene pocos puntos, para no generar cero muestras. |
| **Reentrenamiento incremental** | `RetrainAnomalyWithRealReport`: agrega 10 árboles (`WARM_START_TREES_INCREMENT`) por cada fermentación real completada, asumiendo que toda fermentación que llegó a `completed` es normal (todas sus ventanas se etiquetan `is_anomaly=False`); no reajusta el scaler. |

## 3. Simulador cinético (generador de datos, no un modelo de ML)

| Aspecto | Detalle |
|---|---|
| **Componente** | `SimulateFermentation` + `SensorProfileMapper` |
| **Objetivo** | Resolver numéricamente (`scipy.integrate.odeint`) las ecuaciones diferenciales de crecimiento microbiano y producir un perfil de fermentación sintético completo, usado para generar datasets de entrenamiento cuando no hay suficientes datos reales. |
| **Modelos cinéticos disponibles** | `logistic` (**recomendado**, calibrado con datos reales, R²=0.9955) y `monod` (disponible para comparación, no calibrado). |
| **Entradas** | `KineticParameters` (`mu_max`, `Xm`, `Yxs`, `Yps`, `S0`, `X0`, `tf`). |
| **Salidas** | `FermentationProfile`: series de tiempo de biomasa, azúcar, etanol y las 5 lecturas de sensor derivadas (`SensorProfileMapper`, calibrado contra datos reales, curva de pH R²=0.981). |

## Ciclo de vida y versionado de modelos

- Los artefactos (`.pkl`) se serializan con `joblib` y viven en `MODELS_DIR` (filesystem del contenedor), no versionados en Git (excluidos en `.dockerignore`/`.gitignore`).
- La imagen Docker ejecuta `scripts/train_initial_models.py` durante el *build*, por lo que cada imagen nueva parte de un modelo base entrenado con datos sintéticos.
- El campo `model_version` (actualmente fijo en `"1.0.0"`, ver `DetectAnomaly.MODEL_VERSION` y los DTOs de resultado) identifica la versión del modelo en las inferencias persistidas y en las notificaciones publicadas; **no** se incrementa automáticamente en cada reentrenamiento incremental.
- Antes de usar cualquiera de los dos modelos, los endpoints correspondientes verifican `ModelRepository.exists(...)`; si el modelo no ha sido entrenado todavía, la API responde `503 Service Unavailable`.