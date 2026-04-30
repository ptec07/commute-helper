import { useState } from 'react'
import { createProfile } from '../lib/api'
import { AppShell } from '../components/ui'
import { ProfileForm } from '../components/ProfileForm'

type NewProfilePageProps = {
  onCreated?: (profile: { id: string; name: string }) => void
}

export function NewProfilePage({ onCreated }: NewProfilePageProps) {
  const [error, setError] = useState<string | null>(null)

  return (
    <AppShell>
      <section className='hero-card stack'>
        <div>
          <p className='eyebrow'>1단계</p>
          <h1 className='page-title'>출근길 만들기</h1>
          <p className='page-lead'>매일 확인할 출근길 이름을 정해주세요.</p>
        </div>
        {error ? <p className='error'>{error}</p> : null}
        <ProfileForm
          onSubmit={async (payload) => {
            try {
              const created = await createProfile(payload)
              setError(null)
              onCreated?.(created)
            } catch {
              setError('프로필을 저장하지 못했습니다.')
            }
          }}
        />
      </section>
    </AppShell>
  )
}
