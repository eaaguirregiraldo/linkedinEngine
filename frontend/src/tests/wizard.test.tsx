import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from '../App'
import type {
  CandidateOut,
  CandidateScore,
  DemoIdeaOut,
  EvaluationOut,
  ProjectOut,
  PublicationOut,
  RunDetailOut,
  RunOut,
  VisualOut,
} from '../api/client'
import { ApproveStep } from '../components/steps/ApproveStep'
import { BriefStep } from '../components/steps/BriefStep'
import { EvaluateStep } from '../components/steps/EvaluateStep'
import { GeneratingStep } from '../components/steps/GeneratingStep'
import { IdeaStep } from '../components/steps/IdeaStep'
import { PublishStep } from '../components/steps/PublishStep'
import { ReviewStep } from '../components/steps/ReviewStep'
import { TraceStep } from '../components/steps/TraceStep'
import { VisualStep } from '../components/steps/VisualStep'

const idea: DemoIdeaOut = {
  id: 'demo-1',
  raw_idea: 'Migrar COBOL es recuperar conocimiento operativo',
  default_audience: 'líderes de modernización',
  default_objective: 'reencuadrar el riesgo de migración',
}

const project: ProjectOut = {
  id: 11,
  raw_idea: idea.raw_idea,
  title: null,
  status: 'IDEA',
  created_at: '2026-08-09T00:00:00Z',
  updated_at: '2026-08-09T00:00:00Z',
}

const candidates: CandidateOut[] = [
  { id: 21, angle: 'problem-story', hook: 'El riesgo no está en la sintaxis', body: 'Está en las reglas que nadie documentó.', cta: '¿Dónde vive tu conocimiento operativo?', claims: [{ text: 'Hay reglas no documentadas', support: 'evidence-1' }], content_version: 1, evaluation: null, decision: null },
  { id: 22, angle: 'practical-framework', hook: 'Tres capas antes de migrar', body: 'Inventario, reglas y excepciones.', cta: '¿Cuál mapearías primero?', claims: [], content_version: 1, evaluation: null, decision: null },
  { id: 23, angle: 'argued-position', hook: 'Traducir COBOL no moderniza', body: 'Modernizar cambia el modelo de riesgo.', cta: '¿Qué riesgo seguís midiendo mal?', claims: [], content_version: 1, evaluation: null, decision: null },
]

function score(candidateId: number, scoreFinal: number, blocker = false): CandidateScore {
  const dimension = { rating: 4, quote: 'frase concreta', rubric_rule: 'regla versionada' }
  return {
    candidate_id: candidateId,
    dimensions: { hook: dimension, niche_relevance: dimension, specificity_evidence: dimension, clarity: dimension, conversation_potential: dimension, voice_fit: dimension },
    penalties: { risk: blocker ? 10 : 0, generic: 0 },
    score_final: scoreFinal,
    blockers: blocker ? [{ code: 'UNSUPPORTED_CLAIM', message: 'Claim sin soporte', detail: 'Vinculá evidencia o retiralo' }] : [],
  }
}

const evaluation: EvaluationOut = {
  candidate_scores: [score(21, 91), score(22, 84), score(23, 78)],
  decision: { outcome: 'RECOMMENDED', best_candidate_id: 21, reason: 'Mejor score sin blockers y diferencia suficiente.', brief_needs_revision: false },
}

const run: RunOut = {
  id: 31,
  project_id: 11,
  status: 'GENERATED',
  provider: 'DEMO_PROVIDER',
  model: null,
  prompt_version: '1.0.0',
  schema_version: '1.0.0',
  prompt_hash: 'sha256:abc123',
  candidates,
  error_code: null,
  started_at: '2026-08-09T00:00:01Z',
  completed_at: '2026-08-09T00:00:02Z',
}

const approved: CandidateOut = { ...candidates[0], evaluation: { score_final: 91, decision: 'RECOMMENDED' }, decision: 'APPROVED' }

const visual: VisualOut = {
  id: 41,
  candidate_id: 21,
  thesis: 'Migrar es recuperar conocimiento operativo',
  concept: 'Dos capas: código visible y reglas ocultas',
  elements: [{ element_id: 'layers', kind: 'diagram', description: 'Dos capas conectadas', rationale: 'Representa “conocimiento operativo” de la tesis' }],
  alt_text: 'Diagrama de código visible sobre reglas operativas ocultas',
  status: 'VISUAL_DRAFT',
  svg_path: null,
}

const publication: PublicationOut = {
  receipt: { id: 51, mode: 'simulated', status: 'SIMULATED_PUBLISHED', candidate_id: 21, visual_id: 41, created_at: '2026-08-09T00:00:03Z', notice: 'no se envió contenido a LinkedIn', remote_id: null },
  candidate_id: 21,
  visual_id: 41,
  mode: 'simulated',
  status: 'SIMULATED_PUBLISHED',
}

