import { useEffect, useState } from 'react'
import { getDashboard as defaultGetDashboard } from '../lib/api'
import type { DashboardData } from '../lib/types'
import { AppShell, MetricCard } from '../components/ui'
import { BusArrivalCard } from '../components/BusArrivalCard'
import { RecommendationCard } from '../components/RecommendationCard'
import { SubwayArrivalCard } from '../components/SubwayArrivalCard'

type DashboardPageProps = {
  profileId: string
  getDashboard?: (profileId: string) => Promise<DashboardData>
}

function firstArrival(items: Array<{ arrivalInMin?: number; arrival_in_min?: number }>) {
  const minutes = items.map((item) => item.arrivalInMin ?? item.arrival_in_min).find((value) => typeof value === 'number')
  return typeof minutes === 'number' ? `${minutes}분` : '정보 없음'
}

export function DashboardPage({ profileId, getDashboard = defaultGetDashboard }: DashboardPageProps) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    void getDashboard(profileId)
      .then((payload) => {
        if (cancelled) return
        setData(payload)
        setError(null)
      })
      .catch(() => {
        if (cancelled) return
        setError('대시보드를 불러오지 못했습니다.')
      })

    return () => {
      cancelled = true
    }
  }, [getDashboard, profileId])

  if (error) {
    return (
      <AppShell>
        <p className='error'>{error}</p>
      </AppShell>
    )
  }

  if (!data) {
    return (
      <AppShell>
        <p className='loading'>불러오는 중...</p>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className='stack-lg'>
        <section className='hero-card'>
          <p className='eyebrow'>오늘의 출근</p>
          <h1 className='page-title'>{data.profile.name}</h1>
          <p className='page-lead'>실시간 공공데이터 기준</p>
        </section>
        <RecommendationCard message={data.recommendation.message} reason={data.recommendation.reason} />
        <section className='metric-grid' aria-label='도착 요약'>
          <MetricCard label='지하철' value={firstArrival(data.subway)} tone='primary' />
          <MetricCard label='버스' value={firstArrival(data.bus)} tone='green' />
        </section>
        <SubwayArrivalCard items={data.subway} />
        <BusArrivalCard items={data.bus} />
      </div>
    </AppShell>
  )
}
