# Especificación de dominio: `capture` — Captura y normalización de idea → brief

> Dominio NUEVO (no existe spec previa): spec completa.
> Capacidad P0: RF-01 | Voz provisional: SOLUTION.md §4.2 | Normalización de afirmaciones: §12.8.

## Purpose

El sistema debe convertir una idea (demo o manual) en un brief editorial completo y validado —tesis, audiencia, objetivo, evidencia y restricciones—, separando hechos, opiniones del autor y preguntas abiertas, y aplicando el perfil de voz v0 etiquetado como provisional. Sin brief válido no puede haber generación (RF-01, §12.8).

## Requirements

### Requirement: CAP-01 — Ideas demo y entrada manual

El sistema MUST ofrecer al menos tres ideas demo y MUST permitir al usuario escribir una idea propia. La entrada manual MUST NOT aceptar texto vacío ni compuesto solo de espacios.

#### Scenario: elección de idea demo

- GIVEN una instalación local recién inicializada en modo demo
- WHEN el usuario elige una de las ideas demo ofrecidas
- THEN el sistema crea un `ContentProject` con la `rawIdea` seleccionada y estado `IDEA`
- AND la UI muestra la idea como base para completar el brief

#### Scenario: idea manual vacía

- GIVEN el usuario opta por escribir una idea propia
- WHEN envía una idea vacía o compuesta solo de espacios
- THEN el sistema rechaza el envío con un error accionable
- AND no crea ningún proyecto ni persiste estado

#### Scenario: idea manual válida

- GIVEN el usuario escribe una idea propia con al menos un carácter significativo
- WHEN confirma la idea
- THEN el sistema normaliza el texto (trim y colapso de espacios) y crea el `ContentProject` en `IDEA`
- AND el texto normalizado queda disponible para completar el brief

### Requirement: CAP-02 — Brief obligatorio antes de generar

El sistema MUST exigir una tesis única y al menos una evidencia, experiencia autorizada o ejemplo concreto antes de permitir la generación de candidatos. Sin estos elementos, la generación MUST NOT estar disponible (RF-01, §12.8).

#### Scenario: brief válido

- GIVEN un proyecto en `IDEA` con la idea seleccionada
- WHEN el usuario completa tesis, audiencia, objetivo, evidencia y restricciones y confirma
- THEN el sistema guarda el brief con estado `BRIEF_READY`
- AND muestra el perfil de voz v0 provisional aplicado (ver `voice` VOI-01)
- AND habilita la acción de generar candidatos

#### Scenario: tesis ausente o vacía

- GIVEN un proyecto en `IDEA`
- WHEN el usuario intenta confirmar el brief sin tesis o con tesis vacía
- THEN el sistema rechaza la confirmación con un error accionable
- AND el proyecto permanece en `IDEA`, sin estado intermedio persistido

#### Scenario: sin evidencia

- GIVEN un brief con tesis pero sin ninguna evidencia, experiencia o ejemplo concreto
- WHEN el usuario intenta continuar a generación
- THEN el sistema solicita al menos una evidencia o un ejemplo concreto
- AND bloquea la transición a generación hasta que se cumpla el requisito

### Requirement: CAP-03 — Campos del brief

El sistema MUST permitir definir, al menos: `audience`, `objective`, `thesis`, `evidence` (lista) y `constraints`/`restrictions` (RF-01). La audiencia y el objetivo MUST admitir valores por defecto de demo cuando el usuario no los provea.

#### Scenario: brief completo con valores demo

- GIVEN un usuario que no completa audiencia ni objetivo
- WHEN confirma el brief con tesis y evidencia
- THEN el sistema aplica la audiencia y el objetivo por defecto de la idea demo seleccionada
- AND el brief guardado queda en `BRIEF_READY` con esos valores visibles y editables

#### Scenario: brief con restricciones explícitas

- GIVEN un brief donde el usuario declara restricciones (p. ej. "no usar cifras de empresas")
- WHEN se confirma el brief
- THEN las restricciones se persisten como parte del brief
- AND la generación posterior MUST respetarlas (reglas de guardrail, ver `genai-harness` HARN-06)

### Requirement: CAP-04 — Afirmaciones no respaldadas

El sistema MUST detectar en el brief afirmaciones que requieren cautela (cifras, causalidades, experiencias personales) y, ante una afirmación sin evidencia, MUST solicitar evidencia o permitir retirar la afirmación; MUST NOT presentar el dato como validado (RF-01 escenario "evidencia insuficiente").

#### Scenario: cifra sin fuente

- GIVEN un brief cuya tesis o evidencia contiene una cifra sin fuente aportada
- WHEN el usuario intenta continuar
- THEN el sistema marca la afirmación como no respaldada y pide fuente o retiro
- AND no presenta la cifra como validada en ninguna vista del brief

#### Scenario: experiencia personal sin evidencia

- GIVEN un brief que declara una experiencia en primera persona ("lideré X") sin evidencia aportada por el autor
- WHEN se valida el brief
- THEN el sistema la clasifica como `author_opinion` no verificada o `needs_review`
- AND la generación MUST NOT tratarla como hecho (ver `genai-harness` HARN-06 y `evaluation` EVAL-05)

### Requirement: CAP-05 — Separación de tipos de afirmación

El sistema MUST separar en el brief las afirmaciones en `known_facts`, `author_opinions` y `open_questions` (SOLUTION.md §12.8) y MUST persistir esa clasificación junto al brief.

#### Scenario: brief con los tres tipos

- GIVEN un brief con hechos aportados, una opinión del autor y una pregunta abierta
- WHEN el brief se valida y guarda
- THEN cada afirmación queda clasificada en su tipo correspondiente
- AND la clasificación queda disponible para el harness de generación y la evaluación

#### Scenario: afirmación sin clasificar

- GIVEN una afirmación del brief que no puede clasificarse en ningún tipo
- WHEN se valida el brief
- THEN el sistema la marca `needs_review` y no la asume como hecho
- AND puede bloquear su uso como evidencia hasta resolución humana

### Requirement: CAP-06 — Transición a `BRIEF_READY`

El sistema MUST transicionar el proyecto a `BRIEF_READY` solo cuando el brief es válido (tesis + evidencia + clasificación coherente); cualquier intento de transición sin validación MUST ser rechazado sin mutar el estado.

#### Scenario: transición válida

- GIVEN un brief completo y validado
- WHEN se confirma
- THEN el proyecto pasa de `IDEA` a `BRIEF_READY` mediante la transición legal de la FSM

#### Scenario: transición ilegal (salto a generación)

- GIVEN un proyecto en `IDEA` con brief incompleto
- WHEN se intenta invocar la acción de generación directamente
- THEN la FSM rechaza la transición `IDEA → GENERATING` como ilegal
- AND el estado permanece `IDEA` y el error indica el requisito faltante
