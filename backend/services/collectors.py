"""공공데이터 축제 수집기.

여러 공공 API 를 하나의 정규화된 스키마로 변환하여 반환한다.
- 지자체 축제 API (대전/울산/부산 등, JSON·XML 혼재)
- 한국관광공사 TourAPI 지역축제 (문화체육관광부 데이터)
- ifac.or.kr 지역축제

설계 포인트
- 응답 봉투(envelope)가 API 마다 다르므로, 파싱 결과에서 '축제 레코드로 보이는
  dict 리스트'를 재귀적으로 찾아낸다. → 새 지자체 API 추가 시 코드 수정 최소화.
- 좌표는 값의 범위(위도 33~39 / 경도 124~132)로 자동 판별한다.
- source + source_id 로 DB 에서 중복 제거된다.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
import xmltodict
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from services.geocode import detect_region, normalize_coords, region_centroid

# ---------------------------------------------------------------------------
# 소스 설정
# ---------------------------------------------------------------------------


@dataclass
class SourceConfig:
    name: str                       # DB 에 저장될 source 식별자
    label: str                      # 사람이 읽는 이름
    url: str
    kind: str = "datagokr"          # datagokr | tourapi | ifac | kopis
    fmt: str = "json"               # json | xml
    # datagokr 계열 페이지 파라미터 스타일 (지자체마다 다름)
    #  std        : pageNo / numOfRows            (data.go.kr 표준, 부산·대전 등)
    #  egov_unit  : pageIndex / pageUnit          (서천군 등)
    #  egov_first : firstIndex / pageIndex(=행수) (괴산군 등)
    param_style: str = "std"
    region_hint: Optional[str] = None  # 좌표 없을 때 근사 배치용 광역시도
    enabled: bool = True
    extra_params: dict = field(default_factory=dict)


# 표준 data.go.kr 지자체 축제 엔드포인트 레지스트리
# (name, label, url, fmt, param_style, region_hint)
# 새 지자체 축제 API 는 여기 한 줄만 추가하면 자동 연동된다.
DATAGOKR_ENDPOINTS: list[tuple[str, str, str, str, str, Optional[str]]] = [
    # ⭐ 전국문화축제표준데이터 — 전국 모든 문화축제 + 위경도 (대표 소스)
    ("national", "전국문화축제표준데이터",
     "https://api.data.go.kr/openapi/tn_pubr_public_cltur_fstvl_api", "json", "std", None),
    ("daejeon", "대전광역시 문화축제",
     "https://apis.data.go.kr/6300000/openapi2022/festv/getfestv", "json", "std", "대전광역시"),
    ("ulsan", "울산광역시 문화축제",
     "https://apis.data.go.kr/6310000/ulsanfestival/getUlsanfestivalList", "xml", "std", "울산광역시"),
    ("busan", "부산광역시 축제정보",
     "https://apis.data.go.kr/6260000/FestivalService/getFestivalKr", "json", "std", "부산광역시"),
    ("boseong_event", "전남 보성군 문화행사",
     "https://apis.data.go.kr/4890000/boseongEventInfo/getBoseongEventInfoList", "xml", "std", "전라남도"),
    ("boseong_fest", "전남 보성군 문화축제",
     "https://apis.data.go.kr/4890000/boseongFestInfo/getBoseongFestInfo", "xml", "std", "전라남도"),
    ("jeonnam", "전남 남도여행길잡이 축제",
     "https://apis.data.go.kr/6460000/rest/jnFestivalInfo/getFestivalInfoList", "xml", "std", "전라남도"),
    ("goesan", "충북 괴산군 문화축제",
     "https://apis.data.go.kr/4460000/GetCulturalFestivalService/getCulturalFestivalInfo", "xml", "egov_first", "충청북도"),
    ("seocheon", "충남 서천군 축제정보",
     "https://apis.data.go.kr/4580000/SCAPI10/SC_Festival", "json", "egov_unit", "충청남도"),
    ("sejong", "세종특별자치시 문화축제",
     "https://apis.data.go.kr/5690000/sjFestival/sj_00000360", "xml", "egov_unit", "세종특별자치시"),
    ("yeongcheon", "경북 영천시 행사·축제",
     "https://apis.data.go.kr/5100000/YeongcheonFestival/getResult", "json", "std", "경상북도"),
    ("gyeongju", "경북 경주시 축제현황",
     "https://apis.data.go.kr/5050000/festivalStatusService/getFestivalStatus", "json", "std", "경상북도"),
    ("chuncheon", "강원 춘천시 문화축제",
     "https://apis.data.go.kr/4180000/ccculture/get_cultureList", "json", "std", "강원특별자치도"),
    ("gwangyang", "전남 광양시 문화축제",
     "https://apis.data.go.kr/4840000/culturalfestival1/getculturalfestivalList1", "xml", "std", "전라남도"),
]


def default_sources() -> list[SourceConfig]:
    """기본 내장 소스 목록.

    .env 의 EXTRA_SOURCES_JSON 로 추가 소스를 덧붙일 수 있다.
    각 소스는 발급된 인증키가 있어야 실제로 동작한다.
    """
    sources: list[SourceConfig] = []

    if settings.PUBLIC_DATA_API_KEY:
        for name, label, url, fmt, style, region in DATAGOKR_ENDPOINTS:
            sources.append(SourceConfig(
                name=name, label=label, url=url,
                kind="datagokr", fmt=fmt, param_style=style, region_hint=region,
            ))
        # 한국관광공사 TourAPI: 전국·좌표·날짜 포함 (문화체육관광부 데이터)
        sources.append(SourceConfig(
            name="tourapi",
            label="한국관광공사 전국 지역축제",
            url="https://apis.data.go.kr/B551011/KorService2/searchFestival2",
            kind="tourapi", fmt="json", region_hint=None,
        ))

    if settings.SEOUL_OPEN_API_KEY:
        sources.append(SourceConfig(
            name="seoul",
            label="서울시 문화행사",
            url="http://openapi.seoul.go.kr:8088",
            kind="seoul", fmt="json", region_hint="서울특별시",
        ))

    if settings.KOPIS_API_KEY:
        sources.append(SourceConfig(
            name="kopis",
            label="KOPIS 전국 축제성 공연",
            url="http://kopis.or.kr/openApi/restful/prffest",
            kind="kopis", fmt="xml", region_hint=None,
        ))

    if settings.IFAC_API_KEY:
        sources.append(SourceConfig(
            name="ifac",
            label="ifac 지역축제",
            url="https://ifac.or.kr/openAPI/real/search.do",
            kind="ifac", fmt="json", region_hint=None,
        ))

    # .env 로 추가 소스 주입 (동일 스키마의 다른 지자체 API 등)
    raw = getattr(settings, "EXTRA_SOURCES_JSON", "") or ""
    if raw.strip():
        try:
            for item in json.loads(raw):
                sources.append(SourceConfig(**item))
        except Exception as exc:  # noqa: BLE001
            print(f"[collector] EXTRA_SOURCES_JSON 파싱 실패: {exc}")

    return [s for s in sources if s.enabled]


# ---------------------------------------------------------------------------
# 필드 정규화
# ---------------------------------------------------------------------------

_TITLE_KEYS = ["name", "title", "main_title", "fstvlnm", "festivalnm", "cnttsnm",
               "fstvl_nm", "event_nm", "evnt_nm", "prfnm", "fest_nm"]
_ID_KEYS = ["idx", "uc_seq", "contentid", "unqid", "seq", "id", "no", "fstvlseq", "mt20id"]
_CATEGORY_KEYS = ["category", "gubun", "cat", "fstvlse", "dvsn", "dvsn1", "type",
                  "genrenm", "codename", "themecode"]
_DESC_KEYS = ["content", "itemcntnts", "description", "cn", "dc", "fstvlcn", "cntnts",
              "event_cntnt", "evnt_cntnt", "evnt_cn", "fstvlco"]
_ADDR_KEYS = ["address", "addr1", "addr", "rdnmadr", "lnmadr", "fstvlplc", "location"]
_PLACE_KEYS = ["place", "main_place", "opar", "spot", "searchplc",
               "eventplace", "std_nm", "fcltynm", "plc"]
_ORG_KEYS = ["manage", "opener", "organ", "host", "hostinsttnm", "organizer",
             "mnnstnm", "auspc", "sponsor", "event_host", "evnt_host",
             "auspcinsttnm", "suprtinsttnm", "org_name"]
_TEL_KEYS = ["phone", "tel", "cntct_tel", "cntctno", "telno", "cntctnumber",
             "phonenumber", "inquiry"]
_HOMEPAGE_KEYS = ["homepage", "homepage_url", "hmpg", "url", "relate_url", "hmpgurl",
                  "homepageurl", "hmpg_addr", "org_link"]
_FEE_KEYS = ["fee", "usage_amount", "utztnprc", "charge", "price", "fee_info", "use_fee"]
_PERIOD_KEYS = ["undecided", "period", "usage_day", "fstvlperiod", "playtime"]
_SDATE_KEYS = ["sdate", "eventstartdate", "startdate", "fstvlstdt", "begin_de",
               "start", "fstvlstartdate", "st_date", "evnt_bgng_ymd", "evnt_bgng_de",
               "prfpdfrom", "fest_bgng_ymd", "strtdate"]
_EDATE_KEYS = ["edate", "eventenddate", "enddate", "fstvlenddt", "end_de",
               "end", "fstvlenddate", "ed_date", "evnt_end_ymd", "evnt_end_de",
               "prfpdto", "fest_end_ymd", "end_date"]
_IMG_KEYS = ["images", "main_img_normal", "firstimage", "image", "img",
             "main_img_thumb", "imageurl", "filepath", "imgurl", "poster", "main_img"]
_COORD_KEYS = ["xposition", "yposition", "lat", "lng", "latitude", "longitude",
               "mapx", "mapy", "la", "lo", "gpsx", "gpsy", "x", "y", "coord_x", "coord_y",
               "lot"]
_LINK_KEYS = ["link", "detail_url", "url", "homepage_url"]


def _lower_map(raw: dict) -> dict:
    """키를 소문자로 통일한 사본 (원본 값 유지)."""
    return {str(k).lower(): v for k, v in raw.items()}


def _pick(lm: dict, keys: list[str]) -> Optional[Any]:
    for k in keys:
        if k in lm and lm[k] not in (None, "", "null"):
            return lm[k]
    return None


def _clean_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _first_image(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, list):
        return _clean_str(v[0]) if v else None
    if isinstance(v, dict):
        # {"item": [...]} 형태 방어
        for val in v.values():
            r = _first_image(val)
            if r:
                return r
        return None
    return _clean_str(v)


_DATE_RE = re.compile(r"(\d{4})[.\-/]?\s?(\d{1,2})[.\-/]?\s?(\d{1,2})")


def _to_date(m: re.Match) -> Optional[dt.date]:
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def parse_date(v: Any) -> Optional[dt.date]:
    s = _clean_str(v)
    if not s:
        return None
    m = _DATE_RE.search(s)
    return _to_date(m) if m else None


def parse_period_range(v: Any) -> tuple[Optional[dt.date], Optional[dt.date]]:
    """'2026-07-01 ~ 2026-07-05' 같은 기간 문자열에서 (시작, 종료) 추출."""
    s = _clean_str(v)
    if not s:
        return None, None
    matches = list(_DATE_RE.finditer(s))
    if not matches:
        return None, None
    start = _to_date(matches[0])
    end = _to_date(matches[-1]) if len(matches) > 1 else start
    return start, end


def normalize_item(
    raw: dict, source: SourceConfig
) -> Optional[dict]:
    """단일 API 레코드를 통합 스키마 dict 로 변환. 실패 시 None."""
    if not isinstance(raw, dict):
        return None
    lm = _lower_map(raw)

    title = _clean_str(_pick(lm, _TITLE_KEYS))
    if not title:
        return None  # 제목 없으면 유효 데이터로 보지 않음

    # 고유번호가 없으면 제목+장소/주소로 키를 구성 (동명 축제 충돌 방지)
    explicit_id = _clean_str(_pick(lm, _ID_KEYS))
    if explicit_id:
        source_id = explicit_id
    else:
        place_hint = _clean_str(_pick(lm, _PLACE_KEYS)) or _clean_str(
            _pick(lm, _ADDR_KEYS)
        ) or ""
        source_id = f"{title}|{place_hint}"[:64]

    # 좌표 자동 판별
    coord_candidates = [lm.get(k) for k in _COORD_KEYS]
    lat, lng = normalize_coords(coord_candidates)

    address = _clean_str(_pick(lm, _ADDR_KEYS))
    organizer = _clean_str(_pick(lm, _ORG_KEYS))
    region = source.region_hint or detect_region(address, organizer, title)

    # 좌표가 없으면 광역시도 중심으로 근사 배치 (지도에 최소한 표시되도록)
    if lat is None or lng is None:
        c_lat, c_lng = region_centroid(region)
        lat = lat or c_lat
        lng = lng or c_lng

    return {
        "source": source.name,
        "source_id": str(source_id)[:64],
        "title": title[:300],
        "category": _clean_str(_pick(lm, _CATEGORY_KEYS)),
        "region": region,
        "sigungu": _clean_str(
            lm.get("area") or lm.get("gugun_nm") or lm.get("sigungu") or lm.get("guname")
        ),
        "place": _clean_str(_pick(lm, _PLACE_KEYS)),
        "address": address,
        "lat": lat,
        "lng": lng,
        "start_date": parse_date(_pick(lm, _SDATE_KEYS)),
        "end_date": parse_date(_pick(lm, _EDATE_KEYS)),
        "period_text": _clean_str(_pick(lm, _PERIOD_KEYS)),
        "organizer": organizer,
        "tel": _clean_str(_pick(lm, _TEL_KEYS)),
        "homepage": _clean_str(_pick(lm, _HOMEPAGE_KEYS)),
        "image_url": _first_image(_pick(lm, _IMG_KEYS)),
        "detail_url": _clean_str(_pick(lm, _LINK_KEYS)),
        "description": _clean_str(_pick(lm, _DESC_KEYS)),
        "fee": _clean_str(_pick(lm, _FEE_KEYS)),
    }


# ---------------------------------------------------------------------------
# 응답에서 레코드 리스트 추출
# ---------------------------------------------------------------------------

def _looks_like_record(d: Any) -> bool:
    if not isinstance(d, dict):
        return False
    lm = _lower_map(d)
    return any(k in lm for k in _TITLE_KEYS)


def find_records(data: Any) -> list[dict]:
    """파싱된 응답 구조를 재귀 탐색하여 축제 레코드 리스트를 찾는다."""
    best: list[dict] = []

    def walk(node: Any):
        nonlocal best
        if isinstance(node, list):
            records = [x for x in node if _looks_like_record(x)]
            if len(records) > len(best):
                best = records
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    walk(data)
    # 단일 레코드가 dict 로 온 경우 방어
    if not best and _looks_like_record(data):
        best = [data]
    return best


# ---------------------------------------------------------------------------
# HTTP 요청 / 파라미터 빌드
# ---------------------------------------------------------------------------

def _build_params(
    source: SourceConfig,
    page: int,
    page_size: int,
    window: Optional[tuple[str, str]] = None,
) -> dict:
    if source.kind == "ifac":
        return {
            "svID": "festival",
            "apiKey": settings.IFAC_API_KEY,
            "resultType": "json",
            "cPage": page,
            "pSize": page_size,
            **source.extra_params,
        }
    if source.kind == "tourapi":
        return {
            "serviceKey": settings.PUBLIC_DATA_API_KEY,
            "MobileOS": "ETC",
            "MobileApp": "FestivalAIMap",
            "_type": "json",
            "arrange": "A",
            "listYN": "Y",
            "eventStartDate": "20200101",  # 과거~현재 폭넓게 수집
            "numOfRows": page_size,
            "pageNo": page,
            **source.extra_params,
        }
    if source.kind == "kopis":
        stdate, eddate = window or ("20200101", "20200131")
        return {
            "service": settings.KOPIS_API_KEY,
            "stdate": stdate,
            "eddate": eddate,
            "cpage": page,
            "rows": min(page_size, 100),  # KOPIS 최대 100건
            **source.extra_params,
        }
    # datagokr 계열: 지자체별 페이지 파라미터 스타일에 맞춰 구성
    fmt = "json" if source.fmt == "json" else "xml"
    params: dict = {"serviceKey": settings.PUBLIC_DATA_API_KEY}

    if source.param_style == "egov_unit":       # 서천군: pageIndex(페이지)/pageUnit(행수)
        params.update({"pageIndex": page, "pageUnit": page_size})
    elif source.param_style == "egov_first":    # 괴산군: firstIndex(페이지)/pageIndex(행수)
        params.update({"firstIndex": page, "pageIndex": page_size})
    else:                                        # std: data.go.kr 표준
        params.update({"pageNo": page, "numOfRows": page_size})

    # 포맷 플래그는 API 마다 이름이 달라 흔한 것들을 함께 전달 (모르는 값은 무시됨)
    params.update({
        "resultType": fmt, "_type": fmt, "dataType": fmt.upper(),
        "dataTy": fmt, "returnType": fmt, "type": fmt,
    })
    params.update(source.extra_params)
    return params


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _http_get(url: str, params: dict, fmt: str) -> Any:
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        text = resp.text.strip()
    # 포맷이 json 이라도 서버가 xml 로 줄 수 있으니 내용으로 판별
    if text.startswith("<"):
        return xmltodict.parse(text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return xmltodict.parse(text)


def _month_windows(months_back: int = 18, months_ahead: int = 6) -> list[tuple[str, str]]:
    """KOPIS 용 월 단위 (시작일, 종료일) 목록. 31일 제약 대응."""
    today = dt.date.today()
    base_year = today.year
    base_month = today.month
    windows: list[tuple[str, str]] = []
    for offset in range(-months_back, months_ahead + 1):
        m_index = (base_year * 12 + (base_month - 1)) + offset
        y, m = divmod(m_index, 12)
        m += 1
        start = dt.date(y, m, 1)
        # 다음 달 1일 - 1일 = 말일
        if m == 12:
            nxt = dt.date(y + 1, 1, 1)
        else:
            nxt = dt.date(y, m + 1, 1)
        end = nxt - dt.timedelta(days=1)
        windows.append((start.strftime("%Y%m%d"), end.strftime("%Y%m%d")))
    return windows


def _collect_paged(
    source: SourceConfig,
    page_size: int,
    max_pages: int,
    seen_ids: set[str],
    collected: list[dict],
    window: Optional[tuple[str, str]] = None,
) -> None:
    for page in range(1, max_pages + 1):
        params = _build_params(source, page, page_size, window)
        try:
            data = _http_get(source.url, params, source.fmt)
        except Exception as exc:  # noqa: BLE001
            print(f"[collector:{source.name}] page {page} 요청 실패: {exc}")
            break

        records = find_records(data)
        if not records:
            break

        new_on_page = 0
        for rec in records:
            norm = normalize_item(rec, source)
            if not norm:
                continue
            key = norm["source_id"]
            if key in seen_ids:
                continue
            seen_ids.add(key)
            collected.append(norm)
            new_on_page += 1

        # 새 항목이 없으면(=중복 페이지 또는 마지막 페이지) 종료.
        # 서버가 페이지 크기를 고정(예: 20건)하는 경우에도 안전하게 전 페이지 순회.
        if new_on_page == 0:
            break


def _collect_seoul(
    source: SourceConfig, seen_ids: set[str], collected: list[dict],
    chunk: int = 1000, max_total: int = 20000,
) -> None:
    """서울 열린데이터광장: 경로형 URL + 인덱스 구간 페이징."""
    base = source.url.rstrip("/")
    key = settings.SEOUL_OPEN_API_KEY
    start = 1
    while start <= max_total:
        end = start + chunk - 1
        url = f"{base}/{key}/json/culturalEventInfo/{start}/{end}/"
        try:
            data = _http_get(url, {}, "json")
        except Exception as exc:  # noqa: BLE001
            print(f"[collector:seoul] {start}-{end} 요청 실패: {exc}")
            break
        records = find_records(data)
        if not records:
            break
        new_on_chunk = 0
        for rec in records:
            norm = normalize_item(rec, source)
            if not norm:
                continue
            if norm["source_id"] in seen_ids:
                continue
            seen_ids.add(norm["source_id"])
            collected.append(norm)
            new_on_chunk += 1
        if len(records) < chunk or new_on_chunk == 0:
            break
        start += chunk


def fetch_source(
    source: SourceConfig, page_size: int = 100, max_pages: int = 30
) -> list[dict]:
    """한 소스에서 전체 페이지를 순회하며 정규화된 레코드 리스트를 반환."""
    collected: list[dict] = []
    seen_ids: set[str] = set()

    if source.kind == "seoul":
        _collect_seoul(source, seen_ids, collected)
    elif source.kind == "kopis":
        for window in _month_windows():
            _collect_paged(source, min(page_size, 100), max_pages,
                           seen_ids, collected, window)
    else:
        _collect_paged(source, page_size, max_pages, seen_ids, collected)

    print(f"[collector:{source.name}] 정규화 {len(collected)}건 수집")
    return collected


def fetch_markets(page_size: int = 1000, max_pages: int = 20) -> list[dict]:
    """전국전통시장표준데이터 수집 → 정규화된 시장 레코드 리스트."""
    if not settings.PUBLIC_DATA_API_KEY:
        return []
    url = "https://api.data.go.kr/openapi/tn_pubr_public_trdit_mrkt_api"
    out: list[dict] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        params = {
            "serviceKey": settings.PUBLIC_DATA_API_KEY,
            "pageNo": page, "numOfRows": page_size, "type": "json",
        }
        try:
            data = _http_get(url, params, "json")
        except Exception as exc:  # noqa: BLE001
            print(f"[collector:markets] page {page} 실패: {exc}")
            break
        records = find_records(data) or [
            r for r in _iter_dicts(data) if _lower_map(r).get("mrktnm")
        ]
        if not records:
            break
        new = 0
        for raw in records:
            lm = _lower_map(raw)
            name = _clean_str(lm.get("mrktnm"))
            if not name:
                continue
            addr = _clean_str(lm.get("rdnmadr") or lm.get("lnmadr"))
            lat, lng = normalize_coords([lm.get("latitude"), lm.get("longitude")])
            sid = f"{name}|{addr or ''}"[:120]
            if sid in seen:
                continue
            seen.add(sid)
            try:
                stores = int(float(str(lm.get("stornumber")).replace(",", "")))
            except (TypeError, ValueError):
                stores = None
            out.append({
                "source_id": sid,
                "name": name[:200],
                "market_type": _clean_str(lm.get("mrkttype")),
                "region": detect_region(addr, name),
                "sigungu": None,
                "address": addr,
                "lat": lat, "lng": lng,
                "stores": stores,
                "items": _clean_str(lm.get("trtmntprdlst")),
                "homepage": _clean_str(lm.get("homepageurl")),
                "tel": _clean_str(lm.get("phonenumber")),
                "estbl_year": _clean_str(lm.get("estblyear")),
            })
            new += 1
        if len(records) < page_size or new == 0:
            break
    print(f"[collector:markets] 전통시장 {len(out)}건 수집")
    return out


def diag_markets() -> dict:
    """전통시장 표준데이터 API 원시 응답 진단."""
    if not settings.PUBLIC_DATA_API_KEY:
        return {"ok": False, "error": "PUBLIC_DATA_API_KEY 미설정"}
    url = "https://api.data.go.kr/openapi/tn_pubr_public_trdit_mrkt_api"
    params = {
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "pageNo": 1, "numOfRows": 3, "type": "json",
    }
    out: dict = {"url": url, "key_len": len(settings.PUBLIC_DATA_API_KEY)}
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(url, params=params)
        out["http_status"] = resp.status_code
        text = resp.text.strip()
        out["raw_snippet"] = text[:700]
        parsed: Any = None
        try:
            parsed = json.loads(text) if text.startswith("{") else xmltodict.parse(text)
        except Exception:  # noqa: BLE001
            parsed = None
        out["records_found"] = len(find_records(parsed)) if parsed else 0
        out["ok"] = out["records_found"] > 0
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
    return out


def _iter_dicts(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _iter_dicts(v)
    elif isinstance(node, list):
        for v in node:
            yield from _iter_dicts(v)


def fetch_all() -> dict[str, list[dict]]:
    """모든 활성 소스를 수집하여 {source_name: [records]} 반환."""
    result: dict[str, list[dict]] = {}

    # 1) 로컬 시드(문화체육관광부 엑셀) — API 키 없이도 전국 데이터 확보
    try:
        from services import local_import
        records = local_import.load_festivals(settings.LOCAL_FESTIVAL_XLSX)
        if records:
            result[local_import.SOURCE_NAME] = records
    except Exception as exc:  # noqa: BLE001
        print(f"[collector:local] 로컬 임포트 실패: {exc}")

    # 2) 공공 API 소스들
    for source in default_sources():
        try:
            result[source.name] = fetch_source(source)
        except Exception as exc:  # noqa: BLE001
            print(f"[collector:{source.name}] 수집 실패: {exc}")
            result[source.name] = []
    return result
