import { execFileSync } from 'node:child_process'
import { readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const frontendRoot = resolve(process.cwd())
const schemaPath = resolve(frontendRoot, 'src/api/schema.d.ts')

describe('OpenAPI anti-drift', () => {
  it('keeps generated TypeScript byte-for-byte aligned with the live API', async () => {
    const response = await fetch('http://localhost:8000/openapi.json')
    expect(response.ok, 'backend vivo requerido en http://localhost:8000').toBe(true)

    const outputPath = join(tmpdir(), `linkedin-schema-${process.pid}.d.ts`)
    const binary = resolve(frontendRoot, 'node_modules/.bin/openapi-typescript')

    try {
      execFileSync(binary, ['http://localhost:8000/openapi.json', '-o', outputPath], {
        cwd: frontendRoot,
        stdio: 'pipe',
      })
      expect(readFileSync(outputPath, 'utf8'), 'corré npm run schema:generate').toBe(
        readFileSync(schemaPath, 'utf8'),
      )
    } finally {
      rmSync(outputPath, { force: true })
    }
  })
})