const trace: RunDetailOut = {
  run: { ...run, candidates: [approved, candidates[1], candidates[2]] },
  trace_events: [
    { ts: '2026-08-09T00:00:01Z', type: 'prompt_resolved', prompt_id: 'linkedin-candidate-generator@1.0.0', schema_version: '1.0.0', prompt_hash: 'sha256:abc123' },
    { ts: '2026-08-09T00:00:02Z', type: 'evaluation_scored', candidate_id: 21, score_final: 91, content_version: 1 },
    { ts: '2026-08-09T00:00:03Z', type: 'publication_simulated', mode: 'simulated', api_key: 'secret-that-must-not-render' },
  ],
  brief: { thesis: visual.thesis, audience: idea.default_audience, objective: idea.default_objective, evidence: [{ id: 'evidence-1', text: 'Las reglas operativas exceden la sintaxis', type: 'known_facts' }], constraints: [] },
  voice_profile: { version: 'v0', label: 'perfil de voz provisional v0', provisional: true, rules: [] },
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function installHappyPathFetch() {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input)
    const method = init?.method ?? 'GET'
    if (path === '/api/health') return jsonResponse({ status: 'ok', provider: 'demo' })
    if (path === '/api/ideas/demo') return jsonResponse([idea, { ...idea, id: 'demo-2', raw_idea: 'El mainframe conserva reglas críticas' }, { ...idea, id: 'demo-3', raw_idea: 'Modernizar cambia el modelo de riesgo' }])
    if (path === '/api/projects' && method === 'POST') return jsonResponse(project, 201)
    if (path === '/api/projects/11/brief') return jsonResponse({ ...project, status: 'BRIEF_READY' })
    if (path === '/api/projects/11/generate') return jsonResponse(run)
    if (path === '/api/runs/31/evaluate') return jsonResponse(evaluation)
    if (path === '/api/candidates/21/approve') return jsonResponse(approved)
    if (path === '/api/candidates/21/visual') return jsonResponse(visual)
    if (path === '/api/visuals/41/approve') return jsonResponse({ ...visual, status: 'VISUAL_READY' })
    if (path === '/api/candidates/21/publish-simulated') return jsonResponse(publication)
    if (path === '/api/runs/31') return jsonResponse(trace)
    return jsonResponse({ error: { code: 'NOT_FOUND', message: `${method} ${path}`, details: {} } }, 404)
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('Wizard H2 integración', () => {
  it('recorre el happy path real por API hasta recibo y traza honesta', async () => {
    installHappyPathFetch()
    render(<App />)

    expect(await screen.findByText('DEMO_PROVIDER')).toBeTruthy()
    expect(screen.getByText('perfil de voz provisional v0')).toBeTruthy()
    fireEvent.click(await screen.findByText(idea.raw_idea))

    fireEvent.change(await screen.findByLabelText('Tesis única'), { target: { value: visual.thesis } })
    fireEvent.change(screen.getByLabelText('Afirmación'), { target: { value: 'Las reglas operativas exceden la sintaxis' } })
    fireEvent.click(screen.getByText('Agregar evidencia'))
    fireEvent.click(screen.getByText('Guardar brief'))

    fireEvent.click(await screen.findByText('Generar 3 candidatos'))
    expect(await screen.findByText('Compará tres enfoques, no tres paráfrasis')).toBeTruthy()
    expect(document.querySelectorAll('[data-testid^="candidate-"]')).toHaveLength(3)
    expect(screen.getByText('Historia de problema')).toBeTruthy()
    expect(screen.getByText('Marco práctico')).toBeTruthy()
    expect(screen.getByText('Posición argumentada')).toBeTruthy()

    fireEvent.click(screen.getByText('Evaluar candidatos'))
    fireEvent.click(await screen.findByText('Evaluar candidatos'))
    expect((await screen.findAllByText(/RECOMMENDED/)).length).toBeGreaterThan(0)
    expect(document.querySelectorAll('[data-testid="score-breakdown"]')).toHaveLength(3)
    fireEvent.click(screen.getByText('Revisar y seleccionar'))
    fireEvent.click(await screen.findByText('Continuar a aprobación'))

    fireEvent.change(await screen.findByLabelText('Razón de aprobación'), { target: { value: 'La tesis y la evidencia están alineadas.' } })
    fireEvent.click(screen.getByText('Aprobar candidato'))
    fireEvent.click(await screen.findByText('Generar propuesta SVG'))
    expect(await screen.findByText('Visual rationale')).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Razón de la revisión visual'), { target: { value: 'La metáfora representa la tesis.' } })
    fireEvent.click(screen.getByText('Aprobar visual'))
    fireEvent.click(await screen.findByText('Revisar publicación simulada'))

    expect(await screen.findByText('Vista previa, sin ejecutar ningún envío')).toBeTruthy()
    expect(screen.getByText(/SIMULACIÓN/)).toBeTruthy()
    fireEvent.click(screen.getByText('Simular publicación'))
    expect(await screen.findByText('SIMULATED_PUBLISHED')).toBeTruthy()
    expect(document.body.textContent).toContain('no se envió contenido a LinkedIn')
    expect(document.body.textContent).not.toContain('remote_id')
    expect(document.body.textContent).not.toContain('linkedin.com')

    fireEvent.click(screen.getByText('Abrir traza completa'))
    fireEvent.click(await screen.findByText('Cargar traza'))
    expect(await screen.findByText('sha256:abc123')).toBeTruthy()
    expect(screen.getByText('prompt_resolved')).toBeTruthy()
    expect(screen.getByText('evaluation_scored')).toBeTruthy()
    expect(screen.getByText('publication_simulated')).toBeTruthy()
    expect(document.body.textContent).not.toContain('secret-that-must-not-render')
    expect(document.body.textContent).toContain('[REDACTED]')
  })

  it('bloquea doble generación mientras el request está en curso', async () => {
    let resolveGeneration: ((response: Response) => void) | undefined
    const generationResponse = new Promise<Response>((resolve) => { resolveGeneration = resolve })
    const fetchMock = installHappyPathFetch()
    fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input)
      if (path === '/api/projects/11/generate') return generationResponse
      if (path === '/api/health') return jsonResponse({ status: 'ok', provider: 'demo' })
      if (path === '/api/ideas/demo') return jsonResponse([idea])
      if (path === '/api/projects' && init?.method === 'POST') return jsonResponse(project, 201)
      if (path === '/api/projects/11/brief') return jsonResponse({ ...project, status: 'BRIEF_READY' })
      return jsonResponse({ error: { code: 'NOT_FOUND', message: path, details: {} } }, 404)
    })
    render(<App />)
    fireEvent.click(await screen.findByText(idea.raw_idea))
    fireEvent.change(await screen.findByLabelText('Tesis única'), { target: { value: visual.thesis } })
    fireEvent.change(screen.getByLabelText('Afirmación'), { target: { value: 'Evidencia concreta' } })
    fireEvent.click(screen.getByText('Agregar evidencia'))
    fireEvent.click(screen.getByText('Guardar brief'))
    const button = await screen.findByText('Generar 3 candidatos')
    fireEvent.click(button)
    fireEvent.click(button)
    expect(await screen.findByText(/GENERATING:/)).toBeTruthy()
    expect(fetchMock.mock.calls.filter(([input]) => String(input) === '/api/projects/11/generate')).toHaveLength(1)
    resolveGeneration?.(jsonResponse(run))
    expect(await screen.findByText('Compará tres enfoques, no tres paráfrasis')).toBeTruthy()
  })
})

