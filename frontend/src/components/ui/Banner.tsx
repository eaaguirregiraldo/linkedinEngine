/**
 * Banner — banda persistente de estado (H1.3).
 *
 * - `simulation`: banda "SIMULACIÓN" en toda vista de una publicación
 *   simulada (RUN-03, invariante 1: nunca sugerir publicación real).
 * - `demo`/`openai`: etiqueta el provider real en vistas de generación/evaluación,
 *   aclarando que los datos son demo, no respuesta remota (RUN-06).
 */
export interface BannerProps {
  variant: 'simulation' | 'demo' | 'openai'
}

const TEXT: Record<BannerProps['variant'], string> = {
  simulation: 'SIMULACIÓN — no se envió contenido a LinkedIn',
  demo: 'DEMO_PROVIDER — datos generados localmente, sin llamada GenAI remota',
  openai: 'OPENAI_PROVIDER — respuesta generativa real, validada por el mismo harness',
}

export function Banner({ variant }: BannerProps) {
  return (
    <div className={`banner banner--${variant}`} role="status" data-variant={variant}>
      {TEXT[variant]}
    </div>
  )
}
