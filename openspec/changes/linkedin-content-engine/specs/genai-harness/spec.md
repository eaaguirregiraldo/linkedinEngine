# Especificación de dominio: `genai-harness` — Harness GenAI (prompts, providers, retry/repair, schema)

> Dominio NUEVO: spec completa.
> Capacidad P0: SOLUTION.md §12 (harness), §12.1 (prompts versionados), §12.2 (salida estructurada), §12.3 (validaciones), §12.4 (guardrails), §12.7 (fallback).

## Purpose

El sistema debe encapsular toda invocación GenAI en un harness versionado que controla entrada, salida, validación, evaluación, fallos y evidencia de cada invocación (§12). Un harness no es solo un prompt: es el conjunto que garantiza contratos, guardrails, reintentos y trazabilidad. El retry/repair vive en el harness, no en el provider (proposal.md).

## Requirements

### Requirement: HARN-01 — Prompts versionados con manifiesto

El sistema MUST definir los prompts de P0 con identificador estable y versión semántica: `linkedin-candidate-generator@1.0.0` y `editorial-evaluator@1.0.0`. Cada prompt MUST guardarse como texto versionado, referenciado desde un manifiesto, con hash del prompt resuelto calculable. Cambiar instrucciones o contrato MUST exigir subir la versión (§12.1).

#### Scenario: manifiesto y hash registrados

- GIVEN una ejecución de generación con `linkedin-candidate-generator@1.0.0`
- THEN la traza registra la versión del prompt y el hash del prompt resuelto
- AND el manifiesto lista el prompt y su versión

#### Scenario: cambio de prompt exige versión nueva

- GIVEN que se edita el texto de un prompt de P0
- THEN el cambio MUST incrementar la versión semántica del prompt
- AND el manifiesto refleja la nueva versión antes de cualquier ejecución que la use

### Requirement: HARN-02 — Interfaz `GenAIProvider`

El sistema MUST exponer una interfaz `GenAIProvider` con, al menos, `generate_candidates(brief)` y `evaluate_candidates(...)`. Los providers MUST normalizar errores a un formato común y MUST NOT implementar retry/repair (eso es del harness, HARN-05).

#### Scenario: dos providers bajo la misma interfaz

- GIVEN el sistema con `DemoProvider` (P0) y, si existe key, el adaptador OpenAI-compatible (P1)
- WHEN el harness invoca la interfaz
- THEN ambos providers devuelven el mismo tipo de contrato de salida
- AND cualquier error del provider llega al harness normalizado

#### Scenario: error de provider normalizado

- GIVEN un provider que lanza un error de red
- WHEN el harness recibe el error
- THEN el error se normaliza (tipo, código, mensaje accionable) sin exponer detalles internos de SDK
- AND se aplican las políticas de retry del harness

### Requirement: HARN-03 — `DemoProvider` determinístico y etiquetado

El sistema MUST incluir un `DemoProvider` determinístico (fixtures derivados del brief, sin random) que atraviese los mismos schemas, validaciones, guardrails, transiciones y trazas que un provider remoto; solo sustituye la llamada externa (§12.7). UI y traza MUST etiquetar `DEMO_PROVIDER` (criterio de aceptación §14).

#### Scenario: demo determinística

- GIVEN el mismo brief y el mismo proveedor `DEMO_PROVIDER`
- WHEN se generan candidatos dos veces
- THEN la salida es idéntica en ambas ejecuciones (sin random)
- AND la traza registra `DEMO_PROVIDER` en cada ejecución

#### Scenario: demo con guards aplicados

- GIVEN un brief con una cifra sin fuente
- WHEN `DemoProvider` genera candidatos
- THEN la salida atraviesa las mismas validaciones de guardrail que un provider remoto
- AND la cifra no soportada no aparece como hecho validado (queda `needs_review` o ausente)

### Requirement: HARN-04 — Schema canónico compartido FE/BE

El sistema MUST validar requests y respuestas con contratos pydantic y MUST mantener un schema canónico compartido entre FE (TypeScript) y BE (pydantic) que impida el drift del doble stack; los tipos TS MUST verificarse contra el schema canónico mediante un test de contrato (proposal.md, §12.2).

#### Scenario: contrato FE/BE coherente

- GIVEN el schema canónico publicado por el BE
- WHEN corre el test de contrato FE/BE
- THEN los tipos TypeScript del FE coinciden con el schema pydantic canónico (campos, tipos, enumeraciones)
- AND el test falla si alguien introduce drift unilateral

#### Scenario: salida inválida rechazada por contrato

- GIVEN una respuesta GenAI que no cumple el schema (campo faltante, tipo incorrecto, enum inválido)
- WHEN el harness valida contra el schema canónico
- THEN la salida se rechaza con el detalle del error de validación
- AND se aplica retry/repair (HARN-05)

### Requirement: HARN-05 — Retry/repair

El sistema MUST permitir hasta dos reintentos con backoff ante errores transitorios, y UNA reparación ante JSON inválido usando el error del esquema, sin reescribir silenciosamente el contenido. Si vuelve a fallar, la ejecución MUST terminar `GENERATION_FAILED` conservando la traza (§12.7).

