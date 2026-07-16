"""AI(Gemini) 라우터: 축제 상세 분석 / 자유 질문."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Festival
from schemas import AIAnalysisResponse, AskRequest, AskResponse
from services import gemini_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/analyze/{festival_id}", response_model=AIAnalysisResponse)
def analyze(festival_id: int, db: Session = Depends(get_db)):
    f = db.get(Festival, festival_id)
    if f is None:
        raise HTTPException(status_code=404, detail="축제를 찾을 수 없습니다.")
    analysis, by = gemini_service.analyze_festival(f.to_dict())
    return AIAnalysisResponse(
        festival_id=festival_id, title=f.title, analysis=analysis, generated_by=by
    )


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    if not payload.question or not payload.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력하세요.")
    festival = None
    if payload.festival_id:
        f = db.get(Festival, payload.festival_id)
        festival = f.to_dict() if f else None
    answer, by = gemini_service.ask_question(payload.question.strip(), festival)
    return AskResponse(answer=answer, generated_by=by)
