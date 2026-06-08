# `HarvestValidater` sample responses

Fixed **registry endpoint** used for capture (URL-encoded in requests):

`https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/oai?`

**Source host:** `http://rofr.ivoa.net` (May 2026 capture). Re-run the steps in [CAPTURE.md](CAPTURE.md) to refresh files after behaviour or endpoint changes.

## Files

| File | Description |
|------|-------------|
| `01-start-session.json` | Body of `op=StartSession&errorFormat=json`. Response is **pseudo-JSON** (single-quoted keys/strings) from the legacy servlet. |
| `02-validate-oai.xml` | Full `op=ValidateOAI&format=xml` document (OAI Explorer phase). Root `OAIValidation`. |
| `03-validate-ivoa.xml` | Full `op=ValidateIVOA&format=xml` (four fixed IVOA GETs + `checkIVOAOAI` output). Root `HarvestValidation`. |
| `04-get-status.json` | `op=GetStatus&errorFormat=json` after asynchronous `cache=true&op=Validate` had run in the same session. |
| `optional-tomcat-500-validate-badverb.html` | Example **HTTP 500** HTML from Tomcat when **`op=Validate`** or similar hit an OAI `badVerb` path (shape only; message may vary). |

## Notes for a new service

1. **Cookies:** Replays must send **`JSESSIONID`** for the same servlet context; the **StartSession** URL may include **`;jsessionid=…`** — use a cookie jar with `curl -c` / `-b`.
2. **`op=Validate` (synchronous)** against the reference deployment has been observed to return **500** (`OAI-PMH badVerb`); use **`ValidateOAI` / `ValidateIVOA` / `ValidateVOR`** and **GetStatus** plus **`cache=true`** for integration tests.
3. **JSON** arrays in `04-get-status.json` use JavaScript-like quoting; a strict JSON parser may need normalisation for tests.
