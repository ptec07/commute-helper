import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { App } from '../App'

describe('app flow', () => {
  beforeEach(() => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)

      if (url === '/api/commute-profiles' && init?.method === 'POST') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'profile-1',
            name: '회사 가기',
            origin_label: '집',
            destination_label: '회사',
            target_arrival_time: '09:00:00',
            preferred_mode: 'balanced',
            walking_tolerance_min: 10,
            created_at: '2026-04-24T00:00:00',
            updated_at: '2026-04-24T00:00:00',
            stops: [],
          }),
        } as Response
      }

      if (url.startsWith('/api/search/stops?q=')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            busStops: [],
            subwayStations: [{ externalId: 'station-100', name: '상계역', lineName: '4호선' }],
          }),
        } as Response
      }

      if (url === '/api/commute-profiles/profile-1/stops' && init?.method === 'POST') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'stop-1',
            externalId: 'station-100',
            name: '상계역',
            lineName: '4호선',
          }),
        } as Response
      }

      if (url === '/api/dashboard/profile-1') {
        await new Promise((resolve) => setTimeout(resolve, 50))
        return {
          ok: true,
          status: 200,
          json: async () => ({
            profile: { id: 'profile-1', name: '회사 가기', targetArrivalTime: '09:00' },
            bus: [],
            subway: [],
            recommendation: {
              mode: 'bus',
              message: '지금 출발하면 버스가 더 유리합니다.',
              reason: '버스가 빨리 옵니다.',
              leaveBy: '08:17',
            },
          }),
        } as Response
      }

      throw new Error(`Unhandled fetch: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  test('allows user to move from profile setup to dashboard', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(screen.getByText('출근도우미')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '내 출근길 설정하기' }))
    expect(await screen.findByLabelText('프로필 이름')).toBeInTheDocument()

    await user.type(screen.getByLabelText('프로필 이름'), '회사 가기')
    await user.click(screen.getByRole('button', { name: '다음' }))

    expect(await screen.findByLabelText('정류장 또는 역 검색')).toBeInTheDocument()
    await user.type(screen.getByLabelText('정류장 또는 역 검색'), '상계역')
    await user.click(await screen.findByRole('button', { name: '상계역' }))
    expect(await screen.findByText('선택 완료')).toBeInTheDocument()
    expect(screen.getAllByText('상계역').length).toBeGreaterThanOrEqual(1)
    await user.click(screen.getByRole('button', { name: '대시보드 보기' }))
    expect(await screen.findByText('도착 정보를 불러오고 있어요')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('지금 출발하면 버스가 더 유리합니다.')).toBeInTheDocument()
    })
  })
})
