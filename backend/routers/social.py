"""SNS 소셜 피드 라우터.

- YouTube: YOUTUBE_API_KEY 설정 시 Data API v3 로 실제 영상 검색.
- X(트위터)/인스타그램/페이스북/네이버: 공개 검색 API 가 폐쇄/유료화되어
  서버 스크래핑이 불가하므로, 각 플랫폼의 키워드·해시태그 검색 딥링크를 제공.

프론트엔드 우측 소셜 패널에서 사용한다.
"""
from __future__ import annotations

import urllib.parse

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

from config import settings

router = APIRouter(prefix="/api/social", tags=["social"])

# 소상공인/축제 관련 기본 키워드
DEFAULT_KEYWORDS = ["축제", "행사", "지역축제", "소상공인", "전통시장"]


class YouTubeItem(BaseModel):
    title: str
    url: str
    thumbnail: str | None = None
    channel: str | None = None
    published_at: str | None = None


class PlatformLink(BaseModel):
    platform: str
    label: str
    url: str


class SocialResponse(BaseModel):
    query: str
    keywords: list[str]
    youtube: list[YouTubeItem]
    youtube_enabled: bool
    links: list[PlatformLink]


def _deeplinks(query: str) -> list[PlatformLink]:
    q = query.strip()
    enc = urllib.parse.quote(q)
    tag = urllib.parse.quote(q.replace(" ", ""))
    return [
        PlatformLink(platform="x", label=f'X(트위터) "{q}" 검색',
                     url=f"https://twitter.com/search?q={enc}&f=live"),
        PlatformLink(platform="instagram", label=f'인스타그램 #{q.replace(" ", "")} 태그',
                     url=f"https://www.instagram.com/explore/tags/{tag}/"),
        PlatformLink(platform="facebook", label=f'페이스북 "{q}" 검색',
                     url=f"https://www.facebook.com/search/top?q={enc}"),
        PlatformLink(platform="youtube", label=f'유튜브 "{q}" 검색',
                     url=f"https://www.youtube.com/results?search_query={enc}"),
        PlatformLink(platform="naver", label=f'네이버 "{q}" 검색',
                     url=f"https://search.naver.com/search.naver?query={enc}"),
    ]


def _fetch_youtube(query: str, max_results: int = 8) -> list[YouTubeItem]:
    if not settings.YOUTUBE_API_KEY:
        return []
    try:
        resp = httpx.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "order": "relevance",
                "regionCode": "KR",
                "relevanceLanguage": "ko",
                "key": settings.YOUTUBE_API_KEY,
            },
            timeout=12.0,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as exc:  # noqa: BLE001
        print(f"[social] YouTube 검색 실패: {exc}")
        return []

    out: list[YouTubeItem] = []
    for it in items:
        vid = it.get("id", {}).get("videoId")
        sn = it.get("snippet", {})
        if not vid:
            continue
        out.append(YouTubeItem(
            title=sn.get("title", ""),
            url=f"https://www.youtube.com/watch?v={vid}",
            thumbnail=(sn.get("thumbnails", {}).get("medium", {}) or {}).get("url"),
            channel=sn.get("channelTitle"),
            published_at=sn.get("publishedAt"),
        ))
    return out


@router.get("", response_model=SocialResponse)
def social(
    query: str = Query("", description="검색어(축제명 등). 비우면 기본 키워드 사용"),
    keyword: str = Query("", description="추가 키워드(축제/행사/소상공인 등)"),
):
    base = query.strip()
    kw = keyword.strip()
    # 최종 검색어 구성: (축제명) + (키워드)
    if base and kw:
        final = f"{base} {kw}"
    elif base:
        final = base
    elif kw:
        final = kw
    else:
        final = "소상공인 축제"

    return SocialResponse(
        query=final,
        keywords=DEFAULT_KEYWORDS,
        youtube=_fetch_youtube(final),
        youtube_enabled=bool(settings.YOUTUBE_API_KEY),
        links=_deeplinks(final),
    )
