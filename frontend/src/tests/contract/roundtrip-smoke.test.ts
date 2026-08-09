import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { api, type BriefIn, type CandidateOut, type PublicationOut } from '../../api/client'

const nativeFetch = globalThis.fetch

beforeAll(() => {
  globalThis.fetch = (input, init) => {
    const url = typeof input === 'string' || input instanceof URL ? input.toString() : input.url
    return nativeFetch(new URL(url, 'http://localhost:8000').toString(), init)
  }
})

afterAll(() => {
  globalThis.fetch = nativeFetch
})

type JsonObject = Record<string, unknown>
type JsonSchema = JsonObject & {
  $ref?: string
  type?: string
  properties?: JsonObject
  required?: string[]
  items?: JsonSchema
  enum?: unknown[]
  anyOf?: JsonSchema[]
  oneOf?: JsonSchema[]
  allOf?: JsonSchema[]
}

function isObject(value: unknown): value is JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function schemaAt(document: JsonObject, reference: string): JsonSchema {
  const prefix = '#/'
  if (!reference.startsWith(prefix)) throw new Error(`unsupported schema reference: ${reference}`)
  const value = reference.slice(prefix.length).split('/').reduce<unknown>((current, key) => {
    if (!isObject(current)) return undefined
    return current[key]
  }, document)
  if (!isObject(value)) throw new Error(`schema not found: ${reference}`)
  return value as JsonSchema
}

function validateSchema(
  value: unknown,
  schema: JsonSchema,
  document: JsonObject,
  location = '$',
): string[] {
  if (schema.$ref) return validateSchema(value, schemaAt(document, schema.$ref), document, location)

  if (schema.allOf) {
    return schema.allOf.flatMap((part) => validateSchema(value, part, document, location))
  }
  if (schema.anyOf || schema.oneOf) {
    const alternatives = schema.anyOf ?? schema.oneOf ?? []
    if (alternatives.some((part) => validateSchema(value, part, document, location).length === 0)) {
      return []
    }
    return [`${location} does not match any schema alternative`]
  }
  if (schema.enum && !schema.enum.some((allowed) => Object.is(allowed, value))) {
    return [`${location} is not an allowed enum value`]
  }

  const errors: string[] = []
  if (schema.type === 'object') {
    if (!isObject(value)) return [`${location} must be an object`]
    for (const required of schema.required ?? []) {
      if (!(required in value)) errors.push(`${location}.${required} is required`)
    }
    for (const [key, propertySchema] of Object.entries(schema.properties ?? {})) {
      if (key in value) errors.push(...validateSchema(value[key], propertySchema as JsonSchema, document, `${location}.${key}`))
    }
  } else if (schema.type === 'array') {
    if (!Array.isArray(value)) return [`${location} must be an array`]
    if (schema.items) {
      value.forEach((item, index) => {
        errors.push(...validateSchema(item, schema.items as JsonSchema, document, `${location}[${index}]`))
      })
    }
  } else if (schema.type === 'string' && typeof value !== 'string') {
    errors.push(`${location} must be a string`)
  } else if (schema.type === 'integer' && (!Number.isInteger(value))) {
    errors.push(`${location} must be an integer`)
  } else if (schema.type === 'number' && typeof value !== 'number') {
    errors.push(`${location} must be a number`)
  } else if (schema.type === 'boolean' && typeof value !== 'boolean') {
    errors.push(`${location} must be a boolean`)
  }
  return errors
}

async function liveSchema(): Promise<JsonObject> {
  const response = await fetch('http://localhost:8000/openapi.json')
  expect(response.ok, 'backend vivo requerido en http://localhost:8000').toBe(true)
  const document: unknown = await response.json()
  if (!isObject(document)) throw new Error('OpenAPI response is not an object')
  return document
}

function assertContract<T>(value: T, document: JsonObject, name: string): T {
  const schema = schemaAt(document, `#/components/schemas/${name}`)
  expect(validateSchema(value, schema, document), `${name} response violates OpenAPI schema`).toEqual([])
  return value
}

describe('FE/BE contract round-trip', () => {
  it('executes the real DemoProvider flow through simulated publication', async () => {
    const document = await liveSchema()
    const ideasResponse = await fetch('http://localhost:8000/api/ideas/demo')
    expect(ideasResponse.ok).toBe(true)
    const ideas: unknown = await ideasResponse.json()
    if (!Array.isArray(ideas) || !isObject(ideas[0]) || typeof ideas[0].raw_idea !== 'string') {
      throw new Error('demo ideas contract is empty')
    }

    const project = await api.createProject({ raw_idea: ideas[0].raw_idea, title: 'Contract smoke' })
    const brief: BriefIn = {
      thesis: 'El conocimiento operativo hace segura la modernización del mainframe.',
      audience: 'Equipos COBOL',
      objective: 'Compartir un criterio práctico',
      evidence: [{ id: 'e1', text: 'El conocimiento operativo se acumula durante décadas.', type: 'known_facts' }],
      constraints: [],
    }
    await api.submitBrief(project.id, brief)
    const run = await api.generate(project.id)
    expect(run.provider).toBe('DEMO_PROVIDER')
    const candidates = run.candidates
    expect(candidates).toHaveLength(3)
    if (!candidates) throw new Error('generated run has no candidates')
    candidates.forEach((candidate) => assertContract<CandidateOut>(candidate, document, 'CandidateOut'))

    const evaluation = await api.evaluateRun(run.id)
    assertContract(evaluation, document, 'EvaluationOut')
    const selectedId = evaluation.decision.best_candidate_id
    expect(selectedId).not.toBeNull()
    if (selectedId === null || selectedId === undefined) throw new Error('DemoProvider did not select a candidate')

    await api.approveCandidate(selectedId, 'Aprobación humana del smoke contractual')
    const visual = await api.generateVisual(selectedId)
    await api.approveVisual(visual.id, 'Aprobación humana del visual contractual')
    const publication = await api.publishSimulated(selectedId)
    assertContract<PublicationOut>(publication, document, 'PublicationOut')
    expect(publication.status).toBe('SIMULATED_PUBLISHED')
    expect(publication.receipt.remote_id).toBeNull()
  })

  it('allows the configured frontend origin and rejects an unknown origin', async () => {
    const allowed = await fetch('http://localhost:8000/api/health', {
      headers: { Origin: 'http://localhost:5173' },
    })
    expect(allowed.headers.get('access-control-allow-origin')).toBe('http://localhost:5173')

    const rejected = await fetch('http://localhost:8000/api/health', {
      headers: { Origin: 'http://malicious.example' },
    })
    expect(rejected.headers.get('access-control-allow-origin')).toBeNull()
  })
})
