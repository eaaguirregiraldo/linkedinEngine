import { useState } from 'react'
import type { DemoIdeaOut, ErrorBody } from '../../api/client'
import { ErrorBanner } from '../ui/ErrorBanner'

interface IdeaStepProps {
  ideas: DemoIdeaOut[]
  busy: boolean
  error: ErrorBody | null
  onRetry: () => void
  onSubmit: (idea: string, demo?: DemoIdeaOut) => void
}

export function IdeaStep({ ideas, busy, error, onRetry, onSubmit }: IdeaStepProps) {
  const [manualError, setManualError] = useState<string | null>(null)
  const submitManual = (formData: FormData) => {
    const idea = String(formData.get('idea') ?? '').trim().replace(/\s+/g, ' ')
    if (!idea) return setManualError('Escribí una idea con al menos un carácter significativo.')
    setManualError(null)
    onSubmit(idea)
  }

  return (
    <section className="step" aria-labelledby="idea-title">
      <p className="step__eyebrow">Paso 1 de 10</p>
      <h2 id="idea-title">Elegí el punto de partida</h2>
      <p className="step__lead">Usá una idea demo reproducible o escribí una propia.</p>
      {error ? <><ErrorBanner error={error} /><button type="button" className="button button--secondary" onClick={onRetry} disabled={busy}>Reintentar carga</button></> : null}
      <div className="idea-grid" aria-label="Ideas demo">
        {ideas.map((idea) => (
          <button key={idea.id} type="button" className="idea-card" disabled={busy} onClick={() => onSubmit(idea.raw_idea, idea)}>
            <span className="idea-card__label">Idea demo</span>
            <span>{idea.raw_idea}</span>
          </button>
        ))}
      </div>
      <form className="form-card" noValidate onSubmit={(event) => { event.preventDefault(); submitManual(new FormData(event.currentTarget)) }}>
        <label htmlFor="manual-idea">Idea propia</label>
        <textarea id="manual-idea" name="idea" rows={4} required aria-describedby="manual-idea-help" />
        <small id="manual-idea-help">No se crea ningún proyecto si la idea está vacía.</small>
        {manualError ? <p className="form-error" role="alert">{manualError}</p> : null}
        <button className="button" disabled={busy}>{busy ? 'Creando…' : 'Usar esta idea'}</button>
      </form>
    </section>
  )
}
