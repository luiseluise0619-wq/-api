import { useState } from 'react'
import { FestivalAPI } from '../api/client'

interface Props {
  festivalId?: number
  placeholder?: string
}

const SUGGESTIONS = [
  '이 축제 주변에서 장사하면 어떤 업종이 유리해?',
  '방문객을 늘리려면 어떤 홍보가 효과적일까?',
  '가족 단위 방문객에게 추천할 프로그램은?',
]

export default function AskAI({ festivalId, placeholder }: Props) {
  const [q, setQ] = useState('')
  const [answer, setAnswer] = useState<string | null>(null)
  const [by, setBy] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(question: string) {
    const text = question.trim()
    if (!text || loading) return
    setLoading(true)
    setAnswer(null)
    try {
      const res = await FestivalAPI.ask(text, festivalId)
      setAnswer(res.answer)
      setBy(res.generated_by)
    } catch {
      setAnswer('답변을 불러오지 못했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl p-3 space-y-2.5">
      <div className="text-sm font-semibold text-white/90">💬 AI에게 질문하기</div>

      <div className="flex flex-wrap gap-1.5">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => {
              setQ(s)
              submit(s)
            }}
            className="text-[11px] text-white/55 hover:text-white bg-bg border border-border rounded-full px-2.5 py-1 transition"
          >
            {s}
          </button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit(q)}
          placeholder={placeholder || '자유롭게 질문하세요'}
          className="flex-1 bg-bg border border-border rounded-lg px-3 py-2 text-sm outline-none focus:border-neon"
        />
        <button
          onClick={() => submit(q)}
          disabled={loading}
          className="bg-neon/90 hover:bg-neon text-black font-semibold text-sm px-3.5 rounded-lg disabled:opacity-40"
        >
          {loading ? '...' : '질문'}
        </button>
      </div>

      {answer && (
        <div className="bg-bg border border-border rounded-lg p-3 animate-fade">
          <p className="text-[13px] leading-relaxed text-white/75 whitespace-pre-line">
            {answer}
          </p>
          <div className="text-[10px] text-white/30 mt-1.5">
            {by === 'gemini' ? 'Gemini 생성' : '규칙 기반(키 미설정)'}
          </div>
        </div>
      )}
    </div>
  )
}
