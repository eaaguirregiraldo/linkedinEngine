# Motor de contenidos para LinkedIn sobre COBOL y mainframes

## Definición de producto y solución previa a implementación

- **Estado:** propuesta para una prueba técnica de 24 horas
- **Propósito:** acordar qué se construirá, cómo se demostrará y qué evidencia permitirá considerarlo terminado
- **Restricción principal:** en 24 horas se prioriza un flujo pequeño, ejecutable y honesto por encima de una plataforma completa

---

## 1. Resumen ejecutivo

La prueba pide demostrar un motor editorial asistido por GenAI capaz de transformar una idea sobre COBOL/mainframes en candidatos de publicación para LinkedIn, evaluarlos de forma trazable, ayudar a elegir el mejor, proponer una imagen relacionada con la tesis y cerrar el flujo con una publicación simulada claramente identificada.

El valor no está en conectar un chat a un modelo ni en prometer que un post será viral. Está en diseñar un proceso editorial reproducible donde:

1. la entrada se convierte en un brief concreto;
2. el modelo genera pocas alternativas estructuradas;
3. cada alternativa pasa por validaciones y una heurística transparente;
4. la señal de potencial cambia una decisión real del flujo;
5. una persona conserva la aprobación final;
6. el sistema registra prompt, modelo, evidencia, puntuación y decisión;
7. la demo nunca confunde una simulación con una publicación real.

La solución recomendada es una aplicación local, con datos de demostración, persistencia liviana y un adaptador de proveedor GenAI intercambiable. Esa elección reduce dependencias externas y permite evaluar el diseño aun sin credenciales de LinkedIn o de un modelo comercial.

---

## 2. Interpretación concreta de la prueba

### 2.1 Qué pide realmente

- Un **flujo de producto completo**, no solamente una caja de texto que llama a un LLM.
- Un motor enfocado en el nicho **COBOL/mainframes**, con contexto, vocabulario y controles propios del dominio.
- Asistencia para convertir una idea en contenido publicable y no una automatización editorial sin supervisión.
- Alguna señal de “viralidad” o potencial de rendimiento que sea **explicable y accionable**.
- Una relación semántica verificable entre la tesis del post y su propuesta visual.
- Evidencia de disciplina de ingeniería de GenAI: prompts versionados, contratos de salida, validación, evaluación, trazabilidad y manejo de fallos.
- Una demo que pueda recorrerse de punta a punta dentro de las limitaciones de una prueba de 24 horas.

### 2.2 Qué no pide

- No pide entrenar un modelo propio ni hacer fine-tuning.
- No pide un predictor científico de alcance, impresiones o engagement. Sin datos históricos suficientes y sin experimentos controlados, esa afirmación sería falsa.
- No pide un sistema autónomo que publique sin aprobación humana.
- No pide un calendario editorial, analítica histórica completa, colaboración multiusuario, campañas, A/B testing real ni gestión de comunidad.
- No pide scraping de LinkedIn ni evasión de sus términos de servicio.
- No pide demostrar una publicación real si no existen una aplicación aprobada, permisos OAuth vigentes y una cuenta autorizada.
- No pide resolver en 24 horas la identidad editorial definitiva de Juan Lucas Barbier. Se propone una voz inicial y se deja preparado el mecanismo para validarla.

### 2.3 Resultado esperado de la prueba

Una persona evaluadora debería poder ejecutar localmente la solución, seleccionar una idea de demo, obtener tres borradores distintos, entender por qué uno fue recomendado, revisar el contenido y su concepto visual, aprobarlo y completar una publicación simulada. Al final debe existir una traza que explique qué entradas, prompts, modelo, validaciones y decisiones produjeron el resultado.

---

## 3. Producto

### 3.1 Objetivo

Reducir el tiempo y la variabilidad necesarios para transformar conocimiento experto sobre sistemas legacy en publicaciones de LinkedIn claras, específicas y defendibles, sin diluir la voz del autor ni inventar hechos.

### 3.2 Usuario objetivo

**Usuario primario:** Juan Lucas Barbier, asumido inicialmente como autor o referente que desea construir una presencia profesional alrededor de COBOL, modernización y mainframes.

**Usuario secundario:** una persona editora o evaluadora que revisa calidad, riesgos, coherencia de voz y estado de publicación.

**Audiencia del contenido:** profesionales de COBOL/mainframe, líderes de tecnología, responsables de modernización, arquitectos, reclutadores técnicos y perfiles jóvenes que necesitan entender por qué estos sistemas siguen siendo relevantes.

### 3.3 Propuesta de valor

> Convertir una idea técnica en un borrador de LinkedIn específico, evaluado y trazable en pocos minutos, manteniendo el control humano y haciendo explícitos los límites de la automatización.

### 3.4 Principios de producto

- **Especificidad antes que volumen:** tres candidatos útiles son mejores que veinte variaciones superficiales.
- **Trazabilidad antes que magia:** toda recomendación importante debe poder explicarse.
- **Humano antes que autopublicación:** el sistema recomienda; el autor decide.
- **Dominio antes que prosa genérica:** si falta evidencia, se pregunta o se marca la afirmación; no se rellena.
- **Estados honestos:** `SIMULATED_PUBLISHED` no significa `PUBLISHED_REAL`.

---

## 4. Supuestos sobre Juan Lucas Barbier y voz inicial

No se recibió una entrevista, un corpus validado de publicaciones ni métricas históricas del autor. Por lo tanto, lo siguiente son **hipótesis de trabajo**, no atributos personales afirmados como hechos.

### 4.1 Supuestos materiales

