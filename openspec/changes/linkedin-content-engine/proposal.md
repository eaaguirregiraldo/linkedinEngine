# Proposal: `linkedin-content-engine` — Motor editorial asistido por GenAI para LinkedIn (MVP local)

> Fase: `sdd-propose` | Fecha: 2026-08-08 | Modo de persistencia: **hybrid** (openspec + Engram)
> Dependencias: `SOLUTION.md` (fuente de verdad: RF-01..07, RNF-01..05), `openspec/init.md`, `openspec/changes/linkedin-content-engine/exploration.md`, Engram `sdd/linkedin-content-engine/{explore,state}` y `sdd-init/linkedin`.

## Problema

Convertir conocimiento experto sobre COBOL/mainframes en publicaciones de LinkedIn es un proceso lento y variable. Un chat conectado a un LLM no demuestra un proceso editorial: genera ruido, no justifica sus recomendaciones y no distingue una simulación de una publicación real. `SOLUTION.md` define un MVP de 24 h que sí lo hace: un motor local que transforma una idea en un brief, genera exactamente tres candidatos estructurados, los evalúa con una heurística transparente, exige aprobación humana, propone un visual vinculado a la tesis y cierra con una publicación simulada inequívoca y una traza auditable. Hoy el directorio contiene **solo** ese documento: no hay código, no hay repo git.

Esta propuesta convierte la definición de producto en un plan de construcción ejecutable, respetando el stack ya congelado por el usuario (Vite+React + FastAPI+Python + SQLite con SQLModel, **NO Drizzle**) y acotando P0/P1 para que la demo funcione sin credenciales.

## Objetivo

Construir un MVP local, arrancable con un comando, que recorra de punta a punta `idea → brief → 3 candidatos → evaluación+blockers → aprobación humana → visual SVG → SIMULATED_PUBLISHED → traza`, con disciplina de ingeniería GenAI (prompts versionados, contratos de salida, guardrails, retry/repair, evaluación y trazabilidad) y **sin depender de ninguna API externa**.

## Usuarios

- **Autor (primario):** Juan Lucas Barbier — construye presencia profesional en LinkedIn sobre COBOL/mainframes; conserva su voz (perfil v0 provisional) y la aprobación final.
- **Editor/evaluador (secundario):** revisa calidad, riesgos, coherencia de voz y estado de publicación.
- **Evaluador de la prueba:** arranca localmente, recorre el happy path con resultados determinísticos y verifica los criterios de aceptación sin credenciales.

## Alcance

### In Scope — P0 (obligatorio para la demo)

- App local de un solo usuario: SPA React+Vite (TypeScript) + API FastAPI (Python) + SQLite en fichero vía SQLModel; dos procesos coordinados por script root con `concurrently` + CORS.
- Tres ideas demo + idea propia; brief con tesis, audiencia, objetivo, evidencia y restricciones (RF-01).
- Generación de exactamente tres candidatos con ángulos distintos y salida validada por contrato (RF-02).
- GenAI harness: prompts versionados (`linkedin-candidate-generator@1.0.0`, `editorial-evaluator@1.0.0`) con manifiesto y hash, schemas pydantic compartidos FE/BE, validaciones determinísticas + semánticas, guardrails, retry/repair (2 reintentos con backoff, 1 reparación de JSON inválido) y trazabilidad por ejecución (RF-07).
- `DemoProvider` determinístico (fixtures derivados del brief, no random) que atraviesa los mismos schemas, guardrails y transiciones que un provider remoto; UI y traza etiquetan `DEMO_PROVIDER`.
- Evaluación heurística 0-100 desglosada (fórmula §7.2), penalizaciones, blockers y regla de decisión `RECOMMENDED` / `REVISION_REQUIRED` (RF-03).
- Edición con invalidación de evaluación y aprobación humana explícita con razón registrada (RF-04).
- Visual SVG determinístico con contrato visual, `visual_rationale` (vínculo de cada elemento con la tesis) y alt text; aprobación humana (RF-05).
- Publicación simulada con estado `SIMULATED_PUBLISHED`, banda persistente "SIMULACIÓN" y recibo local; prohibido inventar URLs o IDs remotos (RF-06, RNF-02).
- FSM honesta (~15 estados) en dominio puro Python; `PUBLISHED_REAL` es estado reservado, nunca alcanzable sin API real verificada.
- Tests de dominio (pytest): fórmula, blockers, transiciones y validación de schema; fixtures de regresión (§12.5) incluidos.
- README con prerequisitos, comandos, modo demo y limitaciones; `.env.example` sin secretos.

