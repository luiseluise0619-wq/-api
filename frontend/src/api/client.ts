import axios from 'axios'
import type {
  AIAnalysis,
  AskResult,
  Festival,
  Filters,
  MarketNear,
  SocialResult,
  Stats,
} from '../types'
import { DemoAPI } from './demo'

// 배포 기본 백엔드 주소 (Vercel 환경변수 VITE_API_BASE 로 덮어쓸 수 있음)
const DEFAULT_API = 'https://festival-ai-map-api.onrender.com'

const isDev = import.meta.env.DEV
// 개발: Vite 프록시(/api → localhost:8000). 배포: 환경변수 또는 기본 주소.
const baseURL = import.meta.env.VITE_API_BASE || (isDev ? '' : DEFAULT_API)

const api = axios.create({ baseURL, timeout: 15000 })

function cleanParams(f: Filters): Record<string, string> {
  const p: Record<string, string> = {}
  Object.entries(f).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p[k] = String(v)
  })
  return p
}

const RealAPI = {
  async mapFestivals(f: Filters = {}): Promise<Festival[]> {
    const { data } = await api.get('/api/festivals/map', { params: cleanParams(f) })
    return data
  },
  async list(f: Filters = {}, page = 1, pageSize = 200) {
    const { data } = await api.get('/api/festivals', {
      params: { ...cleanParams(f), page, page_size: pageSize },
    })
    return data as { total: number; items: Festival[] }
  },
  async detail(id: number): Promise<Festival> {
    const { data } = await api.get(`/api/festivals/${id}`)
    return data
  },
  async top(limit = 10): Promise<Festival[]> {
    const { data } = await api.get('/api/festivals/top', { params: { limit } })
    return data
  },
  async thisMonth(limit = 12): Promise<Festival[]> {
    const { data } = await api.get('/api/festivals/this-month', { params: { limit } })
    return data
  },
  async stats(): Promise<Stats> {
    const { data } = await api.get('/api/festivals/stats')
    return data
  },
  async regions(): Promise<string[]> {
    const { data } = await api.get('/api/festivals/regions')
    return data
  },
  async categories(): Promise<string[]> {
    const { data } = await api.get('/api/festivals/categories')
    return data
  },
  async analyze(id: number): Promise<AIAnalysis> {
    const { data } = await api.get(`/api/ai/analyze/${id}`)
    return data
  },
  async ask(question: string, festivalId?: number): Promise<AskResult> {
    const { data } = await api.post('/api/ai/ask', {
      question,
      festival_id: festivalId ?? null,
    })
    return data
  },
  async social(query = '', keyword = ''): Promise<SocialResult> {
    const { data } = await api.get('/api/social', { params: { query, keyword } })
    return data
  },
  async marketsNear(lat: number, lng: number, radiusKm = 2): Promise<MarketNear> {
    const { data } = await api.get('/api/markets/near', {
      params: { lat, lng, radius_km: radiusKm },
    })
    return data
  },
}

// 백엔드를 먼저 시도하고, 실패(콜드스타트·CORS·오프라인) 시 데모 데이터로 폴백.
// → 백엔드가 잠들거나 죽어도 화면이 깨지지 않는다.
function withFallback<T extends object>(real: T, demo: T): T {
  const wrapped: Record<string, unknown> = {}
  for (const key of Object.keys(demo) as (keyof T)[]) {
    const k = key as string
    wrapped[k] = async (...args: unknown[]) => {
      try {
        return await (real as Record<string, (...a: unknown[]) => unknown>)[k](...args)
      } catch (e) {
        console.warn(`[api] 백엔드 호출 실패 → 데모 폴백: ${k}`, e)
        return (demo as Record<string, (...a: unknown[]) => unknown>)[k](...args)
      }
    }
  }
  return wrapped as T
}

// 개발은 프록시로 직접, 배포는 폴백 래퍼 사용
export const FestivalAPI = isDev ? RealAPI : withFallback(RealAPI, DemoAPI)

