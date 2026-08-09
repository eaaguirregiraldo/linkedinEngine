# Spec — `linkedin-content-engine`

> Fase: `sdd-spec` | Fecha: 2026-08-08 | Modo: **hybrid** (openspec + Engram)
> Dependencias: `proposal.md` (espejo Engram #878), `SOLUTION.md` (fuente de verdad: RF-01..07, RNF-01..05), `openspec/init.md`, `exploration.md`, Engram `sdd/linkedin-content-engine/{explore,proposal,state}` y `sdd-init/linkedin`.
> Rol de este archivo: índice consolidado + invariantes transversales + alcance P0/P1 + matriz de cobertura. Las requirements detalladas con escenarios Given/When/Then viven en `specs/{domain}/spec.md`.

## 1. Propósito

Especificar el comportamiento observable (WHAT, no HOW) del motor editorial asistido por GenAI para LinkedIn sobre COBOL/mainframes:

`idea → brief → 3 candidatos → evaluación+blockers → aprobación humana → visual SVG → SIMULATED_PUBLISHED → traza`

100% local, sin credenciales (P0), con adaptadores remotos opcionales (P1). Toda requirement usa RFC 2119 (MUST/SHALL/SHOULD/MAY); todo escenario usa Given/When/Then. Los detalles de stack (Vite/FastAPI/SQLModel, dos procesos) se especifican solo en el nivel necesario para hacer testable el comportamiento; la estructura interna es decisión de `sdd-design`.

## 2. Alcance

### P0 — obligatorio para la demo (todos los dominios de este spec)

| # | Dominio | Capacidad | RF/RNF de referencia |
|---|---|---|---|
| 1 | `capture` | Brief con idea/tesis/audiencia/objetivo/evidencia/restricciones; normalización de afirmaciones | RF-01, §12.8 |
| 2 | `generation` | Exactamente 3 candidatos diferenciados con contrato validado | RF-02 |
| 3 | `voice` | Perfil de voz v0 provisional + especificidad COBOL/mainframe | §4.2, RF-03 (dimensión voz) |
| 4 | `genai-harness` | Harness GenAI: prompts versionados, providers (Demo/OpenAI), retry/repair, guardrails, schema canónico | §12.1-12.7, RF-07 |
| 5 | `evaluation` | Heurística 0-100 desglosada, penalizaciones, blockers, regla de decisión | RF-03, §7 |
| 6 | `approval` | Edición con invalidación de evaluación + aprobación humana explícita con razón | RF-04 |
| 7 | `visual` | Contrato visual + tarjeta SVG determinística con `visual_rationale` y alt text | RF-05, §8 |
| 8 | `simulation` | Publicación simulada honesta; `PUBLISHED_REAL` reservado e inalcanzable | RF-06, RNF-02, §9 |
| 9 | `fsm-trace` | FSM (~15 estados), transiciones legales/ilegales, trazabilidad, persistencia | RF-07, RNF-03, RNF-04, §6.2, §11 |
| 10 | `api` | Contrato OpenAPI FE-BE, schema canónico compartido, CORS, errores estructurados | Contrato FE/BE (proposal), RNF-02 |
| 11 | `local-run` | Arranque local con un comando, demo sin credenciales, UX de estados en curso | RNF-01, RNF-05 |

### P1 — opcional, NO bloqueante (ver §6)

## 3. Invariantes transversales

Estas invariantes aplican a TODOS los dominios y cualquier escenario de cualquier dominio debe respetarlas. Un test que las viole indica un bug de producto, no una variación aceptable.

1. **Simulación honesta.** `SIMULATED_PUBLISHED` MUST NOT presentarse como `PUBLISHED_REAL` en ninguna vista, traza o exportación. La banda "SIMULACIÓN" MUST ser persistente en todas las vistas relevantes de una publicación simulada.
2. **Blocker sobre score.** Ningún candidato con un blocker activo puede pasar a `RECOMMENDED` ni a `APPROVED`, sin importar su puntaje (RF-03, §7.3).
3. **Aprobación humana.** La aprobación final del contenido y del visual MUST ser siempre una acción humana explícita con razón registrada; el sistema MUST NOT autoaprobar.
4. **Sin secretos.** Ninguna traza, log visible, recibo ni exportación MUST contener API keys, tokens OAuth, cabeceras de autorización ni secretos (RNF-04).
5. **Determinismo demo.** `DemoProvider` MUST ser determinístico (mismo brief → misma salida) y MUST estar etiquetado `DEMO_PROVIDER` en UI y traza; MUST atravesar los mismos schemas, guardrails, validaciones y transiciones que un provider remoto.
6. **P0 sin red.** El happy path P0 MUST funcionar sin API keys, sin red y sin servicios cloud (RNF-01).
7. **Fallos no destructivos.** Un fallo de proveedor o de validación MUST NOT destruir el brief ni el trabajo previo, y MUST NOT representarse como éxito (RNF-03).

## 4. Matriz de cobertura vs criterios de aceptación (SOLUTION.md §14)

| Criterio de aceptación P0 | Cubierto por |
|---|---|
| Arranca localmente siguiendo README, sin credenciales, en modo demo | `local-run` RUN-01, RUN-02, RUN-05 |
| UI y traza identifican `DEMO_PROVIDER` | `genai-harness` HARN-03; `local-run` RUN-06 |
| `DemoProvider` atraviesa mismos schemas/guardrails/transiciones | `genai-harness` HARN-03 |
| Al menos tres ideas demo + idea manual | `capture` CAP-01 |
| Obliga tesis y evidencia antes de generar | `capture` CAP-02, CAP-05 |
| Exactamente tres candidatos, `angle` únicos, sin hooks/bodies idénticos, contrato válido | `generation` GEN-01..GEN-04 |
| Heurística desglosada con penalizaciones y umbrales visibles | `evaluation` EVAL-01..EVAL-04, EVAL-08 |
| `RECOMMENDED`/`REVISION_REQUIRED` reproducibles | `evaluation` EVAL-06 |
| Blocker de evidencia impide recomendar con score alto | `evaluation` EVAL-05 |
| Edición invalida evaluación previa | `approval` APPR-02 |
| Aprobación final siempre humana | `approval` APPR-01; invariante 3 |
| Visual vincula cada elemento con la tesis, alt text, aprobación humana | `visual` VIS-03, VIS-04, VIS-06 |
| Happy path termina en `SIMULATED_PUBLISHED` con advertencia inequívoca | `simulation` SIM-01; `fsm-trace` FSM-01 |
| Sin URL/ID remoto inventado | `simulation` SIM-02, SIM-05 |
| Traza muestra versiones de prompt/schema, proveedor, validaciones, decisión; sin secretos | `fsm-trace` TRC-01, TRC-02 |
| Fallo de proveedor no destruye brief ni se representa como éxito | `genai-harness` HARN-05; `fsm-trace` PST-01 |
| Tests automatizados: fórmula, blockers, transiciones, schema | `evaluation`, `fsm-trace`, `genai-harness`, `api` (requerimientos de testabilidad) |
| Un comando arranca ambos procesos | `local-run` RUN-01 |

## 5. FSM de referencia (SOLUTION.md §6.2, ampliada)

Estados: `IDEA, BRIEF_READY, GENERATING, GENERATED, EVALUATING, GENERATION_FAILED, EVALUATION_PARTIAL, RECOMMENDED, REVISION_REQUIRED, APPROVED, VISUAL_DRAFT, VISUAL_READY, VISUAL_REVISION_REQUIRED, SIMULATED_PUBLISHED` + reservados `PUBLISHING_REAL, PUBLISHED_REAL, REAL_PUBLISH_FAILED`.

Transiciones legales (tabla completa y escenarios de transiciones ilegales en `fsm-trace`):

```text
IDEA -> BRIEF_READY
BRIEF_READY -> GENERATING
GENERATING -> GENERATED | GENERATION_FAILED
GENERATED -> EVALUATING
EVALUATING -> RECOMMENDED | REVISION_REQUIRED | EVALUATION_PARTIAL
EVALUATION_PARTIAL -> REVISION_REQUIRED
RECOMMENDED -> APPROVED            (revisión humana, sin blockers)
REVISION_REQUIRED -> APPROVED      (override humano con razón, sin blockers)
GENERATED | RECOMMENDED | REVISION_REQUIRED -> GENERATED   (CANDIDATE_EDITED: edición invalida evaluación, contentVersion++ )
APPROVED -> VISUAL_DRAFT
VISUAL_DRAFT -> VISUAL_READY | VISUAL_REVISION_REQUIRED
VISUAL_REVISION_REQUIRED -> VISUAL_DRAFT
VISUAL_READY -> SIMULATED_PUBLISHED
```

Reservado (integración futura, inalcanzable en P0): `VISUAL_READY -> PUBLISHING_REAL -> PUBLISHED_REAL | REAL_PUBLISH_FAILED`.

> Nota: la transición `CANDIDATE_EDITED → GENERATED` es una ampliación especificada de la FSM de SOLUTION.md para hacer explícito el requisito RF-04 de invalidación + reevaluación. `sdd-design` decide la representación interna (nivel run vs nivel candidato), el comportamiento observable ya está especificado.

## 6. P1 — opcional y NO bloqueante

Estas requirements son P1: MUST NOT bloquear, retrasar ni condicionar la aceptación de P0. La demo oficial corre con `DemoProvider` + SVG determinístico, sin key y sin red. Las reglas de corte (§19 SOLUTION.md) aplican.

- **P1-01 — Adaptador OpenAI-compatible.** El sistema SHOULD exponer un adaptador remoto OpenAI-compatible (chat completions) detrás de la interfaz `GenAIProvider`, activable por API key del usuario. Si se usa, la traza MUST registrar proveedor y modelo; si no se usa, la UI MUST decir `DEMO_PROVIDER`. El adaptador MUST respetar los mismos schemas, guardrails, retry/repair y transiciones que `DemoProvider`.
- **P1-02 — Historial navegable.** El sistema SHOULD permitir navegar ejecuciones históricas (persistidas en SQLite en fichero).
- **P1-03 — E2E.** El equipo SHOULD cubrir el happy path con una prueba E2E (Playwright) cuando P0 esté estable.
- **P1-04 — API de imágenes opcional.** El sistema MAY exponer una API de imágenes generativas detrás de una interfaz, DESACTIVADA por defecto; P0 usa solo SVG determinístico. Activarla MUST NOT cambiar el contrato visual observable definido en `visual`.

Reglas de corte (P0 en riesgo):
- Si P0 se atrasa (regla de corte hora 14), NO se implementa ningún P1.
- Sin API key configurada, el sistema MUST funcionar completo en modo demo; un fallo del adaptador P1 MUST degradarse desactivándolo sin tocar P0.

## 7. Referencias

- `SOLUTION.md` §4 (voz), §6 (flujo y FSM), §7 (heurística), §8 (visual), §9 (simulación), §11 (entidades), §12 (harness), §13 (RF-01..07, RNF-01..05), §14 (aceptación), §19 (plan y regla de corte).
- `proposal.md` (alcance P0/P1, enfoque, riesgos, decisiones abiertas para design).
- `openspec/config.yaml` (reglas de fase `specs`: RFC 2119, Given/When/Then, FSM honesta).