| Supuesto inicial | Por qué importa | Cómo se valida después |
|---|---|---|
| Juan tiene experiencia o acceso a conocimiento verificable sobre COBOL/mainframes | Define el nivel de autoridad permitido | Entrevista de 30 minutos y revisión de fuentes o experiencias autorizadas |
| Busca posicionamiento profesional, no venta agresiva | Cambia llamadas a la acción y tono | Acordar objetivo de marca: autoridad, contratación, consultoría o comunidad |
| Publicará principalmente en español | Define idioma, ejemplos y mercado | Confirmar idiomas y países objetivo |
| Su audiencia mezcla especialistas y decisores no especialistas | Obliga a explicar sin banalizar | Revisar perfiles objetivo y métricas por segmento |
| Prefiere revisar antes de publicar | Justifica aprobación humana obligatoria | Confirmar nivel de autonomía deseado |
| Puede aportar anécdotas y tesis propias | Evita contenido intercambiable | Crear un banco aprobado de experiencias, posturas y temas prohibidos |

### 4.2 Hipótesis de voz v0

- Técnica y sobria, con autoridad basada en experiencia, no en grandilocuencia.
- Didáctica para personas no especialistas, sin tratar a COBOL como una curiosidad arqueológica.
- Directa y levemente contraria a lugares comunes, pero no provocadora por defecto.
- Usa ejemplos concretos, consecuencias operativas y decisiones de negocio.
- Evita frases vacías como “el futuro ya llegó”, “en un mundo en constante evolución” o “COBOL está más vivo que nunca” sin evidencia.
- No inventa experiencias en primera persona. Solo usa “vi”, “lideré” o “aprendí” cuando el autor haya aportado esa evidencia.
- Cierra con una pregunta específica o invitación a compartir experiencia, no con engagement bait.

### 4.3 Validación de voz posterior

La voz v0 debe validarse con 10 a 20 publicaciones reales aprobadas por Juan. Se compararán elecciones de apertura, longitud, tecnicidad, estructura, expresiones preferidas, llamadas a la acción y correcciones manuales. Hasta entonces, la interfaz debe etiquetarla como **perfil de voz provisional**.

---

## 5. Alcance del MVP de 24 horas

### 5.1 Incluido

- Aplicación local de un solo usuario.
- Tres ideas demo y posibilidad de escribir una idea propia.
- Brief editorial con tesis, audiencia, objetivo, evidencia disponible y restricciones.
- Generación de exactamente tres candidatos con enfoques diferenciados.
- Salida estructurada y validada para generación y evaluación.
- Heurística de potencial editorial de 0 a 100, visible por dimensión.
- Regla de decisión que recomienda candidato o exige revisión.
- Edición manual y aprobación explícita.
- Concepto visual y una pieza visual simple ligada a la tesis.
- Publicación simulada, con etiqueta persistente y recibo de simulación.
- Trazabilidad técnica de la ejecución actual.
- Modo demo/fallback sin dependencia obligatoria de una API externa.

### 5.2 Recortes explícitos

- Sin autenticación ni múltiples usuarios.
- Sin publicación real en LinkedIn como requisito de aceptación.
- Sin lectura automática de publicaciones o métricas de LinkedIn.
- Sin scheduler, calendario ni colas distribuidas.
- Sin generación avanzada de imágenes fotorrealistas.
- Sin RAG complejo, base vectorial ni fine-tuning.
- Sin predicción estadística de viralidad.
- Sin aprendizaje automático a partir de resultados históricos.
- Sin soporte multicanal.
- Sin moderación legal automatizada como sustituto de revisión humana.
- Sin infraestructura cloud obligatoria.

### 5.3 Por qué este recorte es convincente

El MVP demuestra el riesgo central: si el sistema puede producir contenido específico, explicar una recomendación y mantener integridad editorial. OAuth, scheduling y dashboards agregan integración, pero no prueban la calidad del motor. Meterlos en 24 horas desplazaría tiempo desde el núcleo hacia plumbing y credenciales.

### 5.4 Prioridad de entrega

**P0, obligatorio para la demo:** brief, tres candidatos, contratos de salida, evaluación y blockers, selección/aprobación humana, tarjeta visual SVG, publicación simulada, traza de la ejecución actual, provider demo y pruebas del dominio.

**P1, solo si P0 está estable:** un provider GenAI remoto activable por API key, historial navegable de ejecuciones y una prueba E2E. La interfaz intercambiable y el provider demo son P0; el adaptador remoto es P1 y la aceptación no depende de credenciales externas. Si se usa, su llamada exitosa y el modelo real deben quedar identificados; si no se usa, la UI debe decir `DEMO_PROVIDER`.

---

## 6. Flujo end-to-end demostrable

### 6.1 Flujo principal

1. **Elegir o crear una idea:** el usuario parte de una idea como: “Migrar COBOL no es un proyecto de traducción de código; es recuperación de conocimiento operativo”.

2. **Completar el brief:** se define audiencia, objetivo, tesis, evidencia disponible, nivel técnico y afirmaciones que requieren cautela.

3. **Generar tres candidatos:** el motor produce tres enfoques realmente distintos: historia/problema, marco práctico y postura argumentada. No se aceptan simples paráfrasis.

4. **Validar los contratos:** se controla esquema, longitud, presencia de tesis, afirmaciones no sustentadas, expresiones prohibidas y diferencias entre candidatos.

5. **Evaluar y puntuar:** cada candidato recibe dimensiones visibles, penalizaciones y explicación. La puntuación se guarda junto a la versión del evaluador.

6. **Tomar una decisión:** el candidato con mejor puntaje solo se recomienda si supera el umbral y no tiene bloqueos. De lo contrario, el flujo pasa a `REVISION_REQUIRED`.

7. **Revisar y aprobar:** el usuario puede editar, comparar y aprobar. Una edición invalida la evaluación anterior y requiere una reevaluación liviana.

8. **Crear propuesta visual:** el sistema extrae la tesis visual, propone una metáfora o diagrama y genera una tarjeta local simple con texto alternativo.

9. **Publicar de forma simulada:** al confirmar, se crea un recibo local con estado `SIMULATED_PUBLISHED`, fecha, contenido final y visual asociado. La pantalla dice “Simulación: no se envió contenido a LinkedIn”.

10. **Consultar la traza:** se muestran ejecución, entradas, versiones de prompt/esquema, proveedor/modelo, validaciones, puntajes, ediciones y transición final.

### 6.2 Estados honestos

