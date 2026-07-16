"""애플리케이션 환경설정 로딩.

.env 파일 또는 실제 환경변수에서 설정을 읽어온다.
민감정보(API 키, DB URL)는 절대 하드코딩하지 않는다.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Database -----------------------------------------------------------
    # 예) postgresql+psycopg2://user:pass@host:5432/dbname
    # Supabase 사용 시 대시보드의 connection string 을 그대로 넣으면 된다.
    DATABASE_URL: str = "sqlite:///./festival.db"

    # --- 공공데이터 API 키 ---------------------------------------------------
    # 공공데이터포털(data.go.kr)에서 발급받은 일반 인증키(Decoding)
    PUBLIC_DATA_API_KEY: str = ""
    # ifac.or.kr 지역축제 API 키 (선택)
    IFAC_API_KEY: str = ""
    # KOPIS 공연예술통합전산망 인증키 (선택)
    KOPIS_API_KEY: str = ""
    # YouTube Data API v3 키 (선택) — 소셜 패널에서 실제 영상 검색에 사용
    YOUTUBE_API_KEY: str = ""

    # 추가 소스 주입용 JSON 배열 문자열.
    # 예) '[{"name":"changnyeong","label":"창녕군 행사",
    #       "url":"https://.../getEvent","fmt":"xml","region_hint":"경상남도"}]'
    EXTRA_SOURCES_JSON: str = ""

    # 문화체육관광부 2026 지역축제 엑셀 (로컬 시드 데이터, API 키 불필요)
    LOCAL_FESTIVAL_XLSX: str = "data/2026_festivals.xlsx"

    # --- Google Gemini ------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- 스케줄러 -----------------------------------------------------------
    # 하루 1회 자동 수집 실행 시각 (24h 기준)
    SCHEDULE_HOUR: int = 4
    SCHEDULE_MINUTE: int = 0
    # 앱 시작 직후 1회 수집을 즉시 실행할지 여부
    COLLECT_ON_STARTUP: bool = False

    # --- CORS ---------------------------------------------------------------
    # 프론트엔드 origin (쉼표로 여러 개 지정 가능)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
