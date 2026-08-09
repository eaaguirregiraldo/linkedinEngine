import { useState } from 'react'
import type { CandidateOut, CandidateScore, ErrorBody } from '../../api/client'
import { BlockersList } from '../ui/BlockersList'
import { CandidateCard } from '../ui/CandidateCard'
import { ErrorBanner } from '../ui/ErrorBanner'

interface ApproveStepProps {
  candidate: CandidateOut
  score?: CandidateScore
  selectionReason: string
  busy: boolean
  error: ErrorBody | null
  onApprove: (reason: string) => void
}

export function ApproveStep({ candidate, score, selectionReason, busy, error, onApprove }: ApproveStepProps) {
  const [reason, setReason] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const blockers = score?.blockers ?? []
  const submit = () => {
    if (blockers.length) return setValidation('Resolvé los blockers antes de aprobar.')
    if (!reason.trim()) return setValidation('La aprobación humana exige una razón.')
    setValidation(null)
    onApprove(selectionReason ? `Selección alternativa: ${selectionReason}. Aprobación: ${reason.trim()}` : reason.trim())
  }
  return (
    <section className="step" aria-labelledby="approve-title">
      <p className="step__eyebrow">Paso 7 de 10</p>
      <h2 id="approve-title">Aprobación humana explícita</h2>
      {candidate.decision === 'REVISION_REQUIRED' ? <p className="override-notice">Override desde REVISION_REQUIRED: justificá la decisión editorial.</p> : null}
      <CandidateCard candidate={candidate} />
      <BlockersList blockers={blockers} />
      {error ? <ErrorBanner error={error} /> : null}
      {validation ? <p className="form-error" role="alert">{validation}</p> : null}
      <label className="field">Razón de aprobación<textarea rows={3} value={reason} onChange={(event) => setReason(event.target.value)} required /></label>
      <button className="button" type="button" disabled={busy || blockers.length > 0} onClick={submit}>{busy ? 'Aprobando…' : 'Aprobar candidato'}</button>
    </section>
  )
}
