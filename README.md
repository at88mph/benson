# Benson

IVOA registry validator: OAI-PMH harvest checks, IVOA four-GET profile, VOResource XSD/XSLT validation.

Web UI colors and typography follow [ivoa.net](https://ivoa.net); design tokens live in [`assets/static/css/ivoa-theme.css`](assets/static/css/ivoa-theme.css).

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
source .venv/bin/activate
```

Production (no reload):

```bash
benson
# Proxy headers are on by default (--proxy-headers). Disable with: benson --no-proxy-headers
# or: uvicorn benson.app:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers
```

Development (auto-reload on changes under `src/` and `assets/`):

```bash
benson --reload
# or: BENSON_DEV=1 benson
# or: uvicorn benson.app:create_app --factory --host 0.0.0.0 --port 8000 --reload --reload-dir src --reload-dir assets
```

Endpoints: `/validator` and `/regvalidate` (async harvest validation form), `POST /validator/jobs`, `GET /oai` (IVOA standards OAI-PMH catalog from `assets/standards`), `GET /list-publishers` (publishers OAI XML catalog), `GET /api/v1/registry/publishers` (JSON), `/api/v1/registry-validate/harvest`, `POST /api/v1/registry-validate/voresource`.

Environment: `SCHEMA_ROOT` (default `./assets/schemas`), `ASSETS_ROOT` (XSLT under `./assets/validate`), `STANDARDS_DIR` (default `./assets/standards`, indexed at `/oai`), `OAI_REPOSITORY_NAME`, `OAI_ADMIN_EMAIL`, `OAI_REGISTRY_IDENTIFIER`, `OAI_MANAGED_AUTHORITY`, `OAI_MAX_RECORDS`, `TEMPLATES_DIR`, `STATIC_DIR`, `PUBLISHERS_DATA_DIR`, `PUBLISHERS_REGISTRY_FILE` (default `./data/publishers/publishers.json`), `REGISTRATION_MAX_FAILURES` (default `0`), `REGISTRATION_MAX_WARNINGS`, `REGISTRATION_REQUIRE_BUILTIN_SCHEMAS` (default on), `BENSON_PROXY_HEADERS` (default on; fixes template `url_for` behind a reverse proxy), `FORWARDED_ALLOW_IPS` (default `*`; tighten in production), `COMPLY_PATH`, `LOG_LEVEL` (default `INFO`), `BENSON_PARITY_JSON=1`, `BENSON_EXPOSE_ERRORS=1` (debug only).

### Built-in XSD catalog (`builtinSchemas`)

When the validator form enables **Use built-in XSD schemas**, phase 2 (IVOA four GETs) and phase 3 (harvested records) use the bundled namespace map in [`src/benson/xml/catalog.py`](src/benson/xml/catalog.py) under `SCHEMA_ROOT` (default [`assets/schemas/`](assets/schemas/)).

OAI responses are validated in two steps: embedded `description` / `metadata` / `about` payloads are checked against the appropriate IVOA XSDs (Registry Interface records use [`benson-ivoa-bundle.xsd`](assets/schemas/benson-ivoa-bundle.xsd) so `xsi:type` extensions such as `vg:Registry` resolve), then the OAI-PMH envelope is checked via [`benson-oai-bundle.xsd`](assets/schemas/benson-oai-bundle.xsd). Imports are resolved locally (no network). This matches the regvalidate functional contract intent; validating against `OAI-v2.xsd` alone is not sufficient for registry `Identify` responses that embed `ri:Resource` metadata.

**Developer guide:** [docs/schemas-and-validation-assets.md](docs/schemas-and-validation-assets.md) — directory layout, bundle composition, namespace table, XSLT assets (`assets/validate/`), standards catalog (`assets/standards/`), and how each validation phase uses them.

## Tests

After installing with `.[dev]` (see **Run** above):

```bash
pytest
```

On Debian/Ubuntu, install system libraries for `lxml` if needed: `apt-get install libxml2 libxslt1.1`.

## Docker

Build and run locally:

```bash
docker build -t benson:local .
docker run --rm -p 8000:8000 benson:local
```

Pull from GitLab Container Registry (after CI has pushed an image):

```bash
docker login registry.gitlab.com
docker pull registry.gitlab.com/djenkins.cadc/benson:latest
```

### Docker Compose

[`docker-compose.yml`](docker-compose.yml) runs Benson with host directories for registry catalogue data:

| Host path | Container path | Purpose |
|-----------|----------------|---------|
| `./data/searchables/` | `/data/searchables` | CSV exports of full searchable registries (RegTAP). Set `SEARCHABLES_CACHE_DIR` to this path. |
| `./data/publishers/` | `/data/publishers` | Registered publishing registries (`publishers.json`). Served as OAI XML at `/list-publishers`. |

Example layout:

```text
data/
  searchables/
    registries.csv          # RegTAP sync export
  publishers/
    publishers.json         # canonical registry list (OAI XML generated at /list-publishers)
```

```bash
docker compose up --build
```

Then open `http://localhost:8000/` (landing page) or `http://localhost:8000/validator`.

When the cache directory is empty, searchables are fetched live from `SEARCHABLES_REGTAP_SYNC_URL` if configured. An empty `publishers.json` is created automatically; register registries via the validator after a successful dry-run validation.
