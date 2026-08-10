# LinkedIn Content Engine

MVP local para transformar una idea sobre COBOL/mainframes en un brief, tres candidatos, una evaluación trazable, un visual SVG y una publicación simulada honesta.

## Entregable y estructura

- `frontend/`: SPA React + Vite con el wizard de 10 pasos.
- `backend/`: API FastAPI, dominio, persistencia SQLite y seed de demo.
- `docs/demo/`: guion reproducible y fixture del brief de mainframe.
- `docs/decisions.md`: decisiones, supuestos materiales y plan de una semana adicional.
- `SOLUTION.md`: especificación funcional completa y criterios de aceptación.

El trabajo se organizó con el ecosistema **Gentle AI**, usando **Engram SDD** para persistir contexto y artefactos de exploración, propuesta, especificación, diseño, tareas y verificación. En este proyecto SDD aportó trazabilidad entre requisitos y entregables, implementación incremental por lotes y un registro explícito de decisiones y riesgos; también permitió recuperar el contexto entre sesiones sin convertir la documentación en una suposición implícita.

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

Abrí `http://localhost:5173`, elegí una de las tres ideas demo y seguí el wizard. Antes de generar elegí explícitamente el proveedor:

- `DemoProvider` / `DEMO_PROVIDER`: local, determinístico, sin red ni API key.
- `OpenAI` / `OPENAI_PROVIDER`: IA generativa real. La key se configura únicamente en el backend y nunca se pide ni se persiste en el frontend.

El guion reproducible de revisión está en [`docs/demo/review-script.md`](docs/demo/review-script.md) y el brief base en [`docs/demo/brief-mainframe.json`](docs/demo/brief-mainframe.json).

También podés verificar el flujo HTTP contra un backend ya levantado:

```bash
python scripts/demo_smoke.py
```

El smoke usa `http://localhost:8000` por defecto. Para otra URL, definí `DEMO_BASE_URL`; por ejemplo, `DEMO_BASE_URL=http://localhost:8000 python scripts/demo_smoke.py`. El caso de fallo controlado se ejecuta con `--failure` mientras el backend corre con `DEMO_FORCE_INVALID=1`.

Para correr las verificaciones automatizadas disponibles, sin modificar el flujo de demo:

```bash
npm test
npm run test:contract
```

`schema:generate` y `schema:check` requieren que la API ya esté levantada porque leen `http://localhost:8000/openapi.json`.

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

## Usar OpenAI

Copiá `.env.example` a `.env` y configurá en el backend:

```dotenv
GENAI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=60
OPENAI_BASE_URL=https://api.openai.com/v1
```

Reiniciá `npm run dev`. La UI permite elegir OpenAI antes de generar; el backend envía la solicitud, valida la respuesta con el mismo schema Pydantic, guardrails, retry/repair y traza que DemoProvider. Si falta la key o el proveedor falla, la UI muestra una instrucción accionable: corregí `.env`, reintentá o elegí DemoProvider. No hay fallback automático.

## Limitaciones y supuestos

La voz v0 es provisional y no representa una validación del autor. Los umbrales `72 / 4 / 60`, los pesos y las penalizaciones son heurísticas calibrables, no una medición científica. La señal de evaluación indica potencial editorial explicable; no predice viralidad, alcance ni engagement.

La publicación es exclusivamente simulada: no hay OAuth, permisos ni envío a LinkedIn. SQLite es un fichero descartable; el arranque crea el esquema y reinyecta las tres ideas si la base está vacía. Ver [`docs/decisions.md`](docs/decisions.md) para ADRs y supuestos completos.

## Semana adicional

Con una semana adicional priorizaría, en este orden: (1) instrumentar pruebas E2E del happy path y del fallo no destructivo; (2) validar la voz y calibrar la rúbrica con 10-20 publicaciones aprobadas y revisión humana; (3) agregar historial navegable y migraciones Alembic si empiezan a preservarse datos; y (4) dejar diseñada, pero separada del camino demo, una integración de publicación real con OAuth, permisos y respuesta remota verificable. No habilitaría publicación real ni afirmaría mejoras de rendimiento sin esa evidencia.

## Definición de terminado P0

P0 está terminado cuando el evaluador puede arrancar ambos procesos con el README, recorrer `idea → brief → 3 candidatos → evaluación → aprobación → visual → SIMULATED_PUBLISHED → traza`, ver `DEMO_PROVIDER` y `SIMULACIÓN`, y reproducir el fallo controlado sin pérdida del brief. La evidencia automatizada requerida está en `pytest`, Vitest, `tsc`, `schema:check`, `test:contract` y el smoke HTTP documentado.

La especificación funcional completa y sus criterios de aceptación viven en [`SOLUTION.md`](SOLUTION.md). Wave 7/K es P1 y no forma parte de este cierre.
