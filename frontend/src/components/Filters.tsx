import { useEffect, useState } from 'react'
import type { Filters as FiltersType } from '../types'

interface Props {
  regions: string[]
  categories: string[]
  value: FiltersType
  onChange: (f: FiltersType) => void
  heatmap: boolean
  onToggleHeatmap: (v: boolean) => void
}

const STATUS = [
  { v: '', label: '전체' },
  { v: 'ongoing', label: '진행중' },
  { v: 'upcoming', label: '예정' },
  { v: 'ended', label: '종료' },
]

// 월별 필터 기준 연도 (시드 데이터 기준)
const MONTH_YEAR = 2026
function monthRange(m: number): { date_from: string; date_to: string } {
  const mm = String(m).padStart(2, '0')
  const last = new Date(MONTH_YEAR, m, 0).getDate()
  return { date_from: `${MONTH_YEAR}-${mm}-01`, date_to: `${MONTH_YEAR}-${mm}-${last}` }
}
function currentMonthValue(v: FiltersType): string {
  if (!v.date_from) return ''
  const m = v.date_from.slice(5, 7)
  return String(Number(m))
}

export default function Filters({
  regions,
  categories,
  value,
  onChange,
  heatmap,
  onToggleHeatmap,
}: Props) {
  const [q, setQ] = useState(value.q || '')

  useEffect(() => {
    const t = setTimeout(() => onChange({ ...value, q: q || undefined }), 350)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q])

  const selectCls =
    'w-full bg-card border border-border rounded-lg px-2.5 py-2 text-sm text-white/90 outline-none focus:border-accent'

  return (
    <div className="space-y-2.5">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="축제명·내용 검색"
        className={selectCls}
      />

      <div className="grid grid-cols-2 gap-2">
        <select
          className={selectCls}
          value={value.region || ''}
          onChange={(e) => onChange({ ...value, region: e.target.value || undefined })}
        >
          <option value="">전 지역</option>
          {regions.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        <select
          className={selectCls}
          value={value.category || ''}
          onChange={(e) => onChange({ ...value, category: e.target.value || undefined })}
        >
          <option value="">전 분류</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="flex gap-1.5">
        {STATUS.map((s) => (
          <button
            key={s.v}
            onClick={() => onChange({ ...value, status: s.v || undefined })}
            className={`flex-1 text-xs py-1.5 rounded-lg border transition ${
              (value.status || '') === s.v
                ? 'bg-accent/20 border-accent text-white'
                : 'bg-card border-border text-white/50 hover:text-white/80'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <select
        className={selectCls}
        value={currentMonthValue(value)}
        onChange={(e) => {
          const m = e.target.value
          if (!m) onChange({ ...value, date_from: undefined, date_to: undefined })
          else onChange({ ...value, ...monthRange(Number(m)) })
        }}
      >
        <option value="">월별 보기 · 전체 기간</option>
        {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
          <option key={m} value={m}>
            {MONTH_YEAR}년 {m}월 축제
          </option>
        ))}
      </select>

      <div className="grid grid-cols-2 gap-2">
        <input
          type="date"
          className={selectCls}
          value={value.date_from || ''}
          onChange={(e) => onChange({ ...value, date_from: e.target.value || undefined })}
        />
        <input
          type="date"
          className={selectCls}
          value={value.date_to || ''}
          onChange={(e) => onChange({ ...value, date_to: e.target.value || undefined })}
        />
      </div>

      <label className="flex items-center justify-between bg-card border border-border rounded-lg px-3 py-2 cursor-pointer">
        <span className="text-sm text-white/70">지역별 밀집도 히트맵</span>
        <input
          type="checkbox"
          checked={heatmap}
          onChange={(e) => onToggleHeatmap(e.target.checked)}
          className="accent-neon"
        />
      </label>
    </div>
  )
}
