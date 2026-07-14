"""
Lee un archivo de laboratorio (csv o xlsx) subido por el usuario y lo
normaliza a un DataFrame con columna 'time_hours', detectando cuál de
los dos formatos soportados trae:

- "kinetic": datos crudos de laboratorio tipo Sacharomyces.xlsx
  (Hora, Azúcares, Etanol, pH, Temperatura). No trae turbidez,
  conductividad ni alcohol% -- se derivan en la capa de aplicación.
- "wide": columnas de sensor ya listas (ph, temperature_c, turbidity,
  conductivity, alcohol_percent) -- mismo formato que
  CsvSensorReadingRepository ya espera.

IMPORTANTE sobre el orden de detección: 'ph' aparece en AMBOS
formatos, así que no sirve como marcador exclusivo. 'kinetic' se
revisa PRIMERO porque sus marcadores (azucares, etanol) son
exclusivos de ese formato -- si se revisara 'wide' primero, cualquier
archivo kinetic con columna 'ph' (que siempre la tiene) se
clasificaría incorrectamente como 'wide'.
"""

import unicodedata
from pathlib import Path
from typing import Literal

import pandas as pd

FileFormat = Literal["wide", "kinetic"]

_TIME_KEYWORDS = {"hora", "time_hours", "tiempo"}
_KINETIC_MARKER_COLUMNS = {"azucares", "etanol"}
_WIDE_MARKER_COLUMNS = {"ph", "temperature_c", "turbidity", "conductivity", "alcohol_percent"}


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(text)) if unicodedata.category(c) != "Mn")


def _normalize_col(col: object) -> str:
    return _strip_accents(str(col)).strip().lower().replace(" ", "_")


class LabFileReader:
    def read(self, path: Path) -> tuple[pd.DataFrame, FileFormat]:
        raw = (
            pd.read_excel(path, header=None)
            if path.suffix.lower() in (".xlsx", ".xls")
            else pd.read_csv(path, header=None)
        )

        header_row = self._find_header_row(raw)
        df = raw.iloc[header_row + 1:].copy()
        df.columns = [_normalize_col(c) for c in raw.iloc[header_row]]
        df = df.dropna(axis=1, how="all")
        df = df.apply(pd.to_numeric, errors="coerce")

        time_col = "hora" if "hora" in df.columns else "time_hours"
        df = df.dropna(subset=[time_col]).rename(columns={time_col: "time_hours"}).reset_index(drop=True)

        fmt = self._detect_format(set(df.columns), path)
        return df, fmt

    @staticmethod
    def _find_header_row(raw: pd.DataFrame) -> int:
        for i in range(min(10, len(raw))):
            values = {_normalize_col(v) for v in raw.iloc[i].tolist() if pd.notna(v)}
            if values & _TIME_KEYWORDS:
                return i
        raise ValueError("No se encontró columna de tiempo ('Hora'/'time_hours') en las primeras 10 filas.")

    @staticmethod
    def _detect_format(columns: set[str], path: Path) -> FileFormat:
        # 'kinetic' primero: azucares/etanol son marcadores exclusivos.
        # 'ph' NO se usa como decisor porque aparece en ambos formatos.
        if columns & _KINETIC_MARKER_COLUMNS:
            return "kinetic"
        if columns & _WIDE_MARKER_COLUMNS:
            return "wide"
        raise ValueError(
            f"No se reconoce el formato de '{path.name}'. Se esperaban columnas de "
            f"laboratorio crudo ({_KINETIC_MARKER_COLUMNS}) o columnas de sensor "
            f"({_WIDE_MARKER_COLUMNS})."
        )