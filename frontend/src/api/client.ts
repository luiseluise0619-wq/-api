import axios from 'axios'
import type {
  AIAnalysis,
  AskResult,
  Festival,
  Filters,
  SocialResult,
  Stats,
} from '../types'

const baseURL = import.meta.env.VITE_API_BASE || ''

const api = axios.create({ baseURL, timeout: 30000 })

function cleanParams(f: Filters): Record<string, string> {
  const p: Record<string, string> = {}
  Object.entries(f).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') p[k] = String(v)
  })
  return p
}

export const FestivalAPI = {
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
}
