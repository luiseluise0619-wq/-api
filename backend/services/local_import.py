"""문화체육관광부 '2026년 지역축제 개최계획' 엑셀 로컬 임포터.

공공데이터 API 키가 없어도 전국 축제 데이터로 서비스가 동작하도록 하는 시드 소스.
좌표가 없으므로 광역 중심점 주변에 결정적으로 분산 배치한다.
방문객수(전년) 실측치를 인기도 점수에 반영한다.
"""
from __future__ import annotations

import datetime as dt
import math
import os
from typing import Optional

from services.geocode import REGION_ALIASES, jittered_centroid, sigungu_centroid

SOURCE_NAME = "mocst2026"


def _strip_code(v) -> Optional[str]:
    """'01. 문화예술' → '문화예술', '-' → None."""
    if v is None:
        return None
    s = str(v).strip()
    if not s or s == "-":
        return None
    # 앞의 'NN. ' 코드 프리픽스 제거
    if len(s) > 4 and s[:2].isdigit() and s[2:4] in (". ", ". "):
        s = s[4:].strip()
    elif ". " in s[:5] and s.split(".")[0].strip().isdigit():
        s = s.split(".", 1)[1].strip()
    return s or None


def _to_region(v) -> Optional[str]:
    s = _strip_code(v)
    if not s:
        return None
    if s in REGION_ALIASES:
        return REGION_ALIASES[s]
    for short, full in REGION_ALIASES.items():
        if s.startswith(short):
            return full
    return s


def _cell(row, idx) -> Optional[str]:
    if idx >= len(row):
        return None
    v = row[idx]
    return None if v is None else str(v).strip()


def _hash_offset(seed: str, spread: float) -> tuple[float, float]:
    """seed 기반 결정적 (dx, dy) 오프셋. 같은 축제는 항상 같은 위치."""
    h = 0
    for ch in seed:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    dx = ((h & 0xFFFF) / 0xFFFF - 0.5) * 2 * spread
    dy = (((h >> 16) & 0xFFFF) / 0xFFFF - 0.5) * 2 * spread
    return dx, dy


def _mk_date(y, m, d) -> Optional[dt.date]:
    try:
        return dt.date(int(float(y)), int(float(m)), int(float(d)))
    except (TypeError, ValueError):
        return None


def _visitor_popularity(v) -> Optional[int]:
    try:
        n = int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    # 방문객 수(로그 스케일) → 0~100
    return max(10, min(100, round(math.log10(n + 1) * 17)))


def load_festivals(path: str) -> list[dict]:
    """엑셀을 읽어 정규화된 축제 레코드 리스트 반환."""
    if not path or not os.path.exists(path):
        print(f"[local_import] 파일 없음: {path}")
        return []
    try:
        import openpyxl
    except ImportError:
        print("[local_import] openpyxl 미설치 — 로컬 임포트 건너뜀")
        return []

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    records: list[dict] = []

    for row in ws.iter_rows(min_row=9, values_only=True):
        title = _cell(row, 4)
        if not title:
            continue
        seq = _cell(row, 1) or title
        region = _to_region(row[2] if len(row) > 2 else None)
        sigungu = _strip_code(row[3] if len(row) > 3 else None)
        category = _strip_code(row[5] if len(row) > 5 else None)
        place = _cell(row, 6)
        start = _mk_date(_cell(row, 11), _cell(row, 12), _cell(row, 13))
        end = _mk_date(_cell(row, 14), _cell(row, 15), _cell(row, 16)) or start
        tel = _cell(row, 38)
        visitors = row[26] if len(row) > 26 else None

        addr_parts = [region, sigungu, _cell(row, 10), place]
        address = " ".join(p for p in addr_parts if p) or None

        # 1) 시군구 중심좌표(정확) + 소폭 결정적 오프셋(겹침 방지)
        # 2) 시군구 미확인 시 시도 중심 근사 배치
        sg_lat, sg_lng = sigungu_centroid(region, sigungu)
        if sg_lat is not None:
            dx, dy = _hash_offset(f"{seq}:{title}", spread=0.018)
            lat, lng = round(sg_lat + dy, 6), round(sg_lng + dx, 6)
        else:
            lat, lng = jittered_centroid(region, f"{seq}:{title}", spread=0.15)

        rec = {
            "source": SOURCE_NAME,
            "source_id": str(seq)[:64],
            "title": title[:300],
            "category": category,
            "region": region,
            "sigungu": sigungu,
            "place": place,
            "address": address,
            "lat": lat,
            "lng": lng,
            "start_date": start,
            "end_date": end,
            "period_text": None,
            "organizer": _cell(row, 31),
            "tel": tel,
            "homepage": None,
            "image_url": None,
            "detail_url": None,
            "description": None,
            "fee": None,
            "_visitors": visitors,  # 스코어링용 임시 필드 (저장 전 제거)
        }
        records.append(rec)

    print(f"[local_import] 엑셀에서 {len(records)}건 로드")
    return records
