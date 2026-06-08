# `VOResourceValidater` sample responses

## File

| File | Description |
|------|-------------|
| `post-res-xml-response.xml` | XML body from **`POST`** `multipart/form-data` with `format=xml`, `show=fail warn rec`, and file field `record` set to the in-repo test fixture `ivoaharvest/src/test/java/net/ivoa/registry/vores/res.xml`. Captured from **`http://rofr.ivoa.net/regvalidate/VOResourceValidater`** (May 2026). |

## Replay

```bash
curl -sS -F "format=xml" -F "show=fail warn rec" \
  -F "record=@../../ivoaharvest/src/test/java/net/ivoa/registry/vores/res.xml;type=text/xml" \
  "http://rofr.ivoa.net/regvalidate/VOResourceValidater" \
  -o post-res-xml-response.xml
```

Run from **`docs/samples/voresource-validater/`**, or use an absolute path to `res.xml`.

## Note

The legacy servlet’s **GET** handler does not wire query parameters; interoperability is **POST**-only unless you fix the reference app.
