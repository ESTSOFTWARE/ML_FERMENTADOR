from pydantic import BaseModel, Field, model_validator


class SensorWindowDTO(BaseModel):
    """
    Serie de tiempo del primer 50% de una fermentación, usada como
    input para predecir la eficiencia final.
    Todas las listas deben tener la misma longitud (un valor por timestamp).
    """

    time_hours: list[float] = Field(min_length=2)
    ph: list[float]
    temperature_c: list[float]
    turbidity: list[float]
    conductivity: list[float]
    alcohol_percent: list[float]

    @model_validator(mode="after")
    def validar_misma_longitud(self) -> "SensorWindowDTO":
        n = len(self.time_hours)
        campos = [self.ph, self.temperature_c, self.turbidity, self.conductivity, self.alcohol_percent]
        if any(len(c) != n for c in campos):
            raise ValueError("Todas las listas de sensores deben tener la misma longitud que time_hours.")
        return self