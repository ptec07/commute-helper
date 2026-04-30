import { useState } from 'react'
import type { CommuteProfileInput } from '../lib/types'
import { Button } from './ui'

type ProfileFormProps = {
  onSubmit: (payload: CommuteProfileInput) => void | Promise<void>
}

export function ProfileForm({ onSubmit }: ProfileFormProps) {
  const [name, setName] = useState('')

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await onSubmit({
      name,
      origin_label: '집',
      destination_label: '회사',
      target_arrival_time: '09:00:00',
      preferred_mode: 'balanced',
      walking_tolerance_min: 10,
    })
  }

  return (
    <form className='form' onSubmit={handleSubmit}>
      <label className='field'>
        프로필 이름
        <input
          className='input'
          value={name}
          placeholder='평일 출근'
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <Button type='submit'>다음</Button>
    </form>
  )
}
