import type { ErrorBody } from '../../api/client'

/**
 * ErrorBanner — error estructurado y accionable (H1.3, API-04).
 * Muestra code + message + detalle (cuando aplica) del envelope `ErrorBody`.
 */
export function ErrorBanner({ error }: { error: ErrorBody }) {
  const { code, message, details } = error.error
  const detailText =
    details && typeof details === 'object' && Object.keys(details).length > 0
      ? JSON.stringify(details)
      : null
  return (
    <div className="error-banner" role="alert" data-code={code}>
      <p className="error-banner__code">{code}</p>
      <p className="error-banner__message">{message}</p>
      {detailText ? <pre className="error-banner__details">{detailText}</pre> : null}
    </div>
  )
}
