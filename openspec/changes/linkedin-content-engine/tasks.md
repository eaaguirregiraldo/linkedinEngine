# Tasks: `linkedin-content-engine` — Motor editorial asistido por GenAI para LinkedIn (MVP local)

> Fase: `sdd-tasks` | Fecha: 2026-08-09 | Modo de persistencia: **hybrid** (openspec + Engram)
> Dependencias: `spec.md` + `specs/{dominio}/spec.md` (11 dominios, fuente de requisitos), `design.md` (9 ADRs, §4 FSM, §5 contrato, §6 harness, §9 DB, §11 script root), `proposal.md` (P0/P1, rollback, criterios de aceptación), `state.yaml`.
> Reglas de fase aplicadas (openspec/config.yaml `rules.tasks`): agrupar por fases (infraestructura, implementación, testing), numeración jerárquica, tareas de una sesión.

## 0. Cómo usar este plan

- **Lotes = unidades delegables.** Un lote es un bloque que UN agente ejecuta completo; los lotes de la misma wave corren en PARALELO sin pisar archivos ajenos (ver §2 Matriz de propiedad de archivos).
- **Orden por waves.** Wave 1 (paralela) → Wave 2 (paralela) → Waves 3-6 (SECUENCIALES: integración backend → frontend → contrato → cierre). La integración final es secuencial por diseño.
- **P0 vs P1.** Toda tarea lleva tag `[P0]` (obligatoria para la demo) o `[P1]` (opcional, NO bloqueante). La aceptación depende SOLO de P0.
- **Criterios de corte** en §4. Regla de oro (proposal Rollback + SOLUTION.md §19): si P0 atrasa a la hora 14 del plan, NO se toca P1.
- **Cada tarea lista:** archivos objetivo → criterio verificable → referencia a requisito/spec.
- Convenciones del repo: conventional commits SIN atribución IA, commit por vertical slice al cerrar cada lote (proposal Rollback Plan), nunca build tras cambios (regla global), no se modifica `SOLUTION.md`.

## 1. Fases y waves

| Wave | Lotes | Agentes en paralelo | Naturaleza | Contenido |
|---|---|---|---|---|
| 1 — Fundación | A1, B, C, D | 4 | PARALELA | Scaffold + dominio puro + contratos pydantic + persistencia |
| 2 — Capacidades | E, F | 2 | PARALELA (requiere W1) | Harness GenAI/DemoProvider + visual SVG |
| 3 — Integración BE | G | 1 | SECUENCIAL | API FastAPI + workflow + openapi.json + schema.d.ts |
| 4 — Frontend | H1 → H2 | 1 (secuencial entre sí) | SECUENCIAL | Client tipado + useAsync + UI primitivas → Wizard 10 pasos |
| 5 — Contrato FE/BE | I | 1 | SECUENCIAL | Suite vitest `contract` anti-drift |
| 6 — Cierre P0 | J | 1 | SECUENCIAL | README, decisiones/supuestos, semana adicional, datos demo + guion, verificación aceptación |
| 7 — P1 (opcional) | K | 1 | SECUENCIAL (solo si P0 verde) | OpenAI adapter, historial UI, E2E, ImageProvider, Alembic |

## 2. Matriz de propiedad de archivos (evita conflictos de edición en paralelo)

| Lote | Archivos EXCLUSIVOS |
|---|---|
| A1 | `package.json` (raíz), `.gitignore`, `.env.example`, `backend/package.json`, `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/pyproject.toml`, `backend/core/*`, `backend/tests/conftest.py`, `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts` (base), `frontend/index.html`, repo git |
| B | `backend/domain/*`, `backend/tests/domain/*`, `backend/tests/fixtures/*` |
| C | `backend/api/schemas.py`, `backend/ai/contracts.py` |
| D | `backend/db/*`, `backend/tests/db/*` |
| E | `backend/ai/harness.py`, `backend/ai/providers.py`, `backend/ai/demo_provider.py`, `backend/ai/prompts/*`, `backend/tests/harness/*` |
| F | `backend/visual/*`, `backend/tests/visual/*` |
| G | `backend/api/main.py`, `backend/api/dependencies.py`, `backend/api/errors.py`, `backend/api/workflow.py`, `backend/api/routers/*`, `backend/tests/api/*`, `frontend/src/api/schema.d.ts` (generado), `frontend/src/api/openapi.json` (cacheado) |
| H1 | `frontend/src/api/client.ts`, `frontend/src/hooks/useAsync.ts`, `frontend/src/components/ui/*`, `frontend/src/styles/*`, `frontend/src/tests/*` (unit base) + edición del bloque `test` en `frontend/vite.config.ts` (SECUENCIAL sobre A1) |
| H2 | `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/components/Wizard.tsx`, `frontend/src/components/steps/*` |
| I | `frontend/src/tests/contract/*` |
| J | `README.md`, `docs/decisions.md` (si aplica), datos demo/guion, verificación final |
| K | `backend/ai/openai_compat.py`, `frontend/src/...` (historial UI), `e2e/*`, `backend/visual/image_provider.py` (implementación P1), Alembic |

Dependencias de lote: `B` y `C` y `D` dependen solo de `A1` (config/conftest). `E` depende de `B+C+A1`. `F` depende de `B+A1`. `G` depende de `A1+B+C+D+E+F`. `H1` depende de `G` (schema.d.ts + backend vivo). `H2` depende de `H1`. `I` depende de `G+H`. `J` depende de `I`. `K` depende de P0 completo verde.

---

## Phase 1 — Fundación (Wave 1: A1, B, C, D en paralelo)

### Batch A1 — Scaffold del workspace y scripts de dos procesos `[P0]`

