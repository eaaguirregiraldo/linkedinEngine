# Especificación de dominio: `fsm-trace` — FSM, trazabilidad y persistencia

> Dominio NUEVO: spec completa.
> Capacidad P0: RF-07, RNF-03, RNF-04 | FSM: SOLUTION.md §6.2 | Entidades: §11.1 | Trazabilidad: §12.6 | Persistencia: proposal.md (SQLModel/SQLite en fichero).

## Purpose

El sistema debe gobernar el flujo con una FSM honesta en dominio puro (transiciones legales con guards, rechazo de transiciones ilegales sin corrupción de estado), debe persistir los agregados en SQLite en fichero y debe exponer una traza completa sin secretos (RF-07, RNF-04). `SIMULATED_PUBLISHED` nunca es `PUBLISHED_REAL` (invariante 1).

## Requirements

### Requirement: FSM-01 — FSM en dominio puro con `apply(state, event)`

El sistema MUST implementar la FSM en el dominio puro (cero dependencias) con una función `apply(state, event) -> result` que valide guards antes de transicionar y MUST NO mutar estado ante un evento inválido (proposal.md, §6.2, plan de rollback).

#### Scenario: transición legal aplicada

- GIVEN un proyecto en `BRIEF_READY`
- WHEN se aplica el evento de solicitud de generación
- THEN `apply` devuelve el nuevo estado `GENERATING`
- AND el evento queda registrado

#### Scenario: estado no mutado ante evento inválido

- GIVEN un proyecto en `GENERATING`
- WHEN se aplica un evento ilegal (p. ej., aprobar sin evaluación)
- THEN `apply` devuelve un resultado de error con la transición rechazada
- AND el estado del proyecto permanece `GENERATING` (sin corrupción)

### Requirement: FSM-02 — Transiciones legales e ilegales

El sistema MUST aceptar solo las transiciones legales de la tabla de §5 de `spec.md` (FSM de referencia) y MUST rechazar cualquier otra como ilegal, con un error accionable que indique la transición intentada y el estado actual. Las transiciones reservadas (`VISUAL_READY → PUBLISHING_REAL → PUBLISHED_REAL | REAL_PUBLISH_FAILED`) MUST no tener ruta alcanzable en P0.

#### Scenario: tabla de transiciones como test

- GIVEN la tabla de transiciones legales (12 transiciones P0 + 1 evento de edición)
- WHEN corre la suite de tests de tabla de la FSM
- THEN cada transición legal aplica correctamente
- AND cada combinación estado+evento no declarada se rechaza sin mutar estado

#### Scenario: transición ilegal de ejemplo

- GIVEN un proyecto en `IDEA`
- WHEN se aplica el evento "simular publicación"
- THEN la FSM rechaza la transición `IDEA → SIMULATED_PUBLISHED` como ilegal
- AND el error indica el requisito faltante del camino correcto

#### Scenario: salto de aprobación

- GIVEN un proyecto en `GENERATED`
- WHEN se aplica el evento de aprobación directa
- THEN la FSM rechaza la transición `GENERATED → APPROVED` como ilegal (requiere evaluación previa)
- AND el estado permanece `GENERATED`

### Requirement: FSM-03 — Evento de edición con invalidación

El sistema MUST definir el evento `CANDIDATE_EDITED` como transición legal desde `GENERATED`, `RECOMMENDED` o `REVISION_REQUIRED` hacia `GENERATED`, incrementando `contentVersion` del candidato y marcando su evaluación como desactualizada (ampliación de la FSM de §6.2; ver `approval` APPR-02/APPR-03).

#### Scenario: edición desde `RECOMMENDED`

- GIVEN un proyecto en `RECOMMENDED` con un candidato evaluado
- WHEN el usuario edita el candidato
- THEN el proyecto transiciona por `CANDIDATE_EDITED` a `GENERATED`
- AND la evaluación previa queda desactualizada y la decisión previa deja de estar vigente

#### Scenario: edición en `GENERATED`

- GIVEN un proyecto en `GENERATED` (candidatos sin evaluar)
- WHEN el usuario edita un candidato
- THEN el `contentVersion` se incrementa
- AND el estado permanece `GENERATED` (no requiere invalidación porque no hay evaluación vigente)

#### Scenario: edición durante operación en curso

- GIVEN un proyecto en `GENERATING` o `EVALUATING` (operación asíncrona en curso)
- WHEN el usuario intenta editar
- THEN la FSM rechaza la edición (evento no permitido en ese estado, RNF-05)
- AND la UI bloquea la edición hasta que la operación termine

