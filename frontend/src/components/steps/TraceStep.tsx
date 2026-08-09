import type { ErrorBody, RunDetailOut } from '../../api/client'
import { Banner } from '../ui/Banner'
import { ErrorBanner } from '../ui/ErrorBanner'
import { VoiceBadge } from '../ui/VoiceBadge'

const SENSITIVE = /api[_-]?key|authorization|token|secret|password|credential/i

function safeJson(value: unknown): string {
  return JSON.stringify(value, (key, item: unknown) => SENSITIVE.test(key) ? '[REDACTED]' : item, 2)
}

export function TraceStep({ trace, busy, error, onLoad }: { trace: RunDetailOut | null; busy: boolean; error: ErrorBody | null; onLoad: () => void }) {
  return (
    <section className="step" aria-labelledby="trace-title">
      <p className="step__eyebrow">Paso 10 de 10</p>
      <h2 id="trace-title">Recibo y traza auditable</h2>
      <Banner variant="demo" /><Banner variant="simulation" /><VoiceBadge />
      {error ? <><ErrorBanner error={error} /><button className="button button--secondary" type="button" onClick={onLoad}>Reintentar traza</button></> : null}
      {!trace && !error ? <button className="button" type="button" disabled={busy} onClick={onLoad}>{busy ? 'Cargando traza…' : 'Cargar traza'}</button> : null}
      {trace ? <><dl className="trace-meta"><dt>Proveedor</dt><dd>{trace.run.provider}</dd><dt>Prompt</dt><dd>{trace.run.prompt_version}</dd><dt>Schema</dt><dd>{trace.run.schema_version}</dd><dt>Hash</dt><dd>{trace.run.prompt_hash}</dd></dl><ol className="trace-list">{trace.trace_events?.map((event, index) => <li key={`${event.ts}-${index}`} className={`trace-event trace-event--${event.type}`}><header><strong>{event.type}</strong><time>{event.ts}</time></header><pre>{safeJson(event)}</pre></li>)}</ol></> : null}
    </section>
  )
}