- [ ] **A1.1** Crear repo git en la raíz (`git init`) + `.gitignore` con `.env`, `data/`, `node_modules/`, `__pycache__/`, `dist/`, `.venv/`, `*.db`. **Criterio:** `git status` no muestra archivos ignorados; commit inicial con `SOLUTION.md` y `openspec/` intactos. **Ref:** proposal Rollback Plan.
- [ ] **A1.2** Crear `package.json` (raíz) con scripts: `dev` (`concurrently -n api,web -c blue,green "npm:dev:api" "npm:dev:web"`), `dev:api` (`npm --prefix backend run dev` → uvicorn `api.main:app --reload --port 8000`), `dev:web` (`npm --prefix frontend run dev` → vite `--port 5173`), `schema:generate`, `schema:check` (generar a `/tmp` + `diff --exit-code`), `test` (pytest + vitest), `test:contract`, `demo`; devDependency `concurrently@^9.1.0`. **Criterio:** `npm install` en raíz resuelve; `npm run` lista los 9 scripts; `npm run dev` levanta AMBOS procesos en puertos fijos 8000/5173 (con stubs mínimos). **Ref:** design §11.1, spec `local-run` RUN-01.
- [x] **A1.3** Crear `backend/requirements.txt` (pines: `fastapi`, `uvicorn`, `sqlmodel>=0.0.22`, `pydantic`, `pydantic-settings`, `python-dotenv`, `httpx`) + `backend/requirements-dev.txt` (`pytest`, `ruff`) + `backend/pyproject.toml` mínimo (tooling pytest/ruff) + `backend/package.json` (wrappers `dev`/`test`). **Criterio:** instalación limpia resuelve en Python 3.12.7; `pytest --version` ok; `npm --prefix backend run test` ejecuta pytest. **Ref:** proposal Dependencies, design §16.
- [x] **A1.4** Crear `backend/core/config.py` — `Settings` con pydantic-settings cubriendo TODAS las vars de design §11.3 con defaults (`APP_ENV=dev`, `API_PORT=8000`, `DATABASE_PATH=data/engine.db`, `GENAI_PROVIDER=demo`, `OPENAI_BASE_URL`, `OPENAI_API_KEY=""`, `OPENAI_MODEL=gpt-4o-mini`, `OPENAI_TIMEOUT=60`, `DEMO_FORCE_INVALID=false`, `TRACE_STORE_RAW_OUTPUT=false`, `VISUAL_PROVIDER=svg`, `IMAGE_API_URL/KEY`, `CORS_ORIGINS=http://localhost:5173`). **Criterio:** test unit: defaults correctos, `GENAI_PROVIDER == "demo"` sin env; `.env` de la raíz se carga. **Ref:** design §11.3, spec `local-run` RUN-05.
- [x] **A1.5** Crear `backend/core/trace.py` — `build_trace_event(type, **data)` (dict con `ts`+`type`) + `redact_secrets(obj)` (redacta keys/tokens/cabeceras de autorización recursivamente). **Criterio:** test unit: `redact_secrets` elimina valores de `api_key`/`authorization`; evento tipado con ts. **Ref:** design §6.6/§13, spec `fsm-trace` TRC-02.
- [x] **A1.6** Crear `backend/tests/conftest.py` — setup de `sys.path`/rootdir para que los tests importen `domain.*`, `ai.*`, `api.*`, `db.*`; helpers de sesión SQLite temp. **Criterio:** `pytest -q backend/tests` descubre las subcarpetas de lotes B/D/E/F/G sin conflictos. **Ref:** design §15.
- [x] **A1.7** Crear scaffold `frontend/`: `package.json` (react, react-dom, typescript, vite, @vitejs/plugin-react, vitest, @testing-library/react, openapi-typescript; scripts `dev`, `test`, `test:contract`), `tsconfig.json` (strict), `vite.config.ts` (base: plugin react, port 5173, proxy `/api → http://localhost:8000`), `index.html`. **Criterio:** `npm install` en frontend resuelve; `vite` arranca (aún sin src). **Ref:** design §10.1/§11.2, spec `api` API-03.
- [x] **A1.8** Crear `.env.example` sin secretos (todas las vars con defaults/placeholders vacíos y comentarios; `OPENAI_API_KEY=` y `IMAGE_API_KEY=` vacías). **Criterio:** grep no encuentra credenciales reales; el sistema corre con defaults. **Ref:** spec `local-run` RUN-05, RNF-04.

### Batch B — Dominio puro: FSM, evaluación, blockers, validación + tests `[P0]`

> CERO dependencias (solo stdlib) — design §4.1. Es el lote de mayor prioridad: G depende de él. Incluye TDD: escribir el test de tabla primero (RED) → implementar (GREEN).

