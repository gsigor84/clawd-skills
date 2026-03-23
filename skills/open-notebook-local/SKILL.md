---
name: open-notebook-local
description: Query and manage a local Open Notebook knowledge base / research assistant running on this machine (UI typically at http://localhost:8502). Use when you need to search/ask the KB, create/list/update notebooks, create sources, attach sources to notebooks, rebuild embeddings, or check service health via the local Open Notebook HTTP API (FastAPI Swagger docs at http://localhost:5055/docs).
---

# Open Notebook (local) — API workflow

Assume the services are local-only. Prefer `http://127.0.0.1` over `http://localhost`.

## Base URLs

- UI: `http://127.0.0.1:8502`
- API: `http://127.0.0.1:5055`
- Swagger: `http://127.0.0.1:5055/docs`
- OpenAPI spec: `http://127.0.0.1:5055/openapi.json`

## Tooling

- Use `exec` with `curl` for API calls.
- If you need to inspect the docs interactively, use the `browser` tool and open `http://127.0.0.1:5055/docs`.

## Quick checks

1) Health:

```bash
curl -sS http://127.0.0.1:5055/health | cat
```

2) Auth status:

```bash
curl -sS http://127.0.0.1:5055/api/auth/status | cat
```

3) Config:

```bash
curl -sS http://127.0.0.1:5055/api/config | cat
```

If endpoints return 401/403, re-check `/api/auth/status` and any required headers/cookies described in `/openapi.json`.

## High-value endpoints (from /docs)

### Search / Ask (KB querying)

- `POST /api/search` — Search Knowledge Base
- `POST /api/search/ask` — Ask Knowledge Base
- `POST /api/search/ask/simple` — Ask Knowledge Base Simple

Typical pattern:

```bash
curl -sS -X POST http://127.0.0.1:5055/api/search/ask/simple \
  -H 'Content-Type: application/json' \
  -d '{"question":"<your question>"}' | cat
```

If the API requires additional fields (e.g., notebook_id, model, top_k), read them from the OpenAPI spec:

```bash
curl -sS http://127.0.0.1:5055/openapi.json > /tmp/open-notebook-openapi.json
```

### Notebooks

- `GET /api/notebooks` — list notebooks
- `POST /api/notebooks` — create notebook
- `GET /api/notebooks/{notebook_id}` — get notebook
- `PUT /api/notebooks/{notebook_id}` — update notebook
- `GET /api/notebooks/{notebook_id}/delete-preview` — preview delete
- `DELETE /api/notebooks/{notebook_id}` — delete notebook
- `POST /api/notebooks/{notebook_id}/sources/{source_id}` — add source to notebook
- `DELETE /api/notebooks/{notebook_id}/sources/{source_id}` — remove source from notebook
- `POST /api/notebooks/{notebook_id}/context` — get notebook context

### Sources (documents/URLs ingested into the KB)

- `GET /api/sources`
- `POST /api/sources` — create source (often file upload)
- `POST /api/sources/json` — create source from JSON payload
- `GET /api/sources/{source_id}`
- `PUT /api/sources/{source_id}`
- `DELETE /api/sources/{source_id}`
- `GET /api/sources/{source_id}/status`
- `POST /api/sources/{source_id}/retry`
- `GET /api/sources/{source_id}/insights`
- `POST /api/sources/{source_id}/insights`
- `HEAD/GET /api/sources/{source_id}/download` — check/download stored file

### Embeddings

- `POST /api/embeddings/rebuild` — start rebuild
- `GET /api/embeddings/rebuild/{command_id}/status` — rebuild status

### Notes

- `GET /api/notes`
- `POST /api/notes`
- `GET /api/notes/{note_id}`
- `PUT /api/notes/{note_id}`
- `DELETE /api/notes/{note_id}`

### Models / Transformations / Chat (advanced)

- Models: `GET/POST /api/models`, plus defaults/sync/discover/test endpoints
- Transformations: `GET/POST /api/transformations`, execute endpoint, default-prompt endpoints
- Chat: `GET/POST /api/chat/sessions`, `POST /api/chat/execute`, `POST /api/chat/context`
- Source chat: `/api/sources/{source_id}/chat/...`

## Working recipes

### Create a notebook, add a URL source, then ask a question

1) Create notebook:

```bash
curl -sS -X POST http://127.0.0.1:5055/api/notebooks \
  -H 'Content-Type: application/json' \
  -d '{"title":"My notebook"}' | cat
```

2) Create a source from JSON (example fields vary — confirm via `/openapi.json`):

```bash
curl -sS -X POST http://127.0.0.1:5055/api/sources/json \
  -H 'Content-Type: application/json' \
  -d '{"title":"Example","source_type":"url","url":"https://example.com"}' | cat
```

3) Attach source to notebook:

```bash
curl -sS -X POST \
  http://127.0.0.1:5055/api/notebooks/<notebook_id>/sources/<source_id> | cat
```

4) Ask:

```bash
curl -sS -X POST http://127.0.0.1:5055/api/search/ask/simple \
  -H 'Content-Type: application/json' \
  -d '{"question":"Summarize the key points"}' | cat
```

Replace payload fields to match your installation’s schema.

## Safety / operational notes

- Keep requests local (`127.0.0.1`). Don’t expose tokens/credentials in chat logs.
- If you need exact request/response schemas, always consult `/openapi.json`.

## Use

Describe what the skill does and when to use it.

## Inputs

- Describe required inputs.

## Outputs

- Describe outputs and formats.

## Failure modes

- List hard blockers and expected exact error strings when applicable.

## Toolset

- `read`
- `write`
- `edit`
- `exec`

## Acceptance tests

1. **Behavioral: happy path**
   - Run: `/open-notebook-local <example-input>`
   - Expected: produces the documented output shape.

2. **Negative case: invalid input**
   - Run: `/open-notebook-local <bad-input>`
   - Expected: returns the exact documented error string and stops.

3. **Structural validator**
```bash
/opt/anaconda3/bin/python3 /Users/igorsilva/clawd/skills/skillmd-builder-agent/scripts/validate_skillmd.py \
  ~/clawd/skills/open-notebook-local/SKILL.md
```
Expected: `PASS`.
