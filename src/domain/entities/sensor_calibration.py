from dataclasses import dataclass


@dataclass(frozen=True)
class SensorCalibration:
    """
    Coeficientes de conversión: (X, S, E, t) → lecturas de sensores.
    Calibrado contra el Excel real (curva de pH con R²=0.981).

    Nota: 'conversion_factor' de efficiency_formula (BD, = 0.51) y
    YPS_MAXIMO_TEORICO (0.511) son el mismo concepto con distinta
    precisión. Se mantiene 0.511 aquí como verdad del dominio; el
    valor de la BD se usa solo si se desea sincronizar dinámicamente
    desde el backend (no implementado todavía).
    """

    od_por_biomasa: float = 0.7
    ph_inicial: float = 4.60
    ph_delta_max: float = 0.332
    ph_velocidad: float = 0.0874
    temperatura_base: float = 30.0
    alcohol_por_etanol: float = 12.9
    conductividad_inicial: float = 2000.0
    conductividad_por_azucar: float = 8.0

    def __post_init__(self) -> None:
        for nombre, valor in self.__dict__.items():
            if valor <= 0:
                raise ValueError(f"'{nombre}' debe ser > 0, recibido: {valor}")

    @classmethod
    def calibrado_sacharomyces(cls) -> "SensorCalibration":
        return cls()