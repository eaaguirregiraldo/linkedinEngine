# LinkedIn Content Engine

MVP local para transformar una idea sobre COBOL/mainframes en un brief, tres candidatos, una evaluación trazable, un visual SVG y una publicación simulada honesta.

## Requisitos e instalación

- Node.js `24.14.0` (o compatible con `>=24`)
- Python `3.12.7`

Desde la raíz:

```bash
npm install
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt -r backend/requirements-dev.txt
```

No se necesitan API keys ni acceso a Internet para el flujo P0. Los comandos npm usan automáticamente `backend/.venv`; no hace falta activar el entorno manualmente.

## Arranque y demo

Un solo comando levanta FastAPI en `http://localhost:8000` y Vite en `http://localhost:5173`:

```bash
npm run dev
```

El comando falla de forma explícita si `backend/.venv` no existe. En ese caso, ejecutá nuevamente la creación e instalación del entorno del bloque anterior.

Abrí `http://localhost:5173`, elegí una de las tres ideas demo y seguí el wizard. El proveedor visible debe ser `DEMO_PROVIDER`. El guion reproducible de revisión está en [`docs/demo/review-script.md`](docs/demo/review-script.md) y el brief base en [`docs/demo/brief-mainframe.json`](docs/demo/brief-mainframe.json).

También podés verificar el flujo HTTP contra un backend ya levantado:

```bash
python scripts/demo_smoke.py
```

## Qué demuestra el MVP

- Exactamente tres candidatos con ángulos distintos y claims ligados a evidencia.
- Evaluación determinística 0-100, penalizaciones y blockers visibles.
- Aprobación humana explícita del contenido y del visual.
- Tarjeta SVG determinística con rationale y alt text.
- Recibo `SIMULATED_PUBLISHED`, sin URL, URN ni ID remoto.
- Traza con proveedor, versiones, validaciones, decisiones y redacción de secretos.

## DemoProvider y fallo controlado

`DemoProvider` deriva siempre la misma salida del mismo brief y usa los mismos contratos, guardrails y transiciones del harness. Para revisar el camino de error:

```bash
DEMO_FORCE_INVALID=1 npm run dev
```

La generación termina en `GENERATION_FAILED`, conserva el brief y registra `repair_failed`; al quitar la variable y reintentar, se obtiene un run nuevo sin destruir el trabajo previo.

## Limitaciones y supuestos

La voz v0 es provisional y no representa una validación del autor. Los umbrales `72 / 4 / 60`, los pesos y las penalizaciones son heurísticas calibrables, no una medición científica. La señal de evaluación indica potencial editorial explicable; no predice viralidad, alcance ni engagement.

La publicación es exclusivamente simulada: no hay OAuth, permisos ni envío a LinkedIn. SQLite es un fichero descartable; el arranque crea el esquema y reinyecta las tres ideas si la base está vacía. Ver [`docs/decisions.md`](docs/decisions.md) para ADRs y supuestos completos.

## Semana adicional

Fuera de P0 quedan la publicación real vía OAuth y una app de LinkedIn aprobada, migraciones Alembic cuando haya datos que preservar, validación de voz contra 10-20 publicaciones aprobadas, adaptador OpenAI-compatible, proveedor de imágenes, historial navegable y E2E. También hace falta calibrar la rúbrica con datos reales antes de atribuir cualquier señal a rendimiento.

## Definición de terminado P0

P0 está terminado cuando el evaluador puede arrancar ambos procesos con el README, recorrer `idea → brief → 3 candidatos → evaluación → aprobación → visual → SIMULATED_PUBLISHED → traza`, ver `DEMO_PROVIDER` y `SIMULACIÓN`, y reproducir el fallo controlado sin pérdida del brief. La evidencia automatizada requerida está en `pytest`, Vitest, `tsc`, `schema:check`, `test:contract` y el smoke HTTP documentado.

La especificación funcional completa y sus criterios de aceptación viven en [`SOLUTION.md`](SOLUTION.md). Wave 7/K es P1 y no forma parte de este cierre.
