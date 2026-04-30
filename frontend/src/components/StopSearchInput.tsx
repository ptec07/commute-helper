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

  const hasResults = results.busStops.length > 0 || results.subwayStations.length > 0

  return (
    <section className='card stack'>
      <label className='field'>
        정류장 또는 역 검색
        <input className='input' placeholder='상계역 검색' onChange={handleChange} />
      </label>
      {error ? <p className='error'>{error}</p> : null}
      {hasResults ? (
        <div className='stack'>
          {results.subwayStations.length > 0 ? (
            <div>
              <h2 className='section-title'>지하철역</h2>
              <ul className='result-list'>
                {results.subwayStations.map((item) => (
                  <li key={item.externalId}>
                    <button className='result-button' type='button' aria-label={item.name} onClick={() => onSelect(item)}>
                      <span>{item.name}</span>
                      <span className='result-meta'>{item.lineName ?? '지하철'}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {results.busStops.length > 0 ? (
            <div>
              <h2 className='section-title'>버스 정류장</h2>
              <ul className='result-list'>
                {results.busStops.map((item) => (
                  <li key={item.externalId}>
                    <button className='result-button' type='button' aria-label={item.name} onClick={() => onSelect(item)}>
                      <span>{item.name}</span>
                      <span className='result-meta'>{item.lineName ?? '버스'}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  )
}
