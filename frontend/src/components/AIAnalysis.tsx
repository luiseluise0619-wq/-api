import { useEffect, useState } from 'react'
import { FestivalAPI } from '../api/client'
import type { AIAnalysis as AIAnalysisType } from '../types'

interface Props {
  festivalId: number
}

const SECTIONS: { key: string; label: string; icon: string }[] = [
  { key: 'summary', label: '축제 개요', icon: '📌' },
  { key: 'visitors', label: '예상 방문객 분석', icon: '👥' },
  { key: 'commerce_impact', label: '주변 소상공인 매출 영향', icon: '🏪' },
  { key: 'local_economy', label: '지역경제 활성화 가능성', icon: '📈' },
  { key: 'promotion', label: '추천 홍보 전략', icon: '📣' },
  { key: 'sns_ideas', label: 'SNS 콘텐츠 아이디어', icon: '🎬' },
  { key: 'improvements', label: '개선점', icon: '🛠️' },
]

export default function AIAnalysis({ festivalId }: Props) {
  const [data, setData] = useState<AIAnalysisType | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    setData(null)
    setError(null)
    setLoading(true)
    FestivalAPI.analyze(festivalId)
      .then((d) => alive && setData(d))
      .catch(() => alive && setError('AI 분석을 불러오지 못했습니다.'))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [festivalId])

  if (loading)
    return (
      <div className="flex items-center gap-2 text-sm text-white/50 py-6">
        <span className="w-3.5 h-3.5 border-2 border-neon/40 border-t-neon rounded-full animate-spin" />
        Gemini AI 분석 생성 중...
      </div>
    )
  if (error) return <div className="text-sm text-red-400/80 py-4">{error}</div>
  if (!data) return null

  return (
    <div className="space-y-2.5 animate-fade">
      <div className="flex items-center gap-2 text-xs">
        <span className="text-neon font-semibold">✦ AI 심층 분석</span>
        <span className="text-white/30">
          {data.generated_by === 'gemini' ? 'Gemini 생성' : '규칙 기반(키 미설정)'}
        </span>
      </div>
      {SECTIONS.map((s) => {
        const text = data.analysis[s.key]
        if (!text) return null
        return (
          <div key={s.key} className="bg-card border border-border rounded-xl p-3">
            <div className="text-sm font-semibold text-white/90 mb-1">
              {s.icon} {s.label}
            </div>
            <p className="text-[13px] leading-relaxed text-white/65 whitespace-pre-line">
              {text}
            </p>
          </div>
        )
      })}
    </div>
  )
}
