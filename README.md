# Nich-Ká ML Service

Microservicio de **Machine Learning (ML) y análisis de datos de fermentación** para la plataforma Nich-Ká. Predice la eficiencia final de una fermentación y detecta anomalías en el proceso a partir de lecturas de sensores (pH, temperatura, turbidez, conductividad y % de alcohol), tanto en modo síncrono (HTTP) como en tiempo real (RabbitMQ).

> **Versión documentada:** `1.0.0` (según `main.py`, campo `version` de la app FastAPI).

---

## Índice de documentación

| Documento | Contenido |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Arquitectura del servicio, capas, responsabilidades, componentes e integraciones externas |
| [docs/data-flow.md](docs/data-flow.md) | Flujo de generación de datos, entrenamiento, inferencia en tiempo real y reentrenamiento incremental |
| [docs/models.md](docs/models.md) | Modelos de ML utilizados: objetivo, entradas, salidas, features y formato de datos |
| [docs/api.md](docs/api.md) | Endpoints expuestos: método, ruta, parámetros, cuerpo, respuestas y códigos de estado |
| [docs/configuration.md](docs/configuration.md) | Variables de entorno, dependencias y librerías |
| [docs/deployment.md](docs/deployment.md) | Instalación local, ejecución y proceso de despliegue (Docker) |

---

## Descripción general

El servicio resuelve dos problemas de negocio sobre el proceso de fermentación:

1. **Predicción de eficiencia final** (`%`) usando un modelo `XGBoost` entrenado sobre el primer 50 % del tiempo de una fermentación.
2. **Detección de anomalías** en el proceso usando un `Isolation Forest` no supervisado sobre ventanas deslizantes de lecturas recientes.

Ambos modelos pueden entrenarse desde datos **sintéticos** (simulador cinético propio), desde **archivos de laboratorio** (CSV/XLSX) o reentrenarse **incrementalmente** con fermentaciones reales ya completadas (batch nocturno o evento puntual).

Para el detalle completo de arquitectura y flujo de datos ver [docs/architecture.md](docs/architecture.md) y [docs/data-flow.md](docs/data-flow.md).

## Inicio rápido

```bash
git clone https://github.com/ESTSOFTWARE/ML_FERMENTADOR.git
cd nicka-ml-service

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env          # completar credenciales, ver docs/configuration.md

uvicorn main:app --reload --port 8000
```

Guía completa de instalación, configuración y despliegue: [docs/deployment.md](docs/deployment.md).

## Estructura del proyecto

```
├── data/                # Datasets generados (sintéticos) y reales
├── models/               # Artefactos de modelos entrenados (.pkl)
├── scripts/
│   └── train_initial_models.py    # Entrenamiento inicial con datos sintéticos
├── src/
│   ├── application/
│   │   └── use_cases/    # Lógica de negocio (casos de uso), agrupada por dominio
│   │       ├── dataset_generation/
│   │       ├── feature_engineering/
│   │       ├── inference/
│   │       ├── realtime/
│   │       ├── shared/
│   │       ├── simulation/
│   │       └── training/
│   ├── domain/
│   │   ├── dtos/          # Contratos de entrada/salida (Pydantic)
│   │   ├── entities/      # Entidades de dominio
│   │   └── repositories/  # Puertos (interfaces abstractas)
│   └── infrastructure/
│       ├── adapters/      # Implementaciones concretas de los puertos
│       ├── config/        # Configuración (variables de entorno)
│       ├── controllers/   # Traducción HTTP <-> casos de uso
│       ├── parsers/       # Lectura/normalización de archivos de laboratorio
│       └── routes/        # Definición de endpoints FastAPI
├── Dockerfile
├── main.py                # Punto de entrada (FastAPI + scheduler + consumer)
└── requirements.txt
```

El proyecto sigue **arquitectura limpia / hexagonal** (Domain → Application → Infrastructure). El detalle de cada capa y su responsabilidad está en [docs/architecture.md](docs/architecture.md).

## Tecnologías principales

FastAPI · XGBoost · scikit-learn · pandas / numpy · SciPy (integración de EDOs) · PostgreSQL · RabbitMQ · APScheduler · Docker.

Ver el listado completo en [docs/configuration.md](docs/configuration.md#dependencias-y-librerías).

## Enlaces internos

- [Arquitectura](docs/architecture.md)
- [Flujo de procesamiento de datos](docs/data-flow.md)
- [Modelos de ML](docs/models.md)
- [API / Endpoints](docs/api.md)
- [Configuración y variables de entorno](docs/configuration.md)
- [Despliegue](docs/deployment.md)