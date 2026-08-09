"""Paquete de persistencia (lote D, Wave 1): SQLModel/SQLite en fichero.

Propiedad de archivos (tasks.md §2): ``backend/db/*`` + ``backend/tests/db/*``
corresponden al lote D. Los módulos expuestos son:

- ``db.engine`` — engine + session factory + ``create_all`` idempotente (D.1).
- ``db.models`` — las 5 tablas SQLModel de design §9.1 (D.2).
- ``db.repos`` — repos finos por agregado, traza append-only (D.3).
- ``db.seed`` — 3 ideas demo idempotentes + voz v0 provisional (D.4).
"""
