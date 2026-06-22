# Nicka ML Service

Un servicio de machine learning moderno y escalable.

## Descripción

Este proyecto proporciona funcionalidades de machine learning para procesamiento de datos, entrenamiento de modelos e inferencia en tiempo real.

## Requisitos

- Python 3.8+
- Docker (opcional)
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd nicka-ml-service
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Ejecutar localmente

```bash
python main.py
```

### Usar Docker

```bash
docker-compose up
```

## Estructura del Proyecto

```
├── src/               # Código fuente principal
├── data/              # Datos (generados y reales)
├── models/            # Modelos entrenados
├── scripts/           # Scripts de utilidad
├── tests/             # Tests
└── main.py            # Punto de entrada
```

## Configuración

Las variables de entorno se configuran en el archivo `.env`. Asegúrate de crear este archivo con las configuraciones necesarias.

## API

El servicio expone endpoints HTTP para:
- Predicciones
- Detección de anomalías
- Entrenamiento de modelos
- Procesamiento en tiempo real

Consulta la documentación de rutas para más detalles.

## Testing

```bash
pytest
```

## Deployment

Para desplegar en producción, usar Docker:

```bash
docker build -t nicka-ml-service .
docker run -p 8000:8000 nicka-ml-service
```

## Contribuciones

Las contribuciones son bienvenidas. Favor de seguir los estándares del proyecto.

## Licencia

Consulta el archivo LICENSE para más información.

## Soporte

Para soporte o preguntas, contacta al equipo de desarrollo.