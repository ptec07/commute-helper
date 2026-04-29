import { buildAddStopUrl, buildApiUrl, buildDashboardUrl, buildSearchStopsUrl } from '../lib/api'

test('builds dashboard url from profile id', () => {
  expect(buildDashboardUrl('abc')).toBe('/api/dashboard/abc')
})

test('builds absolute api url when a base url is configured', () => {
  expect(buildApiUrl('/api/search/stops?q=%EC%83%81%EA%B3%84', 'http://localhost:8000')).toBe(
    'http://localhost:8000/api/search/stops?q=%EC%83%81%EA%B3%84',
  )
})

test('builds relative api url when no base url is configured', () => {
  expect(buildApiUrl('/api/commute-profiles', '')).toBe('/api/commute-profiles')
})

test('builds search stops url with encoded query and configured base url', () => {
  expect(buildSearchStopsUrl('상계역', 'https://api.example.com')).toBe(
    'https://api.example.com/api/search/stops?q=%EC%83%81%EA%B3%84%EC%97%AD',
  )
})

test('builds add stop url with configured base url', () => {
  expect(buildAddStopUrl('profile-1', 'https://api.example.com/')).toBe(
    'https://api.example.com/api/commute-profiles/profile-1/stops',
  )
})
