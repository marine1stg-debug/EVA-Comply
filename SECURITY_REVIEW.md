# EVA Comply — OWASP Top 10 (2021) Security Review

> **Follow-up status (2026-06-23, v1.3.0): 6 findings RESOLVED, 3 PARTIALLY resolved, 0 unresolved; no new High.**
> Resolved: backup-restore lockdown (A08), secrets encrypted at rest (A02), viewer RBAC + MSP role-tiering (A01), `/docs`+CORS prod hardening (A05), password policy ≥12 (A04), secrets removed from logs (A09).
> Partially resolved (residual Medium): SSRF DNS-rebinding TOCTOU (A10), rate-limit X-Forwarded-For spoofing (A04), inline-served SVG stored XSS on S3/R2 (A08).
> Still-open Low: security headers (HSTS/CSP), refresh-token revocation, `/request-verification` user-enumeration, python-jose → PyJWT.
> Full follow-up write-up: **EVA_Comply_Audit_Suivi_v2.docx**. The findings below are the original (pre-fix) report, retained for traceability.

---

**Date:** 2026-06-23
**Scope:** Source code (`backend/app/**`) + deployment config (`docker-compose.yml`, `nginx/`, `caddy/`, Dockerfiles)
**Method:** Static code + configuration audit, evidence-based (file:line + code quotes). This is a white-box code review, **not** a live exploit/network pentest. For CMMC certification you will still need an accredited third-party penetration test against the running environment.

---

## Executive summary

The application's **multi-tenant isolation model is fundamentally sound** — no cross-tenant data-exfiltration IDOR was found. Auth (JWT type checks, MFA-pending token handling, lockout), SQL safety (ORM throughout), dependency hygiene (CVE-tracked pins), and backup credential-stripping are all done well.

The issues that matter most are **insider/privileged-account abuse surfaces and missing perimeter controls**: a server-side SSRF primitive in the LLM connector, an over-powerful backup restore, plaintext secrets at rest, and no rate limiting on auth endpoints.

**Risk counts:** High ×5 · Medium ×9 · Low ×6 · Good/Info ×many

---

## Top fixes (prioritized)

1. **[High] Validate the LLM `base_url` (SSRF)** — block private/loopback/link-local hosts; enforce scheme/host allowlist.
2. **[High] Lock down backup restore** — whitelist mutable columns; never accept `role`/`is_active`/`subscription_status`/`tenant_id` from an uploaded bundle; sign bundles; audit every restore.
3. **[High] Encrypt `api_key` and `mfa_secret` at rest** — plaintext today.
4. **[High] Rate-limit auth endpoints** — login/refresh/register/verify/mfa are unthrottled.
5. **[Medium] Enforce role on client write endpoints** — exclude `viewer` from evidence/control/self-assessment mutations.
6. **[Medium] Disable `/docs` & `/openapi.json` and tighten CORS in production.**
7. **[Medium] Validate upload content** — magic-byte + extension allowlist; stop trusting client `content_type`.
8. **[Medium] Strengthen password policy + broaden MFA enforcement** to all admin-capable roles (incl. `client_admin`).
9. **[Medium] Stop logging verification codes / unlock tokens to stdout.**
10. **[Medium] Fix MSP cross-tier role assignment; audit-log destructive framework deletion.**

---

## A01 — Broken Access Control / IDOR / Multi-Tenant Isolation

The tenant boundary is `resolve_org()` (`backend/app/core/client_context.py:38-51`): client roles always resolve to their own `tenant_id` and ignore `X-Client-Id`; reviewers resolve `X-Client-Id` only through `_in_scope()` (`:27-35`). The header **cannot** reach another tenant. Across `controls.py`, `evidence.py`, `recommendations.py`, `maturity.py`, `review.py`, `billing.py`, tenant-owned queries are filtered by the resolved `org_id`, with `org_id is None` rejected (HTTP 400). User-management escalation is blocked via `INVITABLE_ROLES` allowlists. **No cross-tenant IDOR found.** Residual issues:

