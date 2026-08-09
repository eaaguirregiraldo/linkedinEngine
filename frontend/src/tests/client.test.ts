import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, toErrorBody } from '../api/client'
import type { BriefIn, ErrorBody, ProjectOut } from '../api/client'

/** Fake minimal de Response (el client solo usa ok/status/json). */
function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response
}

describe('api/client — fetch wrapper tipado contra schema.d.ts (H1.1)', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('expone ErrorBody {code,message,details} ante un 409 (API-04)', async () => {
    const body: ErrorBody = {
      error: {
        code: 'STATE_TRANSITION_REJECTED',
        message: 'se requiere: una evaluacion previa del candidato',
        details: {
          fields: ['evaluation'],
          code: 'MISSING_REQUIREMENT',
        },
      },
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(409, body)))

    let caught: unknown
    try {
      await api.submitBrief(1, {
        thesis: 'tesis',
        audience: '',
        objective: '',
        evidence: [],
      })
    } catch (err) {
      caught = err
    }

    expect(caught).toBeInstanceOf(ApiError)
    const err = caught as ApiError
    expect(err.status).toBe(409)
    expect(err.body.error.code).toBe('STATE_TRANSITION_REJECTED')
    expect(err.body.error.message).toContain('se requiere')
    expect(err.body.error.details).toEqual({
      fields: ['evaluation'],
      code: 'MISSING_REQUIREMENT',
    })
  })

  it('POST /api/projects con cuerpo JSON y response tipada (success)', async () => {
    const project: ProjectOut = {
      id: 1,
      raw_idea: 'Migrar COBOL no es traducir sintaxis',
      title: null,
      status: 'IDEA',
      created_at: '2026-08-09T00:00:00Z',
      updated_at: '2026-08-09T00:00:00Z',
    }
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(201, project))
    vi.stubGlobal('fetch', fetchMock)

    const result = await api.createProject({ raw_idea: project.raw_idea })

    expect(result.id).toBe(1)
    expect(result.status).toBe('IDEA')
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/projects')
    expect(init.method).toBe('POST')
    expect(JSON.parse(String(init.body))).toEqual({ raw_idea: project.raw_idea })
  })

  it('error de red (fetch rechaza) se normaliza a ErrorBody NETWORK_ERROR', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    let caught: unknown
    try {
      await api.health()
    } catch (err) {
      caught = err
    }

    const err = caught as ApiError
    expect(err).toBeInstanceOf(ApiError)
    expect(err.body.error.code).toBe('NETWORK_ERROR')
    expect(err.body.error.message).toContain('backend')
  })

  it('toErrorBody normaliza ApiError / Error / desconocido', () => {
    const apiErr = new ApiError(409, {
      error: { code: 'CONFLICT', message: 'conflicto', details: {} },
    })
    expect(toErrorBody(apiErr).error.code).toBe('CONFLICT')

    expect(toErrorBody(new Error('boom')).error.code).toBe('ERROR')
    expect(toErrorBody(new Error('boom')).error.message).toBe('boom')

    expect(toErrorBody('texto suelto').error.code).toBe('ERROR')
  })

  it('visualSvgUrl devuelve la ruta del SVG sin parsear JSON', () => {
    expect(api.visualSvgUrl(42)).toBe('/api/visuals/42/svg')
  })
})

const _briefTypeCheck: BriefIn = {
  thesis: 't',
  audience: '',
  objective: '',
  evidence: [],
}
void _briefTypeCheck
