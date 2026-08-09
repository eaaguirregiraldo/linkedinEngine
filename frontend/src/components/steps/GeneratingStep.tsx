import type { ErrorBody, RunOut } from '../../api/client'
import { Banner } from '../ui/Banner'
import { ErrorBanner } from '../ui/ErrorBanner'

interface GeneratingStepProps {
  busy: boolean
  run: RunOut | null
  error: ErrorBody | null
  onGenerate: (retry: boolean) => void
}

export function GeneratingStep({ busy, run, error, onGenerate }: GeneratingStepProps) {
  const failed = run?.status === 'GENERATION_FAILED'
  return (
    <section className="step" aria-labelledby="generating-title" aria-busy={busy}>
      <p className="step__eyebrow">Paso 3 de 10</p>
      <h2 id="generating-title">Generá exactamente tres candidatos</h2>
      <Banner variant="demo" />
      {busy ? <div className="loading" role="status"><span className="spinner" aria-hidden="true" />GENERATING: validando contrato y guardrails…</div> : null}
      {error ? <ErrorBanner error={error} /> : null}
      {failed ? <p className="failure-state" role="alert">GENERATION_FAILED ({run.error_code ?? 'UNKNOWN'}). El brief sigue intacto.</p> : null}
      <button className="button" type="button" disabled={busy} onClick={() => onGenerate(failed)}>
        {failed ? 'Reintentar generación' : 'Generar 3 candidatos'}
      </button>
    </section>
  )
}