### In Scope — P1 (solo si P0 está estable; la aceptación NO depende de esto)

- Adaptador remoto **OpenAI-compatible** (chat completions) detrás de la interfaz `GenAIProvider`, activable por API key del usuario; si se usa, proveedor/modelo quedan identificados en la traza; si no, la UI dice `DEMO_PROVIDER`.
- Historial navegable de ejecuciones (ya soportado por SQLite en fichero).
- Prueba E2E (Playwright) del happy path.
- **API de imágenes opcional** detrás de una interfaz, **desactivada por defecto** (P0 usa solo SVG determinístico).

### Out of Scope (explícito)

- **Publicación real en LinkedIn** (OAuth, app registrada, permisos): requiere credenciales y permisos fuera del control del MVP; el camino futuro queda documentado (§9.2 de SOLUTION.md), no implementado.
- Autenticación, multiusuario, workspaces.
- Scheduler, calendario, colas, RAG/vectores, fine-tuning.
- Predicción estadística de viralidad (la heurística NO estima impresiones/likes).
- Imágenes fotorrealistas generativas como requisito; cloud/serverless (la app es 100% local, RNF-01).
- Scraping de LinkedIn o evasión de términos de servicio.

## Capacidades

1. Crear un brief válido con la voz provisional aplicada (RF-01).
2. Generar exactamente 3 candidatos diferenciados con contrato validado (RF-02).
3. Validar (determinístico + semántico) y evaluar con señal desglosada 0-100 (RF-03).
4. Recomendar o exigir revisión según umbrales reproducibles; un blocker de evidencia impide recomendar aunque el score sea alto (RF-03).
5. Editar con invalidación de la evaluación previa y aprobar humanamente (RF-04).
6. Producir un contrato visual + tarjeta SVG con rationale y alt text (RF-05).
7. Simular la publicación con estado y etiqueta inequívocos (RF-06).
8. Consultar la traza completa sin exponer secretos (RF-07, RNF-04).
9. Correr en modo demo sin credenciales con resultados determinísticos (RNF-01).
10. Degradar con control ante fallos: `GENERATION_FAILED` conserva traza y el brief queda disponible (RNF-03).

## Flujo de valor

1. Elegir/crear idea → 2. completar brief → 3. generar 3 candidatos → 4. validar contratos → 5. evaluar y puntuar (dimensión + penalizaciones + explicación) → 6. decidir (`RECOMMENDED` / `REVISION_REQUIRED`) → 7. editar/reevaluar/aprobar (humano) → 8. visual SVG vinculado a la tesis → 9. `SIMULATED_PUBLISHED` con advertencia → 10. consultar traza (prompt, schema, proveedor, score, decisión). Demo oficial de 5-7 min definida en SOLUTION.md §15.

## Enfoque (Approach)

Dos procesos coordinados por un script root (`concurrently`): SPA React+Vite consumiendo la API FastAPI (uvicorn) con CORS. Capas en Python:

- **`backend/domain/`** (cero dependencias): FSM tipada `apply(state, event) -> result` con guards, fórmula de evaluación (§7.2) y reglas de blockers. Testeable con repos in-memory.
- **`backend/ai/`**: prompts versionados + manifiesto; interfaz `GenAIProvider` (`generate_candidates(brief)`, `evaluate_candidates(...)`) con `DemoProvider` (P0) y adaptador OpenAI-compatible (P1); harness con retry/repair y traza. Retry/repair viven en el harness, no en el provider.
- **`backend/api/`**: FastAPI; contratos pydantic validan requests y respuestas; **schema canónico** compartido FE/BE (mitiga el drift del doble stack).
- **`backend/db/`**: SQLite en fichero con repos finos sobre 5 agregados (`ContentProject`, `GenerationRun`, `Candidate`, `VisualAsset`, `PublicationAttempt`); evaluación/decisiones/traza como JSON en `GenerationRun`/`Candidate`.
- **`frontend/`**: React+Vite (TS); wizard de 10 pasos; etiquetas `DEMO_PROVIDER` y "SIMULACIÓN" persistentes; estados en curso con bloqueo de envíos duplicados (RNF-05).
- **Script root + `.env.example` + README.**

