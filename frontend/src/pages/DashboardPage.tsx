import { useEffect, useState } from 'react'
import { getDashboard as defaultGetDashboard } from '../lib/api'
import type { DashboardData } from '../lib/types'
import { BusArrivalCard } from '../components/BusArrivalCard'
import { RecommendationCard } from '../components/RecommendationCard'
import { SubwayArrivalCard } from '../components/SubwayArrivalCard'

type DashboardPageProps = {
  profileId: string
  getDashboard?: (profileId: string) => Promise<DashboardData>
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

  if (error) return <p>{error}</p>
  if (!data) return <p>불러오는 중...</p>

  return (
    <section>
      <h1>{data.profile.name}</h1>
      <RecommendationCard message={data.recommendation.message} reason={data.recommendation.reason} />
      <BusArrivalCard items={data.bus} />
      <SubwayArrivalCard items={data.subway} />
    </section>
  )
}
