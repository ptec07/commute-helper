import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

test('build creates a Vercel 404.html fallback for direct SPA routes', () => {
  const packageJson = JSON.parse(readFileSync(resolve(__dirname, '../../package.json'), 'utf-8')) as {
    scripts?: Record<string, string>
  }

  expect(packageJson.scripts?.build).toContain('cp dist/index.html dist/404.html')
})