- [x] **B.1** `backend/domain/fsm.py` — `STATES`/`EVENTS` frozensets, `Transition` (source/event/guard/target), tabla declarativa `TRANSITIONS` con las 25 filas de design §4.2 (incluidas las 3 reservadas con guard muerto `real_publish_enabled()==False`), `FsmContext` (brief, candidatos, evaluación, blockers, visual, flag proveedor real), `apply(state, event, ctx) -> TransitionResult{ok, state, reason}`. **Criterio:** `backend/tests/domain/test_fsm.py` — test de tabla recorre cada transición legal (incl. `CANDIDATE_EDITED` desde `GENERATED|RECOMMENDED|REVISION_REQUIRED|VISUAL_DRAFT|VISUAL_READY` → `GENERATED`) y cada combinación ilegal se rechaza SIN mutar estado; test verifica que `PUBLISHED_REAL`/`PUBLISHING_REAL` son INALCANZABLES desde todos los estados P0 (guard muerto). **Ref:** spec.md §5, `fsm-trace` FSM-01/02/03, `simulation` SIM-05, design §4.2-4.3.
- [x] **B.2** `backend/domain/score.py` — `DIMENSION_WEIGHTS` (hook .20, niche_relevance .20, specificity_evidence .20, clarity .15, conversation_potential .15, voice_fit .10; suma 1.0), `dimension_100(rating)=rating*20`, `base_score`, `clamp`, constantes `PENALTY_RISK_INVENTED_EXPERIENCE=25`, `PENALTY_RISK_PER_UNSUPPORTED_CLAIM=10` (máx 25), `PENALTY_GENERICITY_PER_CLICHE=5` (máx 15), `penalizacion_riesgo`, `penalizacion_genericidad`, `score_final = round(clamp(base - risk - generic))`. **Criterio:** `test_score.py` con tabla: clamping a 0 y 100; máximos 25/15 con 3 cifras / 4 clichés; pesos suman 1.0; validez de nota exige `quote`+`rubric_rule` por dimensión (sin ambas → nota inválida). **Ref:** `evaluation` EVAL-01/02/03/04, design §4.4.
- [x] **B.3** `backend/domain/blockers.py` — activación de blockers (claim sin soporte, experiencia personal inventada, contenido prohibido §12.4, `needs_review` sin resolver); `decide(scores, blockers, top2_gap) -> Decision{outcome, best_candidate_id, reason, brief_needs_revision}` con umbrales `THRESHOLD_RECOMMEND=72`, `MIN_TOP_GAP=4`, `THRESHOLD_REVISION_LOW=60` (versionados/calibrables). **Criterio:** `test_blockers.py` cubre: blocker con score ≥72 NO queda `RECOMMENDED`; 78/71/64 sin blockers → `RECOMMENDED`; 74/72 → `REVISION_REQUIRED` (gap<4); 68/62/55 → `REVISION_REQUIRED` con 2 mejoras; 58/54/50 → `REVISION_REQUIRED` con `brief_needs_revision=True`; misma entrada → misma decisión (reproducible). **Ref:** `evaluation` EVAL-05/06, design §4.5.
- [x] **B.4** `backend/domain/validation.py` — chequeos determinísticos: normalización (mayúsculas/espacios/puntuación), duplicados de hook/body, paráfrasis sustancial, claims con `support` existente, texto fuera del JSON, prohibidos (§12.4), cifras/afirmaciones absolutas sin fuente, detección de experiencia en primera persona sin evidencia. **Criterio:** `test_validation.py` cubre: hooks idénticos tras normalizar → rechazo; bodies con alta similitud → rechazo; claim sin soporte → `needs_review`; instrucciones maliciosas en evidencia tratadas como DATO (no reflejadas); prohibidos detectados. **Ref:** `generation` GEN-03/04, `genai-harness` HARN-06, `voice` VOI-03/04, design §4.4 (nota §7.2).
- [x] **B.5** `backend/domain/cliches_v1.txt` — catálogo versionado de clichés/placeholders + carga con versión/hash estable. **Criterio:** test: carga ok; versión/hash estable entre cargas; incluye los clichés de VOI-03 ("el futuro ya llegó", "en un mundo en constante evolución", "COBOL está más vivo que nunca", cierre "¿Qué opinas?"). **Ref:** `voice` VOI-03/06, design §16 (`domain/cliches_v1.txt`).
- [x] **B.6** `backend/tests/fixtures/regression_{solid,generic,invented_claim,invalid_json}.json` — 4 fixtures versionados §12.5 con expectativas declaradas. **Criterio:** parametrizado de regresión: sólido → sin blockers y score en rango; genérico → penalización de genericidad; cifra inventada → blocker; JSON inválido → apto para camino repair→`GENERATION_FAILED` (consumido por E). Sin scores exactos de LLM (rangos + reglas). **Ref:** `evaluation` EVAL-09, design §15.
- [x] **B.7** Cierre del lote: `pytest -q backend/tests/domain backend/tests/fixtures` verde 100%. **Criterio:** suite de dominio completa en verde. **Ref:** design §15, proposal "Tests de dominio (pytest)".

### Batch C — Contratos canónicos pydantic + generación de tipos TS (fuente única anti-drift) `[P0]`

- [x] **C.1** `backend/api/schemas.py` — TODOS los modelos de design §5.5 como pydantic (única fuente de verdad): `BriefIn` (thesis no vacía; `evidence: list[EvidenceItem]` clasificados `known_facts|author_opinions|open_questions`; constraints), `CandidateOut` (angle Literal cerrado `problem-story|practical-framework|argued-position`, hook/body/cta, claims `{text, support}`, content_version, evaluation/decision nullable), `GenerationOutput` con `model_validator` (exactamente 3, `angle` únicos), `EvaluationOutput`/`CandidateScore` (6 dimensiones con `rating: int 0..5` + `quote` + `rubric_rule`, `penalties{risk,generic}`, `score_final`, `blockers[]`), `DecisionOut`, `VisualContract`/`VisualElement` (rationale obligatorio), `ReceiptOut` (`mode="simulated"`, `status="SIMULATED_PUBLISHED"`, `notice="no se envió contenido a LinkedIn"`, `remote_id: None = None`), `ErrorBody`, `DemoIdeaOut`, `ProjectOut`/`ProjectDetailOut`, `RunOut`/`RunDetailOut`, `PublicationOut`, `HealthOut`. **Criterio:** test de contratos: 2 o 4 candidatos → rechazo; angles duplicados → rechazo; rating 7 → rechazo; dimensión sin quote/rubric_rule → inválida; `ReceiptOut(remote_id=...)` distinto de None → falla en construcción. **Ref:** `generation` GEN-01/02/04, `evaluation` EVAL-02/03, `simulation` SIM-02, `api` API-01, `genai-harness` HARN-04, design §5.5.
- [x] **C.2** `backend/ai/contracts.py` — reexporta/usa los MISMOS modelos pydantic de C.1 para la salida LLM (`GenerationOutput`, `EvaluationOutput`): el mismo schema que valida la salida del provider es el del contrato API. **Criterio:** test de identidad de clases (no redefinición); import desde `ai.contracts` y `api.schemas` referencia el mismo objeto. **Ref:** design §5.1, `genai-harness` HARN-04.
- [x] **C.3** Cierre del lote: tests de C.1/C.2 en verde. **Criterio:** suite de contratos pydantic pasa. **Ref:** design §15.

### Batch D — Persistencia SQLModel/SQLite en fichero + traza + seed `[P0]`

