import { useEffect, useMemo, useState } from 'react'
import { FestivalAPI } from '../api/client'
import type { Festival, Filters } from '../types'
import { festStatus, formatPeriod, statusMeta } from '../utils'

interface Props {
  filters: Filters
  onSelect: (f: Festival) => void
}

const MONTHS = Array.from({ length: 12 }, (_, i) => i + 1)

export default function MonthlyList({ filters, onSelect }: Props) {
  const [items, setItems] = useState<Festival[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState<number | null>(new Date().getMonth() + 1)

  const ongoing = filters.status === 'ongoing'

  useEffect(() => {
    let alive = true
    setLoading(true)
    // 월 범위(date_from/to)는 무시하고 전체를 월별로. 상태/지역/분류/검색은 반영.
    const { date_from, date_to, ...rest } = filters
    FestivalAPI.list(rest, 1, 3000)
      .then((r) => alive && setItems(r.items))
      .catch(() => alive && setItems([]))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [filters.region, filters.category, filters.q, filters.status])

  const byMonth = useMemo(() => {
    const map: Record<number, Festival[]> = {}
    const undated: Festival[] = []
    for (const f of items) {
      if (!f.start_date) {
        undated.push(f)
        continue
      }
      const m = Number(f.start_date.slice(5, 7))
      ;(map[m] ||= []).push(f)
    }
    for (const m of Object.keys(map)) {
      map[+m].sort((a, b) => (a.start_date || '').localeCompare(b.start_date || ''))
    }
    return { map, undated }
  }, [items])

  return (
    <div>
      <div className="text-xs font-semibold text-white/60 mb-2 flex items-center justify-between">
        <span>
          {ongoing ? '🟢 진행중인 축제 (월별)' : '🗓️ 월별 전체 축제'}
        </span>
        <span className="text-white/30">{items.length.toLocaleString()}건</span>
      </div>

      {loading && <div className="text-xs text-white/40 py-2">불러오는 중...</div>}

      <div className="space-y-1.5">
        {MONTHS.map((m) => {
          const list = byMonth.map[m] || []
          if (ongoing && list.length === 0) return null // 진행중 필터 땐 빈 달 숨김
          const isOpen = open === m
          return (
            <div key={m} className="border border-border rounded-lg overflow-hidden bg-card">
              <button
                onClick={() => setOpen(isOpen ? null : m)}
                className="w-full flex items-center justify-between px-3 py-2 hover:bg-cardhover transition"
              >
                <span className="text-sm font-medium text-white/85">{m}월</span>
                <span className="flex items-center gap-2">
                  <span className="text-[11px] text-white/40">{list.length}건</span>
                  <span className="text-white/30 text-xs">{isOpen ? '▾' : '▸'}</span>
                </span>
              </button>

              {isOpen && list.length > 0 && (
                <div className="border-t border-border divide-y divide-border/60">
                  {list.map((f) => {
                    const st = statusMeta[festStatus(f)]
                    return (
                      <button
                        key={f.id}
                        onClick={() => onSelect(f)}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-cardhover transition"
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full shrink-0"
                          style={{ background: st.color }}
                        />
                        <span className="flex-1 min-w-0">
                          <span className="block text-[13px] text-white/85 truncate">
                            {f.title}
                          </span>
                          <span className="block text-[11px] text-white/40 truncate">
                            {f.region?.replace(/특별자치도|특별자치시|특별시|광역시|도$/g, '')} ·{' '}
                            {formatPeriod(f)}
                          </span>
                        </span>
                        <span
                          className="text-[10px] shrink-0"
                          style={{ color: st.color }}
                        >
                          {st.label}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}
              {isOpen && list.length === 0 && (
                <div className="px-3 py-2 text-[11px] text-white/30 border-t border-border">
                  해당 월 축제 없음
                </div>
              )}
            </div>
          )
        })}

        {byMonth.undated.length > 0 && !ongoing && (
          <div className="text-[11px] text-white/30 px-1 pt-1">
            + 날짜 미정 {byMonth.undated.length}건
          </div>
        )}
      </div>
    </div>
  )
}
