import { useState } from 'react'
import type { BriefIn, DemoIdeaOut, EvidenceItem } from '../../api/client'
import { VoiceBadge } from '../ui/VoiceBadge'

interface BriefStepProps {
  idea: string
  demo?: DemoIdeaOut
  busy: boolean
  onSubmit: (brief: BriefIn) => void
}

export function BriefStep({ idea, demo, busy, onSubmit }: BriefStepProps) {
  const [error, setError] = useState<string | null>(null)
  const [evidence, setEvidence] = useState<EvidenceItem[]>([])

  const addEvidence = (form: HTMLFormElement) => {
    const data = new FormData(form)
    const text = String(data.get('evidenceText') ?? '').trim()
    const type = String(data.get('evidenceType')) as EvidenceItem['type']
    if (!text) return
    setEvidence((items) => [...items, { id: `evidence-${items.length + 1}`, text, type }])
    form.reset()
  }

  const submit = (formData: FormData) => {
    const thesis = String(formData.get('thesis') ?? '').trim()
    if (!thesis) return setError('Ingresá una tesis única antes de continuar.')
    if (evidence.length === 0) return setError('Agregá al menos una evidencia, opinión o pregunta abierta.')
    setError(null)
    onSubmit({
      thesis,
      audience: String(formData.get('audience') ?? '').trim() || demo?.default_audience || 'líderes de modernización',
      objective: String(formData.get('objective') ?? '').trim() || demo?.default_objective || 'abrir una conversación técnica informada',
      evidence,
      constraints: String(formData.get('constraints') ?? '').split('\n').map((item) => item.trim()).filter(Boolean),
    })
  }

  return (
    <section className="step" aria-labelledby="brief-title">
      <p className="step__eyebrow">Paso 2 de 10</p>
      <h2 id="brief-title">Convertí la idea en un brief verificable</h2>
      <blockquote>{idea}</blockquote>
      <VoiceBadge />
      <form className="form-grid" noValidate onSubmit={(event) => { event.preventDefault(); submit(new FormData(event.currentTarget)) }}>
        <label className="field field--wide">Tesis única<textarea name="thesis" rows={3} required /></label>
        <label className="field">Audiencia<input name="audience" defaultValue={demo?.default_audience} placeholder="Default demo si queda vacío" /></label>
        <label className="field">Objetivo<input name="objective" defaultValue={demo?.default_objective} placeholder="Default demo si queda vacío" /></label>
        <label className="field field--wide">Restricciones, una por línea<textarea name="constraints" rows={3} /></label>
        {error ? <p className="form-error field--wide" role="alert">{error}</p> : null}
        <div className="field--wide evidence-list" aria-live="polite">
          <h3>Evidencia clasificada ({evidence.length})</h3>
          {evidence.map((item) => <p key={item.id}><strong>{item.type}</strong>: {item.text}</p>)}
        </div>
        <button className="button field--wide" disabled={busy}>{busy ? 'Guardando brief…' : 'Guardar brief'}</button>
      </form>
      <form className="evidence-form" onSubmit={(event) => { event.preventDefault(); addEvidence(event.currentTarget) }}>
        <label className="field">Tipo<select name="evidenceType" defaultValue="known_facts"><option value="known_facts">Hecho conocido</option><option value="author_opinions">Opinión del autor</option><option value="open_questions">Pregunta abierta</option></select></label>
        <label className="field">Afirmación<input name="evidenceText" required /></label>
        <button className="button button--secondary" type="submit">Agregar evidencia</button>
      </form>
    </section>
  )
}
