import { useEffect } from 'react'
import { api, toErrorBody, type HealthOut } from './api/client'
import { Wizard } from './components/Wizard'
import { ErrorBanner } from './components/ui/ErrorBanner'
import { VoiceBadge } from './components/ui/VoiceBadge'
import { useAsync } from './hooks/useAsync'

export function App() {
  const health = useAsync<HealthOut>()
  const loadHealth = () => { void health.run(api.health) }
  useEffect(loadHealth, [])
  const provider = health.data?.provider === 'openai' ? 'OPENAI_PROVIDER' : health.data?.provider === 'demo' ? 'DEMO_PROVIDER' : health.data?.provider

  return (
    <div className="app-shell">
      <header className="app-header">
        <div><p className="app-header__kicker">LinkedIn Content Engine</p><h1>Del argumento al recibo, sin caja negra</h1></div>
        <div className="app-header__status"><span className="provider-badge">{provider ?? (health.busy ? 'verificando proveedor…' : 'proveedor no disponible')}</span><VoiceBadge /></div>
      </header>
      {health.error ? <div className="global-error"><ErrorBanner error={toErrorBody(health.error)} /><button className="button button--secondary" type="button" onClick={loadHealth}>Reintentar health</button></div> : null}
      <Wizard />
      <footer className="app-footer">MVP local. No publica en LinkedIn ni predice viralidad.</footer>
    </div>
  )
}
