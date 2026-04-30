import type { ReactNode } from 'react'

type AppShellProps = {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <main className='app-shell'>
      <div className='app-frame'>
        <header className='app-header'>
          <div className='brand' aria-label='출근도우미'>
            <span className='brand-mark'>출</span>
            <span>출근도우미</span>
          </div>
          <p className='header-note'>Seoul commute</p>
        </header>
        {children}
      </div>
    </main>
  )
}

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary'
}

export function Button({ variant = 'primary', className = '', ...props }: ButtonProps) {
  return <button className={`${variant === 'primary' ? 'primary-button' : 'secondary-button'} ${className}`.trim()} {...props} />
}

type CardProps = {
  children: ReactNode
  className?: string
}

export function Card({ children, className = '' }: CardProps) {
  return <section className={`card ${className}`.trim()}>{children}</section>
}

type BadgeProps = {
  children: ReactNode
  tone?: 'blue' | 'green' | 'amber'
}

export function Badge({ children, tone = 'blue' }: BadgeProps) {
  const toneClass = tone === 'green' ? 'badge-green' : tone === 'amber' ? 'badge-amber' : ''
  return <span className={`badge ${toneClass}`.trim()}>{children}</span>
}

type MetricCardProps = {
  label: string
  value: string
  tone?: 'default' | 'primary' | 'green'
}

export function MetricCard({ label, value, tone = 'default' }: MetricCardProps) {
  return (
    <div className={`metric-card ${tone === 'default' ? '' : tone}`.trim()}>
      <p className='metric-label'>{label}</p>
      <p className='metric-value'>{value}</p>
    </div>
  )
}
