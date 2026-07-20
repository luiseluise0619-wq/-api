"""파일 임포트 라우터.

data.go.kr 등에서 다운로드한 파일을 업로드하거나, 서버 폴더의 파일을 스캔해
축제/행사/박람회 데이터로 즉시 반영한다. (API 키 불필요)
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Festival
from services import file_import
from services.scoring import compute_scores

router = APIRouter(prefix="/api/import", tags=["import"])


def _save(records: list[dict], db: Session) -> tuple[int, int]:
    inserted = updated = 0
    for rec in records:
        ai, pop = compute_scores(rec)
        rec = {k: v for k, v in rec.items() if not k.startswith("_")}
        rec["ai_score"] = ai
        rec["popularity"] = pop
        existing = db.execute(
            select(Festival).where(
                Festival.source == rec["source"],
                Festival.source_id == rec["source_id"],
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(Festival(**rec))
            inserted += 1
        else:
            for k, v in rec.items():
                setattr(existing, k, v)
            updated += 1
    db.commit()
    return inserted, updated


@router.post("/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """CSV/XLSX/JSON 파일을 업로드하면 즉시 파싱·정규화·저장."""
    os.makedirs(settings.LOCAL_IMPORT_DIR, exist_ok=True)
    fname = os.path.basename(file.filename or "upload")
    dest = os.path.join(settings.LOCAL_IMPORT_DIR, fname)
    with open(dest, "wb") as f:
        f.write(await file.read())
    name = "file_" + os.path.splitext(fname)[0]
    recs = file_import.import_rows(file_import.parse_file(dest), name)
    ins, upd = _save(recs, db)
    return {
        "file": fname,
        "normalized": len(recs),
        "inserted": ins,
        "updated": upd,
        "message": f"{fname} → {ins}건 신규, {upd}건 갱신",
    }


@router.get("/scan")
@router.post("/scan")
def scan(db: Session = Depends(get_db)):
    """서버의 imports 폴더에 있는 모든 파일을 스캔·임포트."""
    recs = file_import.import_dir(settings.LOCAL_IMPORT_DIR)
    ins, upd = _save(recs, db)
    return {
        "dir": settings.LOCAL_IMPORT_DIR,
        "normalized": len(recs),
        "inserted": ins,
        "updated": upd,
    }