**Elección de persistencia (razonada): SQLModel sobre SQLAlchemy puro.** El proyecto ya usa pydantic como contrato canónico (requests y salida GenAI). SQLModel unifica modelo de datos y validación en una sola clase pydantic, eliminando la duplicación de modelos que implica SQLAlchemy puro (declarative + conversión a pydantic), y se apoya en SQLAlchemy 2.0 debajo (transacciones, sesiones, migraciones Alembic futuras). Es del mismo autor que FastAPI → ecosistema coherente y menos piezas en 24 h. Drizzle queda descartado (es TypeScript; el dominio y la persistencia viven en Python). Tradeoff aceptado: una capa de abstracción sobre SQLAlchemy; si un caso no lo cubre, se degrada a SQLAlchemy puro sin cambiar la interfaz de repos.

**Aclaración explícita sobre adaptadores opcionales:** OpenAI y la API de imágenes son adaptadores OPCIONALES (P1), NO requisitos de la demo. La demo oficial corre con `DemoProvider` + SVG determinístico, sin API key y sin red.

## Áreas afectadas (Affected Areas)

| Área | Impacto | Descripción |
|---|---|---|
| `backend/domain/` | Nuevo | FSM tipada, fórmula de evaluación, reglas de blockers; cero dependencias |
| `backend/ai/` | Nuevo | Harness GenAI: prompts versionados + manifiesto, providers (Demo + adaptador P1), retry/repair, traza |
| `backend/api/` | Nuevo | FastAPI: endpoints del flujo, contratos pydantic, CORS |
| `backend/db/` | Nuevo | SQLite + SQLModel: repos finos, 5 agregados, seed de ideas demo |
| `frontend/` | Nuevo | SPA React+Vite: wizard, comparación, edición, visual, recibo, traza |
| raíz (`package.json`, script) | Nuevo | Script root de arranque (`concurrently`), `.env.example`, README |
| `tests/` | Nuevo | pytest (fórmula, blockers, transiciones, schema) + fixtures de regresión; vitest FE; tests de contrato FE/BE |
| `SOLUTION.md` | Referencia (no se modifica) | Fuente de verdad de producto: RF-01..07, RNF-01..05, criterios de aceptación |

## Supuestos

- No hay API keys GenAI configuradas → la demo corre con `DemoProvider`; el adaptador P1 solo si el usuario provee key.
- La voz de Juan Lucas es un perfil PROVISIONAL (v0) etiquetado como tal; no existe corpus validado.
- La heurística es señal de calidad/potencial de conversación, NO predicción de viralidad.
- SQLite en fichero (no in-memory) para que el historial P1 sobreviva reinicios.
- La publicación real requiere app de LinkedIn aprobada + OAuth + permisos: fuera de alcance, no se inventan credenciales.
- Umbrales (72 / diferencia 4 / 60) iniciales y documentados como calibrables (§7.3).
- Entorno verificado: Node v24.14.0 + npm 11.9.0 y Python 3.12.7 (sin pnpm/uv) en la máquina (sdd-init).

## Métricas de éxito (criterios de aceptación P0, SOLUTION.md §14)

