import { buildDashboardUrl } from '../lib/api'

test('builds dashboard url from profile id', () => {
  expect(buildDashboardUrl('abc')).toBe('/api/dashboard/abc')
})
