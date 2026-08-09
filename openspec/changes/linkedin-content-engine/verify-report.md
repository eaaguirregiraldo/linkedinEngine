# Verification Report: `linkedin-content-engine`

**status:** completed
**change:** `linkedin-content-engine`
**mode:** hybrid (OpenSpec + Engram)
**date:** 2026-08-09

## Executive Summary

El MVP P0 está funcionalmente integrado y la evidencia ejecutable principal es verde. El dominio, harness, persistencia, API, frontend, contrato anti-drift, visual SVG, flujo feliz y camino de fallo controlado fueron verificados con ejecución real.

La decisión inicial fue **PASS WITH CONDITIONS**. La condición P0 era que `npm run dev` no era reproducible desde una shell sin activar el virtualenv Python: el wrapper encontraba el `uvicorn` global y fallaba importando `sqlmodel`.

La condición quedó corregida: `backend/package.json` valida `backend/.venv/bin/python` y ejecuta `python -m uvicorn` con ese intérprete. Si el venv no existe, el comando termina con un mensaje accionable y conserva el error. README ahora documenta que no hace falta activar el entorno manualmente.

## Artifacts

| Artefacto | Estado |
|---|---|
| `proposal.md` | leído y contrastado |
| `spec.md` | leído y contrastado |
| `specs/capture/spec.md` | leído y contrastado |
| `specs/generation/spec.md` | leído y contrastado |
| `specs/voice/spec.md` | leído y contrastado |
| `specs/genai-harness/spec.md` | leído y contrastado |
| `specs/evaluation/spec.md` | leído y contrastado |
| `specs/approval/spec.md` | leído y contrastado |
| `specs/visual/spec.md` | leído y contrastado |
| `specs/simulation/spec.md` | leído y contrastado |
| `specs/fsm-trace/spec.md` | leído y contrastado |
| `specs/api/spec.md` | leído y contrastado |
| `specs/local-run/spec.md` | leído y contrastado |
| `design.md` | leído completo y contrastado |
| `tasks.md` | leído completo; tareas pendientes preservadas |
| `apply-progress.md` | leído completo; evidencia previa reconciliada |
| `state.yaml` | actualizado: `phase: verify`, `verify: true` |
| `verify-report.md` | creado por esta verificación |

## Coverage Matrix

| Requisito / lote | Cobertura y evidencia | Resultado |
|---|---|---|
| RF-01 / CAP, VOI | Brief con tesis/evidencia, clasificación, defaults, voz v0 y validaciones; tests backend y wizard | PASS |
| RF-02 / GEN | Exactamente 3 candidatos, ángulos cerrados/únicos, validación de contrato y fallo controlado; pytest, contract round-trip, smoke | PASS |
| RF-03 / EVAL | Fórmula 0-100, pesos, penalizaciones, blockers, umbrales 72/4/60, decisión reproducible y `EVALUATION_PARTIAL`; pytest + Vitest | PASS |
| RF-04 / APPR | Razón humana, blocker bloquea aprobación, edición incrementa versión e invalida evaluación/visual, traza append-only; workflow pytest + wizard | PASS |
| RF-05 / VIS | Contrato derivado de tesis, rationale por elemento, alt text, SVG 1200x630 determinístico, rechazo/regeneración y aprobación humana; pytest + wizard | PASS |
| RF-06 / SIM | Recibo local, `SIMULATED_PUBLISHED`, banda `SIMULACIÓN`, `remote_id=None`, prerequisitos y ausencia de publicación real; API/contract/smoke | PASS |
| RF-07 / TRC | Prompt/schema/hash, provider, validaciones, score, decisiones, ediciones, publicación y redacción; pytest + round-trip + UI | PASS |
| RNF-01 / RUN-01/02 | Demo sin key/red, smoke feliz real; arranque raíz usa explícitamente `backend/.venv/bin/python` | PASS |
| RNF-02 / RUN-03/06 | Estados fallidos/parciales/simulados diferenciados; banners y estados verificados en Vitest | PASS |
| RNF-03 / GEN-06/PST | `GENERATION_FAILED` conserva brief y traza; retry disponible; failure smoke real | PASS |
| RNF-04 / TRC-02/PST-02 | Redacción recursiva, raw output desactivado por defecto, tablas sin credenciales, recibo sin IDs remotos; pytest | PASS |
| RNF-05 / API-05/RUN-04 | Lock síncrono `useAsync`, doble envío ignorado, estados en curso y guard API; Vitest + API pytest | PASS |
| A1 | A1.2 funcional y reproducible con `backend/.venv`; A1.1 sin commit; A1.3-A1.8 completos | PARTIAL |
| B-F | Dominio, contratos, DB, harness y visual completos; suites específicas verdes | PASS |
| G | FastAPI, workflow, routers, CORS, OpenAPI y errores estructurados completos | PASS |
| H1-H2 | Client tipado, wizard 10 pasos, estados honestos y UI completa | PASS |
| I | Drift byte a byte, round-trip real, schema coverage y CORS | PASS |
| J | J.1-J.5 verificables; J.6 requiere commits y permanece pendiente | PARTIAL |
| K | P1 opcional; no bloqueante y no ejecutado | N/A P1 |

