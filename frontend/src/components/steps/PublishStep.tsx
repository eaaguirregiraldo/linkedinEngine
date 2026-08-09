import type { CandidateOut, ErrorBody, PublicationOut, VisualOut } from '../../api/client'
import { Banner } from '../ui/Banner'
import { ErrorBanner } from '../ui/ErrorBanner'
import { ReceiptCard } from '../ui/ReceiptCard'

interface PublishStepProps {
  candidate: CandidateOut
  visual: VisualOut
  publication: PublicationOut | null
  busy: boolean
  error: ErrorBody | null
  onPublish: () => void
  onTrace: () => void
}

export function PublishStep({ candidate, visual, publication, busy, error, onPublish, onTrace }: PublishStepProps) {
  return (
    <section className="step" aria-labelledby="publish-title">
      <p className="step__eyebrow">Paso 9 de 10</p>
      <h2 id="publish-title">Vista previa, sin ejecutar ningún envío</h2>
      <Banner variant="simulation" />
      <div className="publish-preview"><div><p className="publish-preview__hook">{candidate.hook}</p><p>{candidate.body}</p><p><strong>{candidate.cta}</strong></p></div><img src={`/api/visuals/${visual.id}/svg`} alt={visual.alt_text} /></div>
      {error ? <ErrorBanner error={error} /> : null}
      {!publication ? <button className="button button--simulation" type="button" disabled={busy} onClick={onPublish}>{busy ? 'Simulando…' : 'Simular publicación'}</button> : <><ReceiptCard publication={publication} /><button className="button" type="button" onClick={onTrace}>Abrir traza completa</button></>}
    </section>
  )
}
