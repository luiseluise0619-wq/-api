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

export function formatPeriod(f: Festival): string {
  if (f.start_date && f.end_date) {
    if (f.start_date === f.end_date) return f.start_date
    return `${f.start_date} ~ ${f.end_date}`
  }
  if (f.start_date) return f.start_date
  return f.period_text || '기간 미정'
}
