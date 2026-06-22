from dataclasses import dataclass

YPS_MAXIMO_TEORICO = 0.511  # límite estequiométrico Gay-Lussac (g etanol / g glucosa)


@dataclass(frozen=True)
class KineticParameters:
    """
    Parámetros cinéticos del modelo Logístico, calibrados con datos
    reales de Saccharomyces (R²=0.9955).

    mu_max : tasa máxima de crecimiento (h⁻¹)
    Xm     : biomasa máxima soportada (g/L)
    Yxs    : rendimiento biomasa/sustrato (g biomasa / g azúcar)
    Yps    : rendimiento etanol/sustrato  (g etanol  / g azúcar)
    S0     : azúcar inicial (g/L)
    X0     : biomasa inicial / inóculo (g/L)
    tf     : duración total de la fermentación (h)
    """

    mu_max: float
    Xm: float
    Yxs: float
    Yps: float
    S0: float
    X0: float
    tf: float

    def __post_init__(self) -> None:
        for nombre, valor in self.__dict__.items():
            if valor <= 0:
                raise ValueError(f"'{nombre}' debe ser > 0, recibido: {valor}")

        if self.Yps > YPS_MAXIMO_TEORICO:
            raise ValueError(
                f"Yps={self.Yps} supera el límite teórico ({YPS_MAXIMO_TEORICO})."
            )

        if self.X0 >= self.Xm:
            raise ValueError(f"X0={self.X0} no puede ser >= Xm={self.Xm}.")

    @classmethod
    def calibrado_sacharomyces(cls) -> "KineticParameters":
        """Ajustado por mínimos cuadrados contra el Excel real (modelo Logístico)."""
        return cls(
            mu_max=0.068,
            Xm=22.2,
            Yxs=0.172,
            Yps=0.474,
            S0=100.02,
            X0=5.5,
            tf=120.0,
        )