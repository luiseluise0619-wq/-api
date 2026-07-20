import type { Festival } from '../types'
import { formatPeriod, scoreStars } from '../utils'

interface Props {
  festival: Festival
}

/**
 * 저장된 축제 정보 기반 분석 (Gemini 미사용 · 즉시 표시).
 * 실시간 AI 답변은 하단 '질문하기'에서만 Gemini를 호출한다.
 */
export default function StoredInsights({ festival: f }: Props) {
  const region = `${f.region || ''} ${f.sigungu || ''}`.trim() || '해당 지역'
  const cat = f.category || '지역'
  const s = f.ai_score
  const stars = scoreStars(s)

  const cards: { icon: string; title: string; body: string }[] = [
    {
      icon: '📌',
      title: '축제 개요',
      body: `'${f.title}'은(는) ${region}에서 열리는 ${cat} 성격의 축제입니다. 개최 시기는 ${formatPeriod(
        f,
      )}이며, 주최/주관은 ${f.organizer || '지자체'}입니다.`,
    },
    {
      icon: '📊',
      title: '상권 영향력 지표',
      body: `종합 점수 ${s}점 (${'★'.repeat(stars)}). 규모·분류·정보 충실도를 반영한 지표로, 점수가 높을수록 주변 유동인구·소비 유입 잠재력이 큽니다.`,
    },
    {
      icon: '🏪',
      title: '주변 상권 참고',
      body: '행사장 반경에서는 요식·카페·간편식·포토/굿즈 업종의 매출 증가가 일반적으로 기대됩니다. 아래 "주변 전통시장" 카드에서 실제 상권 규모를 확인하세요.',
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
        <span className="text-neon font-semibold">✦ 축제 분석</span>
        <span className="text-white/30">저장 정보 기반 · 즉시</span>
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
