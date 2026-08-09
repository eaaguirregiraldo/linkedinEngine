# Skill Registry — proyecto `linkedin`

> Infraestructura (no artefacto SDD). Generado por `sdd-init` el 2026-08-08.
> Fuentes escaneadas: `~/.claude/skills`, `~/.config/opencode/skills`, `~/.gemini/skills`, `~/.cursor/skills`, `~/.copilot/skills` (proyecto sin skills propios).

## Skills no-SDD disponibles

| Skill | Ubicación | Descripción / Triggers |
|---|---|---|
| browser-automation | `~/.claude/skills/browser-automation/SKILL.md` | Verificar trabajo web en navegador headless (console errors, renders, DOM, screenshot). Triggers: "check the page", "does it render", "verify the UI", "QA the app", "is it broken", "console errors", "did my change work" |
| go-testing | `~/.claude/skills/go-testing/SKILL.md` | Patrones de testing Go (Gentleman.Dots, Bubbletea TUI testing). Triggers: escribir tests Go, usar teatest, agregar cobertura |
| skill-creator | `~/.claude/skills/skill-creator/SKILL.md` | Crear skills de IA según Agent Skills spec. Triggers: "create a new skill", "add agent instructions", "document patterns for AI" |

## Skills SDD (no listar aquí como carga automática; se cargan por fase)

`~/.claude/skills/sdd-{init,explore,propose,spec,design,tasks,apply,verify,archive}/SKILL.md`
(duplicadas en `~/.config/opencode/skills/`, `~/.gemini/skills/`, `~/.cursor/skills/`, `~/.copilot/skills/`)

## Convenciones de proyecto

- No hay `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` / `.cursorrules` / `copilot-instructions.md` en la raíz del proyecto.
- Fuente de verdad de producto: `SOLUTION.md` (requisitos RF-01..07, RNF-01..05, criterios de aceptación).
- Reglas globales del agente: `~/.config/opencode/AGENTS.md` (conventional commits sin atribución IA, nunca build tras cambios, verificar antes de afirmar, SDD orchestrator con delegación).

## Reglas de carga para sub-agentes

1. `mem_search(query: "skill-registry", project: "linkedin")` → si existe, `mem_get_observation(id)`
2. Fallback: leer `.atl/skill-registry.md` (este archivo)
3. Cargar el skill cuyo trigger coincida con la tarea y leer su `SKILL.md` antes de escribir código
4. Si no hay coincidencia, proceder sin skills (no es un error)
