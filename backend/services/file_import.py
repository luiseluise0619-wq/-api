"""범용 파일 임포터.

data.go.kr 등에서 '다운로드'한 축제/행사/박람회 파일(CSV·XLSX·JSON)을
API 키 없이 그대로 넣으면 자동으로 정규화하여 수집한다.

- 한글 컬럼명(축제명·위도·개최장소 등)을 표준 키로 매핑
- CSV 인코딩(utf-8 / cp949 / euc-kr) 자동 판별
- 좌표는 위경도 범위로 자동 감지 (collectors.normalize_item 재사용)

사용법
  1) 파일을 backend/data/imports/ 에 넣거나
  2) POST /api/import/upload 로 업로드
  → 다음 수집 또는 /api/import/scan 시 자동 반영
"""
from __future__ import annotations

import csv
import io
import json
import os

from services.collectors import SourceConfig, find_records, normalize_item

# 한글/변형 컬럼명 → 표준 키 (normalize_item 이 이해하는 이름)
KOREAN_ALIAS: dict[str, str] = {
    "축제명": "title", "행사명": "title", "전시명": "title", "박람회명": "title",
    "공연명": "title", "명칭": "title", "축제명칭": "title", "행사명칭": "title",
    "위도": "latitude", "경도": "longitude", "위도(y)": "latitude", "경도(x)": "longitude",
    "y좌표": "latitude", "x좌표": "longitude",
    "주소": "address", "소재지도로명주소": "rdnmadr", "소재지지번주소": "lnmadr",
    "도로명주소": "address", "지번주소": "address", "소재지": "address",
    "장소": "place", "개최장소": "place", "행사장소": "place", "전시장소": "place",
    "시작일": "startdate", "시작일자": "startdate", "개최시작일": "startdate",
    "행사시작일자": "startdate", "축제시작일자": "startdate", "전시시작일": "startdate",
    "종료일": "enddate", "종료일자": "enddate", "개최종료일": "enddate",
    "행사종료일자": "enddate", "축제종료일자": "enddate", "전시종료일": "enddate",
    "주최": "organizer", "주관": "organizer", "주최기관": "organizer", "주관기관": "organizer",
    "주최기관명": "organizer", "주관기관명": "organizer", "주최자": "organizer",
    "전화번호": "tel", "연락처": "tel", "문의처": "tel", "문의": "tel",
    "홈페이지": "homepage", "홈페이지주소": "homepage", "url": "homepage", "누리집": "homepage",
    "내용": "description", "상세내용": "description", "축제내용": "description",
    "행사내용": "description", "설명": "description", "상세설명": "description",
    "분류": "category", "유형": "category", "축제유형": "category", "행사구분": "category",
    "구분": "category", "카테고리": "category",
    "시군구": "sigungu", "시군구명": "sigungu", "군구": "sigungu",
    "시도": "_region_hint", "시도명": "_region_hint", "지역": "_region_hint",
    "광역시도": "_region_hint", "광역자치단체": "_region_hint",
    "이용요금": "fee", "관람료": "fee", "입장료": "fee", "요금": "fee",
}


def _canon(row: dict) -> dict:
    out: dict = {}
    for k, v in row.items():
        if k is None:
            continue
        key = str(k).strip()
        mapped = KOREAN_ALIAS.get(key) or KOREAN_ALIAS.get(key.lower()) or key
        if mapped not in out or out[mapped] in (None, ""):
            out[mapped] = v
    return out


def parse_file(path: str) -> list[dict]:
    ext = path.lower().rsplit(".", 1)[-1]
    try:
        if ext in ("xlsx", "xlsm"):
            import openpyxl

            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            headers = [str(h).strip() if h is not None else "" for h in rows[0]]
            out = []
            for r in rows[1:]:
                out.append({headers[i]: r[i] for i in range(min(len(headers), len(r)))})
            return out
        if ext == "csv":
            text = None
            for enc in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
                try:
                    with open(path, encoding=enc) as f:
                        text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            if text is None:
                return []
            return list(csv.DictReader(io.StringIO(text)))
        if ext == "json":
            with open(path, encoding="utf-8") as f:
                return find_records(json.load(f))
    except Exception as exc:  # noqa: BLE001
        print(f"[file_import] 파싱 실패 {path}: {exc}")
    return []


def import_rows(rows: list[dict], source_name: str) -> list[dict]:
    src = SourceConfig(name=source_name[:20], label=source_name, url="", kind="file")
    out: list[dict] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        canon = _canon(raw)
        # 광역(시도) 힌트를 주소에 병합 → 광역시도 자동 인식
        rh = canon.pop("_region_hint", None)
        if rh:
            addr = canon.get("address") or ""
            if str(rh) not in str(addr):
                canon["address"] = f"{rh} {addr}".strip()
        norm = normalize_item(canon, src)
        if norm:
            out.append(norm)
    return out


def import_dir(directory: str) -> list[dict]:
    """폴더 내 모든 파일을 임포트."""
    results: list[dict] = []
    if not directory or not os.path.isdir(directory):
        return results
    for fn in sorted(os.listdir(directory)):
        path = os.path.join(directory, fn)
        if not os.path.isfile(path):
            continue
        if not fn.lower().endswith((".csv", ".xlsx", ".xlsm", ".json")):
            continue
        name = "file_" + os.path.splitext(fn)[0]
        recs = import_rows(parse_file(path), name)
        print(f"[file_import] {fn}: {len(recs)}건 정규화")
        results.extend(recs)
    return results
