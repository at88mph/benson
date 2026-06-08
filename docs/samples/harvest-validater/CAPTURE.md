## Re-capturing `HarvestValidater` fixtures

Run from **`docs/samples/harvest-validater/`** so output paths match the tracked files.

Replace `ENDPOINT` URL encoding as needed (`?` → `%3F` etc.). Example uses the CADC OAI base URL.

```bash
ENDPOINT_ENCODED='https%3A%2F%2Fws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca%2Freg%2Foai%3F'
BASE='http://rofr.ivoa.net/regvalidate/HarvestValidater'
COOKIEJAR=/tmp/rofr-harvest-cookies.txt

rm -f "$COOKIEJAR"
curl -sS -c "$COOKIEJAR" -b "$COOKIEJAR" \
  "${BASE}?endpoint=${ENDPOINT_ENCODED}&op=StartSession&errorFormat=json" \
  -o 01-start-session.json

# Extract sessionURL from single-quoted pseudo-JSON:
RUNURL=$(python3 -c "
import re
t = open('01-start-session.json').read()
m = re.search(r\"sessionURL:\\s*'([^']+)'\", t)
print(m.group(1) if m else '')
")
echo "RUNURL=$RUNURL"

# Async full pipeline (recommended for GetStatus population)
curl -sS -m 300 -b "$COOKIEJAR" "${RUNURL}cache=true&op=Validate" -o /tmp/cache-reply.txt

sleep 3
curl -sS -b "$COOKIEJAR" "${RUNURL}op=GetStatus&errorFormat=json" -o 04-get-status.json

curl -sS -m 120 -b "$COOKIEJAR" "${RUNURL}op=ValidateOAI&format=xml" -o 02-validate-oai.xml
curl -sS -m 60  -b "$COOKIEJAR" "${RUNURL}op=ValidateIVOA&format=xml" -o 03-validate-ivoa.xml
```

Commit updated files under `docs/samples/harvest-validater/` when refreshing golden shapes.
