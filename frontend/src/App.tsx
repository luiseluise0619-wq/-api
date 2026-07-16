import { useEffect, useMemo, useState } from 'react'
import { FestivalAPI } from './api/client'
import Filters from './components/Filters'
import FestivalDetail from './components/FestivalDetail'
import MapView from './components/MapView'
import SocialPanel from './components/SocialPanel'
import StatCards from './components/StatCards'
import TopFestivals from './components/TopFestivals'
import AskAI from './components/AskAI'
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
  const [top, setTop] = useState<Festival[]>([])
  const [thisMonth, setThisMonth] = useState<Festival[]>([])

  const [filters, setFilters] = useState<FiltersType>({})
  const [heatmap, setHeatmap] = useState(false)
  const [selected, setSelected] = useState<Festival | null>(null)
  const [loading, setLoading] = useState(false)

  // 초기 로드
  useEffect(() => {
    FestivalAPI.stats().then(setStats).catch(() => {})
    FestivalAPI.regions().then(setRegions).catch(() => {})
    FestivalAPI.categories().then(setCategories).catch(() => {})
    FestivalAPI.top(10).then(setTop).catch(() => {})
    FestivalAPI.thisMonth(12).then(setThisMonth).catch(() => {})
  }, [])

  // 필터 변경 시 지도 데이터 재조회
  useEffect(() => {
    setLoading(true)
    FestivalAPI.mapFestivals(filters)
      .then(setFestivals)
      .catch(() => setFestivals([]))
      .finally(() => setLoading(false))
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
          <TopFestivals
            title="🔥 인기 축제 TOP 10"
            festivals={top}
            onSelect={setSelected}
            numbered
          />
          <TopFestivals
            title="📅 이번 달 추천 축제"
            festivals={thisMonth}
            onSelect={setSelected}
          />
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
          selectedId={selected?.id}
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
