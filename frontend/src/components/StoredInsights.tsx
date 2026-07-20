import type { Festival } from '../types'
import { formatPeriod } from '../utils'

interface Props {
  festival: Festival
}

/**
 * 저장된 축제 정보 요약 (Gemini 미사용 · 즉시 표시).
 * 실시간 AI 답변은 하단 '질문하기'에서만 Gemini를 호출한다.
 */
export default function StoredInsights({ festival: f }: Props) {
  const region = `${f.region || ''} ${f.sigungu || ''}`.trim() || '해당 지역'
  const cat = f.category || '지역'

  const cards: { icon: string; title: string; body: string }[] = [
    {
      icon: '📌',
      title: '축제 개요',
      body: `'${f.title}'은(는) ${region}에서 열리는 ${cat} 성격의 축제입니다. 개최 시기는 ${formatPeriod(
        f,
      )}이며, 주최/주관은 ${f.organizer || '지자체'}입니다.`,
    },
    {
      icon: '🗓️',
      title: '방문 팁',
      body: '주말·개막일에 방문객이 집중되는 경향이 있습니다. 대중교통/주차 정보를 미리 확인하고, 저녁 시간대 프로그램도 함께 확인하세요.',
    },
  ]

  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-2 text-xs">
        <span className="text-neon font-semibold">✦ 축제 정보</span>
        <span className="text-white/30">저장 정보 기반</span>
      </div>
      {cards.map((c) => (
        <div key={c.title} className="bg-card border border-border rounded-xl p-3">
          <div className="text-sm font-semibold text-white/90 mb-1">
            {c.icon} {c.title}
          </div>
          <p className="text-[13px] leading-relaxed text-white/65">{c.body}</p>
        </div>
      ))}
    </div>
  )
}