### Requirement: PST-01 — Persistencia de agregados en SQLite en fichero

El sistema MUST persistir los cinco agregados (`ContentProject`, `GenerationRun`, `Candidate`, `VisualAsset`, `PublicationAttempt`) en SQLite en fichero con SQLModel/SQLAlchemy, con evaluación/decisiones/traza como JSON embebido en `GenerationRun`/`Candidate` (§11.1, proposal.md). La persistencia MUST sobrevivir reinicios (historial P1).

#### Scenario: reinicio conserva estado

- GIVEN un proyecto en `VISUAL_READY`
- WHEN se reinicia la aplicación
- THEN el proyecto y sus agregados se recuperan desde el fichero SQLite
- AND el estado y la traza siguen disponibles

#### Scenario: ejecución fallida conserva error y trazas

- GIVEN una ejecución que terminó `GENERATION_FAILED`
- THEN la ejecución persiste con su error y sus trazas
- AND no existen candidatos incompletos marcados como válidos (§11.2 invariante)

#### Scenario: seed reproducible

- GIVEN un fichero SQLite borrado
- WHEN la aplicación arranca
- THEN el seed regenera el estado demo (ideas demo, datos de demo) sin migraciones irreversibles (rollback plan)

### Requirement: PST-02 — Sin secretos en persistencia

El sistema MUST NOT persistir API keys, tokens OAuth ni secretos en las tablas de la demo (§11.1, RNF-04). Si en el futuro hay publicación real, los tokens MUST almacenarse cifrados o delegarse a un secret store.

#### Scenario: inspección de base demo

- GIVEN una ejecución con `DemoProvider`
- WHEN se inspecciona la base de datos demo
- THEN no hay keys ni tokens en ningún campo
- AND los campos de credenciales no existen en las tablas de la demo

### Requirement: TRC-01 — Traza completa de ejecución

El sistema MUST exponer una traza por ejecución que incluya: hash del brief y evidencia; proveedor, modelo y parámetros relevantes; versiones de prompt y esquema; salida cruda protegida y salida validada; errores, reparaciones e intentos; puntajes por dimensión y penalizaciones; ediciones humanas y decisión final; modo y resultado de publicación (§12.6, RF-07).

#### Scenario: auditoría completa

- GIVEN una ejecución terminada (happy path hasta `SIMULATED_PUBLISHED`)
- WHEN el usuario abre el detalle de la traza
- THEN ve versiones de prompt/esquema, proveedor, validaciones, score desglosado, decisiones y modo de publicación
- AND la vista distingue cada tipo de evento (generación, evaluación, edición, decisión, publicación)

#### Scenario: traza de una generación fallida

- GIVEN una ejecución en `GENERATION_FAILED`
- WHEN se consulta su traza
- THEN muestra el error, los intentos y las reparaciones intentadas
- AND no la presenta como exitosa (RNF-03)

### Requirement: TRC-02 — Sin exposición de secretos en traza

El sistema MUST NOT exponer en ninguna traza, log o exportación: API keys, tokens OAuth, cabeceras de autorización ni datos de configuración de credenciales (RNF-04 escenario "inspección de trazas").

#### Scenario: inspección de trazas con proveedor remoto (P1)

- GIVEN una ejecución con proveedor remoto
- WHEN se consulta o exporta la traza
- THEN no aparecen API keys, tokens OAuth ni cabeceras de autorización
- AND cualquier variable de entorno sensible se excluye del contenido de la traza

#### Scenario: salida cruda redactable

- GIVEN un brief con datos potencialmente sensibles
- WHEN la configuración de redacción de salida cruda está activa
- THEN la salida cruda no se expone en la traza (o se redacta)
- AND la salida validada permanece consultable (HARN-07)

### Requirement: TRC-03 — Eventos de traza inmutables

La traza MUST ser de solo escritura (append-only): los eventos registrados MUST NOT modificarse ni eliminarse; las correcciones se registran como eventos nuevos (p. ej., nueva evaluación tras edición).

#### Scenario: evaluación reemplazada sin borrar la anterior

- GIVEN un candidato evaluado y luego editado
- WHEN se consulta la traza
- THEN la evaluación original sigue presente (marcada como desactualizada)
- AND la nueva evaluación aparece como evento posterior, sin sobrescribir la anterior

#### Scenario: intento de mutación de traza

- GIVEN una traza persistida
- WHEN se intenta modificar o eliminar un evento
- THEN el sistema lo impide (append-only)
- AND la operación falla sin alterar el historial
