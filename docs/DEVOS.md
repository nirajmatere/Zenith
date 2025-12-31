# DEVOS: How we build Zenith (AI-first, production-safe)

Every implementation (human or AI) must follow this file.

## Principles
1. **Multi-tenant by design**: every row belongs to an `organization_id` (where applicable).
2. **Permission-based RBAC**: avoid `if role == ...`. Prefer `can(user, action, resource)`.
3. **Small PRs**: ship in increments with tests + docs.
4. **No silent failure**: log, surface, retry, or degrade gracefully.
5. **AI must be measurable**: record latency, cost estimate, input type, and outcome for each AI call.

## Definition of Done (DoD)
- ✅ Unit tests added/updated
- ✅ Lint + type checks pass (`ruff`, `mypy`, `eslint`)
- ✅ Alembic migration included if schema changed
- ✅ API documented (OpenAPI + short docs)
- ✅ No secrets committed
- ✅ AI features: caching + retry + fallback documented

## Required outputs for every feature
1) Plan (1–2 screens)
2) Change list (files/modules)
3) Implementation
4) Tests
5) Docs update
6) How to verify (commands + expected result)

## Security baseline
- Password hashing: Argon2
- Rate limit auth + AI endpoints
- Audit logs for admin/teacher actions
