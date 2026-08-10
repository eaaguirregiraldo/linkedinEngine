# Decisiones y supuestos P0

Este documento resume las decisiones de `openspec/.../design.md`. No agrega alcance.

## Método de trabajo

El proyecto se trabajó con el ecosistema **Gentle AI** y **Engram SDD**. Engram se usó como memoria persistente del proyecto y SDD como proceso para separar exploración, propuesta, especificación, diseño, tareas, implementación y verificación. La ventaja material para este MVP fue mantener trazabilidad entre requisitos y código, dividir el trabajo en incrementos verificables y dejar decisiones y supuestos recuperables entre sesiones. No reemplaza las pruebas ni la revisión humana: reduce ambigüedad y deriva de alcance, pero la evidencia sigue siendo la fuente de verdad.

## ADRs

1. **ADR-001, dos procesos:** React/Vite y FastAPI/uvicorn coordinados por `concurrently`; preserva el stack acordado y permite un dominio Python fuerte.
2. **ADR-002, SQLModel:** SQLite en fichero con repos finos; comparte el modelo pydantic y deja Alembic para P1.
3. **ADR-003, contrato canónico:** pydantic genera OpenAPI y `schema.d.ts`; `test:contract` detecta drift.
4. **ADR-004, FSM artesanal:** tabla declarativa y guards en dominio puro; evita una dependencia de máquina de estados para un flujo pequeño.
5. **ADR-005, retry/repair en harness:** la política es transversal y no se duplica en cada provider.
6. **ADR-006, SVG P0:** visual determinístico, auditable y reproducible; ImageProvider queda detrás de una interfaz P1.
7. **ADR-007, publicación honesta:** `SIMULATED_PUBLISHED` es terminal P0; `PUBLISHED_REAL` tiene guard muerto y no puede alcanzarse.
8. **ADR-008, create_all + seed:** la DB demo es descartable; Alembic se incorpora solo cuando haya datos que preservar.
9. **ADR-009, requests síncronos:** la UI muestra in-flight y bloquea doble envío; colas y polling quedan fuera del MVP.
10. **Enhancement provider explícito:** la UI selecciona `demo` u `openai` por request; la key solo vive en `.env` del backend. OpenAI usa HTTP compatible con Chat Completions para evitar una dependencia SDK y devuelve JSON crudo al mismo harness.

## Supuestos explícitos

- La voz v0 técnica, sobria y didáctica es una hipótesis, no la voz validada del autor.
- La voz se valida luego con 10-20 publicaciones reales aprobadas y correcciones manuales.
- `72` (recomendación), `4` (brecha mínima) y `60` (revisión profunda) son umbrales iniciales calibrables.
- La heurística es una señal editorial explicable, no un predictor de viralidad.
- El DemoProvider no requiere credenciales, red ni servicios cloud y es determinístico.
- La evidencia del brief es dato delimitado, no instrucciones; claims sin soporte activan blockers.
- La aprobación del contenido y del visual siempre requiere una razón humana.
- SQLite se puede borrar para regenerar seed; no se promete preservación de datos en P0.
- La publicación simulada nunca crea URL, URN, remote ID ni afirma haber enviado contenido.
- `OPENAI_PROVIDER` no implica publicación real: solo identifica el proveedor de generación. Toda publicación continúa siendo `SIMULATED_PUBLISHED`.

## Publicación real vs simulada

P0 solo ejecuta `publish-simulated`. La FSM conserva estados reservados para una futura integración, pero `real_publish_enabled()` siempre es falso. Una integración real necesitará OAuth, una aplicación de LinkedIn aprobada, permisos, respuesta remota verificable y trazas sin tokens.

## Viralidad

El score pondera hook, nicho, evidencia, claridad, conversación y voz, y descuenta riesgos y genericidad. Sirve para explicar una recomendación y decidir qué revisar. Sin histórico y experimentos controlados no permite afirmar alcance o viralidad.

## Semana adicional

Con una semana adicional priorizaría E2E del happy path y del fallo controlado, calibración de voz y rúbrica con 10-20 publicaciones aprobadas, historial con Alembic cuando exista persistencia que preservar y el diseño de OAuth/publicación real como una integración aislada. Ninguno debe cambiar el contrato honesto de simulación ni habilitar autoaprobación. La publicación real requiere además una aplicación de LinkedIn aprobada, permisos, pruebas de respuesta remota y trazas sin tokens.
