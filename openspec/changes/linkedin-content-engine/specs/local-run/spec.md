# Especificación de dominio: `local-run` — Arranque local y UX de estados

> Dominio NUEVO: spec completa.
> Capacidad P0: RNF-01, RNF-02, RNF-05 | Arranque: proposal.md (script root + concurrently + CORS) | Demo oficial: SOLUTION.md §15.

## Purpose

El sistema debe poder iniciarse localmente con un comando y con datos demo, sin requerir cuenta de LinkedIn ni credenciales GenAI (RNF-01); la UI debe distinguir visual y textualmente estados reales, simulados, fallidos y pendientes (RNF-02); y debe mostrar estados en curso bloqueando envíos duplicados (RNF-05). El README y `.env.example` deben permitir reproducir la demo sin secretos.

## Requirements

### Requirement: RUN-01 — Un comando arranca ambos procesos

El sistema MUST arrancar con un único comando documentado que levante la API (uvicorn) y la SPA (Vite) coordinadas (script root con `concurrently`), con puertos fijos y CORS funcionando (proposal.md; criterio de aceptación §14 "Un comando arranca ambos procesos").

#### Scenario: arranque limpio

- GIVEN una máquina con Node v24.14.0+ y Python 3.12.7+ y dependencias instaladas
- WHEN el evaluador ejecuta el comando raíz de arranque
- THEN ambos procesos se levantan (API y SPA)
- AND la aplicación responde en los puertos fijos documentados

#### Scenario: arranque sin dependencias instaladas

- GIVEN una máquina sin dependencias del proyecto instaladas
- WHEN se ejecuta el comando de arranque
- THEN el comando falla (o instruye) con un error accionable
- AND el README documenta los pasos de instalación previos

### Requirement: RUN-02 — Demo sin credenciales ni red

El sistema MUST funcionar en modo demo sin API keys, sin red y sin servicios cloud, recorriendo el happy path completo con resultados determinísticos (RNF-01; §15 demo oficial; invariante 6).

#### Scenario: evaluación sin credenciales

- GIVEN una máquina con dependencias instaladas y sin API keys
- WHEN la persona evaluadora inicia el modo demo
- THEN puede recorrer el happy path completo de idea a `SIMULATED_PUBLISHED`
- AND todos los resultados son determinísticos (mismo recorrido → mismos datos)

#### Scenario: ausencia de key con proveedor demo

- GIVEN la API sin key GenAI configurada
- THEN el sistema usa `DemoProvider` por defecto
- AND la UI y la traza lo etiquetan `DEMO_PROVIDER` (ver RUN-06)

### Requirement: RUN-03 — Distinción visual y textual de estados

La UI MUST distinguir visual y textualmente los estados: en curso, simulados, fallidos y pendientes, de modo que no puedan confundirse (RNF-02). Toda vista relevante de una publicación simulada MUST mostrar la banda "SIMULACIÓN" y el estado `SIMULATED_PUBLISHED`.

#### Scenario: inspección de simulación

- GIVEN una publicación simulada
- WHEN se consulta desde cualquier vista relevante (wizard, recibo, traza)
- THEN conserva la etiqueta "SIMULACIÓN" y el estado `SIMULATED_PUBLISHED`
- AND ningún elemento visual sugiere una publicación real

#### Scenario: estados fallidos distinguibles

- GIVEN una ejecución en `GENERATION_FAILED`
- WHEN la UI muestra el estado
- THEN el estado fallido se distingue visual y textualmente de los estados exitosos y en curso
- AND la UI ofrece la acción de reintentar sin representar el fallo como éxito

### Requirement: RUN-04 — Estados en curso y bloqueo de envíos duplicados

La UI MUST mostrar el estado en curso mientras una operación asíncrona está pendiente y MUST bloquear envíos duplicados (RNF-05). No se fija SLA del proveedor remoto.

#### Scenario: generación en curso

- GIVEN una solicitud GenAI en curso
- THEN la UI muestra el estado `GENERATING`
- AND los botones de envío relevante quedan deshabilitados hasta que la operación termine

#### Scenario: doble click de generación

- GIVEN una generación en curso
- WHEN el usuario hace doble click en "generar"
- THEN solo se dispara una ejecución
- AND la UI ignora el segundo envío (ver `api` API-05)

### Requirement: RUN-05 — README y `.env.example`

El sistema MUST incluir un README con prerequisitos, comandos, modo demo y limitaciones, y un `.env.example` sin secretos que documente las variables configurables (entregables §16; RNF-04).

#### Scenario: README reproducible

- GIVEN el README
- THEN documenta prerequisitos (versiones), instalación, arranque, modo demo y limitaciones (incluida la ausencia de publicación real)
- AND documenta el guion de demo de 5-7 min (SOLUTION.md §15)

#### Scenario: `.env.example` sin secretos

- GIVEN el archivo `.env.example`
- THEN no contiene valores de credenciales reales
- AND documenta variables opcionales (p. ej., la key para el adaptador P1) con valores vacíos/placeholder y comentarios

### Requirement: RUN-06 — Etiqueta `DEMO_PROVIDER` en UI y traza

El sistema MUST etiquetar `DEMO_PROVIDER` en la UI y en la traza cuando no hubo llamada GenAI real (criterio de aceptación §14). Si el adaptador P1 se usa, la UI y la traza MUST identificar proveedor y modelo reales.

#### Scenario: etiqueta en todo el recorrido demo

- GIVEN un recorrido completo con `DemoProvider`
- THEN cada vista de generación/evaluación y la traza muestran `DEMO_PROVIDER`
- AND el texto aclara que los datos son demo, no respuesta remota (RF-02)

#### Scenario: proveedor real identificado (P1)

- GIVEN una ejecución con el adaptador OpenAI-compatible (P1) exitosa
- THEN la UI y la traza identifican el proveedor y el modelo reales
- AND no exponen la API key (invariante 4, TRC-02)
