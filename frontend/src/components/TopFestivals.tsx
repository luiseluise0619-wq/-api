import type { Festival } from '../types'
import { formatPeriod, scoreColor } from '../utils'

interface Props {
  title: string
  festivals: Festival[]
  onSelect: (f: Festival) => void
  numbered?: boolean
}

export default function TopFestivals({ title, festivals, onSelect, numbered }: Props) {
  if (!festivals.length) return null
  return (
    <div>
      <div className="text-xs font-semibold text-white/60 mb-2 flex items-center gap-1.5">
        {title}
      </div>
      <div className="space-y-1.5">
        {festivals.map((f, i) => (
          <button
            key={f.id}
            onClick={() => onSelect(f)}
            className="w-full flex items-center gap-2.5 bg-card hover:bg-cardhover border border-border rounded-lg px-2.5 py-2 text-left transition group"
          >
            {numbered && (
              <span
                className="text-sm font-bold w-5 text-center shrink-0"
                style={{ color: scoreColor(f.ai_score) }}
              >
                {i + 1}
              </span>
            )}
            <span
              className="w-1.5 h-1.5 rounded-full shrink-0"
              style={{ background: scoreColor(f.ai_score) }}
            />
            <span className="flex-1 min-w-0">
              <span className="block text-sm text-white/90 truncate group-hover:text-white">
                {f.title}
              </span>
              <span className="block text-[11px] text-white/40 truncate">
                {f.region?.replace(/특별자치도|특별자치시|특별시|광역시|도$/g, '')} ·{' '}
                {formatPeriod(f)}
              </span>
            </span>
            <span
              className="text-xs font-semibold shrink-0"
              style={{ color: scoreColor(f.ai_score) }}
            >
              {f.ai_score}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
