# Especificación de dominio: `generation` — Generación de exactamente 3 candidatos diferenciados

> Dominio NUEVO: spec completa.
> Capacidad P0: RF-02 | Salida estructurada: SOLUTION.md §12.2 | Validaciones determinísticas: §12.3.

## Purpose

El sistema debe generar exactamente tres candidatos de publicación estructurados y diferenciados a partir de un brief válido, validar su salida contra el contrato canónico y registrar proveedor, modelo, prompt y esquema usados (RF-02, §12.2). La generación es una operación asíncrona gobernada por la FSM (`BRIEF_READY → GENERATING → GENERATED | GENERATION_FAILED`).

## Requirements

### Requirement: GEN-01 — Exactamente tres candidatos

El sistema MUST generar exactamente tres candidatos por ejecución a partir de un brief en `BRIEF_READY`. Una salida con menos o más de tres candidatos MUST ser rechazada por el contrato.

#### Scenario: generación válida

- GIVEN un brief en `BRIEF_READY` válido y sin blockers previos
- WHEN el usuario solicita la generación
- THEN el sistema produce exactamente tres candidatos que cumplen el contrato
- AND transiciona a `GENERATED`
- AND registra proveedor, modelo, versión de prompt y versión de esquema (RF-02)

#### Scenario: salida con dos candidatos

- GIVEN un provider que devuelve una salida con solo dos candidatos
- WHEN el harness valida la respuesta contra el contrato
- THEN la salida se rechaza por no cumplir el esquema
- AND se aplican las políticas de retry/repair (ver `genai-harness` HARN-05)
- AND si tras los reintentos sigue fallando, la ejecución termina en `GENERATION_FAILED` sin crear candidatos incompletos como válidos

#### Scenario: salida con cuatro candidatos

- GIVEN un provider que devuelve cuatro candidatos
- WHEN el harness valida la respuesta
- THEN la salida se rechaza por cardinalidad incorrecta
- AND se aplican las mismas políticas de retry/repair que en el caso anterior

### Requirement: GEN-02 — Ángulos únicos de una enumeración cerrada

El sistema MUST asignar a cada candidato un `angle` único perteneciente a una enumeración cerrada (al menos `problem-story`, `practical-framework`, `argued-position`). Ángulos duplicados MUST ser rechazados.

#### Scenario: ángulos diferenciados

- GIVEN una generación válida
- THEN los tres candidatos tienen `angle` únicos dentro de la enumeración cerrada
- AND el mecanismo narrativo de cada uno corresponde a su ángulo (relato/problema, marco práctico, postura argumentada)

#### Scenario: ángulos duplicados

- GIVEN una salida donde dos candidatos declaran el mismo `angle`
- WHEN el harness valida la respuesta
- THEN la salida se rechaza por violar unicidad de ángulos
- AND se aplica retry/repair; si persiste, la ejecución termina `GENERATION_FAILED`

#### Scenario: ángulo fuera de la enumeración

- GIVEN una salida con un `angle` no declarado en la enumeración cerrada
- WHEN se valida el contrato
- THEN la salida se rechaza por valor de enumeración inválido
- AND no se persiste ningún candidato

### Requirement: GEN-03 — Sin duplicación normalizada

El sistema MUST rechazar candidatos cuyos hooks o bodies sean idénticos tras normalizar mayúsculas, espacios y puntuación (SOLUTION.md §12.3). No se aceptan simples paráfrasis.

#### Scenario: hooks idénticos tras normalización

- GIVEN una salida donde dos hooks difieren solo en mayúsculas/espacios/puntuación
- WHEN se ejecuta la validación determinística de duplicación
- THEN la salida se rechaza por duplicación
- AND se aplica retry/repair; si persiste, `GENERATION_FAILED`

#### Scenario: bodies con alta similitud sustancial

- GIVEN una salida donde los bodies comparten estructura y frases sustanciales (paráfrasis)
- WHEN se ejecuta la validación de diferenciación
- THEN la salida se rechaza por falta de diferenciación
- AND el harness la reenvía pidiendo diferenciación real (ver HARN-05); si no se corrige, `GENERATION_FAILED`

### Requirement: GEN-04 — Contrato de salida validado

El sistema MUST validar la salida contra el schema canónico: campos no vacíos (`hook`, `body`, `cta`), enumeraciones cerradas, claims con soporte (`text` + `support`), y ausencia de texto fuera del JSON. Texto fuera del JSON MUST ser considerado inválido (SOLUTION.md §12.2).

#### Scenario: salida con claims soportados

- GIVEN una salida JSON válida con claims donde cada uno referencia una evidencia del brief o `author_opinion`
- WHEN se valida el contrato
- THEN todos los candidatos pasan la validación estructural
- AND los claims `author_opinion` quedan marcados como postura, no como hecho

#### Scenario: claim sin soporte

- GIVEN una salida con un claim sin campo `support` o con soporte inexistente
- WHEN se valida el contrato
- THEN el candidato queda marcado con `needs_review`
- AND eso produce un blocker hasta que una persona vincule el claim con evidencia o lo retire (ver `evaluation` EVAL-05)

#### Scenario: texto fuera del JSON

- GIVEN una respuesta del provider con texto fuera del bloque JSON esperado
- WHEN el harness intenta parsear la salida
- THEN se rechaza como inválida
- AND se permite UNA reparación basada en el error del esquema (HARN-05), sin reescribir contenido silenciosamente

### Requirement: GEN-05 — Registro de la ejecución

El sistema MUST registrar por ejecución: proveedor, modelo, parámetros relevantes, versión del prompt, versión del esquema, hash del prompt resuelto y marca de tiempo (RF-02, §12.6). Esta información MUST quedar disponible en la traza.

#### Scenario: ejecución con `DemoProvider`

- GIVEN una generación con `DemoProvider`
- THEN la traza registra `DEMO_PROVIDER` como proveedor y la versión de prompt/esquema usados
- AND la UI y la traza etiquetan la generación como demo (invariante 5)

#### Scenario: ejecución con proveedor remoto (P1)

- GIVEN una generación con el adaptador OpenAI-compatible (P1)
- THEN la traza registra el proveedor y el modelo reales
- AND no registra la API key ni cabeceras de autorización (invariante 4)

### Requirement: GEN-06 — Fallo controlado

El sistema MUST, ante un fallo definitivo de generación (tras retry/repair agotados o error de proveedor no recuperable), transicionar a `GENERATION_FAILED` conservando la traza y dejando el brief disponible para reintentar; MUST NOT representar el fallo como éxito (RNF-03).

#### Scenario: fallo de proveedor

- GIVEN un proveedor que falla de forma no recuperable durante la generación
- WHEN se agotan las políticas de retry del harness
- THEN la ejecución termina en `GENERATION_FAILED` con el error registrado
- AND el proyecto vuelve a permitir reintentar con el brief intacto (estado de reintento disponible)
- AND la UI muestra un error explícito sin candidatos parciales como válidos

#### Scenario: oferta de modo demo tras fallo

- GIVEN un proveedor remoto sin credenciales o fallando
- WHEN la generación no puede completarse
- THEN el sistema ofrece usar datos demo (`DemoProvider`)
- AND los candidatos resultantes se etiquetan `DEMO_PROVIDER`, sin presentarse como respuesta remota (RF-02 escenario "proveedor no disponible")
