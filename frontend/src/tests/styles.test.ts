import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const read = (p: string): string =>
  readFileSync(new URL(p, import.meta.url), 'utf8')

describe('styles — tokens y primitivas visuales (H1.4)', () => {
  it('tokens.css define primitivas de color/espaciado/borde/tipografía', () => {
    const css = read('../styles/tokens.css')
    expect(css).toContain(':root')
    // colores semánticos de estado (RNF-02: distinguir simulado/demo/error)
    expect(css).toContain('--color-simulation')
    expect(css).toContain('--color-demo')
    expect(css).toContain('--color-error')
    expect(css).toContain('--color-success')
    // escala de espaciado y radios
    expect(css).toContain('--space-4')
    expect(css).toContain('--radius-md')
    expect(css).toContain('--font-sans')
  })

  it('base.css importa tokens y define clases de las primitivas UI', () => {
    const css = read('../styles/base.css')
    expect(css).toContain('@import')
    expect(css).toContain('.banner--simulation')
    expect(css).toContain('.banner--demo')
    expect(css).toContain('.error-banner')
    expect(css).toContain('.voice-badge')
    expect(css).toContain('.angle-tag')
    expect(css).toContain('.candidate-card')
    expect(css).toContain('.receipt-card')
    expect(css).toContain('.score-breakdown')
  })
})