- **[Medium] Client `viewer` can perform writes/deletes** — `evidence.py:31` `CLIENT_ROLES` includes `viewer`; upload/submit/delete (`:159, :238, :256`) and controls writes (`controls.py:656, 745, 769, 795, 847, 1199`) gate on org scope only, not role. *Fix:* restrict writes to `{client_admin, contributor}`.
- **[Medium] Resource-id confusion (intra-tenant)** — `controls.py` validates `control_id`, `ee_id`, `evidence_id` independently; `_load_ee` (`:730`) / `collect_expected_evidence` (`:847`) don't cross-check that the expected-evidence belongs to the path control. Same-tenant only. *Fix:* add `ExpectedEvidence.control_id == control.id`.
- **[Medium] MSP cross-tier role assignment** — `users.py:208-216` validates assignable roles against the caller's role only, not the target tenant's type; an `msp_admin` could set a client user to `msp_analyst`. *Fix:* validate against the target tenant type.
- **[Medium] Caller-controlled billing amount + missing audit on destructive op** — `tenants.py:487,496` writes caller-supplied `amount` to `monthly_price`; `DELETE /{tenant_id}/frameworks/{framework_id}` (`:501-534`) hard-deletes evidence/controls with **no audit record**. Correctly scoped, but flag.
- **[Low] Unscoped follow-up query** — `controls.py:1011-1015` selects `ExpectedEvidence` by id with no `org_id` filter (safe because prior row is scoped). *Fix:* add `org_id` filter for defense-in-depth.

**Good:** backup, `llm_settings`, and `policy` mutations are hard-gated to `super_admin`; `review.py` decisions bind to the reviewer's stage; PATCH bodies use explicit Pydantic schemas (no mass assignment of `org_id`/`role`/price).

## A02 — Cryptographic Failures

- **[Good]** Passwords: bcrypt via passlib — `security.py:10`.
- **[High] Secrets plaintext at rest in DB** — LLM `api_key` (`models/llm_settings.py:30`) and TOTP `mfa_secret` (`models/user.py:33`) are unencrypted. DB/backup access = LLM key + ability to recompute every user's TOTP. *Fix:* encrypt at rest (Fernet/KMS-wrapped column).
- **[Info]** JWT HS256; production guard refuses dev/short secret (`config.py:61-74`). TLS via Caddy + Let's Encrypt (`caddy/Caddyfile:14-18`).

## A03 — Injection

- **[Good]** No SQLi — ORM with bound params throughout. Only `text()` is in a maintenance script (`cleanup_stale_catalogs.py:51,65`) using static constants, not API-reachable.
- **[Good]** No command injection / deserialization (`os.system`/`subprocess`/`eval`/`exec`/`pickle`/`yaml.load` absent).
- **[Good]** No template injection — `reports_gen.py` escapes via `_esc()`; `billing.py` via `html.escape`; docx via python-docx runs.

## A04 — Insecure Design

- **[High] No rate limiting anywhere** — no limiter/middleware; `/auth/login`, `/refresh`, `/register`, `/request-verification`, `/mfa/verify` unthrottled (and nginx exempts `/api/`). Lockout (3/15min) stops single-account brute force but not credential stuffing or MFA-code brute force. *Fix:* per-IP limits (slowapi or nginx `limit_req`).
- **[Medium] Weak password policy** — only `len >= 6` (`auth.py:487-488, 537-538`). *Fix:* ≥12 + breached-password check.
- **[Medium] Narrow/bypassable MFA** — `MFA_REQUIRED_ROLES` (`auth.py:31`) excludes `client_admin`; even required roles are only challenged `if user.mfa_enabled`. *Fix:* force MFA enrollment for all admin-capable roles.
- **[Good]** Updates use explicit field handling (no mass assignment). Signup gated by arithmetic CAPTCHA + email verification.

## A05 — Security Misconfiguration

- **[Medium] `/docs` & `/openapi.json` exposed** (`main.py:19-24`, proxied `nginx.conf.template:51-56`) — behind basic-auth but full schema reachable by any gate holder. *Fix:* `docs_url=None, openapi_url=None` in prod.
- **[Medium] Permissive CORS** — `allow_credentials=True` with `allow_methods=["*"]`, `allow_headers=["*"]` (`main.py:27-37`). Origins fixed today; tighten methods/headers.
- **[Low] SQL echo** tied to `ENVIRONMENT == "development"` (`database.py:8`) — off in prod.
- **[Info/Good]** `.env` empty + gitignored; `server_tokens off`; `X-Robots-Tag noindex`; prod guard blocks dev secrets/console email. No HSTS/CSP/X-Frame-Options headers — *consider adding at Caddy/nginx.*

## A06 — Vulnerable & Outdated Components

