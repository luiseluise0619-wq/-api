"""축제 ORM 모델.

여러 공공 API 를 하나의 통합 스키마로 정규화하여 저장한다.
`source` + `source_id` 조합으로 중복을 제거한다.
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)

from database import Base


class Festival(Base):
    __tablename__ = "festivals"
    __table_args__ = (
        # 동일 소스에서 온 동일 항목은 1건만 유지 (중복 제거의 핵심)
        UniqueConstraint("source", "source_id", name="uq_source_item"),
        Index("ix_festival_dates", "start_date", "end_date"),
        Index("ix_festival_region", "region"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # 데이터 출처 식별 (unified / ifac / busan / tourapi)
    source = Column(String(20), nullable=False)
    source_id = Column(String(64), nullable=False)

    # 공통 정보
    title = Column(String(300), nullable=False, index=True)
    category = Column(String(50))          # 분류 (문화예술/관광특산 등)
    region = Column(String(50), index=True)  # 광역 시/도
    sigungu = Column(String(50))           # 시군구
    place = Column(String(300))            # 개최 장소
    address = Column(String(400))
    lat = Column(Float)                    # 위도
    lng = Column(Float)                    # 경도

    start_date = Column(Date)              # 시작일
    end_date = Column(Date)                # 종료일
    period_text = Column(String(200))      # "매년 10월 중" 등 비정형 기간

    organizer = Column(String(300))        # 주최/주관
    tel = Column(String(100))
    homepage = Column(String(500))
    image_url = Column(String(700))
    detail_url = Column(String(700))
    description = Column(Text)             # 상세 설명
    fee = Column(String(300))             # 이용요금

    # AI 산출 지표 (0~100). 수집 시 규칙 기반으로 계산해 캐싱한다.
    ai_score = Column(Integer, default=0)          # 상권 영향력 종합점수
    popularity = Column(Integer, default=0)        # 인기도 점수

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "source_id": self.source_id,
            "title": self.title,
            "category": self.category,
            "region": self.region,
            "sigungu": self.sigungu,
            "place": self.place,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "period_text": self.period_text,
            "organizer": self.organizer,
            "tel": self.tel,
            "homepage": self.homepage,
            "image_url": self.image_url,
            "detail_url": self.detail_url,
            "description": self.description,
            "fee": self.fee,
            "ai_score": self.ai_score or 0,
            "popularity": self.popularity or 0,
        }