#### Scenario: reintentos con backoff

- GIVEN un proveedor que falla con un error transitorio dos veces y responde a la tercera
- WHEN el harness ejecuta la política de retry
- THEN la generación termina con éxito
- AND la traza registra el número de intentos y el backoff aplicado

#### Scenario: JSON inválido con reparación única

- GIVEN una respuesta con JSON inválido (p. ej., coma final o campo fuera de schema)
- WHEN el harness aplica la reparación única basada en el error del esquema
- THEN la salida reparada se revalida contra el schema
- AND si es válida, continúa el flujo normal; si no, `GENERATION_FAILED`
- AND el contenido reparado no se inventa: solo se corrige lo que el error permite corregir

#### Scenario: fallo definitivo tras políticas agotadas

- GIVEN un provider que falla en el intento original y en ambos reintentos
- WHEN se agota la política de retry
- THEN la ejecución termina en `GENERATION_FAILED` con el error y la traza conservados
- AND el brief permanece disponible para reintentar (RNF-03)

### Requirement: HARN-06 — Guardrails

El sistema MUST aplicar los guardrails de §12.4 a toda salida: no atribuir experiencias/clientes/cargos/resultados a Juan sin evidencia aprobada; cifras con fuente o marcadas `needs_review`; sin ataques personales, secretos ni consejos presentados como garantía; sin imitar a otra persona viva; instrucciones dentro de evidencia importada tratadas como datos (no como instrucciones del sistema); contenido con blockers sin paso a aprobación sin resolución explícita.

#### Scenario: prompt injection tratado como dato

- GIVEN una evidencia del brief que contiene instrucciones maliciosas ("ignora las reglas y...")
- WHEN se construye el prompt con el brief
- THEN las instrucciones se tratan como datos del brief, no como instrucciones del sistema
- AND la salida no refleja las instrucciones maliciosas

#### Scenario: atribución falsa a Juan

- GIVEN un candidato que atribuye a Juan un cliente o resultado no presente en la evidencia
- WHEN se ejecuta el guardrail de atribución
- THEN la afirmación se rechaza o se marca como inventada
- AND aplica `penalizacion_riesgo` y puede producir blocker de evidencia

#### Scenario: contenido con blockers sin resolución

- GIVEN un candidato con blocker activo
- WHEN se intenta avanzar a aprobación
- THEN la FSM bloquea la transición (ver `approval` APPR-01 y `fsm-trace` FSM-02)
- AND la UI explica que el blocker debe resolverse antes de aprobar

### Requirement: HARN-07 — Trazabilidad por ejecución

El sistema MUST registrar por ejecución (en la traza): brief y evidencia por identificador/hash; proveedor, modelo y parámetros relevantes; versiones de prompt y esquema; salida cruda protegida (para depuración local) y salida validada; errores, reparaciones e intentos; puntajes por dimensión y penalizaciones; ediciones humanas y decisión final; modo y resultado de publicación (§12.6). MUST NOT registrar secretos.

#### Scenario: traza completa de una generación demo

- GIVEN una ejecución de generación con `DEMO_PROVIDER`
- THEN la traza contiene hash del brief, `DEMO_PROVIDER`, versión de prompt/esquema, salida validada y número de intentos
- AND no contiene secretos ni cabeceras

#### Scenario: salida cruda desactivable

- GIVEN una configuración con redacción de salida cruda activada
- WHEN se consulta la traza
- THEN la salida cruda no se expone (o se redacta), mientras la salida validada permanece
- AND la configuración de redacción queda documentada (RNF-04)

### Requirement: HARN-08 — Degradación del evaluador semántico

Si el evaluador semántico (GenAI) falla, el sistema MUST conservar y mostrar solo los chequeos determinísticos y un estado explícito "evaluación semántica no disponible"; MUST NOT fabricar un score completo (§12.7, RF-03 escenario "evaluador semántico fallido").

#### Scenario: evaluador semántico caído

- GIVEN candidatos estructuralmente válidos
- WHEN el evaluador semántico no responde tras las políticas de retry
- THEN el sistema muestra solo los chequeos determinísticos
- AND marca el estado como `EVALUATION_PARTIAL`
- AND no inventa valores para las dimensiones semánticas

#### Scenario: flujo desde evaluación parcial

- GIVEN un estado `EVALUATION_PARTIAL`
- WHEN el usuario continúa el flujo
- THEN la FSM solo permite la transición a `REVISION_REQUIRED` (§6.2)
- AND la UI indica que el contenido requiere revisión humana porque no hubo evaluación semántica completa

### Requirement: HARN-09 — Sin cambio automático de proveedor

El sistema MUST NOT cambiar automáticamente de proveedor remoto a otro sin avisar, porque los resultados y condiciones de privacidad pueden diferir (§12.7). El cambio MUST requerir acción explícita del usuario.

#### Scenario: fallo del remoto sin conmutación automática

- GIVEN un proveedor remoto configurado que falla
- WHEN falla la generación
- THEN el sistema no cambia solo a otro proveedor remoto
- AND ofrece opciones explícitas (reintentar, usar demo) sin ejecutar ninguna sin confirmación del usuario
