import { render, screen } from '@testing-library/react'
import { DashboardPage } from '../pages/DashboardPage'

test('renders recommendation message from dashboard payload', async () => {
  const getDashboard = vi.fn().mockResolvedValue({
    profile: { id: '1', name: '회사 가기', targetArrivalTime: '09:00' },
    bus: [],
    subway: [],
    recommendation: {
      mode: 'bus',
      message: '지금 출발하면 버스가 더 유리합니다.',
      reason: '버스가 빨리 옵니다.',
      leaveBy: '08:17',
    },
  })

  render(<DashboardPage profileId='1' getDashboard={getDashboard} />)
  expect(await screen.findByText('지금 출발하면 버스가 더 유리합니다.')).toBeInTheDocument()
})

test('renders a controlled error message when dashboard loading fails', async () => {
  const getDashboard = vi.fn().mockRejectedValue(new Error('boom'))

  render(<DashboardPage profileId='1' getDashboard={getDashboard} />)
  expect(await screen.findByText('대시보드를 불러오지 못했습니다.')).toBeInTheDocument()
})

test('explains when there is no bus arrival information', async () => {
  const getDashboard = vi.fn().mockResolvedValue({
    profile: { id: '1', name: '회사 가기', targetArrivalTime: '09:00' },
    bus: [],
    subway: [],
    recommendation: {
      mode: 'subway',
      message: '지금 출발하면 지하철이 더 유리합니다.',
      reason: '지하철 도착이 더 안정적이거나 빠릅니다.',
      leaveBy: '08:17',
    },
  })

  render(<DashboardPage profileId='1' getDashboard={getDashboard} />)
  expect(await screen.findByText('현재 표시할 버스 도착 정보가 없습니다.')).toBeInTheDocument()
})
