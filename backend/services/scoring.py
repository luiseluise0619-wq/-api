"""규칙 기반 AI 점수 산출.

Gemini 호출은 비용/지연이 있으므로, 목록/마커에 즉시 표시할 '상권 영향력'과
'인기도' 점수는 수집 시점에 규칙 기반으로 계산해 DB 에 캐싱한다.
(Gemini 는 상세 분석/질문에서만 사용)
"""
from __future__ import annotations

import datetime as dt
from typing import Optional


# 규모가 큰/대표성 있는 축제로 추정되는 키워드 (가중치)
_STRONG_KEYWORDS = {
    "국제": 12, "세계": 10, "글로벌": 8, "대표": 8, "전국": 8,
    "페스티벌": 6, "축전": 6, "엑스포": 10, "박람회": 8,
    "불꽃": 8, "영화제": 8, "музык": 0,
}
_MEDIUM_KEYWORDS = {
    "문화": 4, "예술": 4, "관광": 5, "전통": 4, "민속": 3,
    "먹거리": 5, "음식": 5, "특산": 5, "시장": 6, "상권": 6,
    "야시장": 6, "빛": 3, "등": 2, "댄스": 3, "음악": 4, "재즈": 4,
}


def _keyword_score(text: str) -> int:
    score = 0
    for kw, w in _STRONG_KEYWORDS.items():
        if kw and kw in text:
            score += w
    for kw, w in _MEDIUM_KEYWORDS.items():
        if kw in text:
            score += w
    return score


def _visitor_bonus(record: dict) -> int:
    """방문객수(실측) 가 있으면 상권 점수에 반영."""
    import math
    v = record.get("_visitors")
    try:
        n = int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return 0
    if n <= 0:
        return 0
    # 방문객 1만명 ≈ +7, 10만명 ≈ +14, 100만명 ≈ +21 (상한 25)
    return min(25, round(math.log10(n + 1) * 3.5))


def compute_scores(record: dict) -> tuple[int, int]:
    """(ai_score=상권영향력, popularity=인기도) 를 0~100 으로 반환."""
    title = record.get("title") or ""
    desc = record.get("description") or ""
    category = record.get("category") or ""
    text = f"{title} {category} {desc}"

    base = 45
    kw = _keyword_score(text)

    # 상세 설명이 풍부할수록 규모 있는 축제로 가정
    desc_len = len(desc)
    if desc_len > 800:
        base += 12
    elif desc_len > 300:
        base += 7
    elif desc_len > 100:
        base += 3

    # 이미지/홈페이지/연락처가 있으면 정보 충실도 가점
    if record.get("image_url"):
        base += 5
    if record.get("homepage"):
        base += 4
    if record.get("tel"):
        base += 2

    visitor_bonus = _visitor_bonus(record)
    ai_score = max(0, min(100, base + kw + visitor_bonus))

    # 인기도: 상권 점수에 방문객수·대표 키워드 반영
    popularity = ai_score + visitor_bonus
    if "대표" in text or "국제" in text or "세계" in text:
        popularity += 8
    popularity = max(0, min(100, popularity))

    return ai_score, popularity


def stars_from_score(score: int) -> int:
    """0~100 점수를 별점(1~5)으로 변환."""
    return max(1, min(5, round(score / 20)))


def festival_status(
    start: Optional[dt.date],
    end: Optional[dt.date],
    today: Optional[dt.date] = None,
) -> str:
    """진행상태: ongoing(진행중) / upcoming(예정) / ended(종료) / unknown."""
    today = today or dt.date.today()
    if not start and not end:
        return "unknown"
    s = start or end
    e = end or start
    if s <= today <= e:
        return "ongoing"
    if today < s:
        return "upcoming"
    return "ended"