- [x] **D.1** `backend/db/engine.py` — engine + session factory con `DATABASE_PATH` de config; crea `data/` si falta. **Criterio:** test: SQLite temporal crea fichero; `create_all()` idempotente (2 ejecuciones no fallan). **Ref:** design §9.1, ADR-008, `fsm-trace` PST-01.
- [x] **D.2** `backend/db/models.py` — 5 tablas SQLModel (design §9.1): `ContentProject` (raw_idea, brief JSON, status=IDEA, voice_profile JSON default voz v0 provisional, timestamps), `GenerationRun` (project_id FK, status, provider, model?, prompt_version, schema_version, prompt_hash, trace_events JSON, raw_output? default off, error_code?, timestamps), `Candidate` (run_id FK, angle, hook/body/cta, claims JSON, content_version=1, evaluation JSON?, decision_history JSON?, selected=False, selection_reason?), `VisualAsset` (candidate_id FK, thesis, concept, elements JSON, alt_text, svg_path?, status), `PublicationAttempt` (candidate_id FK, mode="simulated", status, remote_id=None SIEMPRE null, receipt JSON, created_at). **Criterio:** test de invariantes §9.2: `angle` único por run; `remote_id` nulo en simulado; SIN columnas de credenciales (PST-02). **Ref:** design §9.1/§9.2, `fsm-trace` PST-01/02.
- [x] **D.3** `backend/db/repos.py` — repos finos por agregado (create/get project, set brief/status, create run, add candidates, get run detail con traza, update evaluation por candidato, update content_version + invalidar evaluación, save visual, update visual status, save publication attempt, list projects — este último P1-ready). Sin métodos de mutación de `trace_events` (append-only, TRC-03). **Criterio:** `test_repos.py` (SQLite temp): round-trip de los 5 agregados; ABRIR NUEVA SESIÓN lee lo persistido (reinicio conserva estado — PST-01); ejecución fallida conserva error+traza y NO expone candidatos incompletos como válidos. **Ref:** `fsm-trace` PST-01/TRC-03, design §9.2.
- [x] **D.4** `backend/db/seed.py` — 3 ideas demo (design §9.3: "Migrar COBOL no es traducir sintaxis…", "El mainframe sigue en producción por una razón…", "Modernizar no es cambiar de lenguaje…") con audiencia/objetivo default + perfil de voz v0 provisional; idempotente (solo si `ContentProject` vacío). **Criterio:** `test_seed.py`: doble seed no duplica; borrar fichero → arranque regenera el estado demo (PST-01 seed reproducible); `GET /api/ideas/demo` devuelve ≥3 (verificado luego en G). **Ref:** `capture` CAP-01/CAP-03, design §9.3, proposal Rollback.
- [x] **D.5** Cierre del lote: `pytest -q backend/tests/db` verde. **Criterio:** suite de persistencia pasa. **Ref:** design §15.

---

## Phase 2 — Capacidades (Wave 2: E y F en paralelo; requieren Wave 1 completa)

### Batch E — GenAI harness: prompts versionados, DemoProvider, retry/repair, traza `[P0]`

> Depende de B (validación determinística), C (contratos) y A1 (config/trace). Retry/repair VIVEN en el harness, NO en el provider (ADR-005).

- [x] **E.1** `backend/ai/prompts/linkedin-candidate-generator@1.0.0.md` + `backend/ai/prompts/editorial-evaluator@1.0.0.md` — estructura de design §6.1: propósito, contexto permitido, reglas de voz v0 PROVISIONAL (VOI-02), delimitadores sistema/datos, formato JSON de salida (contrato), ejemplos mínimos, prohibiciones (VOI-03). **Criterio:** checklist — evidencia del brief viaja como DATOS entre delimitadores (HARN-06 anti-inyección); reglas VOI-02/03 presentes; sin clichés dentro del prompt. **Ref:** `genai-harness` HARN-01/06, `voice` VOI-02/03, design §6.1.
- [x] **E.2** `backend/ai/prompts/manifest.json` — por capacidad: `{file, version, schema_version, sha256}` + resolver por id calculando hash al cargar. **Criterio:** test: `resolve("linkedin-candidate-generator@1.0.0")` devuelve ruta + sha256 estable; editar un prompt SIN subir versión rompe el test de hash (HARN-01 "cambio exige versión nueva"). **Ref:** `genai-harness` HARN-01, `generation` GEN-05, design §6.1.
- [x] **E.3** `backend/ai/providers.py` — `GenAIProvider` (Protocol: `name`, `generate_candidates(brief)`, `evaluate_candidates(candidates, brief, catalog_version)`) + `ProviderError` con `code` ∈ `TRANSIENT|INVALID_OUTPUT|UNAVAILABLE`. **Criterio:** test de protocolo con provider fake (HARN-02): ambos providers devuelven el mismo contrato; errores normalizados sin detalles de SDK. **Ref:** `genai-harness` HARN-02, design §6.2.
- [x] **E.4** `backend/ai/demo_provider.py` — `DemoProvider` DETERMINÍSTICO derivado del brief (sin random/red): los 3 ángulos se rellenan con tesis/audiencia/evidencia reales del brief; `claims` mapean evidence ids (sin evidencia → claims vacíos → blockers útiles para demo de regla); `name="DEMO_PROVIDER"`, `model=None`; `DEMO_FORCE_INVALID=1` devuelve JSON inválido (camino repair→`GENERATION_FAILED`). **Criterio:** `test_demo_provider.py`: mismo brief → misma salida byte a byte (HARN-03); atraviesa los MISMOS guards (cifra sin fuente no aparece como hecho validado); `DEMO_FORCE_INVALID` produce salida que el harness debe reparar/rechazar. **Ref:** `genai-harness` HARN-03, design §6.3, invariante transversal 5.
- [x] **E.5** `backend/ai/harness.py` — `run_generation(brief)`: resolver prompt+hash (traza `prompt_resolved`), loop 1..3 con backoff (0.5s/1.5s) ante `TRANSIENT` (traza `retry_scheduled`), validación pydantic (`output_validated`), `repair_once` ÚNICA con el error del schema (traza `repair_ok`/`repair_failed`; NUNCA reescribe contenido), agotado → `RunResult.failed("INVALID_OUTPUT"|"PROVIDER_TRANSIENT_ERROR")` (traza `generation_failed`); `run_evaluation(...)`: anonimiza candidatos + orden aleatorio con seed fija en demo (EVAL-07), degrada a solo-determinístico con `EVALUATION_PARTIAL` si el evaluador semántico falla (HARN-08, sin fabricar score); `raw_output` guardado SOLO si `TRACE_STORE_RAW_OUTPUT=true`; `redact_secrets` siempre. **Criterio:** `test_harness.py` con provider fake: 2 fallos transitorios + 1 ok → éxito con 3 intentos en traza; JSON inválido → repair 1x → ok; repair falla → `GENERATION_FAILED` conservando traza y con brief intacto (RNF-03); `DEMO_FORCE_INVALID` recorre repair→failed; traza sin secretos; raw_output off por defecto. **Ref:** `genai-harness` HARN-05/07/08, `generation` GEN-06, `evaluation` EVAL-07, design §6.5/§6.6.
- [x] **E.6** Cierre del lote: `pytest -q backend/tests/harness` verde (usa fixtures de B). **Criterio:** suite de harness pasa. **Ref:** design §15.

