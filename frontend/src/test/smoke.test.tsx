import { render, screen } from '@testing-library/react'
import { App } from '../App'

test('renders service name', () => {
  render(<App />)
  expect(screen.getByText('출근도우미')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: '오늘 출근, 지금 나갈까요?' })).toBeInTheDocument()
  expect(screen.getByText('버스와 지하철 도착 정보를 보고 빠르게 판단해드려요.')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: '내 출근길 설정하기' })).toBeInTheDocument()
  expect(screen.getByText('지금은 지하철이 유리해요')).toBeInTheDocument()
})