- **[Good]** `requirements.txt` is CVE-maintained with rationale: `fastapi==0.136.1` + `starlette>=0.49.1`, `python-jose>=3.4.0`, `python-multipart>=0.0.18`, `h11>=0.16`, `requests>=2.32.4`, `pillow>=11.3.0`. No stale/known-vulnerable pins. **Low note:** consider migrating `python-jose` → `PyJWT` (more actively maintained); alg-confusion already mitigated by pinned `algorithms`.

## A07 — Identification & Authentication Failures

- **[Good]** No alg confusion / exp bypass — `decode_token` pins `algorithms=[settings.ALGORITHM]` (`security.py:100-101`); `get_current_user` rejects non-`access` tokens and the `mfa_pending` temp token (`auth.py:91-92`).
- **[Good]** `/refresh` validates `type == "refresh"` + re-checks `is_active` (`auth.py:216-232`). **Low:** stateless JWTs — a stolen refresh token is valid 30 days; consider revocation list + invalidation on password change.
- **[Low] Login user-enumeration** — locked/known vs unknown email take different paths/responses (`auth.py:148-168`); `/request-unlock` is generic but login isn't. *Fix:* uniform timing/response.

## A08 — Software & Data Integrity

- **[Good]** Restore strips `SENSITIVE_COLUMNS = {password_hash, mfa_secret}` on export **and** import (`backup_io.py:97-103, 182-186`); restored users get `"!locked!"` hash (`:190-193`). Cannot inject passwords/MFA.
- **[High] Restore can tamper with any tenant + escalate roles** — `import_bundle` upserts by PK across all tables incl. `users`/`tenants`, copying every non-sensitive column **including `role`, `tenant_id`, `is_active`, `subscription_status`, billing** (`backup_io.py:179-200`). A super_admin uploading a crafted bundle (`backup.py:273`) can flip any user to `super_admin` or rewrite another tenant's data. Insider/compromised-account risk. *Fix:* whitelist mutable columns; reject `role`/`is_active`/`subscription_status`/`tenant_id`; sign bundles; audit every restore with row-level diff.
- **[Medium] No content/type validation on uploads** — evidence (`evidence.py:188-228`), policy `.docx` (`policy.py:191,230`), support (`support.py:148-150`), video (`videos.py:158-164`) validate size only; `python-magic` installed but unused; client `content_type` trusted. *Fix:* magic-byte + extension allowlist.
- **[Low] Path traversal — mostly mitigated** — keys built with `os.path.basename` + uuid prefix (`evidence.py:209`) or sanitized slug (`policy_library.py:16`). `storage.save_bytes` does raw `os.path.join` (`storage.py:45,57`) relying on callers; tighten `safe_name` regex (Windows `..\`).

## A09 — Logging & Monitoring

- **[Good]** Append-only `AuditLog` (`core/audit.py`); logs `auth.login` (`auth.py:182`) and `auth.account_locked` (`:163`); no passwords/tokens in audit log.
- **[Medium] Sensitive data printed to stdout** — `auth.py:319` prints verification codes; `:138` prints unlock token/link; dev SQL echo logs values. Container-log credential leak. *Fix:* remove or strictly guard to non-prod.
- **[Low] Coverage gaps** — no audit rows for backup restore, framework deletion (`tenants.py:501`), role changes, MFA-verify failures, refresh use. *Fix:* add events + alerting.

## A10 — SSRF

- **[High] LLM connector is an SSRF primitive** — `llm.py:85-92` `_resolve_base` uses `s.base_url` verbatim; `chat()` (`:154-155`) posts to it. Set via `PUT /api/v1/llm/settings` (`llm_settings.py:46-67`) with **no scheme/host validation** — can target `http://169.254.169.254/...`, `localhost`, internal services; response snippet surfaced via `test_connection` (`:188`); configured API key/header forwarded to the target. (`ollama` default is `http://localhost:11434`, so internal targets are expected.) Super-admin-gated but meaningful. *Fix:* enforce `https` scheme (http only for allowlisted hosts), block RFC1918/link-local/loopback, consider egress allowlist.
- **[Low] Open redirect (not SSRF)** — `billing.py:149-151,223-224` passes request `success_url`/`cancel_url` to Stripe (browser redirect, not server-fetched). *Fix:* allowlist against `FRONTEND_URL`.
- **[Good]** Stripe webhook signature verified via `construct_event` against raw body (`billing.py:271-282`); rejects when unconfigured.

---

*Generated by code review on 2026-06-23. Remediation items can be tracked individually — happy to implement the High-severity fixes on request.*
