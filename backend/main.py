"""Festival AI Map - FastAPI 엔트리포인트.

실행:
  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import Base, engine
from routers import ai as ai_router
from routers import festivals as festivals_router
from routers import markets as markets_router
from routers import social as social_router
from schemas import CollectResult
from services import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 테이블 생성 (운영에서는 Alembic 권장)
    # DB 가 일시적으로 불가해도 서버는 뜨도록(헬스체크 통과) 실패를 흡수한다.
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        print(f"[startup] DB 초기화 실패(서버는 계속 기동): {exc}")
    scheduler.start_scheduler()
    if settings.COLLECT_ON_STARTUP:
        # 수집을 백그라운드 스레드에서 실행해 서버 부팅(포트 오픈)을 막지 않는다.
        # (Render 등에서 시작이 지연되어 배포 실패로 판정되는 것을 방지)
        def _bg_collect():
            try:
                scheduler.run_collection()
            except Exception as exc:  # noqa: BLE001
                print(f"[startup] 초기 수집 실패: {exc}")

        threading.Thread(target=_bg_collect, daemon=True).start()
    yield
    scheduler.shutdown_scheduler()


app = FastAPI(
    title="Festival AI Map API",
    description="전국 축제·상권 분석 + Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(festivals_router.router)
app.include_router(ai_router.router)
app.include_router(social_router.router)
app.include_router(markets_router.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "festival-ai-map"}


@app.post("/api/collect", response_model=CollectResult, tags=["admin"])
async def collect_now():
    """수동으로 전체 소스 수집을 즉시 실행 (관리용)."""
    summary = await run_in_threadpool(scheduler.run_collection)
    return CollectResult(
        ok=True,
        inserted=summary["inserted"],
        updated=summary["updated"],
        total_seen=summary["total_seen"],
        per_source=summary["per_source"],
        message=f"수집 완료 ({summary['elapsed_sec']}초)",
    )
