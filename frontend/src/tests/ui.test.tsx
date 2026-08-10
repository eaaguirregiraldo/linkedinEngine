import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AngleTag } from '../components/ui/AngleTag'
import { Banner } from '../components/ui/Banner'
import { BlockersList } from '../components/ui/BlockersList'
import { CandidateCard } from '../components/ui/CandidateCard'
import { ErrorBanner } from '../components/ui/ErrorBanner'
import { ReceiptCard } from '../components/ui/ReceiptCard'
import { ScoreBreakdown } from '../components/ui/ScoreBreakdown'
import { VoiceBadge } from '../components/ui/VoiceBadge'
import type {
  Blocker,
  CandidateOut,
  CandidateScore,
  ErrorBody,
  PublicationOut,
} from '../api/client'

describe('components/ui — primitivas (H1.3)', () => {
  describe('Banner', () => {
    it('variante SIMULACIÓN: banda persistente + aclaración de no-envío (RUN-03)', () => {
      const { container } = render(<Banner variant="simulation" />)
      expect(container.textContent).toContain('SIMULACIÓN')
      expect(container.textContent).toContain('no se envió contenido a LinkedIn')
    })

    it('variante DEMO_PROVIDER: etiqueta + aclaración de datos demo (RUN-06)', () => {
      const { container } = render(<Banner variant="demo" />)
      expect(container.textContent).toContain('DEMO_PROVIDER')
      expect(container.textContent).toMatch(/demo|local/i)
    })

    it('variante OPENAI_PROVIDER identifica IA real y el mismo harness', () => {
      const { container } = render(<Banner variant="openai" />)
      expect(container.textContent).toContain('OPENAI_PROVIDER')
      expect(container.textContent).toMatch(/harness|validada/i)
    })
  })

  describe('VoiceBadge', () => {
    it('etiqueta el perfil como provisional v0 (VOI-01)', () => {
      render(<VoiceBadge />)
      expect(screen.getByText('perfil de voz provisional v0')).toBeTruthy()
    })
  })

  describe('AngleTag', () => {
    it.each([
      ['problem-story', 'Historia de problema'],
      ['practical-framework', 'Marco práctico'],
      ['argued-position', 'Posición argumentada'],
    ] as const)('mapea %s a %s', (angle, label) => {
      render(<AngleTag angle={angle} />)
      expect(screen.getByText(label)).toBeTruthy()
    })
  })

  describe('CandidateCard', () => {
    const candidate: CandidateOut = {
      id: 1,
      angle: 'problem-story',
      hook: 'Migrar COBOL no es traducir sintaxis',
      body: 'Es recuperar conocimiento operativo.',
      cta: '¿Cuál fue tu migración más difícil?',
      claims: [{ text: 'COBOL sigue en producción', support: 'known_facts' }],
      content_version: 2,
      evaluation: { score_final: 95, decision: 'RECOMMENDED' },
      decision: 'RECOMMENDED',
    }

    it('renderiza ángulo, hook, body, cta, claims y versión', () => {
      const { container } = render(<CandidateCard candidate={candidate} />)
      const text = container.textContent ?? ''
      expect(text).toContain('Historia de problema')
      expect(text).toContain('Migrar COBOL no es traducir sintaxis')
      expect(text).toContain('Es recuperar conocimiento operativo.')
      expect(text).toContain('¿Cuál fue tu migración más difícil?')
      expect(text).toContain('COBOL sigue en producción')
      expect(text).toContain('v2')
      expect(text).toContain('95')
    })
  })

  describe('BlockersList', () => {
    const blockers: Blocker[] = [
      {
        code: 'UNSUPPORTED_CLAIM',
        message: 'cifra sin evidencia: "5 años"',
        detail: 'agregá evidencia para la cifra',
      },
    ]

    it('lista code + message + detalle accionable', () => {
      const { container } = render(<BlockersList blockers={blockers} />)
      const text = container.textContent ?? ''
      expect(text).toContain('UNSUPPORTED_CLAIM')
      expect(text).toContain('cifra sin evidencia')
      expect(text).toContain('agregá evidencia para la cifra')
    })

    it('sin blockers no renderiza nada', () => {
      const { container } = render(<BlockersList blockers={[]} />)
      expect(container.textContent).toBe('')
    })
  })

  describe('ErrorBanner', () => {
    const body: ErrorBody = {
      error: {
        code: 'STATE_TRANSITION_REJECTED',
        message: 'se requiere: una evaluacion previa del candidato',
        details: {},
      },
    }

    it('muestra code + message + detalle accionable', () => {
      const { container } = render(<ErrorBanner error={body} />)
      const text = container.textContent ?? ''
      expect(text).toContain('STATE_TRANSITION_REJECTED')
      expect(text).toContain('se requiere: una evaluacion previa del candidato')
      expect(text).toContain('evaluacion previa')
    })
  })

  describe('ReceiptCard', () => {
    const publication: PublicationOut = {
      receipt: {
        id: 7,
        mode: 'simulated',
        status: 'SIMULATED_PUBLISHED',
        candidate_id: 3,
        visual_id: 9,
        created_at: '2026-08-09T00:00:00Z',
        notice: 'no se envió contenido a LinkedIn',
        remote_id: null,
      },
      candidate_id: 3,
      visual_id: 9,
      mode: 'simulated',
      status: 'SIMULATED_PUBLISHED',
    }

    it('recibo local con estado y notice; SIN URLs ni IDs remotos (SIM-01/02)', () => {
      const { container } = render(<ReceiptCard publication={publication} />)
      const text = container.textContent ?? ''
      expect(text).toContain('SIMULATED_PUBLISHED')
      expect(text).toContain('no se envió contenido a LinkedIn')
      expect(text).toContain('SIMULACIÓN')

      // SIM-02: cero URLs/URNs/IDs remotos inventados
      expect(text).not.toMatch(/http/i)
      expect(text).not.toMatch(/urn/i)
      expect(text).not.toMatch(/linkedin\.com/i)
      expect(text).not.toContain('remote_id')
      expect(text).not.toContain('remoteId')
    })
  })

  describe('ScoreBreakdown', () => {
    const score: CandidateScore = {
      candidate_id: 1,
      dimensions: {
        hook: { rating: 5, quote: 'Migrar COBOL no es traducir sintaxis', rubric_rule: 'hook concreto y promesa clara' },
        niche_relevance: { rating: 5, quote: 'conocimiento operativo', rubric_rule: 'especificidad mainframe' },
        specificity_evidence: { rating: 4, quote: 'décadas de reglas de negocio', rubric_rule: 'evidencia citada' },
        clarity: { rating: 4, quote: 'frase corta', rubric_rule: 'legible en un paseo' },
        conversation_potential: { rating: 4, quote: '¿Cuál fue tu migración más difícil?', rubric_rule: 'cierre con pregunta específica' },
        voice_fit: { rating: 4, quote: 'técnica y sobria', rubric_rule: 'voz v0 provisional' },
      },
      penalties: { risk: 0, generic: 5 },
      score_final: 95,
      blockers: [],
    }

    it('muestra fórmula, pesos, umbrales y notice de calibración (EVAL-01/EVAL-08)', () => {
      const { container } = render(<ScoreBreakdown score={score} />)
      const text = container.textContent ?? ''
      // EVAL-01: score final sin decimales + desglose por dimensión
      expect(text).toContain('95')
      expect(text).toContain('Fuerza del hook')
      expect(text).toContain('100')
      // penalizaciones
      expect(text).toContain('5')
      // EVAL-08: fórmula y umbrales visibles, calibrables
      expect(text).toContain('Fórmula')
      expect(text).toContain('72')
      expect(text).toContain('4')
      expect(text).toContain('60')
      expect(text).toContain('calibrables')
      expect(text).toContain('0.20')
    })

    it('muestra decision RECOMMENDED cuando llega (EVAL-06)', () => {
      const { container } = render(
        <ScoreBreakdown
          score={score}
          decision={{ outcome: 'RECOMMENDED', best_candidate_id: 1, reason: 'mejor candidato sin blockers', brief_needs_revision: false }}
        />,
      )
      expect(container.textContent).toContain('RECOMMENDED')
    })
  })
})