### Batch F — Visual: contrato SVG determinístico + ImageProvider opcional `[P0]` (P1 marcado donde aplica)

- [x] **F.1** `backend/visual/contract.py` — `build_visual_contract(thesis, candidate)` SIN LLM: mapa keyword→concepto versionado (design §7.1); genera `elements[]` con `{element_id, kind, description, rationale}` donde cada `rationale` cita frase/concepto literal de la tesis. **Criterio:** `test_visual.py`: contrato para la tesis demo de design §9.3 produce concepto NO decorativo; todo elemento con rationale no vacío (VIS-01/03). **Ref:** `visual` VIS-01/03, design §7.1.
- [x] **F.2** `backend/visual/validate.py` — valida: rationale no vacío por elemento, `alt_text` no vacío y específico, elementos prohibidos ausentes (marcas no autorizadas, texto ilegible, estereotipos retro sin relación argumental). **Criterio:** contrato con elemento sin rationale → rechazo → apto para `VISUAL_REVISION_REQUIRED`; sin alt_text → rechazo; elemento prohibido → rechazo (VIS-03/04/05/07). **Ref:** `visual` VIS-03/04/05/07, design §7.2.
- [x] **F.3** `backend/visual/svg.py` — `render_svg(contract)`: UNA plantilla editorial parametrizada 1200×630 (tesis corta + metáfora visual + elementos de dominio); escribe `data/visuals/{id}.svg`. **Criterio:** mismo contrato → SVG idéntico byte a byte (reproducibilidad); incluye alt text (accesibilidad); el asset queda con `svg_path` local (VIS-02). **Ref:** `visual` VIS-02, design §7.3.
- [x] **F.4** `backend/visual/image_provider.py` — interfaz `ImageProvider.generate(contract) -> ImageAsset` detrás de `VISUAL_PROVIDER=image`, DESACTIVADA por defecto; stub P1 que nunca se invoca con `VISUAL_PROVIDER=svg`; fallo → fallback a SVG con aviso + traza, nunca conmutación silenciosa. **[P1]** **Criterio:** con default no se instancia/invoca; contrato visual observable P0 sin cambios. **Ref:** proposal P1 (API de imágenes), design §7.4, ADR-006.
- [x] **F.5** Cierre del lote: `pytest -q backend/tests/visual` verde. **Criterio:** suite visual pasa. **Ref:** design §15.

---

## Phase 3 — Integración backend (Wave 3: SECUENCIAL — un solo agente)

### Batch G — API FastAPI + workflow + contrato OpenAPI vivo `[P0]`

> Depende de A1+B+C+D+E+F. Es la PRIMERA integración: autoriza transiciones FSM ANTES de persistir (design §1); traza ensamblada por el workflow (design §14).

- [x] **G.1** `backend/api/errors.py` — `ErrorBody` único + exception handlers: 400 `VALIDATION_ERROR`, 404 `NOT_FOUND`, 409 `STATE_TRANSITION_REJECTED` (mensaje con requisito faltante), 422 `CONTRACT_INVALID` (interno → expuesto como `GENERATION_FAILED`), 502 `PROVIDER_UNAVAILABLE`, 503 `SEMANTIC_EVALUATION_UNAVAILABLE`. **Criterio:** test de handlers: cada código mapea al body estructurado; mensajes accionables. **Ref:** design §12, `api` API-04.
- [x] **G.2** `backend/api/dependencies.py` — `get_session`, `get_settings`, `get_provider` (demo por default; openai SOLO si `GENAI_PROVIDER=openai` + key; sin conmutación automática — HARN-09), `get_harness`. **Criterio:** test: sin key → `DemoProvider`; con flag → provider correcto; nunca degradación silenciosa. **Ref:** `genai-harness` HARN-09, design §3.
- [x] **G.3** `backend/api/workflow.py` — servicio de aplicación: orquesta FSM+harness+visual+repos; `apply()` antes de persistir (ilegal → 409 con requisito); ensambla traza de `trace_events` + `evaluation/decision_history` + `receipt` (TRC-01); `CANDIDATE_EDITED` → `content_version++` + invalidación de evaluación/visual (APPR-02/03, FSM-03); `approve` exige razón + sin blockers (APPR-01); `simulate_publish` con guard candidato APPROVED + visual VISUAL_READY (SIM-04); `redact_secrets` antes de responder (TRC-02). **Criterio:** `test_workflow.py` (repos SQLite temp): happy path completo; edición invalida evaluación; blocker bloquea approve; `GENERATION_FAILED` conserva brief; traza append-only (la evaluación original sigue tras reevaluar — TRC-03). **Ref:** design §14, `fsm-trace` TRC-01/03, `approval` APPR-01/02/03, `simulation` SIM-04.
- [x] **G.4** Routers: `routers/meta.py` (`GET /api/health`); `routers/projects.py` (`GET /api/ideas/demo`, `POST /api/projects` → IDEA, `POST /api/projects/{id}/brief` → BRIEF_READY, `GET /api/projects/{id}`, `GET /api/projects` P1-ready); `routers/runs.py` (`GET /api/runs/{run_id}` traza redactada, `POST /api/runs/{run_id}/evaluate`); `routers/candidates.py` (`POST /api/projects/{id}/generate`, `POST /api/projects/{id}/retry-generate`, `POST /api/candidates/{id}/edit`, `request-revision`, `approve`, `visual`, `publish-simulated`); `routers/visuals.py` (`POST /api/visuals/{id}/approve`, `reject`, `GET /api/visuals/{id}/svg` resolviendo path DESDE la DB, sin path traversal). **Criterio:** `test_endpoints.py` con TestClient + SQLite temp: cada endpoint valida request/response contra schemas (API-01); brief sin tesis → 422 (API-01); aprobar sin evaluación → 409 accionable (API-04, FSM-02); doble generate → segunda rechazada/ignorada sin segunda ejecución (API-05, RNF-05); `GET svg` responde `image/svg+xml`; flujo completo vía HTTP termina `SIMULATED_PUBLISHED` con traza consultable (API-01, SIM-01). **Ref:** design §5.4/§12/§13.5, `api` API-01/04/05, `simulation` SIM-01.
- [x] **G.5** `backend/api/main.py` — FastAPI app: lifespan con `create_all()` idempotente + seed (ADR-008), CORS allowlist `CORS_ORIGINS` con `allow_credentials=false` (API-03), `/docs`+`/redoc` solo en `APP_ENV=dev`, monta routers, uvicorn bind `127.0.0.1`. **Criterio:** `uvicorn api.main:app` arranca; `GET /openapi.json` 200; preflight CORS responde headers correctos; seed aplicado al primer arranque y no duplica al reiniciar. **Ref:** `api` API-03, `local-run` RUN-01, design §11.2/§13.
- [x] **G.6** Generar y COMMITEAR `frontend/src/api/schema.d.ts` con `npm run schema:generate` (openapi-typescript contra backend vivo) + cachear `frontend/src/api/openapi.json` (open question §19-1, recomendación: sí). **Criterio:** `schema.d.ts` contiene `components["schemas"]["CandidateOut"]` y el resto del contrato; `npm run schema:check` pasa (diff vacío). **Ref:** design §5.2/§5.3, ADR-003, `api` API-02.
- [x] **G.7** Cierre del lote: `pytest -q backend/tests` COMPLETO en verde (domain+harness+visual+db+api). **Criterio:** suite backend P0 100% verde. **Ref:** design §15.

