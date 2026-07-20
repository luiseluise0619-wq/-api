import type { Festival } from './types'

export function scoreStars(score: number): number {
  return Math.max(1, Math.min(5, Math.round(score / 20)))
}

export function scoreColor(score: number): string {
  if (score >= 85) return '#22d3ee' // neon cyan
  if (score >= 70) return '#3b82f6' // blue
  if (score >= 55) return '#8b5cf6' // violet
  if (score >= 40) return '#f59e0b' // amber
  return '#6b7280' // gray
}

export type FestStatus = 'ongoing' | 'upcoming' | 'ended' | 'unknown'

export function festStatus(f: Festival, today = new Date()): FestStatus {
  const s = f.start_date ? new Date(f.start_date) : null
  const e = f.end_date ? new Date(f.end_date) : s
  if (!s && !e) return 'unknown'
  const start = s || e!
  const end = e || s!
  const t = new Date(today.toISOString().slice(0, 10))
  if (start <= t && t <= end) return 'ongoing'
  if (t < start) return 'upcoming'
  return 'ended'
}

export const statusMeta: Record<FestStatus, { label: string; color: string }> = {
  ongoing: { label: '진행중', color: '#22c55e' },
  upcoming: { label: '예정', color: '#3b82f6' },
  ended: { label: '종료', color: '#6b7280' },
  unknown: { label: '미정', color: '#9ca3af' },
}

// 데이터 출처 라벨 + 기본 링크 (출처표시 의무)
const SOURCE_META: Record<string, { label: string; url: string }> = {
  seed: { label: '문화체육관광부 · 2026 지역축제 개최계획', url: 'https://www.data.go.kr' },
  mocst2026: { label: '문화체육관광부 · 2026 지역축제 개최계획', url: 'https://www.data.go.kr' },
  national: { label: '전국문화축제표준데이터 · 공공데이터포털', url: 'https://www.data.go.kr' },
  tourapi: { label: '한국관광공사 TourAPI · 공공데이터포털', url: 'https://www.data.go.kr' },
  busan: { label: '부산광역시 축제정보 · 공공데이터포털', url: 'https://www.data.go.kr' },
  seoul: { label: '서울 열린데이터광장 · 문화행사', url: 'https://data.seoul.go.kr' },
  kopis: { label: 'KOPIS 공연예술통합전산망', url: 'https://www.kopis.or.kr' },
  ifac: { label: 'ifac 지역축제', url: 'https://ifac.or.kr' },
  daejeon: { label: '대전광역시 · 공공데이터포털', url: 'https://www.data.go.kr' },
  ulsan: { label: '울산광역시 · 공공데이터포털', url: 'https://www.data.go.kr' },
  sejong: { label: '세종특별자치시 · 공공데이터포털', url: 'https://www.data.go.kr' },
  boseong_event: { label: '전남 보성군 · 공공데이터포털', url: 'https://www.data.go.kr' },
  boseong_fest: { label: '전남 보성군 · 공공데이터포털', url: 'https://www.data.go.kr' },
  jeonnam: { label: '전남 남도여행길잡이 · 공공데이터포털', url: 'https://www.data.go.kr' },
  gwangyang: { label: '전남 광양시 · 공공데이터포털', url: 'https://www.data.go.kr' },
  goesan: { label: '충북 괴산군 · 공공데이터포털', url: 'https://www.data.go.kr' },
  seocheon: { label: '충남 서천군 · 공공데이터포털', url: 'https://www.data.go.kr' },
  yeongcheon: { label: '경북 영천시 · 공공데이터포털', url: 'https://www.data.go.kr' },
  gyeongju: { label: '경북 경주시 · 공공데이터포털', url: 'https://www.data.go.kr' },
  chuncheon: { label: '강원 춘천시 · 공공데이터포털', url: 'https://www.data.go.kr' },
}

export function sourceMeta(source?: string | null): { label: string; url: string } {
  return (
    (source && SOURCE_META[source]) || {
      label: '공공데이터포털',
      url: 'https://www.data.go.kr',
    }
  )
}

export function formatPeriod(f: Festival): string {
  if (f.start_date && f.end_date) {
    if (f.start_date === f.end_date) return f.start_date
    return `${f.start_date} ~ ${f.end_date}`
  }
  if (f.start_date) return f.start_date
  return f.period_text || '기간 미정'
}
