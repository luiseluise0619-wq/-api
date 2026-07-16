# 🎪 Festival AI Map

**AI 기반 전국 축제·상권 분석 지도 서비스**

대한민국 전국 지역축제 데이터를 공공데이터 API로 수집해 한국 지도 위에 표시하고,
축제를 선택하면 **Google Gemini AI**가 상권 영향·지역경제·홍보전략·SNS 아이디어까지
분석해 주는 풀스택 웹 서비스입니다.

> 검정 배경의 모던 SaaS UI (Linear / Vercel / Notion 스타일) · 반응형 · 카드형 레이아웃

---

## ✨ 핵심 기능

| 구분 | 기능 |
|------|------|
| **데이터 수집** | 문화체육관광부 2026 전국축제(시드) + 공공데이터포털 지자체·TourAPI·KOPIS·ifac 자동 수집 · 하루 1회 스케줄링 · 중복 제거 · DB 저장 |
| **지도** | 대한민국 다크 지도 · 축제 마커(점수별 색상) · 확대/축소 · 지역/분류/날짜/상태 필터 · 진행중 축제 · **지역별 밀집도 히트맵** |
| **AI (Gemini)** | 축제 개요·예상 방문객·소상공인 매출 영향·지역경제·홍보전략·SNS 콘텐츠·개선점 분석 · **AI에게 질문하기** |
| **랭킹/추천** | 축제별 **AI 상권 영향력 점수(★★★★★ / 100점)** · 인기 축제 **TOP 10** · 이번 달 추천 축제 |
| **SNS 소셜 피드** | 우측 패널에서 X·인스타·페북·유튜브·네이버 키워드/해시태그 검색 · YouTube 실검색(API 키 설정 시) |

---

## 🧱 기술 스택

**Frontend** React 18 · Vite · TypeScript · Tailwind CSS · React-Leaflet · Axios
**Backend** Python FastAPI · SQLAlchemy · PostgreSQL/SQLite · APScheduler
**AI** Google Gemini API
**배포** Frontend → Vercel · Backend → Render/AWS · DB → Supabase PostgreSQL

---

## 📁 프로젝트 구조

```
festival-ai-map/
├── backend/
│   ├── main.py                # FastAPI 엔트리 (+ 수동수집 /api/collect)
│   ├── config.py              # 환경변수 로딩
│   ├── database.py            # SQLAlchemy 엔진/세션
│   ├── models.py              # Festival ORM (source+source_id 유니크 → 중복제거)
│   ├── schemas.py             # Pydantic 스키마
│   ├── requirements.txt
│   ├── data/2026_festivals.xlsx  # 문화체육관광부 2026 전국축제 시드(1,266건)
│   ├── services/
│   │   ├── collectors.py      # 범용 수집기 (좌표 자동판별 + 다지자체 포맷 흡수)
│   │   ├── local_import.py    # 엑셀 시드 임포터 (API 키 없이 동작)
│   │   ├── geocode.py         # 지역 좌표 보정/중심점 분산
│   │   ├── scoring.py         # AI 상권 점수 / 인기도 규칙
│   │   ├── gemini_service.py  # Gemini 분석·질문 (키 없으면 폴백)
│   │   └── scheduler.py       # 수집+저장+하루1회 스케줄
│   └── routers/
│       ├── festivals.py       # 조회/필터/TOP/이번달/통계/히트맵
│       ├── ai.py              # Gemini 분석/질문
│       └── social.py          # SNS 소셜 피드 딥링크 + YouTube
└── frontend/
    ├── index.html · vite.config.ts · tailwind.config.js
    └── src/
        ├── App.tsx            # 3단 레이아웃(컨트롤 | 지도 | SNS)
        ├── api/client.ts      # Axios API 래퍼
        ├── types.ts · utils.ts
        └── components/
            ├── MapView.tsx    # Leaflet 지도 + 마커/히트맵
            ├── Filters.tsx    · StatCards.tsx · ScoreBadge.tsx
            ├── TopFestivals.tsx
            ├── FestivalDetail.tsx  # 상세 드로어
            ├── AIAnalysis.tsx · AskAI.tsx
            └── SocialPanel.tsx     # 우측 SNS 패널
```

---

## 🚀 설치 & 실행

### 0) 사전 준비 — API 키 발급 (무료)
- **공공데이터포털** https://www.data.go.kr → "지역축제" 검색 후 활용신청 → **일반 인증키(Decoding)**
  (대전·울산·부산·보성·괴산·서천·세종·영천·경주·춘천·광양 + 한국관광공사 TourAPI 공용)
