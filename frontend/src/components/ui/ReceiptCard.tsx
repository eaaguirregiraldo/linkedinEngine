import type { PublicationOut } from '../../api/client'
import { Banner } from './Banner'

/**
 * ReceiptCard — recibo LOCAL de publicación simulada (H1.3, SIM-01/02).
 *
 * Invariante SIM-02: el recibo solo contiene datos locales. NUNCA se
 * renderiza `remote_id` (es `null` en simulado) ni URLs/URNs inventadas.
 * Acompaña la banda persistente "SIMULACIÓN" (RUN-03).
 */
export function ReceiptCard({ publication }: { publication: PublicationOut }) {
  const { receipt } = publication
  return (
    <section className="receipt-card" data-testid="receipt-card">
      <Banner variant="simulation" />
      <h3 className="receipt-card__title">Recibo de publicación simulada</h3>
      <dl className="receipt-card__dl">
        <dt>Estado</dt>
        <dd>{receipt.status}</dd>
        <dt>Modo</dt>
        <dd>{receipt.mode}</dd>
        <dt>Nota</dt>
        <dd>{receipt.notice}</dd>
        <dt>Candidato</dt>
        <dd>#{receipt.candidate_id}</dd>
        <dt>Visual</dt>
        <dd>#{receipt.visual_id}</dd>
        <dt>Fecha</dt>
        <dd>{receipt.created_at}</dd>
      </dl>
    </section>
  )
}
