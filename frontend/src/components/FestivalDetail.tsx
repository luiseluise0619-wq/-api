import type { Festival } from '../types'
import { festStatus, formatPeriod, sourceMeta, statusMeta } from '../utils'
import AskAI from './AskAI'
import NearbyMarkets from './NearbyMarkets'

interface Props {
  festival: Festival | null
  onClose: () => void
}

export default function FestivalDetail({ festival, onClose }: Props) {
  if (!festival) return null
  const st = statusMeta[festStatus(festival)]

  return (
    <div className="fixed inset-0 z-[1000] flex justify-end">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md h-full bg-bg border-l border-border overflow-y-auto animate-fade">
        {/* 헤더 */}
        <div className="sticky top-0 z-10 bg-bg/95 backdrop-blur border-b border-border px-5 py-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span
                className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
                style={{ color: st.color, background: `${st.color}22` }}
              >
                {st.label}
              </span>
              {festival.category && (
                <span className="text-[10px] text-white/45">{festival.category}</span>
              )}
            </div>
            <h2 className="text-lg font-bold leading-tight">{festival.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white text-xl leading-none shrink-0"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-4">
          {festival.image_url && (
            <img
              src={festival.image_url}
              alt=""
              className="w-full rounded-xl border border-border object-cover max-h-52"
              onError={(e) => ((e.target as HTMLImageElement).style.display = 'none')}
            />
          )}

          {/* 메타 정보 */}
          {festival.lat == null || festival.lng == null ? (
            <div className="text-[12px] text-amber-400/80 bg-amber-400/10 border border-amber-400/20 rounded-lg px-3 py-2">
              📍 이 축제는 좌표(위치)가 제공되지 않아 지도 위치가 미정입니다.
            </div>
          ) : (
            (festival.source === 'seed' || festival.source === 'mocst2026') && (
              <div className="text-[11px] text-white/40 px-1">
                ※ 지도 위치는 시군구 중심 기준 근사값입니다 (원본 데이터에 정확 좌표 없음).
              </div>
            )
          )}

          <div className="bg-card border border-border rounded-xl divide-y divide-border text-sm">
            <Row label="지역" value={`${festival.region || ''} ${festival.sigungu || ''}`.trim()} />
            <Row label="기간" value={formatPeriod(festival)} />
            <Row label="장소" value={festival.place || festival.address} />
            <Row label="주최/주관" value={festival.organizer} />
            <Row label="연락처" value={festival.tel} />
            <Row label="이용요금" value={festival.fee} />
            {festival.homepage && (
              <LinkRow label="홈페이지" href={festival.homepage} text={festival.homepage} />
            )}
            <LinkRow
              label="출처"
              href={festival.detail_url || sourceMeta(festival.source).url}
              text={sourceMeta(festival.source).label}
            />
          </div>

          {festival.description && (
            <div className="bg-card border border-border rounded-xl p-3">
              <div className="text-xs font-semibold text-white/50 mb-1.5">상세 내용</div>
              <p className="text-[13px] leading-relaxed text-white/65 whitespace-pre-line max-h-48 overflow-y-auto">
                {festival.description}
              </p>
            </div>
          )}

          {/* 주변 전통시장 상권 (실제 소상공인시장진흥공단 데이터) */}
          <NearbyMarkets lat={festival.lat} lng={festival.lng} />

          {/* 이 축제에 대한 질문 — 여기서만 Gemini 호출 */}
          <AskAI
            festivalId={festival.id}
            placeholder="이 축제에 대해 질문하세요 (AI)"
          />
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null
  return (
    <div className="flex px-3 py-2.5">
      <span className="text-white/40 w-20 shrink-0">{label}</span>
      <span className="text-white/85 flex-1">{value}</span>
    </div>
  )
}

function LinkRow({ label, href, text }: { label: string; href: string; text: string }) {
  return (
    <div className="flex px-3 py-2.5">
      <span className="text-white/40 w-20 shrink-0">{label}</span>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="text-accent hover:underline truncate flex-1"
      >
        {text} ↗
      </a>
    </div>
  )
}
