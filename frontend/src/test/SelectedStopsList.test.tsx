import { render, screen } from '@testing-library/react'
import { SelectedStopsList } from '../components/SelectedStopsList'

test('shows selected stop names', () => {
  render(<SelectedStopsList items={[{ externalId: 'station-100', name: '상계역', lineName: '4호선' }]} />)
  expect(screen.getByText('상계역')).toBeInTheDocument()
})