---

## Phase 4 — Frontend (Wave 4: SECUENCIAL — H1 y luego H2; requieren G)

### Batch H1 — FE base: client tipado, useAsync, primitivas UI `[P0]`

- [x] **H1.1** `frontend/src/api/client.ts` — fetch wrapper tipado contra `schema.d.ts` (importa SOLO de ahí; PROHIBIDO DTOs de API a mano — ADR-003); errores → `ErrorBody` tipado; helpers por endpoint. **Criterio:** `tsc --noEmit` compila; test unit con fetch mock: error 409 → `ErrorBody{code,message,details}` expuesto. **Ref:** design §5.2/§10.1, `api` API-04.
- [x] **H1.2** `frontend/src/hooks/useAsync.ts` — `{data, error, busy, run}`: `busy` deshabilita botones y BLOQUEA doble envío (RNF-05); sin requests duplicados. **Criterio:** test unit: `run()` dispara request; segundo `run()` mientras `busy` es ignorado; `busy` vuelve a false al terminar. **Ref:** `local-run` RUN-04, design §10.3.
- [x] **H1.3** `frontend/src/components/ui/*` — `Banner` (variantes SIMULACIÓN/DEMO_PROVIDER persistentes), `ScoreBreakdown` (dimensiones + penalizaciones + UMBRALES Y FÓRMULA visibles como calibrables), `CandidateCard`, `AngleTag`, `ErrorBanner` (code+message+detalle accionable), `BlockersList`, `ReceiptCard` (recibo local SIN URLs/IDs remotos), `VoiceBadge` ("perfil de voz provisional v0"). **Criterio:** tests de render (RTL): banner "SIMULACIÓN" presente en vistas de publicación; "DEMO_PROVIDER" en vistas de generación/evaluación (RUN-06); VoiceBadge etiqueta provisional (VOI-01); ScoreBreakdown muestra fórmula y umbrales (EVAL-08). **Ref:** `local-run` RUN-03/06, `voice` VOI-01, `evaluation` EVAL-08, `simulation` SIM-02.
- [x] **H1.4** `frontend/src/styles/*` + editar `frontend/vite.config.ts` agregando bloque `test` (vitest, RTL, tag `contract` excluida del run normal). **Criterio:** `npm --prefix frontend run test` corre la suite unit FE (sin backend). **Ref:** design §10.1/§15.
- [x] **H1.5** Cierre del lote: tests unit de H1 en verde; `tsc --noEmit` ok. **Criterio:** base FE estable para H2. **Ref:** design §15.

### Batch H2 — Wizard 10 pasos + App (flujo completo y estados honestos) `[P0]`

> Depende de H1 (client, useAsync, ui). El wizard espeja la FSM del proyecto (design §10.2).

- [x] **H2.1** `frontend/src/main.tsx` + `frontend/src/App.tsx` — layout global: header con proveedor + voz v0, banda SIMULACIÓN persistente en vistas relevantes, monta `Wizard`. **Criterio:** render test: header muestra provider; banda en vistas de publicación. **Ref:** design §10.1, `local-run` RUN-03.
- [x] **H2.2** `frontend/src/components/Wizard.tsx` + `steps/IdeaStep.tsx` — 3 ideas demo + idea manual con validación (rechaza vacío/solo espacios, CAP-01). **Criterio:** test: idea vacía → error accionable sin crear proyecto; idea demo → `POST /projects` y muestra idea como base. **Ref:** `capture` CAP-01, design §10.2.
- [x] **H2.3** `steps/BriefStep.tsx` — tesis/audiencia/objetivo/evidencia clasificada (`known_facts|author_opinions|open_questions`)/restricciones + badge voz provisional; OBLIGA tesis única + ≥1 evidencia antes de continuar (CAP-02); defaults demo cuando audiencia/objetivo vacíos (CAP-03). **Criterio:** tests: sin tesis → bloqueado; sin evidencia → bloqueado; defaults aplicados. **Ref:** `capture` CAP-02/03/05, `voice` VOI-01.
- [x] **H2.4** `steps/GeneratingStep.tsx` — botón "Generar 3 candidatos"; in-flight `GENERATING` con spinner y botones deshabilitados (RNF-05); `GENERATION_FAILED` con acción reintentar distinguiendo el fallo (RUN-03); resultados etiquetados `DEMO_PROVIDER` (RUN-06). **Criterio:** tests: doble click → una sola ejecución; fallo → reintentar sin representar éxito. **Ref:** `local-run` RUN-03/04/06, `api` API-05.
- [x] **H2.5** `steps/CandidatesStep.tsx` — comparación de 3 candidatos: ángulos distintos, hooks, claims, badges `DEMO_PROVIDER`. **Criterio:** render test con datos del contrato (3 cards, ángulos visibles). **Ref:** `generation` GEN-02, design §10.2.
- [x] **H2.6** `steps/EvaluateStep.tsx` — ScoreBreakdown por candidato (dimensiones+penalizaciones+blockers); umbrales y fórmula como iniciales/calibrables (EVAL-08); `RECOMMENDED`/`REVISION_REQUIRED`; `EVALUATION_PARTIAL` honesto ("evaluación semántica no disponible", sin score fabricado — HARN-08). **Criterio:** tests por estado; en `EVALUATION_PARTIAL` NO se muestra score completo. **Ref:** `evaluation` EVAL-01/08, `genai-harness` HARN-08.
- [x] **H2.7** `steps/ReviewStep.tsx` — editar candidato (invalida evaluación → reevaluar, APPR-02/03); elegir candidato distinto del recomendado CON razón (APPR-04); `request-revision` con razón. **Criterio:** tests: edición marca evaluación desactualizada; selección alternativa sin razón → error. **Ref:** `approval` APPR-02/03/04.
- [x] **H2.8** `steps/ApproveStep.tsx` — aprobación humana con razón OBLIGATORIA; bloqueada con blocker activo y sin razón; override desde `REVISION_REQUIRED` explícito (APPR-01). **Criterio:** tests: aprobar sin razón → rechazo; con blocker → mensaje de resolución; override con razón OK. **Ref:** `approval` APPR-01, `genai-harness` HARN-06, invariante 3.
- [x] **H2.9** `steps/VisualStep.tsx` — muestra SVG (`/api/visuals/{id}/svg`) + `visual_rationale` + alt_text; aprobar/rechazar con razón (VIS-06); regenerar desde `VISUAL_REVISION_REQUIRED`. **Criterio:** tests de interacción; NO hay autoaprobación (VIS-06). **Ref:** `visual` VIS-06, invariante 3.
- [x] **H2.10** `steps/PublishStep.tsx` — vista previa texto+imagen "como se enviarían" SIN ejecutar envío (SIM-03); banda "SIMULACIÓN" persistente (RUN-03); recibo local con notice "no se envió contenido a LinkedIn" y SIN URL/URN/ID remoto (SIM-02). **Criterio:** tests: el recibo renderizado no contiene `remote_id` ni URLs; banda visible en todas las vistas relevantes. **Ref:** `simulation` SIM-01/02/03, `local-run` RUN-03.
- [x] **H2.11** `steps/TraceStep.tsx` — traza: versiones de prompt/schema + hash, proveedor (`DEMO_PROVIDER`), validaciones, score desglosado, decisiones, ediciones (`content_version`), modo/recibo de publicación; distingue tipos de evento; sin secretos (TRC-01/02). **Criterio:** tests de render por tipo de evento; ningún valor de credencial visible. **Ref:** `fsm-trace` TRC-01/02, `local-run` RUN-06.
- [x] **H2.12** Cierre del lote: `npm --prefix frontend run test` COMPLETO en verde (unit, sin suite contract). **Criterio:** suite FE unit 100% verde. **Ref:** design §15.

