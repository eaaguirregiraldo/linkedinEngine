import type { CandidateOut, ErrorBody, EvaluationOut, ProviderChoice } from '../../api/client'
import { Banner } from '../ui/Banner'
import { ErrorBanner } from '../ui/ErrorBanner'
import { ScoreBreakdown } from '../ui/ScoreBreakdown'

interface EvaluateStepProps {
  candidates: CandidateOut[]
  evaluation: EvaluationOut | null
  busy: boolean
  error: ErrorBody | null
  stale: boolean
  onEvaluate: () => void
  onContinue: () => void
  provider?: ProviderChoice
}

export function EvaluateStep({ candidates, evaluation, busy, error, stale, onEvaluate, onContinue, provider = 'demo' }: EvaluateStepProps) {
  const partial = evaluation !== null && evaluation.candidate_scores.length === 0
  return (
    <section className="step" aria-labelledby="evaluate-title" aria-busy={busy}>
      <p className="step__eyebrow">Paso 5 de 10</p>
      <h2 id="evaluate-title">Evaluación explicable, no predicción de viralidad</h2>
      <Banner variant={provider === 'openai' ? 'openai' : 'demo'} />
      {stale ? <p className="notice" role="status">La edición invalidó la evaluación anterior. Reevaluá antes de aprobar.</p> : null}
      {error ? <ErrorBanner error={error} /> : null}
      {partial ? <div className="partial-state" role="alert"><strong>EVALUATION_PARTIAL</strong><p>Evaluación semántica no disponible. No se fabricó un score completo.</p></div> : null}
      {evaluation && !partial ? <div className="score-grid">{evaluation.candidate_scores.map((score) => <ScoreBreakdown key={score.candidate_id} score={score} decision={score.candidate_id === evaluation.decision.best_candidate_id ? evaluation.decision : undefined} />)}</div> : null}
      {!evaluation ? <button className="button" type="button" disabled={busy} onClick={onEvaluate}>{busy ? 'EVALUATING…' : stale ? 'Reevaluar candidatos' : 'Evaluar candidatos'}</button> : null}
      {evaluation && !partial ? <><p className={`decision decision--${evaluation.decision.outcome.toLowerCase()}`}><strong>{evaluation.decision.outcome}</strong>: {evaluation.decision.reason}</p><button className="button" type="button" onClick={onContinue}>Revisar y seleccionar</button></> : null}
      <span className="sr-only">{candidates.length} candidatos disponibles</span>
    </section>
  )
}
