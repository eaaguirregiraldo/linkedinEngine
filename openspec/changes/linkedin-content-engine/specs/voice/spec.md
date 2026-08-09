# Especificación de dominio: `voice` — Voz v0 provisional y especificidad COBOL/mainframe

> Dominio NUEVO: spec completa.
> Capacidad P0: SOLUTION.md §4.2 (hipótesis de voz v0), §3.4 (principios), dimensión "Voz" de la rúbrica (§7.4), penalización de genericidad (§7.2).

## Purpose

El sistema debe generar y evaluar contenido con un perfil de voz provisional (v0) explícitamente etiquetado como tal, y debe exigir especificidad de dominio COBOL/mainframes para evitar contenido intercambiable o genérico (§4.2, §12.8). La voz es una hipótesis de trabajo, no una personalidad validada: el sistema MUST NOT presentarla como definitiva.

## Requirements

### Requirement: VOI-01 — Perfil de voz v0 etiquetado como provisional

El sistema MUST declarar el perfil de voz como PROVISIONAL (v0) en la UI y en el brief; MUST NOT presentarlo como un corpus validado. La interfaz MUST mostrar la etiqueta "perfil de voz provisional" donde se aplique la voz.

#### Scenario: brief con voz provisional visible

- GIVEN un brief confirmado
- THEN la vista de brief muestra la voz v0 aplicada con la etiqueta de provisional
- AND el texto deja claro que el perfil se validará con publicaciones reales aprobadas (§4.3)

#### Scenario: consulta de reglas de voz

- GIVEN un usuario que consulta la documentación de voz del sistema
- THEN el sistema expone las reglas de voz v0 y su carácter provisional
- AND no afirma que la voz esté validada empíricamente

### Requirement: VOI-02 — Reglas de voz positivas

El sistema MUST aplicar las siguientes reglas de voz v0 a la generación y a la evaluación (dimensión voz): técnica y sobria con autoridad basada en experiencia; didáctica para no especialistas sin tratar COBOL como curiosidad arqueológica; directa y levemente contraria a lugares comunes, sin provocación por defecto; con ejemplos concretos, consecuencias operativas y decisiones de negocio (§4.2).

#### Scenario: candidato alineado a voz

- GIVEN un candidato que explica un mecanismo mainframe con consecuencia operativa concreta
- WHEN se evalúa la dimensión voz
- THEN la dimensión voz recibe una nota de rúbrica acorde a las reglas v0
- AND la justificación cita una frase del candidato y la regla de voz aplicada (ver `evaluation` EVAL-03)

#### Scenario: candidato grandilocuente

- GIVEN un candidato con lenguaje grandilocuente y sin evidencia de experiencia
- WHEN se evalúa la dimensión voz
- THEN la dimensión voz recibe una nota baja con justificación
- AND el sistema no lo presenta como coherente con la voz v0

### Requirement: VOI-03 — Prohibiciones de voz

El sistema MUST NOT generar frases vacías ("el futuro ya llegó", "en un mundo en constante evolución"), MUST NOT afirmar "COBOL está más vivo que nunca" sin evidencia, y MUST NOT usar engagement bait como cierre; el cierre MUST ser una pregunta específica o invitación a compartir experiencia (§4.2). Estas expresiones MUST estar en un catálogo versionado de clichés para penalización determinística (§7.2, §12.3).

#### Scenario: cliché detectado y penalizado

- GIVEN un candidato que contiene una expresión del catálogo de clichés
- WHEN se ejecuta el chequeo determinístico de genericidad
- THEN el candidato recibe `penalizacion_genericidad` (+5 por cliché, máx. 15)
- AND la penalización queda visible en el desglose de evaluación (invariante de transparencia)

#### Scenario: cierre con engagement bait

- GIVEN un candidato cuyo cierre es una invitación genérica ("¿Qué opinas?")
- WHEN se evalúa la dimensión "potencial de conversación"
- THEN la dimensión recibe una nota baja (señal negativa de la rúbrica, §7.4)
- AND el desglose explica el motivo con la regla de rúbrica aplicada

### Requirement: VOI-04 — Experiencias en primera persona

El sistema MUST NOT inventar experiencias en primera persona ("vi", "lideré", "aprendí") sin evidencia aportada por el autor en el brief. Un candidato que las atribuya sin evidencia MUST quedar marcado y puede producir blocker de evidencia (§4.2, guardrail §12.4).

#### Scenario: experiencia no soportada

- GIVEN un candidato que afirma "lideré una migración de 5 años" sin evidencia en el brief
- WHEN se ejecutan las validaciones de guardrail
- THEN la afirmación se marca como experiencia personal no soportada
- AND aplica `penalizacion_riesgo` (25) y produce blocker de evidencia (ver `evaluation` EVAL-05)

#### Scenario: experiencia soportada

- GIVEN un candidato que usa una experiencia declarada explícitamente como evidencia en el brief
- WHEN se evalúa
- THEN la afirmación se acepta como evidencia del autor
- AND no recibe penalización de riesgo por esa afirmación

### Requirement: VOI-05 — Especificidad de nicho COBOL/mainframe

El sistema MUST exigir especificidad de dominio: los candidatos MUST nombrar problemas, roles, decisiones o mecanismos reales del mundo mainframe (jobs, CICS, IMS, JCL, migración de reglas de negocio, conocimiento operativo) en lugar de afirmaciones intercambiables aplicables a cualquier tecnología (§7.4, dimensión "Nicho").

#### Scenario: candidato específico de nicho

- GIVEN un candidato que menciona un mecanismo o decisión concreta del ecosistema mainframe
- WHEN se evalúa la dimensión "relevancia para el nicho"
- THEN la dimensión recibe una nota acorde a la especificidad mostrada
- AND la justificación cita el fragmento específico

#### Scenario: contenido intercambiable

- GIVEN un candidato que podría aplicarse a cualquier tecnología sin cambios
- WHEN se evalúa la dimensión de nicho y especificidad
- THEN esas dimensiones reciben notas bajas
- AND el candidato puede recibir `penalizacion_genericidad` por tesis intercambiable (§7.2)

### Requirement: VOI-06 — Catálogo versionado de clichés

El sistema MUST mantener el catálogo de expresiones prohibidas/placeholder versionado (hash y versión), y la versión usada MUST quedar en la traza de evaluación (SOLUTION.md §12.3, §12.6).

#### Scenario: versión de catálogo en traza

- GIVEN una evaluación con penalización de genericidad
- THEN la traza registra la versión/hash del catálogo de clichés usado
- AND el desglose muestra qué expresiones dispararon la penalización

#### Scenario: actualización del catálogo

- GIVEN que el catálogo de clichés cambia
- THEN la nueva versión MUST incrementar la versión/hash del catálogo
- AND las evaluaciones previas conservan la versión con la que se calcularon (trazabilidad)
