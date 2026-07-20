import { useState } from 'react'
import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  Tooltip,
  useMapEvents,
} from 'react-leaflet'
import type { Festival, RegionCount } from '../types'
import { formatPeriod, scoreColor } from '../utils'
import ScoreBadge from './ScoreBadge'

interface Props {
  festivals: Festival[]
  regionCounts: RegionCount[]
  heatmap: boolean
  onSelect: (f: Festival) => void
  selectedId?: number
}

// 줌 레벨에 따른 마커 크기 배율 — 넓게 볼수록 작게, 확대할수록 크게
function zoomFactor(zoom: number): number {
  return Math.max(0.5, Math.min(1.7, (zoom - 5) / 4.5))
}

// 카운트에 비례한 히트맵 원 반경(px)
function heatRadius(count: number, max: number, zf: number): number {
  const r = (16 + (count / Math.max(1, max)) * 40) * Math.min(1.1, zf + 0.35)
  return Math.round(r)
}

function ZoomWatcher({ onZoom }: { onZoom: (z: number) => void }) {
  useMapEvents({ zoomend: (e) => onZoom(e.target.getZoom()) })
  return null
}

export default function MapView({
  festivals,
  regionCounts,
  heatmap,
  onSelect,
  selectedId,
}: Props) {
  const maxCount = Math.max(1, ...regionCounts.map((r) => r.count))
  const [zoom, setZoom] = useState(7)
  const zf = zoomFactor(zoom)

  return (
    <MapContainer
      center={[36.4, 127.9]}
      zoom={7}
      minZoom={6}
      maxZoom={16}
      className="w-full h-full"
      preferCanvas
      worldCopyJump
    >
      <TileLayer
        attribution='&copy; OpenStreetMap &copy; CARTO'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      <ZoomWatcher onZoom={setZoom} />

      {heatmap
        ? regionCounts
            .filter((r) => r.lat && r.lng)
            .map((r) => (
              <CircleMarker
                key={r.region}
                center={[r.lat!, r.lng!]}
                radius={heatRadius(r.count, maxCount, zf)}
                pathOptions={{
                  color: '#22d3ee',
                  fillColor: '#22d3ee',
                  fillOpacity: 0.22,
                  weight: 1,
                }}
              >
                <Tooltip direction="center" permanent className="!bg-transparent !border-0 !shadow-none">
                  <span className="text-white text-xs font-semibold drop-shadow">
                    {r.region.replace(/특별자치도|특별자치시|특별시|광역시|도$/g, '')} {r.count}
                  </span>
                </Tooltip>
              </CircleMarker>
            ))
        : festivals
            .filter((f) => f.lat && f.lng)
            .map((f) => {
              const selected = f.id === selectedId
              const color = scoreColor(f.ai_score)
              return (
                <CircleMarker
                  key={f.id}
                  center={[f.lat!, f.lng!]}
                  radius={
                    selected
                      ? Math.max(9, 11 * zf)
                      : Math.max(2, (3 + f.ai_score / 30) * zf)
                  }
                  pathOptions={{
                    color: selected ? '#fff' : color,
                    fillColor: color,
                    fillOpacity: 0.75,
                    weight: selected ? 2 : 1,
                  }}
                  eventHandlers={{ click: () => onSelect(f) }}
                >
                  <Popup>
                    <div className="min-w-[180px]">
                      <div className="font-semibold text-sm mb-1">{f.title}</div>
                      <div className="text-[11px] text-white/60 mb-1.5">
                        {f.region} {f.sigungu || ''} · {formatPeriod(f)}
                      </div>
                      <ScoreBadge score={f.ai_score} size="sm" />
                      <button
                        onClick={() => onSelect(f)}
                        className="mt-2 w-full text-xs bg-accent/80 hover:bg-accent text-white rounded-md py-1.5"
                      >
                        상세 · AI 분석 보기
                      </button>
                    </div>
                  </Popup>
                </CircleMarker>
              )
            })}
    </MapContainer>
  )
}