- [ ] Arranca localmente siguiendo el README, sin credenciales externas, en modo demo.
- [ ] La UI y la traza identifican inequívocamente `DEMO_PROVIDER` cuando no hubo llamada GenAI real.
- [ ] `DemoProvider` atraviesa los mismos schemas, guardrails y transiciones que un provider remoto.
- [ ] Ofrece al menos tres ideas demo y permite una idea manual.
- [ ] Obliga a definir tesis y evidencia antes de generar.
- [ ] Produce exactamente tres candidatos con `angle` únicos, sin hooks/bodies idénticos normalizados y con contrato válido.
- [ ] Heurística desglosada con penalizaciones y umbrales visibles.
- [ ] `RECOMMENDED` / `REVISION_REQUIRED` reproducibles según reglas.
- [ ] Un blocker de evidencia impide recomendar aunque el score sea alto.
- [ ] Una edición invalida la evaluación previa.
- [ ] La aprobación final siempre es humana.
- [ ] El visual vincula cada elemento con la tesis, tiene alt text y requiere aprobación humana.
- [ ] El happy path termina en `SIMULATED_PUBLISHED` con advertencia inequívoca; sin URL/ID remoto inventado.
- [ ] La traza muestra versiones de prompt/schema, proveedor, validaciones y decisión; sin secretos.
- [ ] El fallo de un proveedor no destruye el brief ni se representa como éxito.
- [ ] Tests automatizados para fórmula, blockers, transiciones y validación de schema.
- [ ] Un comando arranca ambos procesos (script root verificado).

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Doble stack: drift de contrato FE (TS) / BE (pydantic) | Media | Schema canónico pydantic + tests de contrato FE/BE desde el inicio |
| Coordinación de dos procesos (Vite + FastAPI) falla en demo | Media | Script root con `concurrently`, puertos fijos, CORS probado, instalación limpia verificada en README |
| Demo sin API key parece incompleta | Media | `DemoProvider` determinístico etiquetado `DEMO_PROVIDER`; adaptador P1 opcional, aceptación no depende de él |
| Simulación confundida con publicación real | Baja | Estados separados, banda persistente, sin IDs remotos falsos, `PUBLISHED_REAL` reservado e inalcanzable |
| FSM ~15 estados con transiciones ilegales | Media | Tests de tabla desde el inicio; guards en dominio puro |
| Contenido genérico / alucinaciones | Media | Brief obligatorio, claim ledger, blockers, penalización de genericidad, aprobación humana |
| Churn de versiones Node/React/Python | Baja | Pin de versiones exactas en `package.json` y requirements/pyproject al scaffold |
| Alcance excesivo en 24 h | Alta | Recortes congelados; regla de corte (§19 SOLUTION.md): si P0 atrasa, no se toca P1 |

## Rollback Plan

- Proyecto nuevo sin repo git → crear repo git al inicio del apply y commitear por vertical slice; revertir = `git revert` / `git checkout` de un slice, sin migraciones destructivas.
- SQLite en fichero con seed reproducible: borrar el fichero de DB regenera el estado demo (datos de demo por seed, no por migración irreversible).
- Adaptadores P1 (OpenAI, API de imágenes) activables por variable de entorno/flag y DESACTIVADOS por defecto: si fallan, se desactivan sin tocar P0.
- Regla de corte: si P0 se atrasa a la hora 14 del plan, NO se implementa P1; el flujo completo tiene prioridad sobre profundidad cosmética.
- FSM y fórmula en dominio puro sin deps: una regla de decisión errónea se corrige en el módulo y los tests lo verifican; las transiciones se validan antes de persistir, no hay estado corrupto.

## Dependencies

- Node v24.14.0 + npm 11.9.0 y Python 3.12.7 (instalados y verificados en sdd-init).
- Paquetes a agregar en apply: `react`, `vite`, `concurrently` (FE) y `fastapi`, `uvicorn`, `sqlmodel`/`sqlalchemy`, `pydantic`, `pytest` (BE); `typescript` + `vitest` para contratos/tests.
- Ninguna API externa, ninguna key, ningún servicio cloud (RNF-01). P1 opcional: key del usuario + endpoint OpenAI-compatible.
- Fuente de verdad de producto: `SOLUTION.md` (no se modifica en este cambio).

## Decisiones que se cierran en design (no bloquean specs)

- Esquema canónico del contrato FE/BE: pydantic como fuente + tipos TS (generados o espejo verificado por test de contrato).
- Estructura exacta del manifiesto de prompts y del formato de traza.
- Forma del script root (shell + `concurrently`) y puertos fijos.
