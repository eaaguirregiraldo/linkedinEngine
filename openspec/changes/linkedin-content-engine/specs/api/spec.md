# Especificación de dominio: `api` — Contrato OpenAPI FE-BE

> Dominio NUEVO: spec completa.
> Capacidad P0: contrato FE/BE (proposal.md "schema canónico compartido"), RNF-02 (estados en UI), proposal "Decisiones que se cierran en design".

## Purpose

El sistema debe exponer los endpoints del flujo editorial con contratos pydantic que validen requests y respuestas, y debe mantener un schema canónico compartido FE (TypeScript) / BE (pydantic) para mitigar el drift del doble stack (proposal.md, enfoque). Los errores deben ser estructurados y accionables. Las decisiones de forma interna (rutas exactas, formato de polling) se cierran en `sdd-design`; aquí se especifica el comportamiento observable del contrato.

## Requirements

### Requirement: API-01 — Endpoints del flujo con contratos pydantic

El sistema MUST exponer endpoints que cubran el flujo: creación de proyecto/idea, guardado de brief, generación, consulta de estado, evaluación, edición/aprobación, visual, simulación y traza. Cada endpoint MUST validar request y response contra contratos pydantic (proposal.md; RF-01..07).

#### Scenario: flujo completo vía API

- GIVEN la API arrancada en modo demo
- WHEN un cliente recorre los endpoints en orden (idea → brief → generar → evaluar → aprobar → visual → simular → traza)
- THEN cada respuesta cumple el contrato del endpoint
- AND el estado final del proyecto es `SIMULATED_PUBLISHED` con traza consultable

#### Scenario: request que viola el contrato

- GIVEN un cliente que envía un brief sin tesis o con un campo de tipo incorrecto
- WHEN el request llega al endpoint de brief
- THEN la API responde con error de validación (422) y detalle del campo fallido
- AND no persiste ningún estado parcial

### Requirement: API-02 — Schema canónico compartido FE/BE

El sistema MUST mantener un schema canónico (pydantic como fuente) y tipos TypeScript del FE verificados contra él mediante un test de contrato FE/BE; el test MUST fallar ante cualquier drift unilateral (proposal.md, riesgo "doble stack").

#### Scenario: tipos TS coherentes

- GIVEN el schema canónico publicado por el BE
- WHEN corre el test de contrato FE/BE
- THEN los tipos TypeScript coinciden en campos, tipos y enumeraciones con el schema pydantic
- AND el test es parte de la suite de CI/local de tests

#### Scenario: drift detectado

- GIVEN un cambio en el BE que renombra un campo del contrato sin actualizar los tipos TS
- WHEN corre el test de contrato
- THEN el test falla indicando el campo divergente
- AND el equipo debe sincronizar ambos lados antes de continuar

### Requirement: API-03 — CORS para desarrollo local

El sistema MUST configurar CORS para permitir que la SPA de desarrollo (Vite) consuma la API (FastAPI/uvicorn) en el arranque local coordinado (proposal.md, RNF-01).

#### Scenario: request cross-origin en dev

- GIVEN la SPA sirviéndose en el puerto de Vite y la API en el puerto de uvicorn
- WHEN la SPA hace una llamada a la API
- THEN la respuesta incluye los headers CORS correspondientes
- AND el flujo de la UI funciona sin configuración manual del evaluador

### Requirement: API-04 — Errores estructurados y accionables

El sistema MUST responder errores con una estructura consistente (código de error, mensaje accionable, detalle cuando aplique) para los casos: validación de contrato, transición ilegal de FSM, fallo de proveedor, recursos inexistentes. Los mensajes MUST orientar al usuario sobre cómo resolver (RNF-03).

#### Scenario: transición ilegal con mensaje accionable

- GIVEN un proyecto en `GENERATED`
- WHEN un cliente intenta aprobar directamente
- THEN la API responde un error estructurado indicando la transición ilegal
- AND el mensaje explica el requisito faltante (evaluación previa / reevaluación)

#### Scenario: recurso inexistente

- GIVEN un proyecto que no existe
- WHEN un cliente consulta su traza
- THEN la API responde 404 con código de error estable
- AND el mensaje no expone detalles internos de implementación

### Requirement: API-05 — Operaciones asíncronas y estados en curso

El sistema MUST exponer el estado de las operaciones asíncronas (`GENERATING`, `EVALUATING`) de modo que la UI pueda consultarlo, y MUST garantizar idempotencia básica: iniciar una generación ya en curso MUST ser rechazado o ignorado sin disparar una segunda ejecución (RNF-05).

#### Scenario: consulta de estado en curso

- GIVEN una generación iniciada
- WHEN la UI consulta el estado del proyecto
- THEN la respuesta indica `GENERATING` (o equivalente de operación en curso)
- AND la UI muestra el estado y bloquea envíos duplicados

#### Scenario: doble inicio de generación

- GIVEN una generación en curso
- WHEN la UI (o un cliente) intenta iniciar otra generación
- THEN la API rechaza o ignora la segunda solicitud (sin segunda ejecución)
- AND la primera ejecución no se interrumpe ni se duplica

### Requirement: API-06 — Contrato de contrato (endpoints P1 compatibles)

El sistema SHOULD mantener los endpoints de tal forma que el adaptador remoto P1 y el historial navegable P1 puedan añadirse sin romper los contratos P0 existentes (compatibilidad hacia adelante). P1 MUST NOT modificar los contratos P0 ya especificados.

#### Scenario: extensión sin breaking change

- GIVEN los contratos P0 en uso
- WHEN se agrega un endpoint de historial (P1)
- THEN los endpoints P0 existentes permanecen funcionales sin cambios de contrato
- AND los clientes P0 no requieren actualización
