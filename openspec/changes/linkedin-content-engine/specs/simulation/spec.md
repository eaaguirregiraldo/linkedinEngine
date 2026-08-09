# Especificación de dominio: `simulation` — Simulación de publicación honesta

> Dominio NUEVO: spec completa.
> Capacidad P0: RF-06, RNF-02 | Publicación simulada: SOLUTION.md §9 | Estados honestos: §6.2 | Invariante transversal 1.

## Purpose

El sistema debe completar una publicación local simulada con estado `SIMULATED_PUBLISHED`, banda persistente "SIMULACIÓN" y recibo local, sin llamar a LinkedIn y sin inventar URLs, URNs ni IDs remotos (§9.1). `PUBLISHED_REAL` es un estado reservado que MUST ser inalcanzable en P0 (invariante 1, §6.2).

## Requirements

### Requirement: SIM-01 — Publicación simulada con recibo

El sistema MUST, al confirmar la simulación, crear un `PublicationAttempt` en modo simulado con estado `SIMULATED_PUBLISHED`, fecha, contenido final y visual asociado, y MOSTRAR un recibo local (§6.1 paso 9, RF-06).

#### Scenario: happy path a simulación

- GIVEN un candidato aprobado y un visual `VISUAL_READY`
- WHEN el usuario confirma "Simular publicación"
- THEN el sistema crea el recibo con estado `SIMULATED_PUBLISHED`
- AND muestra "Simulación: no se envió contenido a LinkedIn"
- AND el recibo referencia el contenido final y el visual asociado

### Requirement: SIM-02 — Sin identificadores remotos inventados

El sistema MUST NOT presentar URL, URN ni métricas remotas inventadas; la vista previa y el recibo solo contienen datos locales (§9.1, criterio de aceptación §14: "No aparece una URL o identificador remoto inventado").

#### Scenario: recibo sin IDs remotos

- GIVEN una publicación simulada completada
- THEN el recibo y todas las vistas asociadas no contienen URL, URN ni ID remoto
- AND si el modelo de datos tiene un campo `remoteId`, queda vacío/null en modo simulado

#### Scenario: consulta posterior del recibo

- GIVEN una publicación simulada
- WHEN se consulta el recibo desde cualquier vista relevante
- THEN conserva la etiqueta "SIMULACIÓN" y el estado `SIMULATED_PUBLISHED` (RNF-02)
- AND no aparece ninguna métrica remota

### Requirement: SIM-03 — Vista previa honesta

El sistema MUST ofrecer una vista previa del texto y la imagen "como se enviarían" a LinkedIn, sin ejecutar ningún envío (§9.1).

#### Scenario: preview de texto e imagen

- GIVEN un candidato aprobado y un visual listo
- WHEN el usuario abre la vista previa de publicación
- THEN ve el texto final y la imagen como se enviarían
- AND la vista previa se etiqueta explícitamente como simulación

### Requirement: SIM-04 — Bloqueo de transiciones sin prerequisitos

El sistema MUST bloquear la simulación si no hay candidato aprobado o visual `VISUAL_READY`, explicando el requisito faltante (RF-06 escenario "intento sin aprobación").

#### Scenario: intento sin aprobación

- GIVEN un proyecto sin candidato `APPROVED`
- WHEN el usuario intenta simular la publicación
- THEN la FSM bloquea la transición a `SIMULATED_PUBLISHED`
- AND la UI explica el requisito faltante (aprobación humana previa)

#### Scenario: intento sin visual listo

- GIVEN un candidato aprobado pero sin visual `VISUAL_READY`
- WHEN el usuario intenta simular la publicación
- THEN la FSM bloquea la transición
- AND la UI indica que el visual debe estar aprobado primero

### Requirement: SIM-05 — `PUBLISHED_REAL` reservado e inalcanzable

El sistema MUST tratar `PUBLISHED_REAL` como estado reservado para integración futura; en P0 MUST NOT existir ninguna ruta que lo alcance (invariante 1, §6.2, §9.3). La regla de integridad: sin token válido, autorización, respuesta exitosa e identificador remoto, el sistema MUST NOT mostrar `PUBLISHED_REAL`; ante respuesta incierta MUST mostrar `REAL_PUBLISH_FAILED` o "estado remoto pendiente de verificación", nunca éxito optimista (§9.3).

#### Scenario: intento de forzar `PUBLISHED_REAL`

- GIVEN un proyecto en `VISUAL_READY`
- WHEN se intenta transicionar a `PUBLISHED_REAL` sin API real verificada
- THEN la FSM rechaza la transición (estado reservado, sin ruta en P0)
- AND el estado permanece `VISUAL_READY` y la UI no muestra ningún estado de publicación real

#### Scenario: inexistencia de ruta de publicación real

- GIVEN el mapa de transiciones de la FSM
- THEN no existe ninguna transición alcanzable en P0 que conduzca a `PUBLISHING_REAL` ni `PUBLISHED_REAL`
- AND un test de tabla verifica que `PUBLISHED_REAL` es inalcanzable desde todos los estados P0

### Requirement: SIM-06 — Exclusión mutua por intento

`SIMULATED_PUBLISHED` y `PUBLISHED_REAL` MUST ser estados mutuamente excluyentes por intento de publicación (§11.2 invariante).

#### Scenario: un intento, un modo

- GIVEN un `PublicationAttempt` creado en modo simulado
- THEN su modo y estado son coherentes (simulado → `SIMULATED_PUBLISHED`)
- AND el mismo intento no puede presentarse también como real (los estados son mutuamente excluyentes)

#### Scenario: recibo de simulación persistente

- GIVEN un proyecto publicado en simulación
- WHEN se reinicia la aplicación
- THEN el recibo persiste (SQLite en fichero) con estado `SIMULATED_PUBLISHED`
- AND la banda "SIMULACIÓN" sigue visible en las vistas relevantes
