"""Google Gemini 연동 서비스.

- 축제 상세 AI 분석 (개요/방문객/상권영향/지역경제/홍보전략/SNS/개선점)
- 자유 질문 응답 ("이 축제 주변에서 장사하면 어떤 업종이 유리해?")

GEMINI_API_KEY 가 없으면 규칙 기반 폴백 응답을 제공하여 서비스가 항상 동작한다.
"""
from __future__ import annotations

import json
from typing import Optional

from config import settings

try:
    import google.generativeai as genai
except Exception:  # noqa: BLE001
    genai = None


_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    if not settings.GEMINI_API_KEY or genai is None:
        return None
    genai.configure(api_key=settings.GEMINI_API_KEY)
    _model = genai.GenerativeModel(settings.GEMINI_MODEL)
    return _model


ANALYSIS_SECTIONS = [
    ("summary", "축제 개요 요약"),
    ("visitors", "예상 방문객 분석"),
    ("commerce_impact", "주변 소상공인 매출 영향 분석"),
    ("local_economy", "지역경제 활성화 가능성"),
    ("promotion", "추천 홍보 전략"),
    ("sns_ideas", "SNS 콘텐츠 아이디어"),
    ("improvements", "개선점"),
]


def _festival_context(f: dict) -> str:
    parts = [
        f"축제명: {f.get('title')}",
        f"지역: {f.get('region') or ''} {f.get('sigungu') or ''}".strip(),
        f"장소: {f.get('place') or f.get('address') or ''}",
        f"분류: {f.get('category') or '미분류'}",
        f"기간: {f.get('start_date') or ''} ~ {f.get('end_date') or ''} {f.get('period_text') or ''}".strip(),
        f"주최/주관: {f.get('organizer') or ''}",
    ]
    desc = (f.get("description") or "").strip()
    if desc:
        parts.append(f"상세정보: {desc[:1500]}")
    return "\n".join(p for p in parts if p)


def analyze_festival(f: dict) -> tuple[dict, str]:
    """축제 상세 분석 dict 와 생성자(gemini/fallback) 반환."""
    model = _get_model()
    if model is None:
        return _fallback_analysis(f), "fallback"

    section_desc = "\n".join(f"- {key}: {label}" for key, label in ANALYSIS_SECTIONS)
    prompt = f"""너는 대한민국 지역축제와 상권·지역경제를 분석하는 전문 컨설턴트다.
아래 축제 정보를 바탕으로 각 항목을 한국어로 구체적이고 실용적으로 분석하라.
반드시 아래 JSON 스키마의 키만 사용해 순수 JSON 으로만 답하라(코드블록/설명 금지).

[축제 정보]
{_festival_context(f)}

[출력 JSON 키]
{section_desc}

각 값은 2~4문장의 문자열로 작성. sns_ideas 는 3~5개의 아이디어를 한 문자열에 줄바꿈으로.
"""
    try:
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        data = _extract_json(text)
        if data:
            # 누락된 섹션은 빈 문자열로 보정
            return {k: str(data.get(k, "")).strip() for k, _ in ANALYSIS_SECTIONS}, "gemini"
    except Exception as exc:  # noqa: BLE001
        print(f"[gemini] 분석 실패, 폴백 사용: {exc}")
    return _fallback_analysis(f), "fallback"


def ask_question(question: str, f: Optional[dict]) -> tuple[str, str]:
    """축제 맥락(선택) + 질문에 대한 자유 응답."""
    model = _get_model()
    context = _festival_context(f) if f else "특정 축제가 지정되지 않음."
    if model is None:
        return _fallback_answer(question, f), "fallback"
    prompt = f"""너는 대한민국 지역축제·상권 분석 전문가다.
아래 축제 맥락을 참고하여 사용자 질문에 한국어로 구체적이고 실용적으로 답하라.
근거와 함께 3~6문장으로 답하되, 단정적 수치는 추정임을 밝혀라.

[축제 맥락]
{context}

[질문]
{question}
"""
    try:
        resp = model.generate_content(prompt)
        answer = (resp.text or "").strip()
        if answer:
            return answer, "gemini"
    except Exception as exc:  # noqa: BLE001
        print(f"[gemini] 질문 응답 실패, 폴백 사용: {exc}")
    return _fallback_answer(question, f), "fallback"


# ---------------------------------------------------------------------------
# 유틸 / 폴백
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    # 코드블록 제거
    if "```" in text:
        text = text.split("```")[1] if len(text.split("```")) > 1 else text
        text = text.replace("json", "", 1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _fallback_analysis(f: dict) -> dict:
    title = f.get("title", "이 축제")
    region = f.get("region") or "해당 지역"
    cat = f.get("category") or "지역"
    score = f.get("ai_score", 0)
    return {
        "summary": f"'{title}'은(는) {region}에서 열리는 {cat} 성격의 축제입니다. "
                   f"{(f.get('description') or '')[:120]}",
        "visitors": f"규모·분류·정보 충실도를 종합한 추정 상권 영향력 점수는 {score}점입니다. "
                    "가족·지역주민 중심 방문이 예상되며, 주말·개막일에 방문객이 집중될 가능성이 큽니다.",
        "commerce_impact": "행사장 반경 500m 내 요식업·카페·편의점 매출 증가가 기대됩니다. "
                           "특히 축제 시간대(오후~저녁)와 주말에 유동인구가 집중됩니다.",
        "local_economy": "숙박·교통·특산품 판매를 통한 역외 소비 유입 가능성이 있습니다. "
                         "지역 브랜드 홍보와 재방문 유도가 관건입니다.",
        "promotion": "SNS 숏폼(릴스/쇼츠) 중심의 사전 홍보와 인근 상점 제휴 쿠폰이 효과적입니다. "
                     "지역 인플루언서 협업을 권장합니다.",
        "sns_ideas": "\n".join([
            f"1) '{title}' 필수 포토스팟 TOP5 릴스",
            "2) 현장 먹거리 리뷰 쇼츠",
            "3) 방문객 인터뷰 하이라이트",
            "4) 축제 X 지역상점 스탬프 투어 챌린지",
            "5) 타임랩스로 담은 축제의 하루",
        ]),
        "improvements": "주차·대중교통 접근성 안내 강화, 좌표/일정 데이터 정확도 개선, "
                        "다국어 안내와 결제 편의(간편결제) 확대가 필요합니다.",
        "_note": "GEMINI_API_KEY 미설정으로 규칙 기반 요약을 제공했습니다.",
    }


def _fallback_answer(question: str, f: Optional[dict]) -> str:
    title = (f or {}).get("title", "해당 축제")
    return (
        f"(AI 키 미설정 · 규칙 기반 답변) '{title}' 관련 질문 '{question}'에 대해: "
        "일반적으로 축제 상권에서는 회전율이 높은 분식·음료·간편식과 포토·굿즈 판매가 유리합니다. "
        "저녁 시간대 유동인구가 많다면 주류·야식 업종도 고려할 수 있습니다. "
        "정확한 분석을 원하면 백엔드 .env 에 GEMINI_API_KEY 를 설정하세요."
    )
