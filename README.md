# k9x Enterprise Repository

The TOGAF **Architecture Repository** counterpart to
[k9x_continuum](https://github.com/k9aif/continuum), which implements the
Enterprise **Continuum**, the classification and governance lens. This
service is the actual store behind that lens: artifact content, the
Standards Information Base, and a real Governance Log (compliance
assessments, dispensations), searchable and browsable by anyone across the
enterprise. It's the agentic-world equivalent of what an SOA service
registry (UDDI) or an API catalog (SwaggerHub) used to provide, but for
SBB/ABB artifacts instead of services or APIs.

No off-the-shelf open-source "TOGAF repository" product exists. TOGAF
defines the repository structure, not a product. This is that structure,
implemented directly on PostgreSQL, following k9x_continuum's own proven
FastAPI + Postgres + static-webui pattern.

## What it stores

- **Artifacts.** Actual content (YAML specs, PlantUML source, code,
  OpenAPI, ADRs), not just pointers. Each one is keyed to an SBB or ABB in
  `k9x_continuum`'s catalog by `entity_type`/`entity_id`. This is a loose,
  application-level reference, not a database foreign key, since the two
  services use separate databases on the same Postgres host.
- **Standards Information Base.** TOGAF, DoDAF, MODAF, NAF, and custom
  standards as structured, queryable entities, linked to the entities that
  satisfy them.
- **Governance Log.** Compliance assessments and time-boxed dispensations.
  TOGAF practice requires every dispensation to carry an expiry.

## Facade

Read access (search, browse, article pages) is public, modeled on
Wikipedia: a search-first landing page, per-entity "article" pages with an
infobox, artifact content shown inline, a Categories section built from
linked standards, and a "What links here" backlinks list.

Writes (publishing an artifact, registering a standard, granting a
dispensation) require a shared `X-API-Key` header for now. See
`backend/auth_deps.py` for the plan to integrate with k9x_continuum's
user/JWT system once per-user attribution is needed beyond the free-text
`captured_by`/`approver` fields.

## Running locally

```bash
cp .env.sample .env
# Edit .env: point POSTGRES_HOST/PORT/DB/USER/PASSWORD at a running
# PostgreSQL instance, and set REPO_API_KEY to a random value:
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
./run.sh
```

`run.sh` creates a local virtualenv, installs `requirements.txt`, and
starts the app on `$REPO_PORT` (default `8086`; `k9x_continuum` uses
`8085`). On first startup the schema and tables are created if they don't
already exist.

## API

```
GET    /api/v1/search?q=&artifact_type=      List/search entities + standards
GET    /api/v1/search/categories             Frameworks + artifact types for browse

GET    /api/v1/entities/{type}/{id}          The "article" aggregate for one SBB/ABB

GET    /api/v1/artifacts?entity_type=&entity_id=&artifact_type=
GET    /api/v1/artifacts/{id}                Metadata + content
GET    /api/v1/artifacts/{id}/raw            Raw content, correct Content-Type
POST   /api/v1/artifacts                     Publish (requires X-API-Key)
DELETE /api/v1/artifacts/{id}                Requires X-API-Key

GET    /api/v1/standards?framework=
POST   /api/v1/standards                     Requires X-API-Key
POST   /api/v1/standards/link                Attach a standard to an entity, requires X-API-Key
GET    /api/v1/standards/{id}/entities

GET    /api/v1/dispensations?status=
POST   /api/v1/dispensations                 Requires X-API-Key
PATCH  /api/v1/dispensations/{id}/revoke     Requires X-API-Key
```

## Current status and known simplifications (MVP)

- Artifact content is text-only for now (`content_text`). The schema has a
  `content_bytes` column for small rendered binaries (SVG, PNG), but there's
  no upload endpoint for it yet.
- No per-artifact-size streaming. Content is capped at 5MB and stored
  inline in Postgres. Large binaries should graduate to the k9-aif Object
  Storage ABB (S3/MinIO) rather than growing this table. See the parent
  gap-analysis doc, Part 6.1.
- No lineage graph yet (Neo4j). The "backlinks" section on an entity page
  is computed from shared standards only, not full ABB/SBB/Application
  traceability. That's Phase D in the enhancement plan.
- Write auth is a single shared API key, not per-user. Fine for an MVP
  behind a trusted network, not sufficient once this is enterprise-facing.

See `togaf_gap_analysis_and_enhancement_plan.md` in the
[k9x_continuum](https://github.com/k9aif/continuum) repo for the full gap
analysis and phased plan this service implements Part 6 of.

## Part of the K9X ecosystem

Sibling project to [k9x_continuum](https://github.com/k9aif/continuum),
the Enterprise Continuum classification and governance layer this service
stores artifacts for, and [k9x_studio](https://github.com/k9aif/studiox),
a consumer of the same ABB/SBB catalog. Built on
[K9-AIF](https://github.com/k9aif/k9-aif-framework).

## License

Apache License 2.0. See [LICENSE](LICENSE).
