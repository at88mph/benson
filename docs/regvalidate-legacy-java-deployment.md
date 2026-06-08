# Registry validate — legacy Java application and deployment

Maintainer-facing notes for the **existing** `regvalidate` implementation: Ant packaging, servlet wiring, modular dependencies, and source paths. **Behavior** for replacements is documented in [regvalidate-functional-contract.md](regvalidate-functional-contract.md).

---

## Modules (repository layout)

| Module | Role |
|--------|------|
| [`ivoaharvest/`](../ivoaharvest/) | Builds **`regvalidate.war`**, harvest validation servlets, XSL/XSD assets. |
| [`dalvalidate/`](../dalvalidate/) | Shared validation framework: servlet base (`ValidaterWebApp`), `XSLEvaluator`, `HTTPGetTestQuery`, `ResultTypes`. |
| `junx-master` (see [README](../README.md)) | XML schema / validation utilities consumed by Ivy (`ncsa.xml.validation`). |
| [`rofrtar/`](../rofrtar/) | Apache `httpd` content and packaging tarball. |

**Repository Explorer (C)** / **`comply`:** External OAI validation binary; referenced from harvest XML config (`@rofr_home@/bin/comply`). See README module **Repository_Explorer-2.0-1.46**.

---

## Build (`ivoaharvest/build.xml`)

- **Default target:** `package` produces JAR + WAR after tests.
- **Config staging:** Copies filtered [`WebAppValidateHarvest.xml.in`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/WebAppValidateHarvest.xml.in) → `classes/.../config.xml`; [`WebAppValidateVOResource.xml.in`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/WebAppValidateVOResource.xml.in) → `vorconfig.xml`.
- **`registrySchemaLocation.txt`** copied to `classes/.../schemaLocation.txt`.
- **WAR:** [`regvalidate.war`](../ivoaharvest/build.xml) includes `WEB-INF/web.xml`, static HTML from `resources/html/` (filtered `.in`), and **`ivoaharvest`** JAR plus runtime Ivy jars (excluding `xercesImpl.jar` per Ant script).

Deployment properties are interpolated from **`deploy_env.properties`** (via parent `common.xml` / README).

---

## Servlet mapping (`web.xml`)

[`ivoaharvest/src/main/webapp/WEB-INF/web.xml`](../ivoaharvest/src/main/webapp/WEB-INF/web.xml):

| Servlet name | Implementation class | URL pattern |
|--------------|------------------------|-------------|
| `HarvestValidater` | `net.ivoa.registry.validate.HarvestValidaterWebApp` | `/HarvestValidater` |
| `VOResourceValidater` | `net.ivoa.registry.validate.VOResourceValidaterWebApp` | `/VOResourceValidater` |

With context **`/regvalidate`**, URLs are **`/regvalidate/HarvestValidater`** and **`/regvalidate/VOResourceValidater`**.

---

## HTTP front end (Apache + Tomcat)

Typical **`mod_jk`** fragment (see [README](../README.md)):

```
JkMount /regvalidate* rofr
```

Static HTML/CSS/JS for the bundled UI ships **inside** the WAR under the root context; **`rofrtar`** carries site-wide fragments that link into `/regvalidate`.

---

## Key Java sources

### Harvest servlet and session

- [`HarvestValidaterWebApp`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/HarvestValidaterWebApp.java) → extends [`ValidaterWebApp`](../dalvalidate/src/main/java/org/nvo/service/validation/webapp/ValidaterWebApp.java).
- [`HarvestValidationSession`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/HarvestValidationSession.java): `op` dispatch, caching, OAI/IVOA/VOR result streaming.
- [`HarvestValidater`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/HarvestValidater.java): `validateOAI`, `validateIVOAHarvest`, `validateVOResources`, `validate`, `cacheValidation`.

### VOR servlet

- [`VOResourceValidaterWebApp`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/VOResourceValidaterWebApp.java): multipart POST / broken GET path.
- [`VOResourceValidater`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/VOResourceValidater.java): schema + `checkVOResource.xsl`.

### OAI Explorer bridge

- [`OAIExplorerTestQuery`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/OAIExplorerTestQuery.java), [`OAIEvaluator`](../ivoaharvest/src/main/java/net/ivoa/registry/validate/OAIEvaluator.java).

### Harvest iterators

- [`Harvester`](../ivoaharvest/src/main/java/net/ivoa/registry/harvest/Harvester.java), [`HarvestRecordServer`](../ivoaharvest/src/main/java/net/ivoa/registry/harvest/iterator/HarvestRecordServer.java), [`VOResourceExtractor`](../ivoaharvest/src/main/java/net/ivoa/registry/harvest/iterator/VOResourceExtractor.java).

### Framework helpers

- [`HTTPGetTestQuery`](../dalvalidate/src/main/java/org/nvo/service/validation/HTTPGetTestQuery.java), [`ValidationSessionBase`](../dalvalidate/src/main/java/org/nvo/service/validation/webapp/ValidationSessionBase.java), [`ResultTypes`](../dalvalidate/src/main/java/org/nvo/service/validation/ResultTypes.java).

---

## Configuration templates

| File | Runtime name | Purpose |
|------|----------------|---------|
| [`WebAppValidateHarvest.xml.in`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/WebAppValidateHarvest.xml.in) | `config.xml` on classpath | OAI Explorer cmd/URL, `httpget` query list, `registerURL`, cache dir, timeouts, evaluator XSL refs, **`resultStylesheet`**. |
| [`WebAppValidateVOResource.xml.in`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/WebAppValidateVOResource.xml.in) | `vorconfig.xml` | Upload limits, VOR evaluator, result stylesheets per `format`. |

---

## XSD and classpath

Bundled XSDs ship under:

[`ivoaharvest/src/main/resources/net/ivoa/registry/validate/schemas/`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/schemas/)

Namespace map:

[`registrySchemaLocation.txt`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/registrySchemaLocation.txt)

Mirrored for non-Java consumers under [**`docs/schemas/`**](schemas/).

---

## Stylesheets (paths in repo)

| Path |
|------|
| [`checkIVOAOAI.xsl`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/checkIVOAOAI.xsl) |
| [`checkVOResource.xsl`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/checkVOResource.xsl) |
| [`validationCommon.xsl`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/validationCommon.xsl) |
| [`testsVOResource-v1_0.xsl`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/testsVOResource-v1_0.xsl) |
| [`Results-Harvest-html.xsl`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/Results-Harvest-html.xsl) |
| [`Results-VOResource-html.xsl`](../ivoaharvest/src/main/resources/net/ivoa/registry/validate/Results-VOResource-html.xsl) |

Harvest UI XSL refs: [`index.html.in`](../ivoaharvest/src/main/resources/html/index.html.in) (`ResultsFrag-Harvest-html.xsl`, `SummaryFrag-Harvest-html.xsl`).

---

## Registration CGI

`HarvestValidationSession.doRegister` fetches **`registerURL`** + **`runid`** from `config.xml`. URL template is authored in **`WebAppValidateHarvest.xml.in`** (`registerURL` … `cgi-bin/register.pl`).

---

## Install reminder (Tomcat)

From [README](../README.md):

```shell
scp ~/.ivy2/local/nvo/ivoaharvest/<VERSION>/wars/regvalidate.war $CATALINA_HOME/webapps
```

Use **`ant install`** at repo root after `deploy_env.properties` is set for Ivy publish.
