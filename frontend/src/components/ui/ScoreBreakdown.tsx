import type { CandidateScore, DecisionOut } from '../../api/client'
import { BlockersList } from './BlockersList'
import {
  CALIBRATION_NOTICE,
  DIMENSION_LABELS,
  DIMENSION_WEIGHTS,
  MIN_TOP_GAP,
  THRESHOLD_RECOMMEND,
  THRESHOLD_REVISION_LOW,
  dimension100,
} from './calibration'

/**
 * ScoreBreakdown — desglose transparente de la heurística (H1.3, EVAL-01/08).
 *
 * Muestra: score final (sin decimales), cada dimensión con peso, nota 0-5→100,
 * cita y regla de rúbrica; penalizaciones; fórmula y umbrales de decisión
 * VISIBLES como calibrables (EVAL-08) — no universales.
 */
export interface ScoreBreakdownProps {
  score: CandidateScore
  decision?: DecisionOut
}

export function ScoreBreakdown({ score, decision }: ScoreBreakdownProps) {
  const { dimensions, penalties, score_final, blockers } = score

  return (
    <section className="score-breakdown" data-testid="score-breakdown">
      <h3 className="score-breakdown__title">Desglose de score</h3>

      <p className="score-breakdown__final">
        Score final: <strong>{score_final}</strong>
        {decision ? <span className="score-breakdown__decision"> — {decision.outcome}</span> : null}
      </p>

      <table className="score-breakdown__table">
        <thead>
          <tr>
            <th>Dimensión</th>
            <th>Peso</th>
            <th>Nota</th>
            <th>Cita</th>
          </tr>
        </thead>
        <tbody>
          {(Object.keys(DIMENSION_WEIGHTS) as Array<keyof typeof DIMENSION_WEIGHTS>).map((key) => {
            const dim = dimensions[key]
            if (!dim) return null
            return (
              <tr key={key}>
                <td>{DIMENSION_LABELS[key]}</td>
                <td>{(DIMENSION_WEIGHTS[key] as number).toFixed(2)}</td>
                <td>
                  {dim.rating} / {dimension100(dim.rating)}
                </td>
                <td className="score-breakdown__quote">
                  “{dim.quote}”
                  <span className="score-breakdown__rule"> — {dim.rubric_rule}</span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      {penalties ? (
        <p className="score-breakdown__penalties">
          Penalizaciones: riesgo {penalties.risk} — genéricos {penalties.generic}
        </p>
      ) : null}

      <p className="score-breakdown__formula">
        Fórmula: suma de (dimensión × peso) − penalizaciones; umbrales iniciales:{' '}
        {THRESHOLD_RECOMMEND} (recomendar), {MIN_TOP_GAP} (diferencia mínima),{' '}
        {THRESHOLD_REVISION_LOW} (revisar). {CALIBRATION_NOTICE}
      </p>

      {blockers && blockers.length > 0 ? (
        <BlockersList blockers={blockers} />
      ) : null}
    </section>
  )
}
