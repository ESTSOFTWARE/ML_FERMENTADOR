import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.domain.dtos.fermentation_report_dto import FermentationReportDTO
from src.infrastructure.controllers.training_controller import TrainingController
from src.infrastructure.dependencies import get_training_controller

router = APIRouter(prefix="/training", tags=["Entrenamiento"])
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/report-completed")
def report_completed(
    report: FermentationReportDTO,
    controller: TrainingController = Depends(get_training_controller),
) -> dict:
    try:
        return controller.handle_report_completed(report)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _save_uploads(files: list[UploadFile], tmp_dir: Path) -> list[Path]:
    paths = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(422, f"Extensión no soportada: {f.filename} (solo {ALLOWED_EXTENSIONS})")
        dest = tmp_dir / f.filename
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        paths.append(dest)
    return paths


@router.post(
    "/efficiency/upload",
    summary="Entrena el XGBoost de eficiencia desde archivos csv/xlsx",
)
def train_efficiency_upload(
    files: list[UploadFile] = File(..., description="Un archivo por fermentación"),
    fermentation_ids: list[str] | None = Form(None, description="Opcional, mismo orden que files"),
    efficiencies: list[float] | None = Form(
        None, description="Requerido solo para archivos formato 'wide'; mismo orden que files"
    ),
    controller: TrainingController = Depends(get_training_controller),
) -> dict:
    if fermentation_ids and len(fermentation_ids) != len(files):
        raise HTTPException(422, "fermentation_ids debe tener el mismo largo que files")
    if efficiencies and len(efficiencies) != len(files):
        raise HTTPException(422, "efficiencies debe tener el mismo largo que files")

    with tempfile.TemporaryDirectory() as tmp:
        paths = _save_uploads(files, Path(tmp))
        sources = [
            (
                paths[i],
                fermentation_ids[i] if fermentation_ids else f"upload-{i}-{paths[i].stem}",
                efficiencies[i] if efficiencies else None,
            )
            for i in range(len(paths))
        ]
        try:
            return controller.handle_efficiency_upload(sources)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc


@router.post(
    "/anomaly/upload",
    summary="Entrena el Isolation Forest de anomalías desde archivos csv/xlsx",
)
def train_anomaly_upload(
    files: list[UploadFile] = File(..., description="Un archivo por fermentación"),
    fermentation_ids: list[str] | None = Form(None),
    controller: TrainingController = Depends(get_training_controller),
) -> dict:
    if fermentation_ids and len(fermentation_ids) != len(files):
        raise HTTPException(422, "fermentation_ids debe tener el mismo largo que files")

    with tempfile.TemporaryDirectory() as tmp:
        paths = _save_uploads(files, Path(tmp))
        sources = [
            (paths[i], fermentation_ids[i] if fermentation_ids else f"upload-{i}-{paths[i].stem}")
            for i in range(len(paths))
        ]
        try:
            return controller.handle_anomaly_upload(sources)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc