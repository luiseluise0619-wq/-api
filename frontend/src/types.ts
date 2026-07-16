export interface Festival {
  id: number
  source: string
  source_id: string
  title: string
  category?: string | null
  region?: string | null
  sigungu?: string | null
  place?: string | null
  address?: string | null
  lat?: number | null
  lng?: number | null
  start_date?: string | null
  end_date?: string | null
  period_text?: string | null
  organizer?: string | null
  tel?: string | null
  homepage?: string | null
  image_url?: string | null
  detail_url?: string | null
  description?: string | null
  fee?: string | null
  ai_score: number
  popularity: number
}

export interface RegionCount {
  region: string
  count: number
  lat?: number | null
  lng?: number | null
}

export interface Stats {
  total: number
  ongoing: number
  upcoming: number
  regions: number
  by_region: RegionCount[]
}

export interface AIAnalysis {
  festival_id: number
  title: string
  analysis: Record<string, string>
  generated_by: string
}

export interface AskResult {
  answer: string
  generated_by: string
}

export interface Market {
  id: number
  name: string
  market_type?: string | null
  region?: string | null
  address?: string | null
  lat?: number | null
  lng?: number | null
  stores: number
  items?: string | null
  distance_km?: number | null
}

export interface MarketNear {
  center_lat: number
  center_lng: number
  radius_km: number
  market_count: number
  total_stores: number
  markets: Market[]
}

export interface YouTubeItem {
  title: string
  url: string
  thumbnail?: string | null
  channel?: string | null
  published_at?: string | null
}

export interface PlatformLink {
  platform: string
  label: string
  url: string
}

export interface SocialResult {
  query: string
  keywords: string[]
  youtube: YouTubeItem[]
  youtube_enabled: boolean
  links: PlatformLink[]
}

export interface Filters {
  region?: string
  category?: string
  status?: string
  q?: string
  date_from?: string
  date_to?: string
}