## Given/When/Then Evidence

Los escenarios P0 críticos tienen evidencia de runtime en suites de dominio, harness, API, frontend y contrato. En particular:

| Flujo | Evidencia real |
|---|---|
| idea -> brief | `backend/tests/api/test_endpoints.py`, `frontend/src/tests/wizard.test.tsx` |
| brief inválido / evidencia / tesis | tests de schemas, dominio y wizard |
| brief -> 3 candidatos | `test_demo_provider.py`, `test_harness.py`, round-trip contractual |
| blockers y decisión | `test_blockers.py`, `test_score.py`, regresiones P0 |
| edición e invalidación | `test_workflow.py`, `wizard.test.tsx` |
| aprobación humana | workflow y wizard; razones registradas |
| visual semántico | `backend/tests/visual/*`, `VisualStep` y wizard |
| publicación simulada | API workflow, round-trip y `scripts/demo_smoke.py` |
| traza y secretos | `test_trace.py`, workflow y TraceStep |
| fallo no destructivo | failure smoke con `DEMO_FORCE_INVALID=1` |

No todos los escenarios Given/When/Then tienen una prueba 1:1 nombrada. Los escenarios P1, publicación real y adaptador remoto son deliberadamente no aplicables al cierre P0. El escenario de arranque limpio quedó cubierto por la verificación repetida documentada abajo.

## FSM Reconciliation

Existe una discrepancia entre documentos:

- `design.md` §4.2 incluye `EVALUATION_PARTIAL -> GENERATED` mediante `CANDIDATE_EDITED`.
- `tasks.md` B.1, `spec.md` §5 y `specs/fsm-trace/spec.md` especifican edición desde `GENERATED`, `RECOMMENDED` y `REVISION_REQUIRED`, no desde `EVALUATION_PARTIAL`.
- La implementación y los tests siguen `tasks.md`/spec detallada: `EVALUATION_PARTIAL` solo puede continuar a `REVISION_REQUIRED`; la edición requiere primero salir de la evaluación parcial.



| Comando | Resultado |
|---|---|
| `backend/.venv/bin/pytest -q backend/tests` | **287 passed** |
| `npm --prefix frontend run test -- --run` | **34 passed** |
| `npm run test:contract -- --run` | **4 passed** |
| `npm run schema:check` con API viva | **OK, diff vacío** |
| `npm exec tsc -- --noEmit` en `frontend/` | **OK** |
| `backend/.venv/bin/ruff check backend/` | **OK** |
| `python -m compileall -q backend scripts` | **OK** |
| `backend/.venv/bin/python ../scripts/demo_smoke.py` | **OK: SIMULATED_PUBLISHED** |
| `DEMO_BASE_URL=http://127.0.0.1:8001 .venv/bin/python ../scripts/demo_smoke.py --failure` | **OK: GENERATION_FAILED**, brief conservado |
| `GET /api/health` | **HTTP 200** |
| `GET /openapi.json` | **HTTP 200** |
| `npm run dev` sin venv activo, antes de la corrección | **FAIL: uvicorn global no encuentra `sqlmodel`** |
| `npm run dev` con `backend/.venv` existente y sin activar | **PASS: API :8000 + Vite :5173; `/api/health` HTTP 200** |
| `npm run dev` sin `backend/.venv` | **PASS: falla explícitamente con instrucciones para crear e instalar el venv** |