---

## Phase 5 — Contrato FE/BE (Wave 5: SECUENCIAL; requiere G + H)

### Batch I — Suite vitest `contract` anti-drift `[P0]`

> Requiere backend VIVO para round-trip; la suite se omite (tag) sin backend (design §5.3).

- [x] **I.1** `frontend/src/tests/contract/openapi-drift.test.ts` — regenera `schema.d.ts` a temp y compara byte a byte con el commiteado; fallo = "corré `npm run schema:generate`". **Criterio:** pasa con contrato actual; un cambio unilateral en el BE (sandbox) lo hace fallar (API-02 drift detectado). **Ref:** design §5.3, ADR-003, `genai-harness` HARN-04.
- [x] **I.2** `frontend/src/tests/contract/roundtrip-smoke.test.ts` — con backend vivo: `POST` brief demo → `generate` (DemoProvider) → valida la respuesta contra el JSON Schema de `/openapi.json` y compila contra `schema.d.ts`. **Criterio:** test pasa; falla si el FE interpreta mal campos/tipos. **Ref:** design §5.3, `api` API-02.
- [x] **I.3** `frontend/src/tests/contract/schema-coverage.test.ts` — check estático: cada campo referenciado en `src/**` existe en `schema.d.ts`. **Criterio:** pasa; referenciar un campo inexistente → falla. **Ref:** design §5.3.
- [x] **I.4** Verificación: `npm run schema:check` y `npm run test:contract` en verde con backend vivo. **Criterio:** anti-drift operativo de punta a punta. **Ref:** design §5.3, RUN-01.

---

## Phase 6 — Cierre P0 (Wave 6: SECUENCIAL; requiere I)

### Batch J — README, decisiones/supuestos, semana adicional, datos demo + guion, verificación `[P0]`

- [x] **J.1** `README.md` — prerequisitos (Node v24.14.0, Python 3.12.7), instalación limpia (`npm install`, `pip install -r backend/requirements.txt`, `npm run dev`), modo demo sin credenciales ni red, limitaciones (SIN publicación real; SIN predicción de viralidad), guion de demo 5-7 min (SOLUTION.md §15), regla de corte, referencia a `SOLUTION.md`. **Criterio:** un evaluador sigue el README y arranca sin pasos omitidos (RUN-05). **Ref:** `local-run` RUN-01/05, proposal.
- [x] **J.2** Documento de decisiones y supuestos (`docs/decisions.md` o sección del README): los 9 ADR (design §2) + supuestos del proposal (voz v0 PROVISIONAL no validada, umbrales 72/4/60 calibrables, heurística ≠ viralidad, SQLite en fichero, DemoProvider sin keys). **Criterio:** revisión: cubre ADR-001..009 y todos los supuestos del proposal. **Ref:** design §2, proposal Supuestos.
- [x] **J.3** Sección "Semana adicional" (roadmap post-MVP) en README: publicación real vía OAuth + app de LinkedIn (§9.2 SOLUTION.md), Alembic con datos a preservar, validación de voz con publicaciones aprobadas, adaptadores P1 activables, refinamiento de rúbrica con datos. **Criterio:** sección documentada y consistente con el Out of Scope del proposal. **Ref:** proposal Out of Scope, design §18.
- [x] **J.4** Datos demo verificados + guion de demo ejecutado: recorrer el happy path oficial (idea demo → brief → generar 3 → evaluar → aprobar → visual → simular → traza) contra el backend vivo, y el segundo caso (design §6.3, SOLUTION.md §15): `DEMO_FORCE_INVALID=1` → repair → `GENERATION_FAILED` → reintentar con brief intacto. **Criterio:** happy path termina `SIMULATED_PUBLISHED` determinístico; caso de fallo conserva brief y traza (RNF-03). **Ref:** `local-run` RUN-02, `generation` GEN-06, proposal Métricas de éxito.
- [x] **J.5** Verificación final de criterios de aceptación P0 (SOLUTION.md §14, checklist del proposal "Métricas de éxito"): correr `npm test` (raíz) COMPLETO (pytest + vitest) + `npm run test:contract`, y recorrer la checklist contra la app corriendo. **Criterio:** todos los checks P0 verdes; 0 fallos de test. **Ref:** proposal Métricas de éxito, design §15.
- [ ] **J.6** Commits por vertical slice + commit final de integración (conventional commits, sin atribución IA). **Criterio:** `git log` muestra slices por lote; working tree limpio; `git revert` de un slice es viable (rollback plan). **Ref:** proposal Rollback Plan.

