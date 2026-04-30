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

test('shows progress and blocks duplicate submits while creating profile', async () => {
  const user = userEvent.setup()
  let resolveSubmit: () => void = () => undefined
  const onSubmit = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        resolveSubmit = resolve
      }),
  )

  render(<ProfileForm onSubmit={onSubmit} />)

  await user.type(screen.getByLabelText('프로필 이름'), '회사 가기')
  await user.click(screen.getByRole('button', { name: '다음' }))

  expect(screen.getByRole('button', { name: '저장 중...' })).toBeDisabled()
  await user.click(screen.getByRole('button', { name: '저장 중...' }))
  expect(onSubmit).toHaveBeenCalledTimes(1)

  resolveSubmit()
  expect(await screen.findByRole('button', { name: '다음' })).toBeEnabled()
})

test('trims the profile name before submitting', async () => {
  const user = userEvent.setup()
  const onSubmit = vi.fn()

  render(<ProfileForm onSubmit={onSubmit} />)

  await user.type(screen.getByLabelText('프로필 이름'), '  회사 가기  ')
  await user.click(screen.getByRole('button', { name: '다음' }))

  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ name: '회사 가기' }))
})
