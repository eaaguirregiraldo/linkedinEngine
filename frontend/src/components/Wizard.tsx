import { useEffect, useState } from 'react'
import {
  api,
  toErrorBody,
  type BriefIn,
  type CandidateContent,
  type CandidateOut,
  type DemoIdeaOut,
  type EvaluationOut,
  type ProjectOut,
  type PublicationOut,
  type RunDetailOut,
  type RunOut,
  type VisualOut,
} from '../api/client'
import { useAsync } from '../hooks/useAsync'
import { ApproveStep } from './steps/ApproveStep'
import { BriefStep } from './steps/BriefStep'
import { CandidatesStep } from './steps/CandidatesStep'
import { EvaluateStep } from './steps/EvaluateStep'
import { GeneratingStep } from './steps/GeneratingStep'
import { IdeaStep } from './steps/IdeaStep'
import { PublishStep } from './steps/PublishStep'
import { ReviewStep } from './steps/ReviewStep'
import { TraceStep } from './steps/TraceStep'
import { VisualStep } from './steps/VisualStep'

const STEP_LABELS = ['Idea', 'Brief', 'Generar', 'Candidatos', 'Evaluación', 'Revisión', 'Aprobación', 'Visual', 'Publicar', 'Traza']

export function Wizard() {
  const [step, setStep] = useState(0)
  const [demo, setDemo] = useState<DemoIdeaOut>()
  const [project, setProject] = useState<ProjectOut | null>(null)
  const [run, setRun] = useState<RunOut | null>(null)
  const [candidates, setCandidates] = useState<CandidateOut[]>([])
  const [evaluation, setEvaluation] = useState<EvaluationOut | null>(null)
  const [evaluationStale, setEvaluationStale] = useState(false)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectionReason, setSelectionReason] = useState('')
  const [visual, setVisual] = useState<VisualOut | null>(null)
  const [publication, setPublication] = useState<PublicationOut | null>(null)
  const [trace, setTrace] = useState<RunDetailOut | null>(null)

  const ideasRequest = useAsync<DemoIdeaOut[]>()
  const projectRequest = useAsync<ProjectOut>()
  const briefRequest = useAsync<ProjectOut>()
  const generationRequest = useAsync<RunOut>()
  const evaluationRequest = useAsync<EvaluationOut>()
  const editRequest = useAsync<CandidateOut>()
  const revisionRequest = useAsync<CandidateOut>()
  const approvalRequest = useAsync<CandidateOut>()
  const visualRequest = useAsync<VisualOut>()
  const publicationRequest = useAsync<PublicationOut>()
  const traceRequest = useAsync<RunDetailOut>()

  const loadIdeas = () => { void ideasRequest.run(api.listDemoIdeas) }
  useEffect(loadIdeas, [])

  const createProject = async (rawIdea: string, selectedDemo?: DemoIdeaOut) => {
    const result = await projectRequest.run(() => api.createProject({ raw_idea: rawIdea }))
    if (!result) return
    setDemo(selectedDemo)
    setProject(result)
    setStep(1)
  }

  const submitBrief = async (brief: BriefIn) => {
    if (!project) return
    const result = await briefRequest.run(() => api.submitBrief(project.id, brief))
    if (!result) return
    setProject(result)
    setStep(2)
  }

  const generate = async (retry: boolean) => {
    if (!project) return
    const result = await generationRequest.run(() => retry ? api.retryGenerate(project.id) : api.generate(project.id))
    if (!result) return
    setRun(result)
    if (result.status === 'GENERATION_FAILED') return
    if (result.candidates?.length !== 3) throw new Error('El contrato de generación no devolvió exactamente 3 candidatos.')
    setCandidates(result.candidates)
    setStep(3)
  }

  const evaluate = async () => {
    if (!run) return
    const result = await evaluationRequest.run(() => api.evaluateRun(run.id))
    if (!result) return
    setEvaluation(result)
    setEvaluationStale(false)
  }

  const editCandidate = async (candidateId: number, content: CandidateContent) => {
    const result = await editRequest.run(() => api.editCandidate(candidateId, content))
    if (!result) return
    setCandidates((items) => items.map((item) => item.id === candidateId ? result : item))
    setEvaluation(null)
    setEvaluationStale(true)
    setStep(4)
  }

  const requestRevision = async (candidateId: number, reason: string) => {
    const result = await revisionRequest.run(() => api.requestRevision(candidateId, reason))
    if (!result) return
    setCandidates((items) => items.map((item) => item.id === candidateId ? result : item))
    setSelectedId(candidateId)
    setSelectionReason(reason.trim())
    setStep(6)
  }

  const selectCandidate = (candidateId: number, reason: string) => {
    setSelectedId(candidateId)
    setSelectionReason(reason)
    setStep(6)
  }

  const approve = async (reason: string) => {
    if (selectedId === null) return
    const result = await approvalRequest.run(() => api.approveCandidate(selectedId, reason))
    if (!result) return
    setCandidates((items) => items.map((item) => item.id === selectedId ? result : item))
    setStep(7)
  }

  const generateVisual = async () => {
    if (selectedId === null) return
    const result = await visualRequest.run(() => api.generateVisual(selectedId))
    if (result) setVisual(result)
  }

  const approveVisual = async (reason: string) => {
    if (!visual) return
    const result = await visualRequest.run(() => api.approveVisual(visual.id, reason))
    if (result) setVisual(result)
  }

  const rejectVisual = async (reason: string) => {
    if (!visual) return
    const result = await visualRequest.run(() => api.rejectVisual(visual.id, reason))
    if (result) setVisual(result)
  }

  const regenerateVisual = async () => {
    if (!visual) return
    const result = await visualRequest.run(() => api.regenerateVisual(visual.id))
    if (result) setVisual(result)
  }

  const publish = async () => {
    if (selectedId === null) return
    const result = await publicationRequest.run(() => api.publishSimulated(selectedId))
    if (result) setPublication(result)
  }

  const loadTrace = async () => {
    if (!run) return
    const result = await traceRequest.run(() => api.getRun(run.id))
    if (result) setTrace(result)
  }

  const selected = candidates.find((candidate) => candidate.id === selectedId)
  const selectedScore = evaluation?.candidate_scores.find((score) => score.candidate_id === selectedId)

  return (
    <main className="wizard">
      <nav className="wizard-progress" aria-label="Progreso editorial">
        <ol>{STEP_LABELS.map((label, index) => <li key={label} className={index === step ? 'is-current' : index < step ? 'is-complete' : ''} aria-current={index === step ? 'step' : undefined}><span>{index + 1}</span>{label}</li>)}</ol>
      </nav>
      {step === 0 ? <IdeaStep ideas={ideasRequest.data ?? []} busy={ideasRequest.busy || projectRequest.busy} error={ideasRequest.error ? toErrorBody(ideasRequest.error) : projectRequest.error ? toErrorBody(projectRequest.error) : null} onRetry={loadIdeas} onSubmit={(idea, selectedDemo) => { void createProject(idea, selectedDemo) }} /> : null}
      {step === 1 && project ? <BriefStep idea={project.raw_idea} demo={demo} busy={briefRequest.busy} onSubmit={(brief) => { void submitBrief(brief) }} /> : null}
      {step === 2 ? <GeneratingStep busy={generationRequest.busy} run={run} error={generationRequest.error ? toErrorBody(generationRequest.error) : null} onGenerate={(retry) => { void generate(retry) }} /> : null}
      {step === 3 ? <CandidatesStep candidates={candidates} onContinue={() => setStep(4)} /> : null}
      {step === 4 ? <EvaluateStep candidates={candidates} evaluation={evaluation} busy={evaluationRequest.busy} error={evaluationRequest.error ? toErrorBody(evaluationRequest.error) : null} stale={evaluationStale} onEvaluate={() => { void evaluate() }} onContinue={() => setStep(5)} /> : null}
      {step === 5 && evaluation ? <ReviewStep candidates={candidates} evaluation={evaluation} busy={editRequest.busy || revisionRequest.busy} error={editRequest.error ? toErrorBody(editRequest.error) : revisionRequest.error ? toErrorBody(revisionRequest.error) : null} onEdit={(id, content) => { void editCandidate(id, content) }} onRevision={(id, reason) => { void requestRevision(id, reason) }} onContinue={selectCandidate} /> : null}
      {step === 6 && selected ? <ApproveStep candidate={selected} score={selectedScore} selectionReason={selectionReason} busy={approvalRequest.busy} error={approvalRequest.error ? toErrorBody(approvalRequest.error) : null} onApprove={(reason) => { void approve(reason) }} /> : null}
      {step === 7 ? <VisualStep visual={visual} busy={visualRequest.busy} error={visualRequest.error ? toErrorBody(visualRequest.error) : null} onGenerate={() => { void generateVisual() }} onApprove={(reason) => { void approveVisual(reason) }} onReject={(reason) => { void rejectVisual(reason) }} onRegenerate={() => { void regenerateVisual() }} onContinue={() => setStep(8)} /> : null}
      {step === 8 && selected && visual ? <PublishStep candidate={selected} visual={visual} publication={publication} busy={publicationRequest.busy} error={publicationRequest.error ? toErrorBody(publicationRequest.error) : null} onPublish={() => { void publish() }} onTrace={() => setStep(9)} /> : null}
      {step === 9 ? <TraceStep trace={trace} busy={traceRequest.busy} error={traceRequest.error ? toErrorBody(traceRequest.error) : null} onLoad={() => { void loadTrace() }} /> : null}
    </main>
  )
}