---

## Phase 7 — P1 opcional, NO bloqueante (Wave 7: SECUENCIAL; SOLO si P0 verde y hora < corte)

### Batch K — Adaptador OpenAI-compatible, historial UI, E2E, ImageProvider, Alembic `[P1]`

### Enhancement — Selección explícita DemoProvider/OpenAI `[P1]`

- [x] **ENH.1** Implementar provider OpenAI-compatible con `httpx`, selección por request, key solo backend/env, respuesta cruda al harness y errores normalizados.
- [x] **ENH.2** Exponer selector UX antes de generar, etiquetas honestas `DEMO_PROVIDER`/`OPENAI_PROVIDER`, retry y retorno explícito a DemoProvider.
- [x] **ENH.3** Agregar tests mockados de transporte, key ausente, contrato común y documentación de configuración.

- [ ] **K.1** `backend/ai/openai_compat.py` — httpx POST `${OPENAI_BASE_URL}/chat/completions` con `OPENAI_API_KEY`/`OPENAI_MODEL`, `temperature=0.4`, `timeout=60s`, `response_format={"type":"json_object"}` cuando lo soporte; activo SOLO si `GENAI_PROVIDER=openai` + key; sin key/red → `ProviderError(UNAVAILABLE)` → UI sugiere `DemoProvider` (NUNCA conmutación automática); proveedor/modelo en traza, NUNCA la key. **Criterio:** test con `httpx.MockTransport`: 200 → salida validada por el MISMO contrato; 401/network → `UNAVAILABLE`; traza sin key (GEN-05, TRC-02). **Ref:** P1-01, design §6.4, `genai-harness` HARN-02/09.
- [ ] **K.2** Historial navegable: vista de proyectos (`GET /api/projects`, ya soportado) + reapertura de proyecto/run/traza desde la UI. **Criterio:** P1-02 — navegar entre ejecuciones persiste tras reinicio (SQLite fichero). **Ref:** P1-02, `api` API-06.
- [ ] **K.3** Prueba E2E (Playwright) del happy path completo. **Criterio:** P1-03 — `npx playwright test` verde sobre la app corriendo. **Ref:** P1-03.
- [ ] **K.4** Implementación del `ImageProvider` real detrás de la interfaz de F.4 (`VISUAL_PROVIDER=image`), desactivada por defecto; fallo → fallback a SVG con aviso en UI + traza. **Criterio:** P1-04 — con API key genera asset; sin key, fallback con aviso y el contrato visual observable P0 sin cambios. **Ref:** P1-04, design §7.4, ADR-006.
- [ ] **K.5** Alembic (autogenerate) si el esquema evoluciona con datos a preservar; documentado en README. **Criterio:** documentado; sin impacto en P0. **Ref:** ADR-008, design §9.3/§18.

---

## 3. Orden de implementación recomendado (resumen)

1. **Wave 1 en paralelo** (A1 scaffold + B dominio + C contratos + D persistencia) — B y C son los críticos.
2. **Wave 2 en paralelo** (E harness + F visual) — tras B+C.
3. **Wave 3 SECUENCIAL** (G API+workflow) — primer hito integrador; produce `/openapi.json` y `schema.d.ts` commitado.
4. **Wave 4 SECUENCIAL** (H1 → H2 frontend) — contra el contrato vivo.
5. **Wave 5 SECUENCIAL** (I suite contract anti-drift).
6. **Wave 6 SECUENCIAL** (J cierre P0: docs, guion, verificación de aceptación).
7. **Wave 7 (P1)** — SOLO si P0 verde y dentro del corte horario.

## 4. Criterios de corte (regla de corte §19 SOLUTION.md)

- **P0 = Phases 1-6 (A1..J).** La demo NO se entrega sin: flujo completo a `SIMULATED_PUBLISHED`, `DemoProvider` etiquetado, FSM honesta testeada, contrato anti-drift, tests P0 verdes.
- **P1 = Phase 7 (K).** NUNCA bloquea ni condiciona la aceptación de P0. Si P0 atrasa a la **hora 14** del plan de 24 h, NO se implementa ningún P1 (flujo completo > profundidad cosmética).
- **Corte por lote:** un lote está DONE solo cuando su criterio verificable pasa (tests en verde, comando documentado ejecutado, archivos objetivo presentes). Un lote con criterio fallido NO avanza de wave.
- **Sin API key configurada** el sistema MUST funcionar completo en demo; un fallo del adaptador P1 se degrada DESACTIVÁNDOLO sin tocar P0 (spec.md §6).
- **DB descartable:** borrar `data/engine.db` regenera el estado demo (seed) — nunca bloquea la demo por datos corruptos.

## 5. Testing total (resumen por capa)

| Capa | Lote | Comando |
|---|---|---|
| Dominio (fórmula, penalizaciones, blockers, decisión, validaciones, FSM, fixtures) | B | `pytest -q backend/tests/domain backend/tests/fixtures` |
| Harness (DemoProvider, retry/repair, traza, redacción) | E | `pytest -q backend/tests/harness` |
| Visual (contrato, validación, SVG reproducible) | F | `pytest -q backend/tests/visual` |
| Repos/seed (5 agregados, invariantes, idempotencia) | D | `pytest -q backend/tests/db` |
| API (endpoints, 409/422, happy path HTTP, `GENERATION_FAILED` conserva brief) | G | `pytest -q backend/tests/api` |
| FE unit (wizard, banners, in-flight, errores) | H1/H2 | `npm --prefix frontend run test` |
| Contrato FE/BE (drift, round-trip, coverage) | I | `npm run test:contract` (requiere backend vivo) |
| Suite completa | J | `npm test` (raíz: pytest + vitest) |
