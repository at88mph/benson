# IVOA standards catalog records

Default **`STANDARDS_DIR`**: VOResource **metadata records** for IVOA standards (one `*.xml` file per standard). These are **not** XSD schema files.

Served via Benson’s OAI-PMH endpoint (`GET /oai`, `set=ivo_managed`) and loaded by [`src/benson/registry/standards_store.py`](../../src/benson/registry/standards_store.py).

XSD validation of remote registries uses [`assets/schemas/`](../schemas/), not these files directly.

Full context: [`docs/schemas-and-validation-assets.md`](../../docs/schemas-and-validation-assets.md).
