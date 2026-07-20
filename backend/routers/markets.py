"""전통시장(상권) 라우터.

축제 주변 소상공인 상권을 정량적으로 보여주기 위한 엔드포인트.
- /api/markets/near : 좌표 반경 내 전통시장 목록·점포수 합계
- /api/markets      : 전체/지역 목록
"""
from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Market
from schemas import MarketNearResponse, MarketOut
from services import collectors

router = APIRouter(prefix="/api/markets", tags=["markets"])


@router.get("/diag")
def markets_diag(db: Session = Depends(get_db)):
    """전통시장 수집 진단: DB 저장 건수 + 표준데이터 API 원시 응답."""
    count = db.execute(select(func.count(Market.id))).scalar_one()
    return {"markets_in_db": count, "api": collectors.diag_markets()}


@router.get("/collect")
@router.post("/collect")
def collect_markets(db: Session = Depends(get_db)):
    """전통시장만 즉시 수집·저장 (브라우저에서 GET 으로도 실행 가능)."""
    recs = collectors.fetch_markets()
    n = 0
    for m in recs:
        existing = db.execute(
            select(Market).where(Market.source_id == m["source_id"])
        ).scalar_one_or_none()
        if existing is None:
            db.add(Market(**m))
        else:
            for k, v in m.items():
                setattr(existing, k, v)
        n += 1
    db.commit()
    total = db.execute(select(func.count(Market.id))).scalar_one()
    with_coords = db.execute(
        select(func.count(Market.id)).where(Market.lat.is_not(None))
    ).scalar_one()
    return {"collected": n, "total_in_db": total, "with_coords": with_coords}


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@router.get("/near", response_model=MarketNearResponse)
def markets_near(
    lat: float,
    lng: float,
    radius_km: float = Query(2.0, ge=0.1, le=50),
    db: Session = Depends(get_db),
):
    # 대략적 위경도 박스로 1차 필터 후 정밀 거리 계산 (성능)
    dlat = radius_km / 111.0
    dlng = radius_km / (111.0 * max(0.1, math.cos(math.radians(lat))))
    rows = db.execute(
        select(Market).where(
            Market.lat.is_not(None),
            Market.lng.is_not(None),
            Market.lat.between(lat - dlat, lat + dlat),
            Market.lng.between(lng - dlng, lng + dlng),
        )
    ).scalars().all()

    result: list[MarketOut] = []
    total_stores = 0
    for m in rows:
        d = _haversine_km(lat, lng, m.lat, m.lng)
        if d <= radius_km:
            mo = MarketOut.model_validate(m)
            mo.distance_km = round(d, 2)
            result.append(mo)
            total_stores += m.stores or 0
    result.sort(key=lambda x: x.distance_km or 0)

    return MarketNearResponse(
        center_lat=lat, center_lng=lng, radius_km=radius_km,
        market_count=len(result), total_stores=total_stores, markets=result,
    )


@router.get("", response_model=list[MarketOut])
def list_markets(
    region: Optional[str] = None,
    limit: int = Query(2000, le=5000),
    db: Session = Depends(get_db),
):
    stmt = select(Market)
    if region:
        stmt = stmt.where(Market.region == region)
    stmt = stmt.order_by(Market.stores.desc().nullslast()).limit(limit)
    return [MarketOut.model_validate(m) for m in db.execute(stmt).scalars().all()]
