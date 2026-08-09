import type { CandidateOut } from '../../api/client'

/**
 * AngleTag — etiqueta del ángulo editorial (H1.3, GEN-02).
 * Mapea el literal cerrado del contrato a una etiqueta humana.
 */
export const ANGLE_LABELS: Record<CandidateOut['angle'], string> = {
  'problem-story': 'Historia de problema',
  'practical-framework': 'Marco práctico',
  'argued-position': 'Posición argumentada',
}

export function AngleTag({ angle }: { angle: CandidateOut['angle'] }) {
  return <span className="angle-tag" data-angle={angle}>{ANGLE_LABELS[angle]}</span>
}