```text
IDEA -> BRIEF_READY -> GENERATING
GENERATING -> GENERATED -> EVALUATING
GENERATING -> GENERATION_FAILED
EVALUATING -> RECOMMENDED | REVISION_REQUIRED | EVALUATION_PARTIAL
EVALUATION_PARTIAL -> REVISION_REQUIRED
RECOMMENDED -> APPROVED (después de revisión y sin blockers)
REVISION_REQUIRED -> APPROVED (override humano con razón y sin blockers)
APPROVED -> VISUAL_DRAFT
VISUAL_DRAFT -> VISUAL_READY | VISUAL_REVISION_REQUIRED
VISUAL_REVISION_REQUIRED -> VISUAL_DRAFT
VISUAL_READY -> SIMULATED_PUBLISHED

Estado reservado para una integración futura:
VISUAL_READY -> PUBLISHING_REAL
PUBLISHING_REAL -> PUBLISHED_REAL | REAL_PUBLISH_FAILED
```

`PUBLISHED_REAL` solo puede existir si se recibió una respuesta exitosa verificable de la API de LinkedIn y se almacenó el identificador remoto. Nunca se deriva de un timeout, una respuesta ambigua ni un botón presionado.

---

## 7. Señal heurística de potencial editorial

### 7.1 Qué es y qué no es

La señal es una **heurística de calidad y potencial de conversación**, no una probabilidad de viralidad. Sirve para comparar candidatos del mismo brief y detectar debilidades antes de publicar. No estima impresiones, likes ni conversiones.

### 7.2 Fórmula transparente

Cada dimensión se califica primero en una escala ordinal de 0 a 5 y se normaliza con `dimension_100 = rating * 20`. Las anclas comunes son: `0` ausente o contradictorio, `3` adecuado y demostrable, y `5` excepcional para este brief con evidencia textual concreta. Los valores `1`, `2` y `4` representan progresión entre esas anclas. El evaluador debe citar una frase del candidato y una regla de la rúbrica para justificar cada nota; una nota sin ambas referencias es inválida.

```text
base =
  0.20 * fuerza_del_hook
  0.20 * relevancia_para_el_nicho
  0.20 * especificidad_y_evidencia
  0.15 * claridad_y_legibilidad
  0.15 * potencial_de_conversacion
  0.10 * ajuste_a_la_voz

score_final = clamp(base - penalizacion_riesgo - penalizacion_genericidad, 0, 100)
```

Penalizaciones:

- `penalizacion_riesgo`: 25 por experiencia personal inventada; 10 por cada cifra o afirmación absoluta sin evidencia, con máximo de 25. Estos casos además pueden producir un blocker.
- `penalizacion_genericidad`: 5 por cada cliché del catálogo versionado, tesis intercambiable o repetición sustancial detectada, con máximo de 15.

La UI muestra el resultado redondeado y el desglose sin decimales. Las notas generadas por un LLM son recomendaciones editoriales; validaciones determinísticas como longitud, duplicación y términos prohibidos tienen prioridad.

### 7.3 Cómo interviene en una decisión real

- Si existe un bloqueo de evidencia o seguridad, el candidato no puede recomendarse, sin importar su puntaje.
- Si el mejor candidato obtiene `>= 72`, no tiene bloqueos y supera al segundo por al menos 4 puntos, pasa a `RECOMMENDED`.
- Si el mejor obtiene entre `60` y `71`, o la diferencia es menor a 4, pasa a `REVISION_REQUIRED` y se sugieren las dos mejoras de mayor impacto.
- Si todos están por debajo de `60`, se recomienda reformular el brief, no regenerar indefinidamente.
- El usuario puede elegir otro candidato, pero debe quedar registrada la razón. La heurística orienta; no reemplaza criterio editorial.

Los umbrales son iniciales y deberán calibrarse con publicaciones aprobadas y resultados observados. No se presentarán como universales.

### 7.4 Dimensiones observables

| Dimensión | Señal positiva | Señal negativa |
|---|---|---|
| Hook | Plantea tensión concreta en las primeras líneas | Promesa vaga o sensacionalista |
| Nicho | Nombra problemas, roles o decisiones mainframe reales | Podría aplicarse a cualquier tecnología |
| Especificidad/evidencia | Incluye ejemplo, mecanismo o fuente aportada | Cifras o causalidades no respaldadas |
| Claridad | Una tesis, párrafos escaneables, jerga explicada | Varias tesis o densidad innecesaria |
| Conversación | Pregunta debatible y pertinente | “¿Qué opinas?” genérico o engagement bait |
| Voz | Coincide con reglas provisionales y corpus aprobado | Imita una personalidad no validada |

---

## 8. Estrategia de imagen vinculada a la tesis

La imagen no se genera desde palabras clave sueltas. Se deriva de un contrato visual:

```text
tesis -> concepto visual -> elementos obligatorios -> elementos prohibidos
      -> composición -> texto en imagen -> alt text
```

Para la tesis de ejemplo, la propuesta no sería “una computadora antigua con código verde”. Podría ser un diagrama de dos capas donde una pequeña porción representa código y la mayor representa reglas operativas, excepciones y conocimiento tácito. La relación con el argumento puede explicarse en una frase.

### Estrategia MVP

- Generar una tarjeta SVG determinística con una sola plantilla editorial, sin depender de un modelo de imagen.
- Mostrar tesis corta, metáfora visual y uno o dos elementos de dominio.
- Generar texto alternativo específico para accesibilidad.
- Guardar `visual_rationale`: una lista que vincula cada elemento visual con una frase o concepto explícito de la tesis.
- Rechazar visuales que solo decoren, incluyan marcas no autorizadas, texto ilegible o estereotipos retro sin relación argumental.

La validación automática comprueba que cada elemento tenga un vínculo no vacío y que exista texto alternativo; la pertinencia semántica final la aprueba una persona. Un proveedor de imágenes generativas puede agregarse después detrás de otro adaptador. Para 24 horas, una pieza determinística es más rápida, reproducible y auditable.

---

## 9. Publicación real y simulada en LinkedIn

