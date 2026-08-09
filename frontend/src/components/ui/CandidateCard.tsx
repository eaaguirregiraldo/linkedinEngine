import type { CandidateOut } from '../../api/client'
import { AngleTag } from './AngleTag'

/**
 * CandidateCard — tarjeta de comparación de un candidato (H1.3).
 * Muestra ángulo, hook, body, cta, claims y versión; el resumen de
 * evaluación (score + decisión) si ya existe.
 */
export function CandidateCard({ candidate }: { candidate: CandidateOut }) {
  return (
    <article className="candidate-card" data-testid={`candidate-${candidate.id}`}>
      <header className="candidate-card__header">
        <AngleTag angle={candidate.angle} />
        <span className="candidate-card__version">v{candidate.content_version}</span>
      </header>
      <h3 className="candidate-card__hook">{candidate.hook}</h3>
      <p className="candidate-card__body">{candidate.body}</p>
      <p className="candidate-card__cta">{candidate.cta}</p>
      {candidate.claims && candidate.claims.length > 0 ? (
        <ul className="candidate-card__claims">
          {candidate.claims.map((claim, i) => (
            <li key={i}>
              {claim.text} <span className="candidate-card__support">({claim.support})</span>
            </li>
          ))}
        </ul>
      ) : null}
      {candidate.evaluation ? (
        <footer className="candidate-card__score">
          Score: {candidate.evaluation.score_final}
          {candidate.evaluation.decision ? ` — ${candidate.evaluation.decision}` : ''}
        </footer>
      ) : null}
    </article>
  )
}
