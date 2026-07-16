import type { Stats } from '../types'

interface Props {
  stats?: Stats
}

const items = [
  { key: 'total', label: '전체 축제', color: '#3b82f6' },
  { key: 'ongoing', label: '진행중', color: '#22c55e' },
  { key: 'upcoming', label: '예정', color: '#22d3ee' },
  { key: 'regions', label: '지역', color: '#8b5cf6' },
] as const

export default function StatCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map((it) => (
        <div
          key={it.key}
          className="bg-card border border-border rounded-xl px-3 py-2.5"
        >
          <div className="text-[11px] text-white/45">{it.label}</div>
          <div className="text-xl font-bold mt-0.5" style={{ color: it.color }}>
            {stats ? stats[it.key].toLocaleString() : '—'}
          </div>
        </div>
      ))}
    </div>
  )
}
