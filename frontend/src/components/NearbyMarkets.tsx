import { useEffect, useState } from 'react'
import { FestivalAPI } from '../api/client'
import type { MarketNear } from '../types'

interface Props {
  lat?: number | null
  lng?: number | null
}

export default function NearbyMarkets({ lat, lng }: Props) {
  const [data, setData] = useState<MarketNear | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (lat == null || lng == null) return
    let alive = true
    setLoading(true)
    FestivalAPI.marketsNear(lat, lng, 3)
      .then((d) => alive && setData(d))
      .catch(() => alive && setData(null))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
  }, [lat, lng])

  if (lat == null || lng == null) return null

  return (
    <div className="bg-card border border-border rounded-xl p-3">
      <div className="text-sm font-semibold text-white/90 mb-2">
        🏪 주변 전통시장 · 상권 (반경 3km)
      </div>

      {loading && <div className="text-xs text-white/40 py-1">불러오는 중...</div>}

      {!loading && data && (
        <>
          <div className="flex gap-2 mb-2">
            <div className="flex-1 bg-bg border border-border rounded-lg px-3 py-2">
              <div className="text-[11px] text-white/45">전통시장</div>
              <div className="text-lg font-bold text-neon">{data.market_count}곳</div>
            </div>
            <div className="flex-1 bg-bg border border-border rounded-lg px-3 py-2">
              <div className="text-[11px] text-white/45">점포 수 합계</div>
              <div className="text-lg font-bold text-accent">
                {data.total_stores.toLocaleString()}
              </div>
            </div>
          </div>

          {data.markets.length > 0 ? (
            <div className="space-y-1">
              {data.markets.slice(0, 6).map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between text-[12px] px-1 py-0.5"
                >
                  <span className="text-white/75 truncate">{m.name}</span>
                  <span className="text-white/40 shrink-0 ml-2">
                    {m.stores ? `점포 ${m.stores}` : ''} · {m.distance_km}km
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-white/35 leading-relaxed">
              반경 내 전통시장 데이터가 없습니다. (데모 모드이거나 미수집 지역) 백엔드에
              공공데이터 키를 연결하면 전국전통시장표준데이터가 표시됩니다.
            </div>
          )}
        </>
      )}
    </div>
  )
}
