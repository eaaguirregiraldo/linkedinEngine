/**
 * client.ts — fetch wrapper TIPADO contra `schema.d.ts` (H1.1).
 *
 * Reglas (design §5.2, ADR-003):
 *  - Los tipos vienen SOLO de `schema.d.ts` (generado por openapi-typescript
 *    desde /openapi.json del backend). PROHIBIDO definir DTOs de API a mano.
 *  - Errores no-2xx → `ApiError` con `body: ErrorBody` tipado (API-04).
 *  - Error de red → `NETWORK_ERROR` normalizado al mismo envelope.
 *  - Rutas relativas `/api/*`: en dev el proxy de Vite resuelve a :8000.
 */
import type { components } from './schema'

// --- Tipos reexportados desde el contrato canónico (sin duplicar) -----------
export type Blocker = components['schemas']['Blocker']
export type BriefIn = components['schemas']['BriefIn']
export type CandidateContent = components['schemas']['CandidateContent']
export type CandidateOut = components['schemas']['CandidateOut']
export type CandidateScore = components['schemas']['CandidateScore']
export type DecisionOut = components['schemas']['DecisionOut']
export type DemoIdeaOut = components['schemas']['DemoIdeaOut']
export type ErrorBody = components['schemas']['ErrorBody']
export type EvidenceItem = components['schemas']['EvidenceItem']
export type EvaluationOut = components['schemas']['EvaluationOut']
export type HealthOut = components['schemas']['HealthOut']
export type ProjectCreate = components['schemas']['ProjectCreate']
export type ProjectDetailOut = components['schemas']['ProjectDetailOut']
export type ProjectOut = components['schemas']['ProjectOut']
export type PublicationOut = components['schemas']['PublicationOut']
export type ReasonIn = components['schemas']['ReasonIn']
export type ReceiptOut = components['schemas']['ReceiptOut']
export type RunDetailOut = components['schemas']['RunDetailOut']
export type RunOut = components['schemas']['RunOut']
export type VisualOut = components['schemas']['VisualOut']

// --- Error tipado -----------------------------------------------------------

/** Error de API con el envelope canónico `ErrorBody` (design §12). */
export class ApiError extends Error {
  readonly status: number
  readonly body: ErrorBody

  constructor(status: number, body: ErrorBody) {
    super(body.error?.message ?? `HTTP ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

/** Normaliza cualquier error a `ErrorBody` para la UI (ErrorBanner). */
export function toErrorBody(err: unknown): ErrorBody {
  if (err instanceof ApiError) return err.body
  if (err instanceof Error) {
    return { error: { code: 'ERROR', message: err.message, details: {} } }
  }
  return {
    error: { code: 'ERROR', message: 'Ocurrió un error inesperado', details: {} },
  }
}

// --- Core del request -------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, init)
  } catch {
    throw new ApiError(0, {
      error: {
        code: 'NETWORK_ERROR',
        message:
          'No se pudo conectar con la API local. ¿Está el backend levantado en :8000? (npm run dev)',
        details: {},
      },
    })
  }

  if (!res.ok) {
    let body: ErrorBody
    try {
      body = (await res.json()) as ErrorBody
    } catch {
      body = {
        error: {
          code: 'UNEXPECTED_ERROR',
          message: `La API respondió ${res.status} sin cuerpo JSON legible.`,
          details: {},
        },
      }
    }
    throw new ApiError(res.status, body)
  }

  return (await res.json()) as T
}

function jsonInit(method: string, body?: unknown): RequestInit {
  return body === undefined
    ? { method, headers: { Accept: 'application/json' } }
    : {
        method,
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(body),
      }
}

// --- Helpers por endpoint (design §5.4) -------------------------------------

export const api = {
  // meta
  health: () => request<HealthOut>('/api/health'),

  // projects
  listDemoIdeas: () => request<DemoIdeaOut[]>('/api/ideas/demo'),
  listProjects: () => request<ProjectOut[]>('/api/projects'),
  createProject: (body: ProjectCreate) =>
    request<ProjectOut>('/api/projects', jsonInit('POST', body)),
  submitBrief: (projectId: number, body: BriefIn) =>
    request<ProjectOut>(`/api/projects/${projectId}/brief`, jsonInit('POST', body)),
  getProject: (projectId: number) =>
    request<ProjectDetailOut>(`/api/projects/${projectId}`),

  // runs
  getRun: (runId: number) => request<RunDetailOut>(`/api/runs/${runId}`),
  evaluateRun: (runId: number) =>
    request<EvaluationOut>(`/api/runs/${runId}/evaluate`, jsonInit('POST')),

  // candidates
  generate: (projectId: number) =>
    request<RunOut>(`/api/projects/${projectId}/generate`, jsonInit('POST')),
  retryGenerate: (projectId: number) =>
    request<RunOut>(`/api/projects/${projectId}/retry-generate`, jsonInit('POST')),
  editCandidate: (candidateId: number, content: CandidateContent) =>
    request<CandidateOut>(`/api/candidates/${candidateId}/edit`, jsonInit('POST', { content })),
  requestRevision: (candidateId: number, reason: string) =>
    request<CandidateOut>(`/api/candidates/${candidateId}/request-revision`, jsonInit('POST', { reason } satisfies ReasonIn)),
  approveCandidate: (candidateId: number, reason: string) =>
    request<CandidateOut>(`/api/candidates/${candidateId}/approve`, jsonInit('POST', { reason } satisfies ReasonIn)),
  generateVisual: (candidateId: number) =>
    request<VisualOut>(`/api/candidates/${candidateId}/visual`, jsonInit('POST')),
  publishSimulated: (candidateId: number) =>
    request<PublicationOut>(`/api/candidates/${candidateId}/publish-simulated`, jsonInit('POST')),

  // visuals
  approveVisual: (visualId: number, reason: string) =>
    request<VisualOut>(`/api/visuals/${visualId}/approve`, jsonInit('POST', { reason } satisfies ReasonIn)),
  rejectVisual: (visualId: number, reason: string) =>
    request<VisualOut>(`/api/visuals/${visualId}/reject`, jsonInit('POST', { reason } satisfies ReasonIn)),
  regenerateVisual: (visualId: number) =>
    request<VisualOut>(`/api/visuals/${visualId}/regenerate`, jsonInit('POST')),
  /** Ruta del SVG para usar en `<img src>` (la respuesta NO es JSON). */
  visualSvgUrl: (visualId: number) => `/api/visuals/${visualId}/svg`,
}
