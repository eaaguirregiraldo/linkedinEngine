import { useState } from 'react'
import type { ErrorBody, VisualOut } from '../../api/client'
import { ErrorBanner } from '../ui/ErrorBanner'

interface VisualStepProps {
  visual: VisualOut | null
  busy: boolean
  error: ErrorBody | null
  onGenerate: () => void
  onApprove: (reason: string) => void
  onReject: (reason: string) => void
  onRegenerate: () => void
  onContinue: () => void
}

export function VisualStep({ visual, busy, error, onGenerate, onApprove, onReject, onRegenerate, onContinue }: VisualStepProps) {
  const [reason, setReason] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const requireReason = (action: (value: string) => void) => {
    if (!reason.trim()) return setValidation('La revisión humana del visual exige una razón.')
    setValidation(null)
    action(reason.trim())
  }
  return (
    <section className="step" aria-labelledby="visual-title">
      <p className="step__eyebrow">Paso 8 de 10</p>
      <h2 id="visual-title">El visual argumenta la tesis</h2>
      {error ? <ErrorBanner error={error} /> : null}
      {!visual ? <button className="button" type="button" disabled={busy} onClick={onGenerate}>{busy ? 'Generando SVG…' : 'Generar propuesta SVG'}</button> : null}
      {visual ? <div className="visual-review"><img src={`/api/visuals/${visual.id}/svg`} alt={visual.alt_text} /><div><p className="status-chip">{visual.status}</p><h3>{visual.concept}</h3><p><strong>Alt text:</strong> {visual.alt_text}</p><h4>Visual rationale</h4><ul>{visual.elements?.map((element) => <li key={element.element_id}><strong>{element.description}</strong>: {element.rationale}</li>)}</ul></div></div> : null}
      {visual?.status === 'VISUAL_DRAFT' ? <><label className="field">Razón de la revisión visual<textarea value={reason} onChange={(event) => setReason(event.target.value)} rows={3} required /></label>{validation ? <p className="form-error" role="alert">{validation}</p> : null}<div className="action-row"><button className="button" type="button" disabled={busy} onClick={() => requireReason(onApprove)}>Aprobar visual</button><button className="button button--danger" type="button" disabled={busy} onClick={() => requireReason(onReject)}>Rechazar visual</button></div></> : null}
      {visual?.status === 'VISUAL_REVISION_REQUIRED' ? <button className="button" type="button" disabled={busy} onClick={onRegenerate}>Regenerar visual revisado</button> : null}
      {visual?.status === 'VISUAL_READY' ? <button className="button" type="button" onClick={onContinue}>Revisar publicación simulada</button> : null}
    </section>
  )
}
