import { useState } from 'react'
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
    <main>
      <h1>출근도우미</h1>
      <button type="button" onClick={() => setView({ screen: 'create' })}>
        통근 프로필 만들기
      </button>
    </main>
  )
}
