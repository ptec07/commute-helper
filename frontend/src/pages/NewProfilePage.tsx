import { useState } from 'react'
import { createProfile } from '../lib/api'
import { ProfileForm } from '../components/ProfileForm'

type NewProfilePageProps = {
  onCreated?: (profile: { id: string; name: string }) => void
}

export function NewProfilePage({ onCreated }: NewProfilePageProps) {
  const [error, setError] = useState<string | null>(null)

  return (
    <section>
      <h1>통근 프로필 만들기</h1>
      {error ? <p>{error}</p> : null}
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
  )
}
