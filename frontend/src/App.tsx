import { useEffect, useMemo, useState } from 'react'
import { FestivalAPI } from './api/client'
import { DemoAPI } from './api/demo'
import Filters from './components/Filters'
import FestivalDetail from './components/FestivalDetail'
import MapView from './components/MapView'
import MonthlyList from './components/MonthlyList'
import SocialPanel from './components/SocialPanel'
import StatCards from './components/StatCards'
import AskAI from './components/AskAI'
import { downloadCsv, festivalsToCsv } from './utils'
import type {
  Festival,
  Filters as FiltersType,
  Stats,
} from './types'

export default function App() {
  const [stats, setStats] = useState<Stats>()
  const [regions, setRegions] = useState<string[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [festivals, setFestivals] = useState<Festival[]>([])

  const [filters, setFilters] = useState<FiltersType>({})
  const [heatmap, setHeatmap] = useState(false)
  const [selected, setSelected] = useState<Festival | null>(null)
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)

  async function handleExport() {
    setExporting(true)
    try {
      const { items } = await FestivalAPI.list(filters, 1, 5000)
      downloadCsv(`festivals_${new Date().toISOString().slice(0, 10)}.csv`, festivalsToCsv(items))
    } finally {
      setExporting(false)
    }
  }

  // 초기 로드: 번들 시드로 즉시 표시 → 백엔드 응답 오면 최신화
  useEffect(() => {
    const seed = () => {
      DemoAPI.stats().then(setStats).catch(() => {})
      DemoAPI.regions().then(setRegions).catch(() => {})
      DemoAPI.categories().then(setCategories).catch(() => {})
    }
    seed()
    FestivalAPI.stats().then(setStats).catch(() => {})
    FestivalAPI.regions().then(setRegions).catch(() => {})
    FestivalAPI.categories().then(setCategories).catch(() => {})
  }, [])

  // 필터 변경 시: 시드로 즉시 핀 표시 → 라이브 오면 교체 (콜드스타트 대기 없이 바로 보임)
  useEffect(() => {
    let liveDone = false
    setLoading(true)
    FestivalAPI.mapFestivals(filters)
      .then((fs) => {
        liveDone = true
        setFestivals(fs)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
    // 즉시 시드(정적 파일) — 라이브가 먼저 오지 않았다면 표시
    DemoAPI.mapFestivals(filters)
      .then((fs) => {
        if (!liveDone) setFestivals(fs)
      })
      .catch(() => {})
  }, [filters])

  const regionCounts = useMemo(() => stats?.by_region ?? [], [stats])

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-bg text-white">
      {/* 좌측 컨트롤 사이드바 */}
      <aside className="w-[340px] shrink-0 border-r border-border flex flex-col">
        <div className="px-4 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent to-neon grid place-items-center text-black font-black text-sm">
              F
            </div>
            <div>
              <div className="font-bold leading-none">Festival AI Map</div>
              <div className="text-[10px] text-white/40 mt-0.5">
                전국 축제·상권 AI 분석 지도
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          <StatCards stats={stats} />
          <Filters
            regions={regions}
            categories={categories}
            value={filters}
            onChange={setFilters}
            heatmap={heatmap}
            onToggleHeatmap={setHeatmap}
          />
          <button
            onClick={handleExport}
            disabled={exporting}
            className="w-full text-sm bg-card hover:bg-cardhover border border-border rounded-lg py-2 text-white/80 disabled:opacity-50 transition"
          >
            {exporting ? '내보내는 중...' : '⬇ 엑셀(CSV) 목록 다운로드'}
          </button>
          <MonthlyList filters={filters} onSelect={setSelected} />
          <AskAI placeholder="예) 소상공인에게 유리한 축제는?" />
        </div>
      </aside>

      {/* 중앙 지도 */}
      <main className="flex-1 relative">
        <MapView
          festivals={festivals}
          regionCounts={regionCounts}
          heatmap={heatmap}
          onSelect={setSelected}
          selected={selected}
        />
        {/* 지도 상단 상태 배지 */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[500] flex items-center gap-2">
          <div className="bg-card/90 backdrop-blur border border-border rounded-full px-3.5 py-1.5 text-xs text-white/70">
            {heatmap ? '지역별 밀집도 히트맵' : `지도 표시 ${festivals.length.toLocaleString()}건`}
            {loading && <span className="ml-2 text-neon">●</span>}
          </div>
        </div>
      </main>

      {/* 우측 SNS 소셜 패널 */}
      <aside className="w-[320px] shrink-0 hidden lg:block">
        <SocialPanel festivalTitle={selected?.title} />
      </aside>

      {/* 상세 드로어 */}
      <FestivalDetail festival={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
