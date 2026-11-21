"""Datasets router: create, upload, profile, list."""
from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.models.entities import Dataset, DatasetVersion, Table, User
from app.schemas.api import DatasetCreate, DatasetOut

router = APIRouter(prefix="/datasets", tags=["datasets"])

_ALLOWED_EXTS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}


@router.post("", response_model=DatasetOut, status_code=201)
def create_dataset(body: DatasetCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Dataset:
    """Create a dataset record in the user's workspace."""
    ds = Dataset(workspace_id=user.workspace_id, name=body.name, description=body.description, created_by=user.id)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


@router.get("", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Dataset]:
    """List datasets in the current workspace."""
    return db.query(Dataset).filter(Dataset.workspace_id == user.workspace_id).all()


@router.post("/{dataset_id}/upload")
def upload_file(
    dataset_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Validate and store an uploaded file, then profile it deterministically."""
    settings = get_settings()
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == user.workspace_id).first()
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(status_code=422, detail=f"Unsupported extension {ext}")
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, f"{dataset_id}_{uuid.uuid4().hex}{ext}")
    data = file.file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    with open(dest, "wb") as fh:
        fh.write(data)

    profile: dict[str, Any] = {}
    try:
        import sys

        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        from analytics.profiler import profile_file

        profile = profile_file(dest)
    except Exception as exc:  # noqa: BLE001 — profiling failure should not 500 silently
        profile = {"error": str(exc)}

    ver = DatasetVersion(
        dataset_id=ds.id,
        version=len(ds.versions) + 1 if hasattr(ds, "versions") else 1,
        file_path=dest,
        file_format=ext.lstrip("."),
        row_count=int(profile.get("row_count", 0)) if isinstance(profile.get("row_count"), int) else None,
        profile_json=profile,
    )
    db.add(ver)
    # Mirror a default table entry for sandbox allowlisting.
    tbl = Table(dataset_id=ds.id, name="data", row_count=ver.row_count)
    db.add(tbl)
    db.commit()
    return {"dataset_id": ds.id, "file_path": dest, "profile": profile}


@router.get("/{dataset_id}/profile")
def get_profile(dataset_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Return the latest stored profile for a dataset."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == user.workspace_id).first()
    if ds is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ver = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version.desc())
        .first()
    )
    if ver is None:
        return {"dataset_id": dataset_id, "profile": None}
    return {"dataset_id": dataset_id, "version": ver.version, "profile": ver.profile_json}
