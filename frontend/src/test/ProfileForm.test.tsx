import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProfileForm } from '../components/ProfileForm'

test('submits commute profile values', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn()

  render(<ProfileForm onSubmit={onSubmit} />)

  await user.type(screen.getByLabelText('프로필 이름'), '회사 가기')
  await user.click(screen.getByRole('button', { name: '다음' }))

  expect(onSubmit).toHaveBeenCalled()
})
