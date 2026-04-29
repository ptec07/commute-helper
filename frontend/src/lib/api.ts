import type { CommuteProfileInput, DashboardData, SearchStopsResult } from './types'

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function buildApiUrl(path: string, baseUrl = configuredApiBaseUrl) {
  if (!baseUrl) return path
  return `${baseUrl.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`
}

export function buildDashboardUrl(profileId: string) {
  return buildApiUrl(`/api/dashboard/${profileId}`)
}

export async function listProfiles() {
  const response = await fetch(buildApiUrl('/api/commute-profiles'))
  return parseJsonResponse(response)
}

export async function createProfile(payload: CommuteProfileInput) {
  const response = await fetch(buildApiUrl('/api/commute-profiles'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseJsonResponse(response)
}

export async function addStop(profileId: string, payload: Record<string, unknown>) {
  const response = await fetch(`/api/commute-profiles/${profileId}/stops`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseJsonResponse(response)
}

export async function getDashboard(profileId: string): Promise<DashboardData> {
  const response = await fetch(buildDashboardUrl(profileId))
  return parseJsonResponse<DashboardData>(response)
}

export async function searchStops(query: string): Promise<SearchStopsResult> {
  const response = await fetch(`/api/search/stops?q=${encodeURIComponent(query)}`)
  return parseJsonResponse<SearchStopsResult>(response)
}