### 9.1 Modo incluido en el MVP

El MVP implementa **publicación simulada**. Al confirmar:

- no realiza llamadas a LinkedIn;
- guarda un recibo local;
- muestra una banda visible “SIMULACIÓN”;
- usa el estado `SIMULATED_PUBLISHED`;
- ofrece vista previa del texto y la imagen como se enviarían;
- no presenta URL, URN ni métricas remotas inventadas.

### 9.2 Requisitos para publicación real futura

Una integración real requiere, como mínimo:

- aplicación registrada en LinkedIn Developers;
- producto y permisos de publicación habilitados para el caso de uso;
- OAuth 2.0 con redirección segura, `state`, scopes vigentes y consentimiento del miembro;
- gestión segura de tokens, expiración y eventual renovación según las capacidades actuales de la plataforma;
- identificación del autor autorizado;
- carga previa del asset cuando exista imagen y espera de su disponibilidad;
- creación de la publicación mediante la versión vigente de la API;
- almacenamiento del identificador remoto y de la respuesta verificable;
- manejo de revocación, rate limits, errores parciales e idempotencia.

LinkedIn ha cambiado nombres de productos, scopes, endpoints y requisitos de revisión a lo largo del tiempo. Antes de implementar se deben verificar en la documentación oficial vigente permisos como los asociados a publicación por miembros, en lugar de asumir que una credencial de desarrollo alcanza.

### 9.3 Regla de integridad

Si no hay token válido, autorización, respuesta exitosa e identificador remoto, la aplicación **MUST NOT** mostrar `PUBLISHED_REAL`. Ante una respuesta incierta debe mostrar `REAL_PUBLISH_FAILED` o “estado remoto pendiente de verificación”, nunca éxito optimista.

---

## 10. Arquitectura mínima sugerida

### 10.1 Elección

Una aplicación web local full-stack en TypeScript y un solo proceso:

- **Aplicación:** Next.js con UI React y route handlers locales, enfocada en un recorrido lineal.
- **Persistencia:** SQLite mediante una capa pequeña de repositorios.
- **Contratos:** TypeScript + Zod para validar entradas y salidas de GenAI.
- **GenAI:** interfaz `GenAIProvider` con adaptador para un proveedor remoto y `DemoProvider` determinístico.
- **Visual:** una plantilla SVG renderizada localmente.
- **Pruebas:** Vitest para dominio/contratos y Playwright para el happy path, si el tiempo lo permite.

No se asume que este stack ya existe. Es una sugerencia para implementación. Un único proceso evita coordinar Vite y una API separada durante la prueba; las fronteras entre workflow, persistencia y proveedores se conservan como módulos, no como servicios.

### 10.2 Justificación

- Se ejecuta con un único comando y no requiere cloud.
- SQLite conserva trazas sin operar infraestructura.
- TypeScript comparte contratos entre frontend y backend.
- El adaptador desacopla el producto de un modelo concreto.
- El proveedor demo permite evaluar el recorrido sin secretos ni costos.
- No se agregan colas, microservicios, vectores ni observabilidad externa que no resuelven el riesgo principal.

### 10.3 Componentes

```text
[Next.js local: UI + route handlers]
                 |
                 v
       [Workflow / reglas] -> [SQLite]
            |          |
            |          +-> [SVG renderer]
            v
      [GenAI harness]
            |
     +------+-------+
     |              |
[Remote P1]    [Demo provider]
```

### 10.4 Responsabilidades

| Componente | Responsabilidad |
|---|---|
| UI | Capturar brief, comparar candidatos, editar, aprobar y mostrar estados |
| Workflow | Autorizar transiciones y aplicar reglas de recomendación/publicación |
| GenAI harness | Construir prompts, validar salida, reintentar y registrar trazas |
| Evaluador | Combinar chequeos determinísticos, rúbrica y penalizaciones |
| Visual renderer | Convertir contrato visual en una pieza reproducible |
| Repositorio | Persistir ejecuciones, versiones, decisiones y recibos |
| Provider adapter | Ocultar diferencias de SDK/modelo y normalizar errores |

---

## 11. Modelo de datos y estados

### 11.1 Entidades mínimas

| Entidad | Campos esenciales |
|---|---|
| `ContentProject` | `id`, `title`, `rawIdea`, `brief`, `status`, `createdAt`, `updatedAt` |
| `GenerationRun` | `id`, `projectId`, `status`, `provider`, `model`, `promptVersion`, `schemaVersion`, `startedAt`, `completedAt`, `errorCode`, `traceEvents[]` |
| `Candidate` | `id`, `runId`, `angle`, `hook`, `body`, `cta`, `claims[]`, `contentVersion`, `evaluation`, `decision` |
| `VisualAsset` | `id`, `candidateId`, `thesis`, `concept`, `rationale`, `altText`, `localPath`, `status` |
| `PublicationAttempt` | `id`, `candidateId`, `mode`, `status`, `remoteId?`, `receipt`, `createdAt` |

Estos son cinco agregados lógicos, no una obligación de crear una tabla por cada concepto editorial. Evaluación, decisión y eventos de traza pueden persistirse como JSON dentro de `Candidate` y `GenerationRun` para el MVP. No se deben persistir tokens OAuth ni secretos en estas tablas para la demo. Si luego se habilita publicación real, deben almacenarse cifrados o delegarse a un secret store.

### 11.2 Invariantes

- Un candidato editado incrementa `contentVersion` e invalida evaluaciones de versiones anteriores.
- Solo un candidato `APPROVED` puede generar el asset final.
- Solo un candidato aprobado con visual listo puede publicarse en modo simulado.
- Una ejecución fallida conserva el error y sus trazas, pero no crea candidatos incompletos como válidos.
- `SIMULATED_PUBLISHED` y `PUBLISHED_REAL` son estados mutuamente excluyentes por intento.

---

## 12. GenAI harnesses

Un harness no es solamente un prompt. Es el conjunto versionado que controla entrada, salida, validación, evaluación, fallos y evidencia de cada invocación.

### 12.1 Prompts versionados

