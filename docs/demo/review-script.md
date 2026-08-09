# Guion de revisión P0 (5-7 minutos)

## Preparación

1. Ejecutá las instrucciones de instalación del README y `npm run dev`.
2. Confirmá `GET http://localhost:8000/api/health` y abrí `http://localhost:5173`.
3. Usá la primera idea demo o los datos de [`brief-mainframe.json`](brief-mainframe.json).

## Happy path

1. **Idea:** seleccioná la idea de migración y verificá que se crea un proyecto en `IDEA`.
2. **Brief:** confirmá tesis, audiencia, objetivo y las dos evidencias clasificadas; sin tesis o evidencia no se puede continuar.
3. **Generación:** pulsá una vez `Generar 3 candidatos`; verificá tres ángulos distintos, `DEMO_PROVIDER` y que el segundo click no duplica el run.
4. **Evaluación:** revisá score, dimensiones, pesos, umbrales, penalizaciones y blockers. La recomendación es reproducible.
5. **Aprobación:** elegí el candidato recomendado y escribí una razón humana. Un blocker o una razón vacía debe impedir aprobar.
6. **Visual:** generá el SVG, verificá `visual_rationale` y alt text, y aprobalo con otra razón humana. No hay autoaprobación.
7. **Publicación:** revisá la vista previa y pulsá publicar simulado. El estado final debe ser `SIMULATED_PUBLISHED`, con banda `SIMULACIÓN`, notice `no se envió contenido a LinkedIn` y sin ID/URL remoto.
8. **Traza:** verificá prompt/schema/hash, provider, validaciones, decisiones, `content_version`, recibo y ausencia de secretos.

## Caso de error no destructivo

1. Detené el backend y arrancalo con `DEMO_FORCE_INVALID=1 npm run dev`.
2. Repetí idea, brief y generación.
3. Confirmá `GENERATION_FAILED`, `repair_failed`, brief intacto y ausencia de candidatos incompletos.
4. Detené el backend, arrancalo sin `DEMO_FORCE_INVALID` y usá reintentar. Debe crearse un run nuevo y el flujo vuelve a ser válido.

## Evidencia de cierre

El resultado esperado es el happy path terminado en `SIMULATED_PUBLISHED`, el caso de error conservando el brief y las suites de regresión verdes. `PUBLISHED_REAL`, viralidad predicha y publicación remota no son criterios de este MVP.
