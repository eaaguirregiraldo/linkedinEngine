/**
 * calibration.ts — fórmula y umbrales de la heurística, EXPUESTOS como
 * constantes versionadas y calibrables (EVAL-08, design §4.4/§4.5).
 *
 * Espejo del dominio: `backend/domain/score.py` (DIMENSION_WEIGHTS) y
 * `backend/domain/blockers.py` (THRESHOLD_RECOMMEND=72, MIN_TOP_GAP=4,
 * THRESHOLD_REVISION_LOW=60). La UI los muestra como INICIALES, no universales.
 */
export const DIMENSION_WEIGHTS = {
  hook: 0.2,
  niche_relevance: 0.2,
  specificity_evidence: 0.2,
  clarity: 0.15,
  conversation_potential: 0.15,
  voice_fit: 0.1,
} as const

export const DIMENSION_LABELS: Record<keyof typeof DIMENSION_WEIGHTS, string> = {
  hook: 'Fuerza del hook',
  niche_relevance: 'Relevancia para el nicho',
  specificity_evidence: 'Especificidad y evidencia',
  clarity: 'Claridad y legibilidad',
  conversation_potential: 'Potencial de conversación',
  voice_fit: 'Ajuste a la voz',
}

export const THRESHOLD_RECOMMEND = 72
export const MIN_TOP_GAP = 4
export const THRESHOLD_REVISION_LOW = 60

export const CALIBRATION_NOTICE =
  'Umbrales iniciales, calibrables con publicaciones aprobadas — no universales.'

/** rating 0..5 → 0..100 (design §4.4: dimension_100 = rating * 20). */
export const dimension100 = (rating: number): number => rating * 20
