import { scoreColor, scoreStars } from '../utils'

interface Props {
  score: number
  label?: string
  size?: 'sm' | 'md'
}

export default function ScoreBadge({ score, label = '상권 영향력', size = 'md' }: Props) {
  const stars = scoreStars(score)
  const color = scoreColor(score)
  const starSize = size === 'sm' ? 'text-xs' : 'text-sm'
  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-xs text-white/50">{label}</span>}
      <span className={`${starSize} tracking-tight`} style={{ color }}>
        {'★'.repeat(stars)}
        <span className="text-white/15">{'★'.repeat(5 - stars)}</span>
      </span>
      <span
        className="text-xs font-semibold px-1.5 py-0.5 rounded-md"
        style={{ color, background: `${color}1a` }}
      >
        {score}점
      </span>
    </div>
  )
}
