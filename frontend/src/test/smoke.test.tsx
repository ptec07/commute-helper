import { render, screen } from '@testing-library/react'
import { App } from '../App'

test('renders service name', () => {
  render(<App />)
  expect(screen.getByText('출근도우미')).toBeInTheDocument()
})
