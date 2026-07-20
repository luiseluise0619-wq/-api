/**
 * 데모(백엔드 없음) 모드 API.
 *
 * VITE_API_BASE 가 비어 있으면(예: 백엔드 미배포 상태의 Vercel) 이 모듈이
 * public/festivals.seed.json (문화체육관광부 2026 전국축제)을 불러와
 * 필터/통계/TOP/AI 폴백을 모두 클라이언트에서 계산해 서비스가 동작하게 한다.
 */
import type {
  AIAnalysis,
  AskResult,
  Festival,
  Filters,
  MarketNear,
  SocialResult,
  Stats,
} from '../types'

interface Seed {
  id: number
  t: string
  rg?: string
  sg?: string
  c?: string
  pl?: string
  og?: string
  sd?: string | null
  ed?: string | null
  lat?: number | null
  lng?: number | null
  s: number
  p: number
  tel?: string | null
}

let cache: Festival[] | null = null

async function load(): Promise<Festival[]> {
  if (cache) return cache
  const res = await fetch('/festivals.seed.json')
  const rows: Seed[] = await res.json()
  cache = rows.map((r) => ({
    id: r.id,
    source: 'seed',
    source_id: String(r.id),
    title: r.t,
    category: r.c ?? null,
    region: r.rg ?? null,
    sigungu: r.sg ?? null,
    place: r.pl ?? null,
    address: null,
    lat: r.lat ?? null,
    lng: r.lng ?? null,
    start_date: r.sd ?? null,
    end_date: r.ed ?? null,
    period_text: null,
    organizer: r.og ?? null,
    tel: r.tel ?? null,
    homepage: null,
    image_url: null,
    detail_url: null,
    description: null,
    fee: null,
    ai_score: r.s,
    popularity: r.p,
  }))
  return cache
}

const REGION_C: Record<string, [number, number]> = {
  서울특별시: [37.5665, 126.978], 부산광역시: [35.1796, 129.0756],
  대구광역시: [35.8714, 128.6014], 인천광역시: [37.4563, 126.7052],
  광주광역시: [35.1595, 126.8526], 대전광역시: [36.3504, 127.3845],
  울산광역시: [35.5384, 129.3114], 세종특별자치시: [36.4801, 127.289],
  경기도: [37.4138, 127.5183], 강원특별자치도: [37.8228, 128.1555],
  충청북도: [36.6357, 127.4917], 충청남도: [36.5184, 126.8],
  전북특별자치도: [35.7175, 127.153], 전라남도: [34.8161, 126.463],
  경상북도: [36.4919, 128.8889], 경상남도: [35.4606, 128.2132],
  제주특별자치도: [33.489, 126.4983],
}

// 연관 키워드 확장 — '소상공인' 검색 시 관련 축제까지 매칭
const SYNONYMS: Record<string, string[]> = {
  소상공인: ['소상공인', '시장', '상권', '전통시장', '먹거리', '특산', '야시장', '장터', '상인', '골목', '로컬', '창업'],
  전통시장: ['전통시장', '시장', '장터', '상인', '먹거리', '상권'],
  상권: ['상권', '시장', '소상공인', '먹거리', '전통시장'],
  먹거리: ['먹거리', '음식', '맛', '미식', '푸드', '특산', '한우', '막국수', '국밥'],
  꽃: ['꽃', '벚꽃', '장미', '유채', '튤립', '연꽃', '국화', '매화', '코스모스', '철쭉'],
  불꽃: ['불꽃', '불빛', '빛', '야경', '등불', '유등'],
  음악: ['음악', '재즈', '락', '뮤직', '콘서트', '가요', '오케스트라', '버스킹'],
  문화: ['문화', '예술', '전통', '민속', '역사'],
  바다: ['바다', '해변', '해수욕', '항', '포구', '어시장'],
  겨울: ['겨울', '눈', '얼음', '빙어', '산천어', '눈꽃'],
}

function expandQuery(q: string): string[] {
  const key = q.trim().toLowerCase()
  for (const [k, list] of Object.entries(SYNONYMS)) {
    if (key === k || key.includes(k)) return list.map((s) => s.toLowerCase())
  }
  return [key]
}

const TODAY = new Date()
function status(f: Festival): string {
  if (!f.start_date && !f.end_date) return 'unknown'
  const s = new Date(f.start_date || f.end_date!)
  const e = new Date(f.end_date || f.start_date!)
  const t = new Date(TODAY.toISOString().slice(0, 10))
  if (s <= t && t <= e) return 'ongoing'
  return t < s ? 'upcoming' : 'ended'
}

