import type { ErrorBody, ProviderChoice, RunOut } from '../../api/client'
import { Banner } from '../ui/Banner'
import { ErrorBanner } from '../ui/ErrorBanner'

interface GeneratingStepProps {
  busy: boolean
  run: RunOut | null
  error: ErrorBody | null
  onGenerate: (retry: boolean) => void
  provider?: ProviderChoice
  onProviderChange?: (provider: ProviderChoice) => void
}

export function GeneratingStep({ busy, run, error, onGenerate, provider = 'demo', onProviderChange = () => {} }: GeneratingStepProps) {
  const failed = run?.status === 'GENERATION_FAILED'
  return (
    <section className="step" aria-labelledby="generating-title" aria-busy={busy}>
      <p className="step__eyebrow">Paso 3 de 10</p>
      <h2 id="generating-title">Generá exactamente tres candidatos</h2>
      <fieldset className="provider-choice">
        <legend>Elegí el proveedor antes de generar</legend>
        <label><input type="radio" name="provider" value="demo" checked={provider === 'demo'} disabled={busy} onChange={() => onProviderChange('demo')} /> <strong>DemoProvider</strong> <span>local, determinístico y sin API key</span></label>
        <label><input type="radio" name="provider" value="openai" checked={provider === 'openai'} disabled={busy} onChange={() => onProviderChange('openai')} /> <strong>OpenAI</strong> <span>IA generativa real; usa la key configurada solo en backend</span></label>
      </fieldset>
      <Banner variant={provider === 'openai' ? 'openai' : 'demo'} />
      {busy ? <div className="loading" role="status"><span className="spinner" aria-hidden="true" />GENERATING: validando contrato y guardrails…</div> : null}
      {error ? <ErrorBanner error={error} /> : null}
      {failed ? <p className="failure-state" role="alert">GENERATION_FAILED ({run.error_code ?? 'UNKNOWN'}). El brief sigue intacto.</p> : null}
      <button className="button" type="button" disabled={busy} onClick={() => onGenerate(failed)}>
        {failed ? 'Reintentar generación' : 'Generar 3 candidatos'}
      </button>
    </section>
  )
}
