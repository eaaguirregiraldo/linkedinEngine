# Exploración: `linkedin-content-engine` — Arquitectura del MVP de 24 h

> Espejo en Markdown de la exploración persistida en Engram (#874, topic `sdd/linkedin-content-engine/explore`). Copiado por `sdd-init` en modo hybrid.

## Estado actual
- `/Users/eaaguirregiraldo/Downloads/linkedin` contiene SOLO `SOLUTION.md` (887 líneas). No hay código, no es un repo git, no hay `.atl/` ni artefactos SDD previos.
- `SOLUTION.md` fija requisitos (RF-01..07, RNF-01..05), alcance P0/P1, máquina de estados, heurística con fórmula, contrato visual SVG, publicación simulada y DemoProvider. §10.1 sugiere Next.js monoproceso pero declara explícitamente que es "una sugerencia para implementación": NO está congelada.
- Entorno real de la máquina (verificado, no asumido): Node v24.14.0 + npm 11.9.0 (sin pnpm/bun), Python 3.12.7 (sin uv), Go 1.26.0. NO hay API keys de GenAI configuradas (OpenAI/Anthropic/Gemini/etc. ausentes) → la demo real solo puede correr DemoProvider; el provider remoto P1 necesita que el usuario provea una key.
- Memoria previa: #868 (definición MVP en SOLUTION.md, priorizó Next.js monoproceso como sugerencia) y #865 (P0/P1, aprobación humana, DemoProvider bajo mismos schemas/guardrails, voz v0 provisional). Consistentes con lo leído.

## Restricciones que condicionan la arquitectura
- RNF-01: arranque local con UN comando, sin credenciales, sin cloud.
- P0: brief → 3 candidatos → evaluación+blockers → aprobación humana → SVG → SIMULATED_PUBLISHED → traza + tests de dominio (fórmula, blockers, transiciones, schema).
- FSM de ~15 estados honestos; edición invalida evaluación; DemoProvider atraviesa los mismos schemas/guardrails; retry/repair en el harness.
- Sin auth, sin multiusuario, sin colas, sin vectores, sin publicación real.

## Decisiones transversales (aplican a CUALQUIER opción)
1. **Dominio puro independiente del framework**: FSM tipada (`apply(state,event) -> result` con guards) + fórmula de evaluación + reglas de blockers en módulos sin dependencias. Tests sin HTTP ni DB (repositorios in-memory). Es LA decisión que más protege los criterios de aceptación.
2. **FSM artesanal tipada vs XState**: para ~15 estados con guards, tabla de transiciones pura es más simple, testeable y sin deps nuevas. XState válido si se prefiere algo battle-tested, pero agrega dependencia y concepto.
3. **Contratos con schema en el mismo lenguaje del dominio** (Zod en TS / pydantic en Python), usados tanto para validar requests como la salida GenAI (el mismo schema del harness).
4. **Provider GenAI como interfaz**: `generateCandidates(brief)` y `evaluateCandidates(candidates)` devuelven salidas YA validadas. DemoProvider determinístico (fixtures derivados del brief, no random) + adaptador remoto P1 (OpenAI-compatible chat completions como default por portabilidad). Retry/repair viven en el harness, no en el provider.
5. **Persistencia SQLite en fichero** (no in-memory) para que el historial P1 sobreviva reinicios. Repos finos sobre 5 agregados; evaluación/decisiones/traza como JSON en GenerationRun/Candidate.

## Opción 1 — Monolito Next.js + SQLite (TS/React/Zod) — PONDERADO 4.38
**Componentes y límites:** Un solo proceso. UI React (client components) + route handlers locales (`/api/generate|evaluate|visual|publish-simulated`) → servicio de workflow (clase TS pura) → repos (SQLite) y GenAI harness. Límites por carpetas: `src/domain` (FSM+fórmula+reglas, cero deps), `src/ai` (prompts versionados, providers, harness), `src/db` (repos, migraciones), `src/app` (UI+API).
**Flujo:** cada paso del flujo §6.1 es una llamada HTTP local o función directa; el workflow autoriza transiciones contra la FSM y persiste eventos de traza.
**GenAI harness:** Zod comparte tipos entre request y salida LLM; prompts versionados como archivos en `src/ai/prompts/`; adapter remoto P1 + DemoProvider P0.
**Persistencia/FSM:** SQLite (Drizzle con better-sqlite3, o better-sqlite3 crudo con repos finos). FSM pura en dominio. PRISMA NO recomendado por defecto: paso de codegen + engine binario = piezas móviles extra en 24 h (aceptable si el usuario lo prefiere).
**Testabilidad:** Vitest para dominio/contratos (repos in-memory), Playwright E2E P1 natural sobre route handlers.
**Tiempo/riesgo 24 h:** un comando (`npm run dev`), una toolchain, cero CORS. Riesgo: churn de versiones Next/React → PIN de versiones exactas en package.json al scaffold. Nivel: bajo-medio.
**Demo local / deploy:** `npm install && npm run dev`, sin keys. Deploy futuro: Vercel/Fly (SQLite file no va en serverless sin adaptación → migrar a Turso/libSQL o Postgres si hace falta).
**Tradeoffs honestos:** peso de framework y acoplamiento UI-workflow en un proceso; si el usuario no domina TS/React, la curva se paga acá.

## Opción 2 — SPA Vite + API FastAPI (Python) — PONDERADO 3.58
**Componentes y límites:** Dos procesos: Vite (React) + FastAPI/uvicorn; SQLite vía SQLAlchemy/SQLModel o aiosqlite; pydantic para contratos.
**Flujo:** la UI llama a la API para cada paso; FSM en Python puro (módulo domain), evaluador y harness en Python.
**GenAI harness:** ecosistema Python excelente para SDKs de proveedores y eventual generación de imágenes; pydantic valida salida LLM.
**Persistencia/FSM:** SQLite; transiciones en dominio Python.
**Testabilidad:** pytest (dominio) + Vitest (UI) + tests de contrato FE/BE → DOS suites y riesgo de drift entre Zod y pydantic.
**Tiempo/riesgo 24 h:** doble stack (Node+Python), dos procesos a coordinar en la demo (foreman/concurrently), CORS y contrato duplicado. Riesgo: medio-alto para una persona en 24 h.
**Demo local / deploy:** script root; deploy más fragmentado (FE + API + DB).
**Tradeoffs honestos:** separación limpia y Python fuerte en IA, pero el doble contrato y la orquestación de procesos consumen horas que el MVP no tiene.

## Opción 3 — Backend-first con Streamlit — PONDERADO 3.25
**Componentes y límites:** Un proceso Python; UI wizard desde estado; SQLite; dominio puro pytest-eable.
**Flujo:** lineal posible, pero el modelo rerun top-to-bottom de Streamlit pelea con una FSM de ~15 estados y con async GenAI; edición→invalidate→reevaluación se vuelve hacky con `st.session_state`.
**GenAI harness:** bien (Python), pero nada del framework fuerza la arquitectura de providers; hay que imponerla.
**Testabilidad:** dominio OK; UI no testeable, E2E en Streamlit es doloroso (iframes/reruns).
**Tiempo/riesgo 24 h:** es lo MÁS rápido a un flujo que "anda", pero el criterio de aceptación exige disciplina de ingeniería y UX de producto; Streamlit se lee como prototipo y no evoluciona (semana 2 = reescritura de UI).
**Tradeoffs honestos:** gana tiempo, pierde producto, estado y testabilidad. Descartada para ESTE desafío por el énfasis explícito en flujo de producto + pruebas + trazabilidad.

## Opción 4 — Serverless/BaaS (Vercel/Neon/Supabase) — PONDERADO 2.80
**Por qué descartarla en 24 h:** viola RNF-01 (local, un comando, sin credenciales); exige cuentas/red/credenciales fuera del control del candidato; SQLite en serverless no encaja (filesystem efímero) → empuja a Postgres hosteado = más piezas; deploy agrega horas sin valor para la demo. El riesgo del MVP es el motor editorial, no el hosting.
**Cuándo reaparece:** integración real con LinkedIn (OAuth necesita URL pública/callback) y multiusuario. Esa es evolución de semana 2, no MVP.

## Matriz ponderada (pesos justificados por la consigna: demo en 24 h con disciplina de ingeniería)
Criterios/pesos: Tiempo a demo P0 25% | Testabilidad dominio 20% | Encaje GenAI harness 15% | Persistencia+FSM 10% | Demo local 1 comando 10% | Sencillez operativa 10% | Evolución 1 semana 5% | UX producto 5%.
| Opción | Tiempo | Test | GenAI | Pers/FSM | Demo | Op. | Evol | UX | TOTAL |
|---|---|---|---|---|---|---|---|---|---|
| 1. Next monolith + SQLite | 4.5 | 4.5 | 4.5 | 4.0 | 4.5 | 4.0 | 4.0 | 4.5 | **4.38** |
| 2. Vite + FastAPI | 3.0 | 4.0 | 4.5 | 4.0 | 3.0 | 2.5 | 4.0 | 4.0 | **3.58** |
| 3. Streamlit | 4.0 | 2.0 | 4.0 | 2.5 | 4.0 | 4.0 | 2.0 | 2.0 | **3.25** |
| 4. Serverless/BaaS | 2.5 | 3.0 | 3.5 | 3.0 | 2.0 | 2.0 | 3.5 | 3.5 | **2.80** |

## Recomendación (original de la exploración)
**Opción 1** — monolito Next.js monoproceso, confirmando además: TS+React (el perfil declarado del usuario es frontend TS/React, y el spec ya apunta TS/Zod), SQLite con Drizzle o better-sqlite3 crudo (NO Prisma por defecto), Zod para contratos, prompts versionados en `src/ai/prompts/`, dominio puro con FSM artesanal tipada, Vitest + Playwright P1, DemoProvider determinístico + adaptador remoto OpenAI-compatible (P1, requiere key del usuario), SVG determinístico (ya fijado por SOLUTION.md), versiones PINeadas. La frontera UI/workflow se conserva por módulos, no por servicios, tal como pide §10.1.

**Segunda alternativa válida:** Opción 2 (Vite + FastAPI) — elegirla SOLO si el usuario es notablemente más fuerte en Python y acepta: dos procesos, contrato duplicado Zod/pydantic y doble toolchain. Ventaja real: ecosistema Python para iteración GenAI en la semana 2.

> 🔄 **ACTUALIZACIÓN 2026-08-08 (sdd-init):** el usuario **eligió la Opción 2 ajustada** — Vite+React + FastAPI+Python + SQLite con SQLAlchemy/SQLModel (NO Drizzle), DemoProvider determinístico + adaptador OpenAI opcional, SVG determinístico + API de imágenes opcional, demo local. Ver `openspec/init.md` y `state.yaml`.

## Decisión MVP vs evolución a 1 semana
- **MVP (24 h, P0):** local, SQLite file, DemoProvider, SVG determinístico, FSM en dominio puro, traza de ejecución actual, tests de dominio. Cero cloud, cero OAuth, cero historial navegable obligatorio.
- **Semana 2 (evolución sin reescritura):** provider remoto activable (adaptador ya definido en P0), historial navegable (ya lo soporta SQLite file), E2E Playwright, calibración de rúbrica, banco de evidencias, más plantillas SVG, y SOLO entonces evaluar serverless + Postgres + OAuth real si hay app aprobada en LinkedIn. La opción 1 no bloquea NINGUNA de estas evoluciones; la opción 3 las bloquea (reescritura).

## Decisiones que requieren confirmación del usuario ANTES de sdd-propose
1. **Stack/lenguaje:** Next.js+TS (recomendado) vs FastAPI+Python vs Nuxt/Vue. → **RESUELTO 2026-08-08: Vite+React + FastAPI+Python.**
2. **Proveedor GenAI P1:** recomiendo adaptador OpenAI-compatible (chat completions) por portabilidad; → **RESUELTO: adaptador OpenAI opcional.** Confirmar si el usuario proveerá key (sin key, P1 queda demo-only y la aceptación no depende de eso).
3. **Persistencia/ORM:** → **RESUELTO: SQLAlchemy/SQLModel, NO Drizzle.**
4. **Imagen:** SVG determinístico (ya fijado en SOLUTION.md) → **RESUELTO: SVG determinístico + API de imágenes opcional.**
5. **Despliegue:** local-only (recomendado, cumple RNF-01) → **RESUELTO: demo local.**

Nota: no se inventaron credenciales ni capacidades de API de LinkedIn; publicación real sigue fuera de alcance y su integración futura exige app registrada + permisos vigentes.

## Riesgos
- **Churn de versiones** Next/React (2026): mitigar con pin exacto y scaffold verificado al inicio. *(Con Vite: pin de versiones en package.json igualmente.)*
- **Demo sin keys:** mitigado por DemoProvider determinístico; la UI debe etiquetar DEMO_PROVIDER (ya exigido).
- **Acoplamiento UI-workflow en monoproceso:** mitigado por dominio puro + repos; el workflow NO importa Next. *(Con Vite+FastAPI: el dominio vive en Python, el workflow no importa FastAPI.)*
- **Doble stack (Nuevo, por decisión del usuario):** contrato duplicado Zod/pydantic → esquema canónico + tests de contrato FE/BE; coordinación de dos procesos → script root con concurrently; CORS.
- **SQLite file en serverless futuro:** documentar la migración a Turso/libSQL/Postgres en la semana 2, no resolverla ahora.
- **FSM con muchos estados:** cubrir transiciones ilegales con tests de tabla (caso "intento sin aprobación" etc.) desde el inicio.

## Ready for Proposal
Sí, condicionado: sdd-propose puede arrancar ya si el usuario confirma los 5 puntos anteriores (mínimo indispensable: stack, proveedor P1, despliegue). **Los 5 puntos quedaron resueltos el 2026-08-08** → sdd-propose puede arrancar sin bloqueos pendientes (solo confirmar key para P1 y alcance de la API de imágenes opcional).