function applyFilters(items: Festival[], f: Filters): Festival[] {
  return items.filter((x) => {
    if (f.region && x.region !== f.region) return false
    if (f.category && !(x.category || '').includes(f.category)) return false
    if (f.status && status(x) !== f.status) return false
    if (f.q) {
      const terms = expandQuery(f.q)
      const hay = [
        x.title, x.region, x.sigungu, x.category, x.place, x.organizer,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      if (!terms.some((t) => hay.includes(t))) return false
    }
    if (f.date_from && x.end_date && x.end_date < f.date_from) return false
    if (f.date_to && x.start_date && x.start_date > f.date_to) return false
    return true
  })
}

function fallbackAnalysis(f: Festival): Record<string, string> {
  const rg = f.region || '해당 지역'
  const cat = f.category || '지역'
  return {
    summary: `'${f.title}'은(는) ${rg} ${f.sigungu || ''}에서 열리는 ${cat} 성격의 축제입니다. 주최는 ${f.organizer || '지자체'}입니다.`,
    visitors: `종합 상권 영향력 점수는 ${f.ai_score}점입니다. 가족·지역주민 중심 방문이 예상되며 주말·개막일에 방문객이 집중될 가능성이 큽니다.`,
    commerce_impact: '행사장 반경 500m 내 요식업·카페·편의점 매출 증가가 기대됩니다. 오후~저녁·주말에 유동인구가 집중됩니다.',
    local_economy: '숙박·교통·특산품 판매를 통한 역외 소비 유입 가능성이 있습니다. 지역 브랜드 홍보와 재방문 유도가 관건입니다.',
    promotion: 'SNS 숏폼 사전 홍보와 인근 상점 제휴 쿠폰이 효과적입니다. 지역 인플루언서 협업을 권장합니다.',
    sns_ideas: `1) '${f.title}' 포토스팟 TOP5 릴스\n2) 현장 먹거리 리뷰 쇼츠\n3) 방문객 인터뷰\n4) 지역상점 스탬프 투어 챌린지\n5) 축제의 하루 타임랩스`,
    improvements: '주차·대중교통 접근성 안내 강화, 일정/좌표 데이터 정확도 개선, 다국어 안내·간편결제 확대가 필요합니다.',
    _note: '데모 모드(백엔드 미연결) — 규칙 기반 분석입니다. 백엔드+GEMINI_API_KEY 연결 시 실제 Gemini 분석이 제공됩니다.',
  }
}

export const DemoAPI = {
  async mapFestivals(f: Filters = {}): Promise<Festival[]> {
    const all = await load()
    return applyFilters(all, f).filter((x) => x.lat != null && x.lng != null)
  },
  async list(f: Filters = {}, page = 1, pageSize = 200) {
    const all = applyFilters(await load(), f)
    const start = (page - 1) * pageSize
    return { total: all.length, items: all.slice(start, start + pageSize) }
  },
  async detail(id: number): Promise<Festival> {
    const all = await load()
    const f = all.find((x) => x.id === id)
    if (!f) throw new Error('not found')
    return f
  },
  async top(limit = 10): Promise<Festival[]> {
    const all = await load()
    return [...all].sort((a, b) => b.popularity - a.popularity || b.ai_score - a.ai_score).slice(0, limit)
  },
  async thisMonth(limit = 12): Promise<Festival[]> {
    const all = await load()
    const now = new Date()
    const ms = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10)
    const me = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10)
    return all
      .filter((f) => f.start_date && f.start_date <= me && (f.end_date || f.start_date)! >= ms)
      .sort((a, b) => b.ai_score - a.ai_score)
      .slice(0, limit)
  },
  async stats(): Promise<Stats> {
    const all = await load()
    const counts: Record<string, number> = {}
    all.forEach((f) => {
      if (f.region) counts[f.region] = (counts[f.region] || 0) + 1
    })
    const by_region = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .map(([region, count]) => ({
        region,
        count,
        lat: REGION_C[region]?.[0] ?? null,
        lng: REGION_C[region]?.[1] ?? null,
      }))
    return {
      total: all.length,
      ongoing: all.filter((f) => status(f) === 'ongoing').length,
      upcoming: all.filter((f) => status(f) === 'upcoming').length,
      regions: by_region.length,
      by_region,
    }
  },
  async regions(): Promise<string[]> {
    const all = await load()
    return [...new Set(all.map((f) => f.region).filter(Boolean))].sort() as string[]
  },
  async categories(): Promise<string[]> {
    const all = await load()
    return [...new Set(all.map((f) => f.category).filter(Boolean))].sort() as string[]
  },
  async analyze(id: number): Promise<AIAnalysis> {
    const f = await this.detail(id)
    return { festival_id: id, title: f.title, analysis: fallbackAnalysis(f), generated_by: 'fallback' }
  },
  async ask(question: string, festivalId?: number): Promise<AskResult> {
    let title = '해당 축제'
    if (festivalId) {
      try {
        title = (await this.detail(festivalId)).title
      } catch {
        /* ignore */
      }
    }
    return {
      answer: `(데모 모드) '${title}' 관련: 축제 상권에서는 회전율 높은 분식·음료·간편식과 포토·굿즈 판매가 유리합니다. 저녁 유동인구가 많다면 야식·주류도 고려할 만합니다. 백엔드+Gemini 연결 시 축제 상세정보를 반영한 답변이 제공됩니다.`,
      generated_by: 'fallback',
    }
  },
  async social(query = '', keyword = ''): Promise<SocialResult> {
    const final = [query, keyword].filter(Boolean).join(' ') || '소상공인 축제'
    const enc = encodeURIComponent(final)
    const tag = encodeURIComponent(final.replace(/ /g, ''))
    return {
      query: final,
      keywords: ['축제', '행사', '지역축제', '소상공인', '전통시장'],
      youtube: [],
      youtube_enabled: false,
      links: [
        { platform: 'x', label: `X(트위터) "${final}" 검색`, url: `https://twitter.com/search?q=${enc}&f=live` },
        { platform: 'instagram', label: `인스타그램 #${final.replace(/ /g, '')}`, url: `https://www.instagram.com/explore/tags/${tag}/` },
        { platform: 'facebook', label: `페이스북 "${final}" 검색`, url: `https://www.facebook.com/search/top?q=${enc}` },
        { platform: 'youtube', label: `유튜브 "${final}" 검색`, url: `https://www.youtube.com/results?search_query=${enc}` },
        { platform: 'naver', label: `네이버 "${final}" 검색`, url: `https://search.naver.com/search.naver?query=${enc}` },
      ],
    }
  },
  async marketsNear(lat: number, lng: number, radiusKm = 2): Promise<MarketNear> {
    // 데모 모드에는 전통시장 시드가 없다. 백엔드 연결 시 실제 데이터 제공.
    return { center_lat: lat, center_lng: lng, radius_km: radiusKm, market_count: 0, total_stores: 0, markets: [] }
  },
}
