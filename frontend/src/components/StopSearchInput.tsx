import { useRef, useState } from 'react'
import type { CommuteStop, SearchStopsResult } from '../lib/types'

type StopSearchInputProps = {
  searchStops: (query: string) => Promise<SearchStopsResult>
  onSelect: (item: CommuteStop) => void
}

export function StopSearchInput({ searchStops, onSelect }: StopSearchInputProps) {
  const [results, setResults] = useState<SearchStopsResult>({ busStops: [], subwayStations: [] })
  const [error, setError] = useState<string | null>(null)
  const requestSequence = useRef(0)

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const value = event.target.value
    const currentRequest = ++requestSequence.current
    if (!value) {
      setResults({ busStops: [], subwayStations: [] })
      setError(null)
      return
    }

    try {
      const next = await searchStops(value)
      if (currentRequest === requestSequence.current) {
        setResults(next)
        setError(null)
      }
    } catch {
      if (currentRequest === requestSequence.current) {
        setError('검색 결과를 불러오지 못했습니다.')
      }
    }
  }

  return (
    <div>
      <label>
        정류장 또는 역 검색
        <input onChange={handleChange} />
      </label>
      {error ? <p>{error}</p> : null}
      <ul>
        {results.busStops.map((item) => (
          <li key={item.externalId}>
            <button type="button" onClick={() => onSelect(item)}>
              {item.name}
            </button>
          </li>
        ))}
        {results.subwayStations.map((item) => (
          <li key={item.externalId}>
            <button type="button" onClick={() => onSelect(item)}>
              {item.name}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
