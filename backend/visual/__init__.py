"""Visual determinístico (lote F, Wave 2): contrato → validación → SVG.

Propiedad de archivos (tasks.md §2): ``backend/visual/*`` + ``backend/tests/visual/*``
corresponden al lote F. Sin LLM y sin red en P0 (design §7, ADR-006):

- ``visual.contract`` — ``build_visual_contract(thesis, candidate)``: mapa
  keyword→concepto versionado; elementos con ``rationale`` que cita frases
  literales de la tesis (F.1, VIS-01/03).
- ``visual.validate`` — validación automática: rationale no vacío, alt_text
  específico, elementos prohibidos ausentes (F.2, VIS-03/04/05/07).
- ``visual.svg`` — ``render_svg``: plantilla editorial única 1200×630,
  determinística y accesible (F.3, VIS-02).
- ``visual.image_provider`` — interfaz P1 desactivada por defecto (F.4,
  ADR-006): fallo → fallback a SVG con aviso, nunca conmutación silenciosa.

Los módulos usan solo stdlib (sin dependencias del contrato pydantic ni del
framework): el dict generado respeta la forma de ``VisualContract``
(api.schemas, C.1) para que el workflow (G) lo convierta al cruzar la API.
"""
