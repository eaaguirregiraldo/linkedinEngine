# Especificación de dominio: `evaluation` — Evaluación heurística accionable y blockers

> Dominio NUEVO: spec completa.
> Capacidad P0: RF-03 | Fórmula: SOLUTION.md §7.2 | Regla de decisión: §7.3 | Dimensiones: §7.4 | Fixtures: §12.5.

## Purpose

El sistema debe validar y evaluar cada candidato con una señal heurística 0-100 desglosada por dimensión, penalizaciones y explicación, y debe decidir entre `RECOMMENDED` y `REVISION_REQUIRED` con reglas reproducibles. Un blocker de evidencia o seguridad impide recomendar aunque el score sea alto (§7.3). La heurística es señal de calidad/potencial de conversación, NO predicción de viralidad: el sistema MUST NOT presentarla como estimación de impresiones/likes (RF-03, §7.1).

## Requirements

### Requirement: EVAL-01 — Fórmula transparente y desglosada

El sistema MUST calcular el score final con la fórmula de §7.2: `score_final = clamp(base - penalizacion_riesgo - penalizacion_genericidad, 0, 100)`, donde `base = 0.20*fuerza_del_hook + 0.20*relevancia_para_el_nicho + 0.20*especificidad_y_evidencia + 0.15*claridad_y_legibilidad + 0.15*potencial_de_conversacion + 0.10*ajuste_a_la_voz`. La UI MUST mostrar el resultado redondeado sin decimales y el desglose por dimensión y penalización.

#### Scenario: desglose visible

- GIVEN tres candidatos evaluados
- WHEN el usuario abre la vista de evaluación
- THEN ve el score final redondeado y el desglose por dimensión (0-100) y penalizaciones
- AND cada dimensión muestra su justificación (EVAL-03)

#### Scenario: clamping

- GIVEN un candidato cuya fórmula aritmética daría >100 o <0 antes de clamp
- WHEN se calcula el score final
- THEN el resultado se acota a [0, 100]
- AND la UI muestra el valor acotado

### Requirement: EVAL-02 — Escala ordinal 0-5 con anclas

El sistema MUST calificar cada dimensión en escala ordinal 0-5 y normalizar con `dimension_100 = rating * 20`. Anclas: 0 ausente/contradictorio, 3 adecuado y demostrable, 5 excepcional para el brief con evidencia textual concreta; 1/2/4 son progresión (§7.2).

#### Scenario: dimensión con ancla 5

- GIVEN un candidato con un hook excepcional para el brief y evidencia textual concreta
- WHEN se evalúa la dimensión "fuerza del hook"
- THEN recibe rating 5 y `dimension_100 = 100`
- AND la justificación cita la frase y la regla de rúbrica

#### Scenario: rating fuera de rango

- GIVEN un evaluador que emite un rating 7 (fuera de 0-5)
- WHEN el contrato de evaluación valida la salida
- THEN la salida se rechaza por violar la enumeración de rating
- AND se aplica retry/repair del evaluador (HARN-05); si persiste, se degrada a solo determinístico (HARN-08)

### Requirement: EVAL-03 — Justificación obligatoria por dimensión

El sistema MUST exigir que cada nota de dimensión incluya una cita del candidato Y la regla de rúbrica aplicada; una nota sin ambas referencias MUST ser inválida (§7.2). Los scores generados por LLM son recomendaciones editoriales; las validaciones determinísticas tienen prioridad.

#### Scenario: nota con cita y regla

- GIVEN una evaluación donde cada dimensión cita una frase del candidato y una regla de la rúbrica
- WHEN se valida el contrato de evaluación
- THEN la evaluación es válida y se persiste con el desglose

#### Scenario: nota sin justificación

- GIVEN una evaluación con una dimensión sin cita o sin regla
- WHEN se valida el contrato
- THEN la nota es inválida y no se persiste como score
- AND el sistema no presenta esa dimensión como evaluada

### Requirement: EVAL-04 — Penalizaciones

El sistema MUST aplicar `penalizacion_riesgo`: 25 por experiencia personal inventada; 10 por cada cifra o afirmación absoluta sin evidencia, con máximo 25. Y `penalizacion_genericidad`: 5 por cada cliché del catálogo versionado, tesis intercambiable o repetición sustancial, con máximo 15 (§7.2).

#### Scenario: cifra sin evidencia

- GIVEN un candidato con una cifra no soportada por el brief
- WHEN se calculan las penalizaciones
- THEN aplica `penalizacion_riesgo = 10` por esa cifra
- AND la penalización queda visible en el desglose

#### Scenario: máximo de penalización de riesgo

- GIVEN un candidato con tres cifras sin evidencia
- WHEN se calculan las penalizaciones
- THEN `penalizacion_riesgo` se acota a 25 (máximo)
- AND el candidato además tiene blocker de evidencia (EVAL-05)

#### Scenario: clichés acumulados

- GIVEN un candidato con cuatro clichés del catálogo versionado
- WHEN se calcula la penalización de genericidad
- THEN `penalizacion_genericidad` se acota a 15 (máximo)
- AND la traza registra la versión del catálogo usado (VOI-06)

### Requirement: EVAL-05 — Blockers

El sistema MUST activar un blocker de evidencia o seguridad ante: experiencia personal inventada, cifra/afirmación absoluta sin evidencia, claim `needs_review` sin vincular, o contenido que viole guardrails de §12.4. Un candidato con blocker activo MUST NOT quedar `RECOMMENDED` ni `APPROVED`, sin importar su score (RF-03 escenario "claim sin sustento", §7.3).

