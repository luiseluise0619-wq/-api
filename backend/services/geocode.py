"""좌표/지역 보정 유틸리티.

- 여러 API 가 좌표 순서를 제각각 담기 때문에(위도 먼저 vs 경도 먼저)
  값의 범위로 위/경도를 자동 판별한다. (대한민국: 위도 33~39, 경도 124~132)
- 좌표가 아예 없는 데이터(ifac 등)는 주소/주최기관 텍스트에서 광역시도를 추출해
  시도 중심 좌표로 근사 배치한다.
"""
from __future__ import annotations

from typing import Optional

# 대한민국 위/경도 범위
LAT_MIN, LAT_MAX = 33.0, 39.5
LNG_MIN, LNG_MAX = 124.0, 132.5

# 광역 시도 중심 좌표 (근사)
REGION_CENTROIDS: dict[str, tuple[float, float]] = {
    "서울특별시": (37.5665, 126.9780),
    "부산광역시": (35.1796, 129.0756),
    "대구광역시": (35.8714, 128.6014),
    "인천광역시": (37.4563, 126.7052),
    "광주광역시": (35.1595, 126.8526),
    "대전광역시": (36.3504, 127.3845),
    "울산광역시": (35.5384, 129.3114),
    "세종특별자치시": (36.4801, 127.2890),
    "경기도": (37.4138, 127.5183),
    "강원특별자치도": (37.8228, 128.1555),
    "강원도": (37.8228, 128.1555),
    "충청북도": (36.6357, 127.4917),
    "충청남도": (36.5184, 126.8000),
    "전북특별자치도": (35.7175, 127.1530),
    "전라북도": (35.7175, 127.1530),
    "전라남도": (34.8161, 126.4630),
    "경상북도": (36.4919, 128.8889),
    "경상남도": (35.4606, 128.2132),
    "제주특별자치도": (33.4890, 126.4983),
    "제주도": (33.4890, 126.4983),
}

# 축약형 → 표준 광역시도명
REGION_ALIASES: dict[str, str] = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}


def normalize_coords(
    candidates: list[Optional[float]],
) -> tuple[Optional[float], Optional[float]]:
    """숫자 후보들 중 위도/경도 범위에 맞는 값을 골라 (lat, lng)로 반환."""
    nums: list[float] = []
    for c in candidates:
        try:
            if c is None or c == "":
                continue
            v = float(c)
            if v == 0:
                continue
            nums.append(v)
        except (TypeError, ValueError):
            continue

    lat = next((v for v in nums if LAT_MIN <= v <= LAT_MAX), None)
    lng = next((v for v in nums if LNG_MIN <= v <= LNG_MAX), None)
    return lat, lng


def detect_region(*texts: Optional[str]) -> Optional[str]:
    """주소/기관명 등 텍스트에서 광역 시도명을 추출."""
    for text in texts:
        if not text:
            continue
        # 표준 전체 명칭 우선 매칭
        for full in REGION_CENTROIDS:
            if full in text:
                return full
        # 축약형 매칭
        for short, full in REGION_ALIASES.items():
            if text.startswith(short) or f" {short}" in text:
                return full
    return None


def region_centroid(region: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    if not region:
        return None, None
    return REGION_CENTROIDS.get(region, (None, None))


def jittered_centroid(
    region: Optional[str], seed: str, spread: float = 0.28
) -> tuple[Optional[float], Optional[float]]:
    """좌표 없는 축제를 광역 중심점 주변에 결정적으로 분산 배치.

    같은 지역의 축제 마커들이 한 점에 겹치지 않도록 seed(축제명 등) 기반
    해시로 재현 가능한 오프셋을 준다. (정확한 위치가 아닌 근사치임)
    """
    lat, lng = region_centroid(region)
    if lat is None or lng is None:
        return None, None
    h = 0
    for ch in seed:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    dx = ((h & 0xFFFF) / 0xFFFF - 0.5) * 2 * spread
    dy = (((h >> 16) & 0xFFFF) / 0xFFFF - 0.5) * 2 * spread
    return round(lat + dy, 6), round(lng + dx, 6)
