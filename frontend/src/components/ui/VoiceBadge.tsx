/**
 * VoiceBadge — etiqueta "perfil de voz provisional v0" (H1.3, VOI-01).
 *
 * La voz es una hipótesis de trabajo: la UI MUST NOT presentarla como un
 * corpus validado. La etiqueta acompaña a toda vista donde se aplique la voz.
 */
export function VoiceBadge() {
  return (
    <span
      className="voice-badge"
      title="Perfil de voz v0 provisional: no validado empíricamente"
    >
      perfil de voz provisional v0
    </span>
  )
}