Cada capacidad tendrá un identificador estable y versión semántica:

- `linkedin-candidate-generator@1.0.0`
- `editorial-evaluator@1.0.0`

Para P0 son suficientes esos dos prompts. El brief se valida con reglas de aplicación y el SVG se construye desde el contrato visual; agregar llamadas GenAI para normalizarlos sería costo y variabilidad sin valor demostrativo.

Cada prompt se guarda como archivo de texto versionado en `src/ai/prompts/` y se referencia desde un manifiesto; cambiar instrucciones o contrato exige subir su versión. La traza guarda versión, hash del prompt resuelto, parámetros del modelo y versión del esquema. El prompt separa instrucciones del sistema y datos del brief mediante delimitadores, e incluye propósito, contexto permitido, reglas de voz, formato de salida, ejemplos mínimos y prohibiciones.

### 12.2 Salida estructurada

La generación debe devolver JSON validable, por ejemplo:

```json
{
  "candidates": [
    {
      "angle": "practical-framework",
      "hook": "Hook A",
      "body": "Borrador A",
      "cta": "Pregunta A",
      "claims": [
        {
          "text": "Claim A",
          "support": "brief_evidence_id"
        }
      ]
    },
    {
      "angle": "problem-story",
      "hook": "Hook B",
      "body": "Borrador B",
      "cta": "Pregunta B",
      "claims": []
    },
    {
      "angle": "argued-position",
      "hook": "Hook C",
      "body": "Borrador C",
      "cta": "Pregunta C",
      "claims": [
        {
          "text": "Postura C",
          "support": "author_opinion"
        }
      ]
    }
  ]
}
```

El esquema exige exactamente tres candidatos, valores únicos de `angle`, campos no vacíos y enumeraciones cerradas. `author_opinion` debe redactarse como postura, no como hecho, y `needs_review` produce un blocker hasta que una persona lo vincule con evidencia o retire el claim. Texto fuera del JSON se considera inválido. La otra llamada GenAI de P0, el evaluador, también devuelve JSON validado con notas 0-5, citas, penalizaciones y blockers. El workflow construye el contrato visual desde la tesis aprobada y valida por schema sus elementos, vínculos y `altText`, sin una tercera llamada GenAI.

### 12.3 Validaciones

**Determinísticas:**

- esquema y tipos;
- tres candidatos exactos;
- límites configurables de caracteres;
- tesis presente;
- hooks y bodies no idénticos después de normalizar mayúsculas, espacios y puntuación;
- expresiones prohibidas y placeholders;
- afirmaciones marcadas con soporte;
- ausencia de URLs o cifras no presentes en el brief;
- contrato visual completo y `altText` no vacío.

**Semánticas:**

- coherencia con la tesis;
- ajuste a voz;
- especificidad de dominio;
- diferenciación de ángulos, explicando qué mecanismo narrativo cambia entre candidatos;
- relación entre concepto visual y argumento.

Las validaciones semánticas pueden usar un evaluador GenAI, pero su resultado debe mostrarse como juicio heurístico, no como verdad objetiva.

### 12.4 Guardrails

- El modelo no puede atribuir experiencias, clientes, cargos o resultados a Juan si no están en la evidencia aprobada.
- Las cifras requieren fuente aportada o quedan marcadas `needs_review`.
- No se generan ataques personales, secretos, datos personales ni consejos presentados como garantía.
- No se imita a otra persona viva ni se afirma que el texto fue escrito manualmente por Juan.
- Las instrucciones dentro de evidencia importada se tratan como datos, no como instrucciones del sistema.
- El contenido con blockers no puede pasar a aprobación sin resolución explícita.

### 12.5 Evaluación

Se combinan tres capas:

1. **Chequeos determinísticos:** contrato, longitud, duplicación, clichés y soporte de claims.
2. **Rúbrica GenAI:** seis dimensiones con explicación y citas del propio candidato.
3. **Decisión humana:** aprobación, rechazo o selección alternativa con razón.

Para reducir el sesgo del evaluador, este recibe los candidatos anonimizados y en orden aleatorio. El dataset mínimo de regresión contiene cuatro fixtures versionados con expectativas verificables: el candidato sólido queda sin blockers; el genérico recibe penalización de genericidad; el que inventa una cifra recibe blocker; y una salida JSON inválida termina en `GENERATION_FAILED` después de la reparación permitida. No se exige un score exacto producido por el LLM, pero sí rangos y reglas determinísticas esperadas.

### 12.6 Trazabilidad

Por ejecución se registra:

- brief y evidencia por identificador/hash;
- proveedor, modelo y parámetros relevantes;
- versiones de prompt y esquema;
- salida cruda protegida para depuración local y salida validada;
- errores, reparaciones y número de intentos;
- puntajes por dimensión y penalizaciones;
- ediciones humanas y decisión final;
- modo y resultado de publicación.

No se deben registrar secretos. Si los briefs reales contienen información sensible, la salida cruda debe poder desactivarse o redactarse.

### 12.7 Fallback y manejo de fallos

- Un error transitorio permite hasta dos reintentos con backoff.
- Un JSON inválido permite una única reparación usando el error del esquema, sin reescribir silenciosamente el contenido.
- Si vuelve a fallar, la ejecución termina `GENERATION_FAILED` y conserva la traza.
- Si no hay API key o red, el usuario puede elegir `DemoProvider`, que devuelve fixtures claramente etiquetados como datos demo.
- `DemoProvider` debe atravesar los mismos schemas, validaciones, reglas de estado y trazas que un provider remoto; solo sustituye la llamada externa.
- Si el evaluador GenAI falla, se muestran solo chequeos determinísticos y estado “evaluación semántica no disponible”; no se inventa un score completo.
- Nunca se cambia automáticamente de proveedor remoto sin avisar, porque los resultados y condiciones de privacidad pueden diferir.

### 12.8 Cómo evitar contenido genérico y alucinaciones

