import type { CandidateOut } from '../../api/client'
import { Banner } from '../ui/Banner'
import { CandidateCard } from '../ui/CandidateCard'

export function CandidatesStep({ candidates, onContinue }: { candidates: CandidateOut[]; onContinue: () => void }) {
  return (
    <section className="step" aria-labelledby="candidates-title">
      <p className="step__eyebrow">Paso 4 de 10</p>
      <h2 id="candidates-title">Compará tres enfoques, no tres paráfrasis</h2>
      <Banner variant="demo" />
      <div className="candidate-grid">{candidates.map((candidate) => <CandidateCard key={candidate.id} candidate={candidate} />)}</div>
      <button className="button" type="button" onClick={onContinue}>Evaluar candidatos</button>
    </section>
  )
}
