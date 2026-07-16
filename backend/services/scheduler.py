"""수집 실행 + DB 저장(중복제거) + 하루 1회 스케줄링."""
from __future__ import annotations

import datetime as dt

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from config import settings
from database import SessionLocal
from models import Festival
from services import collectors
from services.geocode import LAT_MIN, LAT_MAX, LNG_MIN, LNG_MAX
from services.scoring import compute_scores

_scheduler: BackgroundScheduler | None = None


def _has_real_coords(rec: dict) -> bool:
    lat, lng = rec.get("lat"), rec.get("lng")
    if lat is None or lng is None:
        return False
    return LAT_MIN <= lat <= LAT_MAX and LNG_MIN <= lng <= LNG_MAX


def run_collection() -> dict:
    """모든 소스를 수집하여 DB 에 upsert. 결과 요약 dict 반환."""
    started = dt.datetime.utcnow()
    per_source = collectors.fetch_all()

    inserted = updated = total_seen = 0
    db = SessionLocal()
    try:
        for source_name, records in per_source.items():
            for rec in records:
                total_seen += 1
                ai_score, popularity = compute_scores(rec)
                # 실제 좌표가 있으면 신뢰도 가점
                if _has_real_coords(rec):
                    ai_score = min(100, ai_score + 5)

                # 저장 전 임시 필드(_로 시작) 제거 후 점수 반영
                rec = {k: v for k, v in rec.items() if not k.startswith("_")}
                rec["ai_score"] = ai_score
                rec["popularity"] = popularity

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
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise
    finally:
        db.close()

    summary = {
        "inserted": inserted,
        "updated": updated,
        "total_seen": total_seen,
        "per_source": {k: len(v) for k, v in per_source.items()},
        "elapsed_sec": round((dt.datetime.utcnow() - started).total_seconds(), 1),
    }
    print(f"[scheduler] 수집 완료: {summary}")
    return summary


def start_scheduler() -> None:
    """하루 1회 자동 수집 스케줄 등록."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    _scheduler.add_job(
        run_collection,
        trigger="cron",
        hour=settings.SCHEDULE_HOUR,
        minute=settings.SCHEDULE_MINUTE,
        id="daily_collection",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()
    print(
        f"[scheduler] 하루 1회 자동수집 등록 "
        f"({settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} KST)"
    )


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
