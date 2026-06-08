# HTTP response samples (`docs/samples/`)

Captured or hand-curated artefacts for **parity testing** and onboarding when re-implementing **`/regvalidate`**. They are **not** a full golden-file suite: registry health and deployment differences change pass/fail counts.

**Why parity is central:** There is almost no authoritative written spec beyond this repo and what the services actually return. **`http://rofr.ivoa.net`** (production) and **this codebase** (`ivoaharvest`, `dalvalidate`, XSL/XSD assets) therefore act jointly as **sources of discovery**: compare your replacement against live responses **and** against Java/XSL behaviour where the prose contract is silent. Treat regressions versus those references as defects unless you consciously document intentional differences.

| Subfolder | Contents |
|-----------|----------|
| [**harvest-validater/**](harvest-validater/) | `HarvestValidater` session flow: StartSession, ValidateOAI / ValidateIVOA XML, GetStatus JSON against a live OAI `endpoint`. See folder README for **`curl`** replay. |
| [**voresource-validater/**](voresource-validater/) | `VOResourceValidater` multipart **POST** (`format=xml`) response. |

**Normative behaviour** remains [regvalidate-functional-contract.md](../regvalidate-functional-contract.md). **Build/deploy** of the Java WAR: [regvalidate-legacy-java-deployment.md](../regvalidate-legacy-java-deployment.md).
