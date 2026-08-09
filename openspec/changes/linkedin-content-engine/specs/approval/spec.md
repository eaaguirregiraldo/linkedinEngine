# Especificación de dominio: `approval` — Edición con invalidación y aprobación humana

> Dominio NUEVO: spec completa.
> Capacidad P0: RF-04 | Invariantes de edición: SOLUTION.md §11.2 | FSM: §6.2.

## Purpose

El sistema debe permitir editar un candidato, invalidar la evaluación previa al editar y exigir aprobación humana explícita con razón registrada antes de continuar (RF-04, §6.1 paso 7). La aprobación final siempre es humana: el sistema recomienda, el autor decide (§3.4).

## Requirements

### Requirement: APPR-01 — Aprobación humana explícita

El sistema MUST exigir una acción humana explícita para aprobar un candidato; MUST registrar la razón de aprobación y el actor; MUST NOT autoaprobar contenido (invariante 3). La aprobación desde `RECOMMENDED` solo es válida sin blockers activos; desde `REVISION_REQUIRED` requiere override humano con razón y sin blockers (§6.2).

#### Scenario: aprobación desde `RECOMMENDED`

- GIVEN un candidato en `RECOMMENDED` sin blockers
- WHEN el usuario confirma la aprobación e ingresa una razón
- THEN el candidato pasa a `APPROVED`
- AND la razón y el actor quedan registrados en la traza

#### Scenario: override desde `REVISION_REQUIRED`

- GIVEN un candidato en `REVISION_REQUIRED` sin blockers
- WHEN el usuario aprueba explícitamente con una razón editorial
- THEN el candidato pasa a `APPROVED`
- AND la traza registra el override y su razón

#### Scenario: aprobación con blocker activo

- GIVEN un candidato con un blocker de evidencia activo
- WHEN el usuario intenta aprobar
- THEN la FSM bloquea la transición a `APPROVED`
- AND la UI explica que el blocker debe resolverse primero (HARN-06/EVAL-05)

#### Scenario: aprobación sin razón

- GIVEN un candidato evaluado
- WHEN el usuario intenta aprobar sin ingresar una razón
- THEN el sistema rechaza la aprobación
- AND pide la razón antes de persistir la transición

### Requirement: APPR-02 — Edición invalida la evaluación previa

El sistema MUST invalidar la evaluación y decisión previas al editar el contenido de un candidato, incrementar su `contentVersion` y requerir reevaluación antes de aprobar (RF-04 escenario "edición invalida evaluación", §11.2).

#### Scenario: edición de una línea

- GIVEN un candidato evaluado con score visible
- WHEN el usuario edita una línea del contenido
- THEN el sistema incrementa `contentVersion`
- AND marca la evaluación anterior como desactualizada (no se muestra como vigente)
- AND el flujo vuelve al estado que exige reevaluación (`GENERATED`, vía evento `CANDIDATE_EDITED`)

#### Scenario: versión incrementada en traza

- GIVEN un candidato editado dos veces
- THEN la traza muestra `contentVersion` 1 → 2 → 3 con las ediciones
- AND cada versión conserva el contenido previo y el momento de edición

### Requirement: APPR-03 — Reevaluación antes de aprobar

Tras una edición, el sistema MUST exigir una reevaluación (liviana) antes de permitir la aprobación; MUST NOT permitir aprobar con una evaluación desactualizada (RF-04, §11.2 invariante).

#### Scenario: aprobar sin reevaluar tras edición

- GIVEN un candidato editado con evaluación desactualizada
- WHEN el usuario intenta aprobar directamente
- THEN el sistema bloquea la aprobación
- AND solicita la reevaluación antes de continuar

#### Scenario: reevaluación completada

- GIVEN un candidato editado
- WHEN el usuario ejecuta la reevaluación liviana
- THEN la nueva evaluación reemplaza a la anterior como vigente
- AND la decisión se recalcula con la regla de EVAL-06 sobre el contenido editado

### Requirement: APPR-04 — Selección alternativa con razón

El sistema MUST permitir elegir un candidato distinto del recomendado y MUST registrar la razón editorial de la selección (§7.3, RF-04 escenario "selección distinta a la recomendación"). La heurística orienta; no reemplaza el criterio editorial.

#### Scenario: elegir el segundo mejor

- GIVEN un candidato recomendado y otro con menor score
- WHEN el usuario elige el de menor score e ingresa la razón
- THEN el sistema permite la elección
- AND registra la razón en la traza junto a la decisión

#### Scenario: selección sin razón

- GIVEN dos candidatos evaluados
- WHEN el usuario intenta seleccionar uno distinto del recomendado sin razón
- THEN el sistema solicita la razón antes de persistir la selección

### Requirement: APPR-05 — Solo el candidato aprobado genera el asset final

El sistema MUST garantizar que solo un candidato `APPROVED` pueda generar el visual final y avanzar a `VISUAL_DRAFT` (§11.2 invariante, §6.2). Un candidato no aprobado MUST NOT iniciar el flujo visual.

#### Scenario: candidato aprobado inicia visual

- GIVEN un candidato en `APPROVED`
- WHEN el usuario genera la propuesta visual
- THEN el proyecto transiciona a `VISUAL_DRAFT`
- AND el candidato aprobado queda identificado como fuente del visual

#### Scenario: intento de visual sin aprobación

- GIVEN un proyecto sin candidato `APPROVED`
- WHEN el usuario intenta generar el visual
- THEN la FSM bloquea la transición (`RECOMMENDED`/`GENERATED` → `VISUAL_DRAFT` es ilegal)
- AND la UI explica el requisito faltante (aprobación humana previa)

#### Scenario: transición ilegal directa a publicación

- GIVEN un proyecto con candidato no aprobado y sin visual
- WHEN se intenta simular la publicación
- THEN la FSM rechaza la transición (ver `simulation` SIM-04 y `fsm-trace` FSM-02)
- AND el estado permanece sin cambios