describe('Wizard H2 estados y validaciones', () => {
  it('rechaza una idea manual vacía sin crear proyecto', () => {
    const onSubmit = vi.fn()
    render(<IdeaStep ideas={[]} busy={false} error={null} onRetry={vi.fn()} onSubmit={onSubmit} />)
    fireEvent.change(screen.getByLabelText('Idea propia'), { target: { value: '   ' } })
    fireEvent.submit(screen.getByLabelText('Idea propia').closest('form')!)
    expect(onSubmit).not.toHaveBeenCalled()
    expect(screen.getByRole('alert').textContent).toContain('carácter significativo')
  })

  it('exige tesis y evidencia, y aplica defaults demo', () => {
    const onSubmit = vi.fn()
    render(<BriefStep idea={idea.raw_idea} demo={idea} busy={false} onSubmit={onSubmit} />)
    fireEvent.click(screen.getByText('Guardar brief'))
    expect(screen.getByRole('alert').textContent).toContain('tesis')
    fireEvent.change(screen.getByLabelText('Tesis única'), { target: { value: visual.thesis } })
    fireEvent.click(screen.getByText('Guardar brief'))
    expect(screen.getByRole('alert').textContent).toContain('evidencia')
    fireEvent.change(screen.getByLabelText('Afirmación'), { target: { value: 'Evidencia concreta' } })
    fireEvent.click(screen.getByText('Agregar evidencia'))
    fireEvent.click(screen.getByText('Guardar brief'))
    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ audience: idea.default_audience, objective: idea.default_objective }))
  })

  it('muestra GENERATION_FAILED y reintenta sin fingir éxito', () => {
    const onGenerate = vi.fn()
    render(<GeneratingStep busy={false} error={null} onGenerate={onGenerate} run={{ ...run, status: 'GENERATION_FAILED', candidates: [], error_code: 'INVALID_OUTPUT' }} />)
    expect(screen.getByRole('alert').textContent).toContain('GENERATION_FAILED')
    fireEvent.click(screen.getByText('Reintentar generación'))
    expect(onGenerate).toHaveBeenCalledWith(true)
  })

  it('EVALUATION_PARTIAL no muestra un score completo', () => {
    render(<EvaluateStep candidates={candidates} evaluation={{ candidate_scores: [], decision: { outcome: 'REVISION_REQUIRED', best_candidate_id: null, reason: 'evaluación semántica no disponible', brief_needs_revision: true } }} busy={false} error={null} stale={false} onEvaluate={vi.fn()} onContinue={vi.fn()} />)
    expect(screen.getByRole('alert').textContent).toContain('EVALUATION_PARTIAL')
    expect(screen.queryByTestId('score-breakdown')).toBeNull()
  })

  it('selección alternativa exige razón y editar envía el contenido', () => {
    const onContinue = vi.fn()
    const onEdit = vi.fn()
    render(<ReviewStep candidates={candidates} evaluation={evaluation} busy={false} error={null} onEdit={onEdit} onRevision={vi.fn()} onContinue={onContinue} />)
    fireEvent.click(screen.getAllByRole('radio')[1])
    fireEvent.click(screen.getByText('Continuar a aprobación'))
    expect(screen.getByRole('alert').textContent).toContain('distinto del recomendado')
    fireEvent.change(screen.getByLabelText('Razón de selección alternativa'), { target: { value: 'El marco práctico sirve mejor a esta audiencia.' } })
    fireEvent.click(screen.getByText('Continuar a aprobación'))
    expect(onContinue).toHaveBeenCalledWith(22, 'El marco práctico sirve mejor a esta audiencia.')
    fireEvent.click(screen.getByText('Editar candidato'))
    fireEvent.change(screen.getByLabelText('Hook'), { target: { value: 'Hook editado' } })
    fireEvent.click(screen.getByText('Guardar e invalidar evaluación'))
    expect(onEdit).toHaveBeenCalledWith(22, expect.objectContaining({ hook: 'Hook editado' }))
  })

  it('aprobación exige razón y queda bloqueada con blockers', () => {
    const onApprove = vi.fn()
    const { rerender } = render(<ApproveStep candidate={approved} score={score(21, 91)} selectionReason="" busy={false} error={null} onApprove={onApprove} />)
    fireEvent.click(screen.getByText('Aprobar candidato'))
    expect(screen.getByRole('alert').textContent).toContain('razón')
    rerender(<ApproveStep candidate={approved} score={score(21, 91, true)} selectionReason="" busy={false} error={null} onApprove={onApprove} />)
    expect(screen.getByText('Aprobar candidato')).toHaveProperty('disabled', true)
    expect(screen.getByText('UNSUPPORTED_CLAIM')).toBeTruthy()
  })

  it('visual no se autoaprueba, exige razón y permite regenerar tras rechazo', () => {
    const onApprove = vi.fn()
    const onRegenerate = vi.fn()
    const { rerender } = render(<VisualStep visual={visual} busy={false} error={null} onGenerate={vi.fn()} onApprove={onApprove} onReject={vi.fn()} onRegenerate={onRegenerate} onContinue={vi.fn()} />)
    expect(onApprove).not.toHaveBeenCalled()
    fireEvent.click(screen.getByText('Aprobar visual'))
    expect(screen.getByRole('alert').textContent).toContain('razón')
    rerender(<VisualStep visual={{ ...visual, status: 'VISUAL_REVISION_REQUIRED' }} busy={false} error={null} onGenerate={vi.fn()} onApprove={onApprove} onReject={vi.fn()} onRegenerate={onRegenerate} onContinue={vi.fn()} />)
    fireEvent.click(screen.getByText('Regenerar visual revisado'))
    expect(onRegenerate).toHaveBeenCalledOnce()
  })

  it('publicación y traza mantienen simulación y redacción inequívocas', () => {
    const { rerender } = render(<PublishStep candidate={approved} visual={{ ...visual, status: 'VISUAL_READY' }} publication={publication} busy={false} error={null} onPublish={vi.fn()} onTrace={vi.fn()} />)
    expect(screen.getAllByText(/SIMULACIÓN/).length).toBeGreaterThan(0)
    expect(document.body.textContent).not.toContain('remote_id')
    rerender(<TraceStep trace={trace} busy={false} error={null} onLoad={vi.fn()} />)
    expect(document.body.textContent).not.toContain('secret-that-must-not-render')
    expect(document.body.textContent).toContain('[REDACTED]')
  })
})
