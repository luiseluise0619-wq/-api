"""Pydantic 응답/요청 스키마."""
from datetime import date
from typing import Optional

from pydantic import BaseModel


class FestivalOut(BaseModel):
    id: int
    source: str
    source_id: str
    title: str
    category: Optional[str] = None
    region: Optional[str] = None
    sigungu: Optional[str] = None
    place: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    period_text: Optional[str] = None
    organizer: Optional[str] = None
    tel: Optional[str] = None
    homepage: Optional[str] = None
    image_url: Optional[str] = None
    detail_url: Optional[str] = None
    description: Optional[str] = None
    fee: Optional[str] = None
    ai_score: int = 0
    popularity: int = 0

    class Config:
        from_attributes = True


class FestivalListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[FestivalOut]


class RegionCount(BaseModel):
    region: str
    count: int
    lat: Optional[float] = None
    lng: Optional[float] = None


class StatsResponse(BaseModel):
    total: int
    ongoing: int
    upcoming: int
    regions: int
    by_region: list[RegionCount]


class CollectResult(BaseModel):
    ok: bool
    inserted: int
    updated: int
    total_seen: int
    per_source: dict
    message: str


# --- AI --------------------------------------------------------------------
class AIAnalysisResponse(BaseModel):
    festival_id: int
    title: str
    analysis: dict          # 섹션별 구조화된 분석
    generated_by: str       # gemini / fallback


class AskRequest(BaseModel):
    festival_id: Optional[int] = None
    question: str


class AskResponse(BaseModel):
    answer: str
    generated_by: str
