import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { StopSearchInput } from '../components/StopSearchInput'

test('shows matching station and bus-stop results', async () => {
  const user = userEvent.setup()
  const searchStops = vi.fn().mockResolvedValue({
    busStops: [{ externalId: '200000123', name: '상계주공7단지', lineName: '146', kind: 'bus_stop' }],
    subwayStations: [{ externalId: '1', name: '상계역', lineName: '4호선', kind: 'subway_station' }],
  })

  render(<StopSearchInput searchStops={searchStops} onSelect={vi.fn()} />)

  await user.type(screen.getByLabelText('정류장 또는 역 검색'), '상계')
  expect(await screen.findByText('상계역')).toBeInTheDocument()
  expect(await screen.findByText('상계주공7단지')).toBeInTheDocument()
})

test('selects the first station result when pressing Enter after typing an exact station name', async () => {
  const user = userEvent.setup()
  const station = { externalId: '1', name: '상계역', lineName: '4호선', kind: 'subway_station' as const }
  const searchStops = vi.fn().mockResolvedValue({
    busStops: [],
    subwayStations: [station],
  })
  const onSelect = vi.fn()

  render(<StopSearchInput searchStops={searchStops} onSelect={onSelect} />)

  await user.type(screen.getByLabelText('정류장 또는 역 검색'), '상계역')
  expect(await screen.findByRole('button', { name: '상계역' })).toBeInTheDocument()

  await user.keyboard('{Enter}')

  expect(onSelect).toHaveBeenCalledWith(station)
})
