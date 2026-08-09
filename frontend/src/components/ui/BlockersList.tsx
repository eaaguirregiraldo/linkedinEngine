import type { Blocker } from '../../api/client'

/**
 * BlockersList — lista de blockers de evidencia/seguridad (H1.3, EVAL-05).
 * Cada blocker muestra code + message + detalle accionable.
 */
export function BlockersList({ blockers }: { blockers: Blocker[] }) {
  if (blockers.length === 0) return null
  return (
    <ul className="blockers-list" data-testid="blockers-list">
      {blockers.map((b) => (
        <li key={`${b.code}-${b.message}`} className="blockers-list__item">
          <strong>{b.code}</strong>
          {': '}
          {b.message}
          {b.detail ? <span className="blockers-list__detail"> — {b.detail}</span> : null}
        </li>
      ))}
    </ul>
  )
}