- Exigir una tesis única y al menos una evidencia, experiencia autorizada o ejemplo concreto antes de generar.
- Pedir mecanismos y consecuencias, no adjetivos de autoridad.
- Separar en el brief `known_facts`, `author_opinions` y `open_questions`.
- Crear un ledger de afirmaciones con soporte y bloquear las no sustentadas.
- Comparar similitud entre candidatos para evitar paráfrasis.
- Penalizar clichés y frases intercambiables.
- Permitir “evidencia insuficiente” como salida válida; el modelo no está obligado a completar huecos.
- Mantener temperatura moderada y variación en el ángulo, no en los hechos.
- Requerir revisión humana antes de cualquier publicación.

---

## 13. Especificación SDD

Esta sección define comportamiento observable. Los detalles de stack anteriores son una propuesta de diseño y no alteran estos requisitos.

### RF-01: Crear un brief editorial

El sistema **MUST** permitir crear un brief con idea, tesis, audiencia, objetivo, evidencia y restricciones.

#### Escenario: brief válido

- **GIVEN** una idea demo o escrita por el usuario
- **WHEN** el usuario completa los campos obligatorios y confirma
- **THEN** el sistema guarda el brief con estado `BRIEF_READY`
- **AND** muestra la voz provisional aplicada

#### Escenario: evidencia insuficiente

- **GIVEN** una idea que contiene una cifra o experiencia personal no respaldada
- **WHEN** el usuario intenta continuar
- **THEN** el sistema solicita evidencia o permite retirar la afirmación
- **AND** no presenta el dato como validado

### RF-02: Generar candidatos diferenciados

El sistema **MUST** generar exactamente tres candidatos estructurados y con ángulos distintos a partir de un brief válido.

#### Escenario: generación válida

- **GIVEN** un brief en `BRIEF_READY`
- **WHEN** el usuario solicita generación
- **THEN** el sistema produce tres candidatos válidos
- **AND** registra proveedor, modelo, prompt y esquema usados
- **AND** transiciona a `GENERATED`

#### Escenario: proveedor no disponible

- **GIVEN** que el proveedor remoto no tiene credenciales o falla
- **WHEN** la generación no puede completarse
- **THEN** el sistema muestra un error explícito
- **AND** ofrece usar datos demo sin presentarlos como respuesta remota

### RF-03: Validar y evaluar candidatos

El sistema **MUST** validar cada candidato y calcular una señal heurística desglosada cuando las capas requeridas estén disponibles.

#### Escenario: recomendación válida

- **GIVEN** tres candidatos sin blockers
- **WHEN** finaliza la evaluación
- **THEN** el sistema muestra dimensiones, penalizaciones y puntaje final
- **AND** recomienda el mejor solo si cumple umbral y diferencia definidos

#### Escenario: claim sin sustento

- **GIVEN** un candidato con una cifra no incluida en la evidencia
- **WHEN** se ejecutan las validaciones
- **THEN** el candidato recibe un blocker de evidencia
- **AND** no puede quedar `RECOMMENDED` por puntaje alto

#### Escenario: evaluador semántico fallido

- **GIVEN** candidatos estructuralmente válidos
- **WHEN** el evaluador GenAI no responde
- **THEN** el sistema conserva chequeos determinísticos
- **AND** indica que no hay score semántico completo
- **AND** no fabrica valores faltantes

### RF-04: Revisar y aprobar contenido

El sistema **MUST** permitir editar un candidato y exigir aprobación humana explícita.

#### Escenario: edición invalida evaluación

- **GIVEN** un candidato evaluado
- **WHEN** el usuario modifica su contenido
- **THEN** el sistema incrementa su versión
- **AND** marca la evaluación anterior como desactualizada
- **AND** solicita reevaluación antes de aprobar

#### Escenario: selección distinta a la recomendación

- **GIVEN** un candidato recomendado
- **WHEN** el usuario elige otro candidato
- **THEN** el sistema permite la elección
- **AND** registra una razón editorial

### RF-05: Producir una propuesta visual pertinente

El sistema **MUST** producir un contrato visual y una pieza local vinculados a la tesis del candidato aprobado.

#### Escenario: visual válido

- **GIVEN** un candidato aprobado
- **WHEN** el usuario genera la propuesta visual
- **THEN** el sistema crea concepto, composición y texto alternativo
- **AND** cada elemento visual queda vinculado en `visual_rationale` con una frase o concepto de la tesis
- **AND** una persona puede aprobarlo como `VISUAL_READY` o rechazarlo como `VISUAL_REVISION_REQUIRED`

#### Escenario: visual decorativo

- **GIVEN** un concepto que solo repite palabras clave y no soporta la tesis
- **WHEN** falta un vínculo en `visual_rationale` o la persona rechaza su pertinencia
- **THEN** el sistema lo marca `VISUAL_REVISION_REQUIRED`

### RF-06: Simular publicación sin ambigüedad

El sistema **MUST** completar una publicación local simulada y **MUST NOT** representarla como publicación real.

#### Escenario: publicación simulada

- **GIVEN** un candidato aprobado y un visual listo
- **WHEN** el usuario confirma “Simular publicación”
- **THEN** el sistema crea un recibo con estado `SIMULATED_PUBLISHED`
- **AND** muestra “no se envió contenido a LinkedIn”
- **AND** no crea identificadores remotos ficticios

#### Escenario: intento sin aprobación

- **GIVEN** un candidato no aprobado
- **WHEN** el usuario intenta simular la publicación
- **THEN** el sistema bloquea la transición
- **AND** explica el requisito faltante

### RF-07: Consultar trazabilidad

El sistema **MUST** permitir consultar la historia técnica y editorial de una ejecución.

#### Escenario: auditoría completa

- **GIVEN** una ejecución terminada
- **WHEN** el usuario abre su detalle
- **THEN** el sistema muestra versiones, estados, validaciones, decisiones y modo de publicación
- **AND** no expone secretos

### RNF-01: Ejecución local y reproducible

La solución **MUST** poder iniciarse localmente con instrucciones documentadas y datos demo, sin requerir una cuenta de LinkedIn.

#### Escenario: evaluación sin credenciales