- **Google Gemini** https://aistudio.google.com/app/apikey → `GEMINI_API_KEY`
- (선택) KOPIS, YouTube Data API v3 키

> ⚠️ 키가 하나도 없어도 됩니다. `backend/data/2026_festivals.xlsx`(문화체육관광부 전국 1,266개 축제)로
> 즉시 지도·랭킹·AI(규칙 기반 폴백)가 동작합니다. 키를 넣으면 실시간 API + Gemini가 활성화됩니다.

### 1) Backend 실행

```bash
cd backend
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # .env 에 발급받은 키 입력
uvicorn main:app --reload --port 8000
```

- 최초 실행 시 `COLLECT_ON_STARTUP=true` 이면 부팅 직후 전체 수집이 1회 실행됩니다.
- 언제든 수동 수집: `curl -X POST http://localhost:8000/api/collect`
- API 문서(Swagger): http://localhost:8000/docs

### 2) Frontend 실행 (새 터미널)

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

개발 모드에서는 Vite 프록시가 `/api` 요청을 `localhost:8000` 으로 전달합니다.
브라우저에서 **http://localhost:5173** 접속.

> 실행 순서: **Backend(8000) 먼저 → Frontend(5173)**.

---

## 🔌 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/festivals/map` | 지도 마커용 (좌표 있는 축제) |
| GET | `/api/festivals` | 목록/필터/페이지네이션 |
| GET | `/api/festivals/top?limit=10` | 인기 TOP N |
| GET | `/api/festivals/this-month` | 이번 달 추천 |
| GET | `/api/festivals/stats` | 통계 + 지역별 밀집도(히트맵) |
| GET | `/api/festivals/{id}` | 상세 |
| GET | `/api/ai/analyze/{id}` | Gemini 심층 분석 |
| POST | `/api/ai/ask` | 자유 질문 |
| GET | `/api/social?query=&keyword=` | SNS 소셜 피드 |
| POST | `/api/collect` | 수동 전체 수집 |

---

## ➕ 지자체 축제 API 추가하기 (코드 수정 없이)

공공데이터포털에서 새 지자체 축제 API 를 신청했다면 `.env` 에 한 줄만 추가하세요:

```bash
EXTRA_SOURCES_JSON=[{"name":"changnyeong","label":"창녕군 행사","url":"https://apis.data.go.kr/xxxx/getEvent","fmt":"xml","region_hint":"경상남도","param_style":"std"}]
```

- `param_style`: `std`(pageNo/numOfRows) · `egov_unit`(pageIndex/pageUnit) · `egov_first`(firstIndex/pageIndex)
- 수집기가 좌표(위경도 범위 자동판별)·날짜·필드명을 알아서 매핑합니다.

---

## 🏪 "소상공인 연관 축제"는 어떻게?

1. **키워드 필터** — 수집된 축제를 `시장/상권/먹거리/야시장/특산/전통시장` 키워드로 필터(상권 점수에 가중치 반영).
2. **SNS 소셜 패널** — 우측 패널의 `#소상공인 #전통시장` 칩으로 각 플랫폼 검색.
3. **추가 연동 권장 API** — 소상공인시장진흥공단 **상가(상권)정보** API(전국 상가업소·좌표)를 연동하면
   축제 반경 내 실제 업종 분포로 상권 영향을 정량 분석할 수 있습니다. (`EXTRA_SOURCES_JSON` 또는 별도 라우터로 확장)

---

## ☁️ 배포 가이드

- **DB**: Supabase 프로젝트 생성 → connection string 을 백엔드 `DATABASE_URL` 에 입력
- **Backend (Render)**: `pip install -r requirements.txt` / `uvicorn main:app --host 0.0.0.0 --port $PORT`, 환경변수 등록
- **Frontend (Vercel)**: `frontend` 루트, 빌드 `npm run build`, 출력 `dist`, 환경변수 `VITE_API_BASE=https://<백엔드주소>`
- 백엔드 `CORS_ORIGINS` 에 Vercel 도메인 추가

---

## 📝 라이선스 / 데이터 출처

- 축제 데이터: 공공데이터포털(data.go.kr), 문화체육관광부, 한국관광공사, 각 지자체, KOPIS — 이용허락범위 제한 없음
- 본 프로젝트 코드: MIT
