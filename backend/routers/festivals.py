"""축제 조회/필터/통계 라우터."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from database import get_db
from models import Festival
from schemas import (
    CollectResult,
    FestivalListResponse,
    FestivalOut,
    RegionCount,
    StatsResponse,
)
from services.geocode import REGION_CENTROIDS
from services.scoring import festival_status

router = APIRouter(prefix="/api/festivals", tags=["festivals"])


def _apply_filters(
    stmt,
    region: Optional[str],
    category: Optional[str],
    q: Optional[str],
    status: Optional[str],
    date_from: Optional[dt.date],
    date_to: Optional[dt.date],
):
    if region:
        stmt = stmt.where(Festival.region == region)
    if category:
        stmt = stmt.where(Festival.category.ilike(f"%{category}%"))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Festival.title.ilike(like), Festival.description.ilike(like))
        )
    if date_from:
        stmt = stmt.where(
            or_(Festival.end_date >= date_from, Festival.end_date.is_(None))
        )
    if date_to:
        stmt = stmt.where(
            or_(Festival.start_date <= date_to, Festival.start_date.is_(None))
        )
    if status == "ongoing":
        today = dt.date.today()
        stmt = stmt.where(
            Festival.start_date <= today, Festival.end_date >= today
        )
    elif status == "upcoming":
        today = dt.date.today()
        stmt = stmt.where(Festival.start_date > today)
    elif status == "ended":
        today = dt.date.today()
        stmt = stmt.where(Festival.end_date < today)
    return stmt


@router.get("", response_model=FestivalListResponse)
def list_festivals(
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    status: Optional[str] = Query(None, description="ongoing|upcoming|ended"),
    date_from: Optional[dt.date] = None,
    date_to: Optional[dt.date] = None,
    has_coords: bool = Query(False, description="좌표 있는 축제만"),
    page: int = 1,
    page_size: int = Query(200, le=2000),
):
    base = select(Festival)
    base = _apply_filters(base, region, category, q, status, date_from, date_to)
    if has_coords:
        base = base.where(Festival.lat.is_not(None), Festival.lng.is_not(None))

    total = db.execute(
        select(func.count()).select_from(base.subquery())
    ).scalar_one()

    stmt = (
        base.order_by(Festival.ai_score.desc(), Festival.start_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = db.execute(stmt).scalars().all()
    return FestivalListResponse(
        total=total, page=page, page_size=page_size,
        items=[FestivalOut.model_validate(i) for i in items],
    )


@router.get("/map", response_model=list[FestivalOut])
def map_festivals(
    db: Session = Depends(get_db),
    region: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[dt.date] = None,
    date_to: Optional[dt.date] = None,
    limit: int = Query(3000, le=5000),
):
    """지도 마커용: 좌표가 있는 축제만 반환."""
    stmt = select(Festival).where(
        Festival.lat.is_not(None), Festival.lng.is_not(None)
    )
    stmt = _apply_filters(stmt, region, category, None, status, date_from, date_to)
    stmt = stmt.order_by(Festival.ai_score.desc()).limit(limit)
    items = db.execute(stmt).scalars().all()
    return [FestivalOut.model_validate(i) for i in items]


@router.get("/top", response_model=list[FestivalOut])
def top_festivals(db: Session = Depends(get_db), limit: int = 10):
    """인기 축제 TOP N."""
    stmt = select(Festival).order_by(
        Festival.popularity.desc(), Festival.ai_score.desc()
    ).limit(limit)
    return [FestivalOut.model_validate(i) for i in db.execute(stmt).scalars().all()]


@router.get("/this-month", response_model=list[FestivalOut])
def this_month(db: Session = Depends(get_db), limit: int = 12):
    """이번 달 추천 축제 (이번 달에 진행/시작하는 축제 중 점수 상위)."""
    today = dt.date.today()
    month_start = today.replace(day=1)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - dt.timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - dt.timedelta(days=1)
    stmt = (
        select(Festival)
        .where(
            Festival.start_date.is_not(None),
            Festival.start_date <= month_end,
            Festival.end_date >= month_start,
        )
        .order_by(Festival.ai_score.desc())
        .limit(limit)
    )
    return [FestivalOut.model_validate(i) for i in db.execute(stmt).scalars().all()]


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)):
    today = dt.date.today()
    total = db.execute(select(func.count(Festival.id))).scalar_one()
    ongoing = db.execute(
        select(func.count(Festival.id)).where(
            Festival.start_date <= today, Festival.end_date >= today
        )
    ).scalar_one()
    upcoming = db.execute(
        select(func.count(Festival.id)).where(Festival.start_date > today)
    ).scalar_one()

    rows = db.execute(
        select(Festival.region, func.count(Festival.id))
        .where(Festival.region.is_not(None))
        .group_by(Festival.region)
        .order_by(func.count(Festival.id).desc())
    ).all()
    by_region = []
    for region, count in rows:
        lat, lng = REGION_CENTROIDS.get(region, (None, None))
        by_region.append(RegionCount(region=region, count=count, lat=lat, lng=lng))

    return StatsResponse(
        total=total, ongoing=ongoing, upcoming=upcoming,
        regions=len(by_region), by_region=by_region,
    )


@router.get("/regions", response_model=list[str])
def regions(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Festival.region).where(Festival.region.is_not(None)).distinct()
    ).all()
    return sorted(r[0] for r in rows)


@router.get("/categories", response_model=list[str])
def categories(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Festival.category).where(Festival.category.is_not(None)).distinct()
    ).all()
    return sorted({r[0] for r in rows if r[0]})


@router.get("/{festival_id}", response_model=FestivalOut)
def get_festival(festival_id: int, db: Session = Depends(get_db)):
    f = db.get(Festival, festival_id)
    if f is None:
        raise HTTPException(status_code=404, detail="축제를 찾을 수 없습니다.")
    return FestivalOut.model_validate(f)