- **GIVEN** una máquina con dependencias instaladas y sin API keys
- **WHEN** la persona evaluadora inicia el modo demo
- **THEN** puede recorrer el happy path completo con resultados determinísticos

### RNF-02: Claridad de estados

La UI **MUST** distinguir visual y textualmente estados reales, simulados, fallidos y pendientes.

#### Escenario: inspección de simulación

- **GIVEN** una publicación simulada
- **WHEN** se consulta desde cualquier vista relevante
- **THEN** conserva la etiqueta “SIMULACIÓN” y el estado `SIMULATED_PUBLISHED`

### RNF-03: Resiliencia

El sistema **SHOULD** preservar el trabajo y mostrar errores accionables ante fallos de proveedor o validación.

#### Escenario: salida inválida

- **GIVEN** una respuesta GenAI que no cumple el esquema
- **WHEN** falla también el único intento de reparación
- **THEN** la ejecución termina de forma controlada
- **AND** el brief permanece disponible para reintentar

### RNF-04: Seguridad y privacidad mínimas

El sistema **MUST NOT** guardar secretos en el repositorio, trazas visibles o base demo.

#### Escenario: inspección de trazas

- **GIVEN** una ejecución con proveedor remoto
- **WHEN** se consulta o exporta la traza
- **THEN** no aparecen API keys, tokens OAuth ni cabeceras de autorización

### RNF-05: Respuesta visible de la UI

La UI **MUST** mostrar el estado en curso y bloquear envíos duplicados mientras una operación asíncrona está pendiente. No se fija un SLA de respuesta del proveedor remoto porque está fuera del control del MVP.

#### Escenario: generación remota lenta

- **GIVEN** una solicitud GenAI en curso
- **WHEN** la solicitud queda pendiente
- **THEN** la UI muestra estado `GENERATING`
- **AND** evita solicitudes duplicadas accidentales

---

## 14. Criterios de aceptación

El MVP se acepta si se puede demostrar que todos los siguientes criterios P0 se cumplen:

- [ ] Arranca localmente siguiendo el README y sin credenciales externas en modo demo.
- [ ] La UI y la traza identifican inequívocamente `DEMO_PROVIDER` cuando no hubo una llamada GenAI real.
- [ ] `DemoProvider` atraviesa los mismos schemas, guardrails y transiciones que un provider remoto.
- [ ] Ofrece al menos tres ideas demo y permite una idea manual.
- [ ] Obliga a definir una tesis y evidencia antes de generar.
- [ ] Produce exactamente tres candidatos con valores únicos de `angle`, sin hooks o bodies normalizados idénticos y con contrato válido.
- [ ] Expone una heurística desglosada, penalizaciones y umbrales.
- [ ] La heurística cambia el estado a `RECOMMENDED` o `REVISION_REQUIRED` según reglas reproducibles.
- [ ] Un blocker de evidencia impide recomendar contenido aunque su score sea alto.
- [ ] Una edición invalida la evaluación previa.
- [ ] La aprobación final siempre es humana.
- [ ] La propuesta visual vincula cada elemento con la tesis, incluye texto alternativo y requiere aprobación humana.
- [ ] El happy path termina en `SIMULATED_PUBLISHED` con una advertencia inequívoca.
- [ ] No aparece una URL o identificador remoto inventado.
- [ ] La traza muestra versiones de prompts/esquemas, proveedor, validaciones y decisión.
- [ ] El fallo de un proveedor no destruye el brief ni se representa como éxito.
- [ ] Existen pruebas automatizadas para fórmula, blockers, transiciones y validación de esquema.

---

## 15. Demo principal

### Idea demo

> “Migrar COBOL no es traducir sintaxis; es recuperar conocimiento operativo antes de tocar código”.

### Evidencia demo permitida

- Los programas legacy pueden contener reglas de negocio acumuladas.
- El conocimiento puede estar distribuido entre código, jobs, procedimientos y personas.
- No se usarán cifras, empresas ni anécdotas atribuidas a Juan.

### Recorrido de 5 a 7 minutos

1. Abrir la aplicación en modo demo y elegir la idea.
2. Mostrar tesis, audiencia “líderes de modernización” y restricciones.
3. Generar tres candidatos: relato del riesgo, checklist práctico y postura argumentada.
4. Abrir la comparación y explicar dos dimensiones del score.
5. Mostrar que un candidato con una cifra inventada queda bloqueado en un fixture de prueba.
6. Elegir el candidato recomendado, editar una línea y observar que requiere reevaluación.
7. Aprobar el texto y generar el visual de “código visible vs conocimiento operativo oculto”.
8. Confirmar la simulación y mostrar el recibo `SIMULATED_PUBLISHED`.
9. Abrir la traza y señalar prompt, esquema, provider demo, evaluación y decisión humana.

La demo debe reservar un segundo caso corto con un fixture de salida inválida. Esto prueba que el harness no depende de un happy path perfecto aunque el adaptador remoto P1 no se haya implementado.

---

## 16. Entregables de la prueba

### Entregables esperados al implementar

- Código fuente del MVP.
- `README.md` con prerrequisitos, configuración, comandos, modo demo y limitaciones.
- Archivo `.env.example` sin secretos.
- Datos demo reproducibles.
- Prompts y esquemas versionados en el repositorio.
- Pruebas automatizadas del dominio y contratos críticos.
- Guion de demo y, si es viable, video corto de respaldo.
- Registro de decisiones técnicas y tradeoffs.
- Evidencia explícita de que LinkedIn está simulado.

### Entregable de esta fase

- `SOLUTION.md`: definición de producto, alcance, especificación SDD, diseño mínimo, criterios de aceptación y plan de ejecución. Este documento no afirma que la aplicación esté implementada.

---

## 17. Decisiones y tradeoffs

