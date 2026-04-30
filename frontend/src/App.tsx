import { useState } from 'react'
import { AppShell, Badge, Button, Card, MetricCard } from './components/ui'
import { DashboardPage } from './pages/DashboardPage'
import { NewProfilePage } from './pages/NewProfilePage'
import { StopSelectionPage } from './pages/StopSelectionPage'

type ViewState =
  | { screen: 'home' }
  | { screen: 'create' }
  | { screen: 'stops'; profileId: string }
  | { screen: 'dashboard'; profileId: string }

export function App() {
  const [view, setView] = useState<ViewState>({ screen: 'home' })

  if (view.screen === 'create') {
    return <NewProfilePage onCreated={(profile) => setView({ screen: 'stops', profileId: profile.id })} />
  }

  if (view.screen === 'stops') {
    return <StopSelectionPage profileId={view.profileId} onCompleted={(profileId) => setView({ screen: 'dashboard', profileId })} />
  }

  if (view.screen === 'dashboard') {
    return <DashboardPage profileId={view.profileId} />
  }

  return (
    <AppShell>
      <div className='stack-lg'>
        <section className='hero-card stack'>
          <p className='eyebrow'>출근 판단을 빠르게</p>
          <h1 className='hero-title'>오늘 출근, 지금 나갈까요?</h1>
          <p className='lead'>버스와 지하철 도착 정보를 보고 빠르게 판단해드려요.</p>
          <Button type='button' onClick={() => setView({ screen: 'create' })}>
            내 출근길 설정하기
          </Button>
          <div className='badge-row' aria-label='주요 기능'>
            <Badge>실시간 도착</Badge>
            <Badge tone='green'>버스/지하철</Badge>
            <Badge tone='amber'>짧은 판단</Badge>
          </div>
        </section>

        <Card className='stack'>
          <Badge>미리보기</Badge>
          <div>
            <h2 className='section-title'>지금은 지하철이 유리해요</h2>
            <p className='muted'>도착 정보를 비교해 덜 기다리는 쪽을 보여줍니다.</p>
          </div>
          <div className='preview-grid'>
            <MetricCard label='지하철' value='3분' tone='primary' />
            <MetricCard label='버스' value='정보 없음' tone='green' />
          </div>
        </Card>
      </div>
    </AppShell>
  )
}
