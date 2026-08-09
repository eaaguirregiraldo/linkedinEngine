import { useState } from 'react'
import type { CandidateContent, CandidateOut, ErrorBody, EvaluationOut } from '../../api/client'
import { CandidateCard } from '../ui/CandidateCard'
import { ErrorBanner } from '../ui/ErrorBanner'

interface ReviewStepProps {
  candidates: CandidateOut[]
  evaluation: EvaluationOut
  busy: boolean
  error: ErrorBody | null
  onEdit: (candidateId: number, content: CandidateContent) => void
  onRevision: (candidateId: number, reason: string) => void
  onContinue: (candidateId: number, selectionReason: string) => void
}

export function ReviewStep({ candidates, evaluation, busy, error, onEdit, onRevision, onContinue }: ReviewStepProps) {
  const recommended = evaluation.decision.best_candidate_id
  const [selectedId, setSelectedId] = useState(recommended ?? candidates[0]?.id)
  const selected = candidates.find((item) => item.id === selectedId) ?? candidates[0]
  const [selectionReason, setSelectionReason] = useState('')
  const [revisionReason, setRevisionReason] = useState('')
  const [editing, setEditing] = useState(false)
  const [validation, setValidation] = useState<string | null>(null)

  const continueToApproval = () => {
    if (selected.id !== recommended && !selectionReason.trim()) return setValidation('Explicá por qué elegís un candidato distinto del recomendado.')
    setValidation(null)
    onContinue(selected.id, selectionReason.trim())
  }

  return (
    <section className="step" aria-labelledby="review-title">
      <p className="step__eyebrow">Paso 6 de 10</p>
      <h2 id="review-title">La heurística orienta; vos elegís</h2>
      {error ? <ErrorBanner error={error} /> : null}
      <div className="selection-list" role="radiogroup" aria-label="Seleccionar candidato">
        {candidates.map((candidate) => <label key={candidate.id} className={candidate.id === selected.id ? 'selection selection--active' : 'selection'}><input type="radio" name="candidate" checked={candidate.id === selected.id} onChange={() => setSelectedId(candidate.id)} /><CandidateCard candidate={candidate} />{candidate.id === recommended ? <strong>Recomendado</strong> : null}</label>)}
      </div>
      {selected.id !== recommended ? <label className="field">Razón de selección alternativa<textarea value={selectionReason} onChange={(event) => setSelectionReason(event.target.value)} rows={2} required /></label> : null}
      {validation ? <p className="form-error" role="alert">{validation}</p> : null}
      <div className="action-row"><button className="button button--secondary" type="button" onClick={() => setEditing((value) => !value)}>Editar candidato</button><button className="button" type="button" onClick={continueToApproval} disabled={busy}>Continuar a aprobación</button></div>
      {editing ? <form className="form-card" onSubmit={(event) => { event.preventDefault(); const data = new FormData(event.currentTarget); onEdit(selected.id, { hook: String(data.get('hook')), body: String(data.get('body')), cta: String(data.get('cta')) }) }}><label>Hook<input name="hook" defaultValue={selected.hook} required /></label><label>Cuerpo<textarea name="body" defaultValue={selected.body} rows={8} required /></label><label>CTA<input name="cta" defaultValue={selected.cta} required /></label><button className="button" disabled={busy}>Guardar e invalidar evaluación</button></form> : null}
      <div className="revision-box"><label className="field">Pedir revisión con razón<textarea value={revisionReason} onChange={(event) => setRevisionReason(event.target.value)} rows={2} /></label><button className="button button--secondary" type="button" disabled={busy || !revisionReason.trim()} onClick={() => onRevision(selected.id, revisionReason)}>Solicitar revisión</button></div>
    </section>
  )
}