#### Scenario: blocker con score alto

- GIVEN un candidato con score ≥ 72 pero con una cifra inventada
- WHEN se aplica la regla de decisión
- THEN el candidato NO pasa a `RECOMMENDED`
- AND el flujo muestra el blocker como motivo explícito, aunque el score sea alto

#### Scenario: blocker resuelto por humano

- GIVEN un candidato con blocker por claim `needs_review`
- WHEN una persona vincula el claim con evidencia del brief (o lo retira)
- THEN el blocker se resuelve
- AND el candidato puede volver a evaluarse y eventualmente recomendarse

#### Scenario: blocker en fixture de regresión

- GIVEN el fixture versionado de un candidato que inventa una cifra (§12.5)
- WHEN se ejecutan los tests de dominio de blockers
- THEN el candidato recibe blocker de evidencia
- AND ninguna regla de decisión lo deja `RECOMMENDED` (test automatizado)

### Requirement: EVAL-06 — Regla de decisión reproducible

El sistema MUST aplicar la regla de §7.3: si el mejor candidato tiene score ≥ 72, sin blockers y supera al segundo por ≥ 4 puntos → `RECOMMENDED`. Si el mejor está entre 60 y 71, o la diferencia es < 4 → `REVISION_REQUIRED` con las dos mejoras de mayor impacto sugeridas. Si todos están por debajo de 60 → se recomienda reformular el brief (no regenerar indefinidamente).

#### Scenario: candidato recomendado

- GIVEN tres candidatos sin blockers con scores 78, 71 y 64
- WHEN se aplica la regla de decisión
- THEN el de 78 pasa a `RECOMMENDED` (≥72, sin blockers, +7 sobre el segundo)
- AND el flujo transiciona a `RECOMMENDED` (FSM)

#### Scenario: diferencia menor a 4

- GIVEN scores 74 y 72 (diferencia 2) sin blockers
- WHEN se aplica la regla
- THEN el flujo va a `REVISION_REQUIRED` (diferencia < 4)
- AND se sugieren las dos mejoras de mayor impacto

#### Scenario: banda de revisión

- GIVEN scores 68, 62 y 55 sin blockers
- WHEN se aplica la regla
- THEN el flujo va a `REVISION_REQUIRED` (mejor entre 60-71)
- AND se sugieren las dos mejoras de mayor impacto

#### Scenario: todos por debajo de 60

- GIVEN scores 58, 54 y 50 sin blockers
- WHEN se aplica la regla
- THEN el flujo va a `REVISION_REQUIRED`
- AND la UI recomienda reformular el brief en lugar de regenerar indefinidamente

#### Scenario: reproducción determinística

- GIVEN los mismos candidatos, la misma fórmula y los mismos umbrales (72/4/60)
- WHEN se evalúan en dos ejecuciones
- THEN la decisión (`RECOMMENDED`/`REVISION_REQUIRED`) es idéntica

### Requirement: EVAL-07 — Evaluador con candidatos anonimizados y orden aleatorio

Para reducir sesgo del evaluador, el sistema MUST entregar los candidatos al evaluador anonimizados (sin indicar orden de generación ni metadatos del provider) y en orden aleatorio (§12.5). El orden aleatorio MAY determinarse por seed en modo demo para mantener el determinismo global de la demo.

#### Scenario: anonimización en demo

- GIVEN una evaluación con `DemoProvider`
- WHEN el evaluador recibe los candidatos
- THEN no recibe información de posición original ni de proveedor
- AND en modo demo el orden aleatorio es determinístico (seed fija)

#### Scenario: orden aleatorio en remoto (P1)

- GIVEN una evaluación con proveedor remoto
- WHEN se invoca al evaluador
- THEN los candidatos se presentan en orden aleatorio no determinístico
- AND el score final no depende del orden de llegada

### Requirement: EVAL-08 — Umbrales visibles y calibrables

El sistema MUST exponer los umbrales (72 / diferencia 4 / 60) y la fórmula de manera visible en la UI de evaluación y documentarlos como iniciales y calibrables, no como universales (§7.3).

#### Scenario: umbrales visibles

- GIVEN la vista de evaluación
- THEN la UI muestra los umbrales de decisión y la fórmula con pesos
- AND el texto los describe como iniciales y sujetos a calibración con publicaciones aprobadas

#### Scenario: fixture de candidato sólido

- GIVEN el fixture versionado de un candidato sólido (§12.5)
- WHEN se ejecutan los tests de dominio
- THEN el candidato no recibe blockers
- AND su score cae en el rango esperado por el fixture (sin exigir un score exacto del LLM)

### Requirement: EVAL-09 — Fixtures de regresión

El sistema MUST incluir fixtures versionados con expectativas verificables (§12.5): candidato sólido sin blockers; genérico con penalización de genericidad; cifra inventada con blocker; salida JSON inválida que termina en `GENERATION_FAILED` tras la reparación permitida.

#### Scenario: suite de regresión ejecutable

- GIVEN los cuatro fixtures versionados
- WHEN corre la suite de tests de dominio de evaluación
- THEN cada fixture cumple su expectativa (sin blockers / penalización / blocker / `GENERATION_FAILED`)
- AND los tests no exigen un score exacto del LLM, sino rangos y reglas determinísticas
