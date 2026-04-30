import { useRef, useState } from 'react'
import { addStop, searchStops as defaultSearchStops } from '../lib/api'
import { AppShell, Button } from '../components/ui'
import { SelectedStopsList } from '../components/SelectedStopsList'
import { StopSearchInput } from '../components/StopSearchInput'
import type { CommuteStop } from '../lib/types'

type StopSelectionPageProps = {
  profileId: string
  onCompleted: (profileId: string) => void
}

export function StopSelectionPage({ profileId, onCompleted }: StopSelectionPageProps) {
  const [selected, setSelected] = useState<Array<CommuteStop>>([])
  const [pendingIds, setPendingIds] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const savingRef = useRef(false)

  async function handleSelect(item: CommuteStop) {
    if (selected.some((existing) => existing.externalId === item.externalId)) {
      return
    }
    if (pendingIds.includes(item.externalId) || savingRef.current) {
      return
    }

    const stopType = item.kind ?? (item.lineName ? 'subway_station' : 'bus_stop')
    const direction = item.direction ?? (stopType === 'subway_station' ? '오이도방향' : undefined)
    const sortOrder = selected.length + 1

    savingRef.current = true
    setPendingIds((current) => [...current, item.externalId])
    try {
      await addStop(profileId, {
        type: stopType,
        external_id: item.externalId,
        name: item.name,
        line_name: item.lineName,
        direction,
        sort_order: sortOrder,
      })
      setError(null)
      setSelected((current) => {
        if (current.some((existing) => existing.externalId === item.externalId)) {
          return current
        }
        return [...current, item]
      })
    } catch {
      setError('정류장/역을 저장하지 못했습니다.')
    } finally {
      savingRef.current = false
      setPendingIds((current) => current.filter((id) => id !== item.externalId))
    }
  }

  return (
    <AppShell>
      <div className='stack-lg'>
        <section className='hero-card'>
          <p className='eyebrow'>2단계</p>
          <h1 className='page-title'>정류장/역 선택</h1>
          <p className='page-lead'>자주 타는 곳을 검색하세요.</p>
        </section>
        {error ? <p className='error'>{error}</p> : null}
        <StopSearchInput searchStops={defaultSearchStops} onSelect={handleSelect} />
        <SelectedStopsList items={selected} />
        <Button type='button' onClick={() => onCompleted(profileId)} disabled={selected.length === 0}>
          대시보드 보기
        </Button>
      </div>
    </AppShell>
  )
}
