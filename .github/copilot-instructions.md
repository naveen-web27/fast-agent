# RightConnect project context

- This repo is RightConnect: FastAPI + async SQLAlchemy/PostgreSQL backend, and a static vanilla-JS frontend in `frontend/`.
- Before changing a feature, check its local owner: `backend/app/features/<feature>/`, then the corresponding page or `frontend/assets/workspace.js`.
- Deployment setup, environment variables, regions, auth providers, and release checks: [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md). Product behavior/status: [PRODUCT.md](../PRODUCT.md) and [docs/features/](../docs/features/).
- Python is pinned to 3.12.8. Local backend commands are in [backend/README.md](../backend/README.md). Syntax-check touched Python with `python3 -m py_compile`; JavaScript in HTML can be parsed with JavaScriptCore (`osascript -l JavaScript`).
- Database bootstrap for a fresh Supabase project: run `db/schema.sql` once; it includes current schema and RLS. Do not run `db/seed.sql` in production. For an existing database, apply only migrations newer than its current schema, dev first then prod. Every ORM column change needs a migration before deployment.
- `DB_STATEMENT_CACHE=true` is valid only with Supabase session pooling (port 5432) or a direct connection; leave it false for transaction pooling (port 6543).
- Dev and production are separate Render/Supabase environments. Never copy production secrets into files or messages. Check the active service's `/api/v1/auth/provider-config` and Render/Supabase regions before diagnosing deployment or latency.
- Keep changes focused and preserve the single-file frontend conventions. Do not commit or push unless the user requests it; never expose tokens or credentials in logs or summaries.