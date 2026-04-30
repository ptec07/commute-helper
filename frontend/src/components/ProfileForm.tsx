import { useState } from 'react'
import type { CommuteProfileInput } from '../lib/types'
import { Button } from './ui'

type ProfileFormProps = {
  onSubmit: (payload: CommuteProfileInput) => void | Promise<void>
}

export function ProfileForm({ onSubmit }: ProfileFormProps) {
  const [name, setName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (isSubmitting) {
      return
    }

    setIsSubmitting(true)
    try {
      await onSubmit({
        name: name.trim(),
        origin_label: '집',
        destination_label: '회사',
        target_arrival_time: '09:00:00',
        preferred_mode: 'balanced',
        walking_tolerance_min: 10,
      })
    } finally {
      setIsSubmitting(false)
    }
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
          disabled={isSubmitting}
        />
      </label>
      <Button type='submit' disabled={isSubmitting || name.trim().length === 0}>
        {isSubmitting ? '저장 중...' : '다음'}
      </Button>
    </form>
  )
}