| Decisión | Alternativa descartada para el MVP | Tradeoff |
|---|---|---|
| Aplicación local | Deploy cloud obligatorio | Menor fricción y riesgo; no demuestra operación productiva |
| SQLite | PostgreSQL/servicio administrado | Cero infraestructura; concurrencia limitada, irrelevante para un usuario demo |
| Adaptador GenAI | SDK acoplado a un proveedor | Algo más de interfaz; permite demo y cambio de proveedor |
| Tres candidatos | Generación abierta | Menos variedad total; comparación más clara y controlable |
| Heurística explicable | Predictor de viralidad | Menos promesa comercial; mucha más honestidad y auditabilidad |
| Tarjeta visual determinística | Modelo generativo de imágenes | Menos impacto visual; mayor pertinencia, velocidad y reproducibilidad |
| Publicación simulada | Forzar OAuth en 24 horas | No demuestra integración real; evita depender de permisos fuera del control del candidato |
| Reglas + LLM judge | Solo LLM judge | Más implementación; reduce arbitrariedad y permite degradación parcial |
| Aprobación humana | Autopublicación | Un paso adicional; reduce riesgo reputacional y factual |

---

## 18. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación MVP |
|---|---|---|
| Contenido genérico | La demo parece un wrapper de chat | Brief obligatorio, ángulos distintos, evidencia y penalización de genericidad |
| Alucinaciones | Daño reputacional o técnico | Claim ledger, blockers, fuentes aportadas y aprobación humana |
| Evaluador inconsistente | Ranking poco confiable | Reglas determinísticas, rúbrica versionada, temperatura baja y explicación visible |
| “Viralidad” interpretada como predicción | Expectativas falsas | Llamarla señal heurística, mostrar fórmula y prohibir estimaciones de alcance |
| Voz incorrecta | El contenido no representa al autor | Etiqueta v0 provisional, corpus futuro y registro de ediciones |
| Imagen decorativa | Incoherencia editorial | Contrato visual, rationale y validador de relación con tesis |
| Falta de credenciales | Demo bloqueada | `DemoProvider` y publicación simulada como camino oficial |
| Simulación confundida con éxito real | Pérdida de confianza | Estados separados, banda persistente y ausencia de IDs remotos falsos |
| Alcance excesivo | MVP incompleto | Congelar recortes y proteger primero el flujo principal |
| Datos sensibles en trazas | Riesgo de privacidad | Redacción, hashes, logging configurable y exclusión de secretos |
| Dependencia de latencia/costo del modelo | Demo inestable | Fixtures determinísticos, timeouts y reintentos limitados |

---

## 19. Plan de ejecución de 24 horas

El plan asume una sola persona y prioriza un vertical slice. No incluye tiempo para conseguir aprobación de APIs externas.

| Bloque | Horas | Resultado verificable |
|---|---:|---|
| Congelar alcance y contratos | 0-2 | Estados, entidades, schemas y fixtures definidos |
| Scaffold local y persistencia | 2-4 | La aplicación arranca y SQLite guarda una ejecución |
| Brief y workflow de estados | 4-7 | Idea -> `BRIEF_READY`, con validaciones |
| Harness de generación | 7-11 | Tres candidatos estructurados con interfaz de provider y provider demo |
| Evaluación y regla de decisión | 11-14 | Score desglosado, blockers y recomendación reproducible |
| Revisión y aprobación | 14-16 | Edición, invalidación y decisión humana |
| Visual y publicación simulada | 16-18 | Asset local, alt text y recibo inequívoco |
| Trazabilidad y manejo de error | 18-20 | Vista de ejecución y fallback demostrable |
| Pruebas críticas | 20-22 | Fórmula, estados, schema y blockers cubiertos |
| README, pulido y ensayo | 22-24 | Instalación limpia y demo de 5-7 minutos ensayada |

### Regla de corte

Si P0 está atrasado a la hora 14, no se implementan provider remoto, historial ni E2E. No se recortan validaciones, estados ni integridad de simulación. Si hay atraso a la hora 18, el visual se reduce a la única tarjeta SVG parametrizada ya definida. El flujo completo tiene prioridad sobre profundidad cosmética.

---

## 20. Qué haríamos con una semana adicional

1. Entrevistar a Juan y construir un perfil de voz validado con publicaciones aprobadas.
2. Incorporar un banco curado de evidencias, experiencias y fuentes con procedencia.
3. Calibrar la rúbrica contra decisiones humanas y resultados históricos, sin confundir correlación con causalidad.
4. Agregar comparación ciega y evaluación periódica de prompts sobre un dataset de regresión.
5. Implementar integración real con LinkedIn solo si la aplicación y los permisos están aprobados.
6. Añadir almacenamiento seguro de tokens, idempotencia y reconciliación de estados remotos.
7. Mejorar el sistema visual con más composiciones determinísticas y, opcionalmente, un proveedor generativo.
8. Incorporar calendario, borradores y analítica básica si existe acceso legítimo a datos.
9. Agregar autenticación, separación de workspaces y despliegue controlado.
10. Ejecutar pruebas de seguridad, accesibilidad y observabilidad más completas.

---

## 21. Definición de terminado

La solución está terminada para la prueba cuando:

- el flujo principal puede recorrerse localmente de idea a publicación simulada sin intervención manual en la base de datos;
- cumple todos los criterios de aceptación obligatorios;
- los estados y errores son honestos y recuperables;
- la señal heurística afecta la recomendación y puede explicarse con su fórmula;
- ninguna afirmación sin soporte pasa silenciosamente como hecho validado;
- la voz está declarada como hipótesis provisional;
- el visual puede justificarse desde la tesis y tiene texto alternativo;
- la publicación simulada no puede confundirse con una publicación real;
- los prompts, esquemas, evaluaciones y decisiones quedan trazados;
- el modo demo funciona sin secretos ni servicios externos;
- las pruebas críticas pasan y el README permite reproducir la demo;
- las limitaciones y los pasos para una integración real están documentados;
- no quedan estados ficticios, botones sin comportamiento ni afirmaciones de capacidades no implementadas.

En términos de producto, “terminado” no significa que el motor garantice viralidad ni que haya aprendido definitivamente la voz de Juan. Significa que existe un circuito editorial pequeño, verificable y extensible que demuestra criterio de producto, disciplina SDD y uso responsable de GenAI.