No se ejecutó build, conforme a la restricción. No hay threshold de coverage configurado en `openspec/config.yaml`, por lo que no se reporta porcentaje de coverage.

## Findings

### High

1. **Resuelto en la verificación repetida.** `backend/package.json` ya no depende de `PATH`: valida el venv y ejecuta `.venv/bin/python -m uvicorn`. El arranque limpio se repitió con ambos procesos y `/api/health` respondió 200.

### Medium

1. **Discrepancia FSM entre diseño y tasks/spec.** `design.md` permite edición desde `EVALUATION_PARTIAL`; la spec detallada y la implementación no. Debe decidirse y sincronizarse antes de archivar para evitar que el diseño sea una promesa diferente del comportamiento.
2. **A1.2 queda demostrada funcionalmente.** El checkbox histórico no se modifica porque `tasks.md` conserva el alcance original y no se alteran tareas pendientes/commit bajo esta corrección.
3. **Cobertura Given/When/Then no está trazada 1:1.** La cobertura funcional P0 es fuerte, pero no existe una matriz automatizada que vincule cada escenario de cada spec a un test individual. La afirmación de PASS se limita a los escenarios cubiertos por las suites y smoke enumerados.

### Low

1. **A1.4/A1.5 no tienen tests persistentes propios de core.** Configuración y redacción sí fueron ejercitadas indirectamente por suites de integración/harness, pero faltan tests unitarios dedicados.
2. **A1.1/J.6 requieren commits.** Permanecen pendientes por instrucción explícita de no hacer commit; el worktree sigue sin commits y no se considera un defecto funcional P0.
3. **K no ejecutado.** OpenAI, historial UI, Playwright, ImageProvider real y Alembic son P1 opcionales y no bloquean esta decisión.

## Residual Risks

- El arranque requiere que el usuario cree e instale `backend/.venv`; si falta, el mensaje de error indica exactamente cómo hacerlo.
- La heurística y la voz v0 son provisionales y no calibradas con publicaciones aprobadas reales.
- No hay E2E de navegador Playwright; la interacción está cubierta por Vitest y el round-trip HTTP.
- La integración de publicación real no existe y `PUBLISHED_REAL` permanece reservado/inalcanzable, como corresponde al P0.
- Persisten limitaciones de un MVP local: sin auth, multiusuario, migraciones Alembic ni gestión de secretos remotos.

## Decision

**PASS WITH CONDITIONS**

El núcleo funcional P0 está verificado y la condición HIGH del arranque quedó corregida y repetidamente verificada. Se mantiene `PASS WITH CONDITIONS` por la discrepancia FSM ya documentada y por A1.1/J.6/K pendientes; no se implementa P1 ni se archiva.

## Next Steps

1. Mantener el wrapper de `npm run dev` usando explícitamente `backend/.venv/bin/python -m uvicorn`.
2. Reconciliar la transición de edición desde `EVALUATION_PARTIAL` en `design.md`, `spec.md`, `tasks.md`, implementación y tests; no marcar una tarea sin evidencia.
3. Agregar tests unitarios dedicados para `core/config.py` y `core/trace.py` si se desea elevar los gaps low.
4. Mantener A1.1/J.6 pendientes hasta que el usuario autorice commits; mantener K como P1 opcional.
5. Si las condiciones se resuelven, ejecutar una verificación final breve y luego considerar `sdd-archive`.
