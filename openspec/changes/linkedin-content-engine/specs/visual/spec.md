# Especificación de dominio: `visual` — Visual SVG semántico y revisión

> Dominio NUEVO: spec completa.
> Capacidad P0: RF-05 | Contrato visual: SOLUTION.md §8 | Validación: §8 (validación automática + pertinencia humana).

## Purpose

El sistema debe producir un contrato visual y una tarjeta SVG determinística vinculados a la tesis del candidato aprobado, con `visual_rationale` (cada elemento vinculado a una frase/concepto de la tesis) y texto alternativo para accesibilidad, y debe exigir aprobación humana de la pertinencia semántica (RF-05, §8). El visual no decora: argumenta.

## Requirements

### Requirement: VIS-01 — Contrato visual derivado de la tesis

El sistema MUST derivar el visual desde un contrato visual estructurado: `tesis → concepto visual → elementos obligatorios → elementos prohibidos → composición → texto en imagen → alt text` (§8). MUST NOT generarse desde palabras clave sueltas.

#### Scenario: contrato completo para tesis demo

- GIVEN un candidato aprobado con la tesis "migrar COBOL es recuperar conocimiento operativo"
- WHEN se genera la propuesta visual
- THEN el sistema produce un concepto visual (p. ej., diagrama de dos capas: código vs conocimiento operativo oculto)
- AND el contrato lista elementos obligatorios, prohibidos, composición, texto en imagen y alt text

#### Scenario: concepto sin relación con la tesis

- GIVEN un concepto que solo repite palabras clave del nicho (p. ej., "computadora antigua con código verde") sin soportar la tesis
- WHEN se valida la pertinencia
- THEN el visual se marca como decorativo
- AND el sistema lo rechaza o lo deriva a `VISUAL_REVISION_REQUIRED` (RF-05 escenario "visual decorativo")

### Requirement: VIS-02 — SVG determinístico con plantilla única

El sistema MUST generar la tarjeta visual como SVG determinístico con una única plantilla editorial parametrizada, sin depender de un modelo de imagen (§8 estrategia MVP, proposal.md P0).

#### Scenario: reproducibilidad del SVG

- GIVEN el mismo contrato visual
- WHEN se renderiza el SVG dos veces
- THEN la salida es idéntica (mismo SVG, mismo orden de elementos)
- AND el asset se guarda localmente con su `localPath`

#### Scenario: plantilla única y accesible

- GIVEN una tarjeta SVG generada
- THEN usa la plantilla editorial única
- AND el SVG incluye el `altText` generado (accesibilidad) y texto legible en imagen

### Requirement: VIS-03 — `visual_rationale` con vínculos

El sistema MUST incluir en el contrato visual una lista `visual_rationale` que vincula cada elemento visual con una frase o concepto explícito de la tesis; un elemento sin vínculo no vacío MUST invalidar el contrato (§8, RF-05).

#### Scenario: rationale completo

- GIVEN un contrato visual generado
- THEN cada elemento del SVG tiene una entrada en `visual_rationale`
- AND cada entrada referencia la frase/concepto de la tesis que justifica el elemento

#### Scenario: elemento sin vínculo

- GIVEN un contrato visual con un elemento sin `visual_rationale` o con vínculo vacío
- WHEN se ejecuta la validación automática
- THEN el contrato se rechaza
- AND el visual queda `VISUAL_REVISION_REQUIRED` (no puede avanzar)

### Requirement: VIS-04 — Texto alternativo obligatorio

El sistema MUST generar `altText` específico (no vacío, no genérico) para el visual, y la validación automática MUST rechazar un visual sin alt text (§8, RF-05).

#### Scenario: alt text específico

- GIVEN un visual generado
- THEN el `altText` describe el contenido y su relación con la tesis
- AND la validación automática pasa (alt text no vacío)

#### Scenario: alt text ausente

- GIVEN un contrato visual sin `altText`
- WHEN se ejecuta la validación automática
- THEN el contrato se rechaza por alt text faltante
- AND el visual no puede marcarse `VISUAL_READY`

### Requirement: VIS-05 — Validación automática + pertinencia humana

El sistema MUST validar automáticamente la completitud del contrato (vínculos no vacíos, alt text, elementos prohibidos ausentes) y MUST delegar la pertinencia semántica final a una persona (§8: "la pertinencia semántica final la aprueba una persona").

#### Scenario: validación automática y aprobación humana

- GIVEN un contrato visual completo
- WHEN se ejecuta la validación automática
- THEN la validación estructural pasa
- AND la aprobación de pertinencia queda pendiente de una persona (VIS-06)

#### Scenario: elemento prohibido presente

- GIVEN un visual que incluye una marca no autorizada o texto ilegible
- WHEN se ejecuta la validación automática
- THEN el visual se rechaza (elemento prohibido o ilegible)
- AND queda `VISUAL_REVISION_REQUIRED`

### Requirement: VIS-06 — Aprobación o revisión humana

El sistema MUST permitir que una persona apruebe el visual como `VISUAL_READY` o lo rechace como `VISUAL_REVISION_REQUIRED`; la aprobación del visual MUST ser humana (RF-05, §6.2 FSM: `VISUAL_DRAFT → VISUAL_READY | VISUAL_REVISION_REQUIRED`).

#### Scenario: visual aprobado

- GIVEN un proyecto en `VISUAL_DRAFT` con contrato válido
- WHEN el usuario aprueba la pertinencia del visual
- THEN el proyecto transiciona a `VISUAL_READY`
- AND la aprobación queda registrada con actor y momento

#### Scenario: visual rechazado y regenerado

- GIVEN un visual en `VISUAL_REVISION_REQUIRED`
- WHEN el usuario solicita regenerar el visual corregido
- THEN el proyecto vuelve a `VISUAL_DRAFT`
- AND la nueva versión se genera sobre el mismo candidato aprobado (o con las correcciones indicadas)

#### Scenario: aprobación automática prohibida

- GIVEN un contrato visual que pasa la validación automática
- WHEN el sistema intenta avanzar a `VISUAL_READY` sin acción humana
- THEN la FSM lo impide
- AND `VISUAL_READY` solo se alcanza por aprobación humana explícita

### Requirement: VIS-07 — Rechazo de visuales decorativos o estereotipados

El sistema MUST rechazar visuales que solo decoren, incluyan marcas no autorizadas, texto ilegible o estereotipos retro sin relación argumental con la tesis (§8).

#### Scenario: estereotipo retro sin relación

- GIVEN un visual con estereotipo retro (p. ej., cinta magnética decorativa) sin relación con el argumento de la tesis
- WHEN una persona revisa la pertinencia
- THEN puede rechazarlo como `VISUAL_REVISION_REQUIRED`
- AND el rechazo queda registrado con el motivo

#### Scenario: vínculo semántico defendible

- GIVEN un visual cuyo `visual_rationale` defiende cada elemento desde la tesis
- WHEN una persona revisa la pertinencia
- THEN la persona puede aprobarlo como `VISUAL_READY`
- AND el `visual_rationale` queda disponible en la traza del asset
