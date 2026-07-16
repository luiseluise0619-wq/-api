import { useEffect, useState } from 'react'
import { FestivalAPI } from '../api/client'
import type { SocialResult } from '../types'

interface Props {
  festivalTitle?: string
}

const PLATFORM_META: Record<string, { icon: string; color: string }> = {
  x: { icon: '𝕏', color: '#e7e9ea' },
  instagram: { icon: '📷', color: '#e1306c' },
  facebook: { icon: 'f', color: '#1877f2' },
  youtube: { icon: '▶', color: '#ff0000' },
  naver: { icon: 'N', color: '#03c75a' },
}

const KEYWORDS = ['축제', '행사', '지역축제', '소상공인', '전통시장', '먹거리']

export default function SocialPanel({ festivalTitle }: Props) {
  const [keyword, setKeyword] = useState('축제')
  const [data, setData] = useState<SocialResult | null>(null)
  const [loading, setLoading] = useState(false)

  const query = festivalTitle || ''

  useEffect(() => {
    let alive = true
    setLoading(true)
    FestivalAPI.social(query, keyword)
      .then((d) => alive && setData(d))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [query, keyword])

  return (
    <div className="h-full flex flex-col bg-bg border-l border-border">
      <div className="px-4 pt-4 pb-3 border-b border-border">
        <div className="text-sm font-semibold flex items-center gap-2">
          <span className="text-neon">◎</span> SNS 소셜 피드
        </div>
        <div className="text-[11px] text-white/40 mt-1">
          {festivalTitle ? (
            <>
              <span className="text-white/70">{festivalTitle}</span> + 키워드
            </>
          ) : (
            '축제·행사·소상공인 키워드'
          )}
        </div>

        <div className="flex flex-wrap gap-1.5 mt-2.5">
          {KEYWORDS.map((k) => (
            <button
              key={k}
              onClick={() => setKeyword(k)}
              className={`text-[11px] px-2.5 py-1 rounded-full border transition ${
                keyword === k
                  ? 'bg-neon/20 border-neon text-white'
                  : 'bg-card border-border text-white/50 hover:text-white/80'
              }`}
            >
              #{k}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* 플랫폼 검색 딥링크 */}
        <div>
          <div className="text-[11px] text-white/45 mb-1.5 px-0.5">플랫폼에서 바로 검색</div>
          <div className="space-y-1.5">
            {data?.links.map((l) => {
              const m = PLATFORM_META[l.platform] || { icon: '#', color: '#888' }
              return (
                <a
                  key={l.platform}
                  href={l.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-2.5 bg-card hover:bg-cardhover border border-border rounded-lg px-3 py-2 transition group"
                >
                  <span
                    className="w-6 h-6 rounded-md grid place-items-center text-sm font-bold shrink-0"
                    style={{ color: m.color, background: `${m.color}1a` }}
                  >
                    {m.icon}
                  </span>
                  <span className="text-[12px] text-white/70 group-hover:text-white flex-1 truncate">
                    {l.label}
                  </span>
                  <span className="text-white/30 text-xs">↗</span>
                </a>
              )
            })}
          </div>
        </div>

        {/* YouTube 실검색 결과 */}
        <div>
          <div className="text-[11px] text-white/45 mb-1.5 px-0.5 flex items-center justify-between">
            <span>YouTube 최신 영상</span>
            {data && !data.youtube_enabled && (
              <span className="text-white/25">키 미설정</span>
            )}
          </div>

          {loading && (
            <div className="text-xs text-white/40 py-3 text-center">불러오는 중...</div>
          )}

          {!loading && data && data.youtube.length === 0 && (
            <div className="text-[11px] text-white/35 bg-card border border-border rounded-lg p-3 leading-relaxed">
              {data.youtube_enabled
                ? '검색 결과가 없습니다.'
                : '백엔드 .env 에 YOUTUBE_API_KEY 를 설정하면 실제 영상이 표시됩니다. 지금은 위 유튜브 검색 링크를 이용하세요.'}
            </div>
          )}

          <div className="space-y-2">
            {data?.youtube.map((v) => (
              <a
                key={v.url}
                href={v.url}
                target="_blank"
                rel="noreferrer"
                className="block bg-card hover:bg-cardhover border border-border rounded-lg overflow-hidden transition"
              >
                {v.thumbnail && (
                  <img src={v.thumbnail} alt="" className="w-full aspect-video object-cover" />
                )}
                <div className="p-2.5">
                  <div className="text-[12px] text-white/85 line-clamp-2 leading-snug">
                    {v.title}
                  </div>
                  <div className="text-[10px] text-white/40 mt-1">{v.channel}</div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
