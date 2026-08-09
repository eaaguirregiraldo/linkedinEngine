import { readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const sourceRoot = resolve(process.cwd(), 'src')
const generatedSchema = readFileSync(resolve(sourceRoot, 'api/schema.d.ts'), 'utf8')

function sourceFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name)
    if (entry.isDirectory()) return sourceFiles(path)
    return /\.(ts|tsx)$/.test(entry.name) && !entry.name.endsWith('.d.ts') ? [path] : []
  })
}

describe('generated schema coverage', () => {
  it('contains every generated component schema referenced by frontend source', () => {
    const references = new Set<string>()
    for (const file of sourceFiles(sourceRoot)) {
      const source = readFileSync(file, 'utf8')
      const pattern = /components\s*\[(['"])schemas\1\]\s*\[(['"])([^'"\]]+)\2\]/g
      for (const match of source.matchAll(pattern)) references.add(match[3])
    }

    expect(references.size).toBeGreaterThan(0)
    const missing = [...references].filter(
      (name) => !new RegExp(`^\\s+${name}:`, 'm').test(generatedSchema),
    )
    expect(missing, 'referenced schemas must exist in generated schema.d.ts').toEqual([])
  })
})
