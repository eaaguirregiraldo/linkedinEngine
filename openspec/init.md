# SDD Init — Proyecto `linkedin`

> Fase: `sdd-init` | Fecha: 2026-08-08 | Modo de persistencia: **hybrid** (archivos Markdown + Engram)

## Estado previo detectado

- Directorio: `/Users/eaaguirregiraldo/Downloads/linkedin`
- Contenido: **solo `SOLUTION.md`** (887 líneas). Sin código, sin repo git, sin `.atl/`, sin artefactos SDD previos.
- `SOLUTION.md` es la fuente de verdad de producto: requisitos **RF-01..RF-07**, no funcionales **RNF-01..RNF-05**, alcance P0/P1, FSM de ~15 estados honestos, heurística con fórmula transparente, contrato visual SVG, publicación simulada (`SIMULATED_PUBLISHED`) y `DemoProvider`.
- La sección §10.1 del SOLUTION.md (Next.js monoproceso) es una **sugerencia** de implementación, no una decisión congelada.

## Stack detectado en la máquina (verificado)

| Herramienta | Versión |
|---|---|
| Node.js | v24.14.0 (npm 11.9.0; sin pnpm/bun) |
| Python | 3.12.7 (sin uv) |
| Go | 1.26.0 |
| API keys GenAI | **Ninguna configurada** → la demo solo corre con `DemoProvider`; el adaptador remoto (P1) requiere key del usuario |

## Decisión de arquitectura (confirmada por el usuario el 2026-08-08)

> ⚠️ Supera la recomendación de la exploración (Opción 1: Next.js monoproceso) — el usuario eligió la **Opción 2** ajustada:

- **Frontend:** React + Vite (TypeScript)
- **Backend:** FastAPI + Python
- **Persistencia:** SQLite con **SQLAlchemy / SQLModel** — explícitamente **NO Drizzle** (Drizzle es TypeScript)
- **GenAI:** `DemoProvider` determinístico (P0) + **adaptador OpenAI opcional** (P1, requiere key)
- **Imagen:** SVG determinístico + **API de imágenes opcional**
- **Demo:** 100% local, sin cloud, sin credenciales (cumple RNF-01)
- Contratos: pydantic en el backend; dominio puro con FSM artesanal tipada y fórmula de evaluación sin dependencias

### Implicancias de la decisión (tradeoffs a gestionar en diseño)

1. **Dos procesos** (Vite + FastAPI) → coordinación con `concurrently`/script root + CORS.
2. **Contrato duplicado** entre FE (TS) y BE (pydantic) → riesgo de drift; mitigar con tests de contrato FE/BE y un esquema canónico.
3. **Doble toolchain** (Node + Python) → más piezas, pero ecosistema Python fuerte para iteración GenAI en semana 2.
4. Persistencia SQLite en fichero (no in-memory) para que el historial P1 sobreviva reinicios.

## Estructura creada

```
linkedin/
├── SOLUTION.md                 # Fuente de verdad de producto (existente, no se tocó)
├── openspec/
│   ├── config.yaml             # Config SDD con contexto y reglas por fase
│   ├── init.md                 # ← Este artefacto (contexto de init)
│   ├── specs/                  # Especificaciones principales (vacío; se llena en archive)
│   └── changes/
│       ├── archive/            # Cambios completados
│       └── linkedin-content-engine/
│           ├── state.yaml      # Estado DAG (recuperación tras compactación)
│           └── exploration.md  # Espejo en Markdown de la exploración (Engram #874)
└── .atl/
    └── skill-registry.md       # Registro de skills disponibles (infraestructura, no artefacto SDD)
```

## Persistencia en Engram

| Artifact | Topic key | Observación |
|---|---|---|
| Contexto del proyecto | `sdd-init/linkedin` | Creado en esta fase |
| Exploración | `sdd/linkedin-content-engine/explore` | #874 (existente, intacta) |
| Estado DAG del cambio | `sdd/linkedin-content-engine/state` | #875 → actualizado (init DONE) |
| Registro de skills | `skill-registry` | Creado en esta fase |

## DAG del cambio `linkedin-content-engine`

| Fase | Estado |
|---|---|
| explore | DONE (Engram #874 + `exploration.md`) |
| **init** | **DONE (esta fase)** |
| proposal | NOT_STARTED → **próximo paso** |
| spec / design / tasks / apply / verify / archive | NOT_STARTED |

## Pendientes para sdd-propose

1. Confirmar el proveedor GenAI P1 concreto (adaptador OpenAI-compatible asumido) y si el usuario proveerá una key para P1 (sin key, P1 queda demo-only).
2. Definir el alcance del "API de imágenes opcional" (adaptador detrás de la interfaz, no bloqueante para P0).
3. Confirmar forma de arranque local (script root con `concurrently`).

## Next Steps

1. `/sdd-propose linkedin-content-engine` (o `/sdd-continue`) — crear `proposal.md` + Engram `sdd/linkedin-content-engine/proposal`.
2. Luego `sdd-spec` → `sdd-design` → `sdd-tasks` → `sdd-apply` → `sdd-verify` → `sdd-archive`.
