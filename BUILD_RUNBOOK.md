# EVA Cybersecurity Audit Portal — Build & Operations Runbook

Version 1.0 · Multi-tenant SaaS compliance platform (FastAPI · React · PostgreSQL)

This runbook covers how to build, configure, run, and operate the application,
plus a production-hardening checklist. It is written for a developer or ops
engineer working from the `eva-portal/` project directory.

---

## 1. System overview

The platform is a Docker Compose application made of six services:

| Service | Image / build | Purpose | Port |
|---|---|---|---|
| `db` | postgres:16-alpine | Primary database | 5432 |
| `redis` | redis:7-alpine | Cache + Celery broker/result backend | 6379 |
| `api` | build `./backend` (Python 3.12 / FastAPI) | REST API, migrations, seed | 8000 |
| `worker` | build `./backend` | Celery worker (reports, async tasks) | — |
| `frontend` | build `./frontend` (Node 20 / Vite) | React dev server | 3000 |
| `nginx` | nginx:alpine | Reverse proxy (frontend + `/api`, `/docs`) | 80 |

Request path in dev: browser → Vite (`:3000`) which proxies `/api` → `api:8000`.
Via nginx (`:80`), `/api/`, `/docs`, `/openapi.json` route to the API and
everything else to the frontend.

---

## 2. Prerequisites

- **Docker Desktop** (or Docker Engine) with the Compose plugin.
- ~2 GB free RAM and disk for images/volumes.
- No language toolchains needed on the host — everything builds in containers.
- Optional, for live Stripe testing: a free Stripe **test-mode** account and the
  Stripe CLI.

---

## 3. Quick start

From the project root (`eva-portal/`):

```bash
# Build and start everything (first run pulls images + builds)
docker compose up --build
```

Then open:

- **Frontend / app:** http://localhost:3000  (public site: `/welcome`)
- **Via nginx:** http://localhost
- **API docs (Swagger):** http://localhost:8000/docs

To stop: `Ctrl+C`, then `docker compose down` (keeps data) or
`docker compose down -v` (wipes the database + uploads).

### Clean rebuild + reseed

The seed only runs on an empty database. After schema/seed changes, do a clean
rebuild so migrations and the seed re-run:

```bash
docker compose down -v && docker compose up --build
```

---

## 4. Configuration (environment variables)

Set on the `api` (and where relevant `worker`) service in `docker-compose.yml`.
Dev defaults are shown; **bold** items must change for production.

| Variable | Dev value | Notes / production |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://eva_user:eva_secret_change_in_prod@db:5432/eva_db` | **Rotate the DB password**; point to managed Postgres. |
| `REDIS_URL` | `redis://redis:6379` | Use an auth'd/managed Redis in prod. |
| `SECRET_KEY` | `dev_secret_key_change_in_production_min_32_chars` | **Rotate** — JWT signing key; ≥32 chars, kept secret. |
| `ALGORITHM` | `HS256` | JWT algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access-token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh-token lifetime. |
| `ENVIRONMENT` | `development` | Set to `production`; also disables dev-only behaviors (e.g. returning verification/invite codes in API responses). |
| `STORAGE_BACKEND` | `local` | `local` writes to the uploads volume; switch to `s3`/`r2` in prod. |
| `STORAGE_LOCAL_PATH` | `/app/uploads` | Mount-backed evidence storage. |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET_NAME` | empty / `eva-uploads` | Cloudflare R2 / S3 credentials when not using local storage. |
| `STRIPE_SECRET_KEY` | empty | Stripe API key. Empty = checkout is **simulated**. |
| `STRIPE_WEBHOOK_SECRET` | empty | Stripe webhook signing secret. |
| `EMAIL_BACKEND` | `console` | `console` = no real mail; dev surfaces verification/invite codes/links in the UI/logs. Switch to a real provider in prod. |
| `FROM_EMAIL` | `noreply@eva-technologies.com` | Sender address. |

> Secrets are currently inlined in `docker-compose.yml` for dev convenience.
> For production, move them to an `.env` file or a secrets manager and never
> commit real values.

---

## 5. Database: migrations & seed

Migrations are Alembic, applied automatically on `api` startup
(`alembic upgrade head`). Current chain:

| Revision | Adds |
|---|---|
| `001_initial` | tenants, users, frameworks, controls, org_controls, evidence_items |
| `002_billing_plans` | `billing_plans` table + `tenants.plan_id` |
| `003_platform_settings` | `platform_settings` (billing mode + trial length) |

The **seed** (`python -m app.seed`) runs after migrations and is **idempotent**
— it checks for the super-admin user and skips if already seeded. It creates:
EVA internal tenant, Acme MSP, NovLogix client; the seven demo users; the three
frameworks with CMMC controls; org-control posture + placeholder evidence files;
the two default billing plans; and the default platform settings (no-card trial,
14 days).

To force a reseed, wipe the volume: `docker compose down -v`.

---

## 6. Startup sequence (api container)

The `api` command runs, in order:

1. Wait for Postgres to accept connections.
2. `alembic upgrade head` — apply migrations.
3. `python -m app.seed` — seed if empty.
4. `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.

The backend code is bind-mounted (`./backend:/app`) and runs with `--reload`,
so Python changes hot-reload without a rebuild. `requirements.txt` changes
**do** require `--build`.

---

## 7. API surface

All routes are under `/api/v1`. Router groups:

`auth`, `dashboard`, `frameworks`, `controls`, `evidence`, `review`, `msp`,
`tenants`, `users`, `plans`, `platform`, `billing`, `reports`, `audit`.

Interactive docs at `/docs`; raw schema at `/openapi.json`. Most endpoints
require a Bearer JWT; the public ones are `auth/signup-options`,
`auth/request-verification`, `auth/register`, `auth/invite-info`,
`auth/accept-invite`, and the Stripe `billing/webhook`.

---

## 8. Frontend

Built by Vite in the `frontend` container (`npm install` at image build,
`npm run dev` at runtime, bind-mounted with HMR). The Vite dev server proxies
`/api` to the API. `package.json` changes require `--build`.

Production build (outside compose): `npm run build` produces static assets to
serve from a CDN/nginx; point `VITE_API_URL` / proxy at the API origin.

---

## 9. Storage & evidence files

With `STORAGE_BACKEND=local`, uploaded evidence is written under
`STORAGE_LOCAL_PATH` (`/app/uploads`), backed by the `uploads_data` volume, so
files persist across restarts (until `down -v`). For production, set
`STORAGE_BACKEND=s3`/`r2` and supply credentials; presigned URLs keep large
uploads off the API host.

---

## 10. Stripe (test mode)

Checkout/webhooks are wired but inert until keys are set. To enable test mode:

1. Create a free Stripe account; stay in **Test mode**.
2. Copy the **Secret key** (`sk_test_…`).
3. Forward webhooks locally and copy the printed signing secret (`whsec_…`):
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/billing/webhook
   ```
4. Set on the `api` service:
   ```yaml
   STRIPE_SECRET_KEY: sk_test_xxx
   STRIPE_WEBHOOK_SECRET: whsec_xxx
   ```
5. Rebuild. Test card `4242 4242 4242 4242`, any future expiry/CVC.

The platform billing mode (Plans & Pricing → Billing & Trials) governs whether
signup uses no-card trial, a card-required Stripe trial, or charge-immediately.

---

## 11. Email

`EMAIL_BACKEND=console` means no real mail is sent; verification codes and
invite links are surfaced in the UI (dev) and printed to the `api` logs. For
production, wire SendGrid/SES (keys are stubbed in config) and set
`EMAIL_BACKEND` accordingly so codes/invites are emailed instead.

---

## 12. Operations

```bash
docker compose ps                 # service health
docker compose logs -f api        # follow API logs (also: frontend, db, worker)
docker compose restart api        # restart one service
docker compose down               # stop, keep data
docker compose down -v            # stop, wipe db + uploads (forces reseed)
docker compose exec db psql -U eva_user -d eva_db   # psql shell
```

**Backups (prod):** `pg_dump` the database and snapshot the uploads
bucket/volume on a schedule.

---

## 13. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `passlib`/`bcrypt` error on boot | bcrypt 4.1+ incompatible with passlib 1.7.4 | Pinned `bcrypt==4.0.1` in `requirements.txt`. |
| API crashes importing `EmailStr` | `email-validator` missing | Added `email-validator` to `requirements.txt`. |
| "Failed to load…" on most pages | 15-minute access token expired (no refresh yet) | Sign out and back in; consider longer dev token / auto-logout on 401. |
| `no configuration file provided` | Running compose above `eva-portal/` | `cd eva-portal` first (the compose file lives there). |
| Plans page empty after upgrade | Migrated but not reseeded | `docker compose down -v && up --build`. |
| Stripe button does nothing real | No Stripe keys | Add `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` (Section 10). |
| Container won't start | Stale build after dependency change | `docker compose build --no-cache <svc>`. |

---

## 14. Production hardening checklist

- [ ] Rotate `SECRET_KEY` and the Postgres password; move all secrets out of compose into env/secret store.
- [ ] Set `ENVIRONMENT=production` (disables dev code/link disclosure).
- [ ] Restrict CORS `allow_origins` to your real domains (currently localhost).
- [ ] Put the API behind TLS; serve the frontend as a static build via CDN/nginx.
- [ ] Switch storage to S3/R2 with server-side encryption.
- [ ] Wire a real email provider; verify deliverability.
- [ ] Configure live Stripe keys + a hosted webhook endpoint.
- [ ] Add rate limiting on auth and upload endpoints; enable file-type/AV scanning.
- [ ] Disable SQL `echo`, set sensible Postgres pool sizes, run multiple API workers.
- [ ] Add healthchecks, metrics/log aggregation, and database backups.
- [ ] Review the trial/lock and entitlement enforcement against your commercial terms.

---

## 15. Demo accounts

All use password `demo1234`:

| Email | Role |
|---|---|
| superadmin@eva.com | Super Admin |
| auditor@eva.com | EVA Auditor |
| msp@acmemsp.com | MSP Admin |
| analyst@acmemsp.com | MSP Analyst |
| admin@novlogix.com | Client Admin |
| it@novlogix.com | Contributor |
| coo@novlogix.com | Viewer |

---

## 16. Fix log — duplicate OrgControl crash (control detail 500)

**Symptom:** opening some controls (e.g. ITSP `03.01.01`) for a client returned
"failed to load control"; the API logged `sqlalchemy.exc.MultipleResultsFound`
from `controls.py` `control_detail` / `_get_or_create_oc` and `evidence.py`.

**Cause:** a client (org) had more than one `org_controls` row for the same
control — a double provisioning of a framework. The lookups used
`.scalar_one_or_none()`, which raises when >1 row matches.

**Fix:**
- Made all three `(org_id, control_id)` lookups tolerant: order by `created_at`
  ascending and take `.scalars().first()` (canonical = earliest row).
  Files: `app/api/controls.py` (control_detail, `_get_or_create_oc`),
  `app/api/evidence.py` (upload path).
- Added `app/dedupe_orgcontrols.py` to merge existing duplicates: keeps the
  earliest row, repoints `evidence_items.org_control_id`, deletes the extras.
  Run: `docker compose exec api python -m app.dedupe_orgcontrols` (dry run),
  then `--yes` to commit.

---

## 17. Phase 35 — Evidence-centric review + editable audit status

**Model shift:** review now happens on uploaded **evidence items** (Evidence tab),
not on the expected-evidence requirement. Expected evidence is a suggestion
checklist; it still drives coverage (= expected items with an accepted evidence /
total).

**Backend**
- Migration `010_audit_status.py` (additive): `org_controls.audit_status`,
  `status_mode` (auto|manual), `status_note`, `previous_audit_notes`. Legacy
  `status` enum is left intact and mirrored from a manual audit status, so
  dashboard/MSP/report rollups are unchanged.
- `ControlStatus` vocab: Compliant / Non-Compliant / In Progress / Not Applicable.
- Auto rule (status_mode='auto'): all expected satisfied (accepted linked
  evidence) **and** none flagged → Compliant, else In Progress. Manual override
  pins a status + comment until reverted to auto.
- New endpoints in `controls.py`:
  - `POST /controls/{cid}/evidence/{eid}/review` {decision: accept|return, note}
    — Approve/Flag a single item (comment required on flag); logs a ControlEvent,
    recomputes coverage + auto status.
  - `PATCH /controls/{cid}/status` {mode, status?, note?} — manual set / revert to auto.
  - `PATCH /controls/{cid}/notes` {previous_audit_notes} — reviewer-only.
  - control_detail now returns audit_status(+label/badge), status_mode, status_note,
    previous_audit_notes, audit_status_options, can_review; evidence items carry
    review_state / review_note / file info.

**Frontend (Controls.tsx)**
- Evidence tab: inline Approve / Flag-issue + comment per item (matches SOC2
  screenshot), left-border colour by review state, accepted/returned note shown.
- Header: editable Status (badge + auto/manual + comment via StatusEditor).
- Overview: reviewer-editable Previous Audit Notes (client read-only).
- Expected tab: accept/return removed → suggestion checklist (collect + state only).

**Apply:** `docker compose restart api` (re-runs `alembic upgrade head` → 010).

---

## 18. Phase 36 — Maturity (per-framework, per-domain)

A client-scoped **Maturity** page showing a 0–5 maturity assessment per
framework domain (radar + domain table), modelled on the SOC2-style dashboard.

**Model / decisions**
- Domain-level rating (one 0–5 per domain), generic 0–5 scale with Current /
  Target / Previous series. Hybrid scoring: **Current auto-seeds from each
  domain's compliance** (% of controls Compliant → 0–5) and is overridable by
  reviewers. Target defaults to 4 until set. Risk score = Σ(gap×risk-weight) /
  Σ(max-gap×risk-weight) × 100.

**Backend**
- `app/models/maturity.py`: `MaturityAssessment` (org, framework, domain,
  current_level, target_level, note; unique per org+fw+domain) and
  `MaturitySnapshot` (dated payload of per-domain levels → the Previous series).
- Migration `011_maturity.py`.
- `app/api/maturity.py` (`/api/v1/maturity`): GET `/frameworks` (client's
  subscribed frameworks), GET `/{fw}` (domains + overall current/target/previous
  + risk score), PATCH `/{fw}/domain` (override current/target/note),
  POST `/{fw}/snapshot` (freeze current as Previous baseline). Registered in main.

**Frontend**
- `pages/Maturity.tsx`: framework selector, recharts Radar (Current/Target/
  Previous), domain table (current select, star rating, target select, risk),
  Overall Perceived Maturity + Target + Risk score cards, Save-snapshot.
  Reviewers edit; clients read-only; reviewers must pick a client first.
- Route `/maturity` + sidebar entry under Compliance.

**Apply:** `docker compose restart api` (runs migration 011). Frontend hot-reloads.

---

## 19. Phase 37 — Show full framework + safe control sync

**Visibility fix:** the Controls list (and Maturity domain math) now shows every
control of the frameworks a client is *subscribed to* — subscription derived
from the frameworks the client has any org-control in — instead of only the
controls already provisioned. Controls without a row show as Not started; a row
is created lazily when opened or when evidence is added. (`controls.py`
list_controls, `maturity.py` _build left-join.)

**Re-provision / Sync (additive, non-destructive):**
- `POST /tenants/{id}/frameworks/sync` re-runs `assign_frameworks` for the
  client's assigned frameworks (existing rows ∪ billed ones), creating only the
  MISSING org-control rows. It never deletes org-controls, evidence, or
  expected-evidence — `assign_frameworks` skips controls that already have a row.
- Tenants → Frameworks modal: "↺ Sync controls" button + per-framework
  "N not yet provisioned" hint. Assigned list now shows the framework's full
  control count (with provisioned count separately).
- CLI: `docker compose exec api python -m app.sync_orgcontrols` (dry-run diag),
  `--yes` to provision. Additive only.

---

## 20. Phase 38 — Maturity self-assessment (Perceived ring)

Clients self-rate maturity per control against a generated 5-rung ladder; that
rolls into a **Perceived** ring on the Maturity radar, beside the evidence/
auditor **Assessed** ring. Designed forward-compatible for bespoke questions,
an XLS override column, and a future LLM `ai_suggested` source.

**Backend**
- `maturity_self_assessments` table (org, control, answers JSON {question_key:
  level}, comment) + migration 012.
- `app/core/maturity_questions.py`: 5-rung ladder (None→Optimized) + a
  deterministic per-control question generator (`generate_questions`) and
  `perceived_level` (mean of answers). v1 = one 'default' question/control.
- controls.py: `GET/PUT /controls/{cid}/self-assessment` (questions + answers +
  Comments/Additional-info, org-scoped, client + reviewers).
- maturity.py `_build`: per-domain **Perceived** (mean of answered controls) +
  `overall_perceived`; existing value relabelled **Assessed**.

**Frontend**
- Control detail: new **Self-assessment** tab — ladder radio options + a single
  "Comments / Additional info" box + Save; shows perceived level in the tab label.
- Maturity page: Perceived radar ring + table column, "Overall Perceived
  Maturity" card (self-assessment) alongside "Assessed".

**Apply:** `docker compose restart api` (migration 012). Frontend hot-reloads.

**Roadmap (not yet built):** bespoke multi-question sets per control + XLS
`maturity_questions` override column; per-question evidence attach; LLM evidence
review emitting an `ai_suggested` maturity + rationale (third ring).

---

## 21. Phase 39 — Control-specific self-assessment questions (override)

Controls can carry bespoke, control-specific maturity questions that override
the generic ladder; controls without one keep the generic question.

- `controls.maturity_questions` JSON column + migration 013.
- `generate_questions(control)` returns the authored set when present, else the
  generic ladder. No frontend change — the Self-assessment tab renders whatever
  the API returns.
- `app/seed_maturity_questions.py`: SAMPLE batch of 5 expert-authored NIST
  800-171r3 controls (03.01.01 Account Management, 03.03.01 Event Logging,
  03.05.03 MFA, 03.06.01 Incident Handling, 03.14.01 Flaw Remediation), one per
  family, for quality sign-off before authoring the full catalog. Idempotent,
  only sets the column.

**Apply:** `docker compose restart api` (migration 013), then
`docker compose exec api python -m app.seed_maturity_questions --yes`.

**Next:** on sign-off, author the rest of NIST 800-171r3, then ITSP / SOC 2.
Later: XLS `maturity_questions` import column + LLM-generated drafts.

---

## 22. Phase 39b — Full NIST 800-171r3 self-assessment bank

`app/maturity_banks.py` (`NIST_171R3`): expert-authored, control-specific
5-rung ladder questions for all 97 NIST 800-171r3 controls (every family;
03.14.09 omitted → generic). `seed_maturity_questions.py` now builds its
question map from this bank. Controls with an entry override the generic
generated ladder; everything else keeps the generic question.

**Apply:** `docker compose restart api` (migration 013, if not already), then
`docker compose exec api python -m app.seed_maturity_questions --yes`
(dry-run without --yes lists every matched control).

**Next frameworks:** ITSP.10.171 and SOC 2 banks follow the same pattern.

---

## 23. Phase 39c — ITSP.10.171 self-assessment (ref reuse) + coverage report

ITSP.10.171 (CPCSC) reuses NIST 800-171's 03.xx.xx control IDs, so the authored
NIST_171R3 bank applies to ITSP automatically — the seeder matches by ref across
all frameworks. `seed_maturity_questions.py` now reports coverage per framework
and lists any controls still on the generic ladder (surfaces ITSP-only extras
such as 03.14.09 for later authoring).

**Apply / verify:** `docker compose exec api python -m app.seed_maturity_questions`
(dry run shows per-framework coverage), then `--yes`.

---

## 24. Phase 39d — CMMC L1/L2 self-assessment (mapped to the NIST bank)

CMMC 2.0 practice IDs embed the 800-171 (r2) number (e.g. CM.L2-3.4.1 → 3.4.1).
`seed_maturity_questions.py` maps each CMMC practice to the authored NIST (r3)
bank: direct-pad (3.1.1 → 03.01.01) plus a `CMMC_REDIRECT` table for the r2→r3
consolidations. Result: 126/127 CMMC L1+L2 practices get a control-specific
question reused from NIST; only MA.L2-3.7.1 falls to the generic ladder.

One seed run now covers NIST 800-171r3, ITSP.10.171 (shared refs), and CMMC
L1/L2 (mapped). No CMMC-specific authoring required.

**Apply:** `docker compose exec api python -m app.seed_maturity_questions --yes`
(dry-run first shows per-framework coverage).

---

## 25. Phase 40 — Perceived vs Assessed gap on Dashboard + Portfolio

The maturity gap now surfaces outside the Maturity page.

- maturity.py: `_overall(org)` aggregates Perceived / Assessed / Target / gap /
  risk across a client's subscribed frameworks. `GET /maturity/summary`
  (in-scope client) and `GET /maturity/portfolio` (MSP children / EVA
  single-clients, sorted by biggest over-rating gap).
- Dashboard: "Maturity: perceived vs assessed" card (Perceived/Assessed/Target
  bars + a gap badge), shown when the in-scope client has data; links to /maturity.
- Portfolio: "Maturity: Perceived vs Assessed" table per client (Perceived,
  Assessed, Target, Gap) with over-rating flagged.

Gap = self-assessed − auditor-assessed (0–5). Backend compiles; frontend hot-reloads.

---

## 26. Phase 41 — Private LLM connector (super-admin AI settings)

A platform-wide connection to a private or hosted LLM, used by AI-assisted
evidence review and one-click recommendation generation. Super-admin only.

- Model `llm_settings` (single row): provider (`openai` / `anthropic` /
  `ollama`), base_url, model, api_key (server-side only), enabled, timeout,
  optional custom auth header, and last-test result. Migration `014`.
- `app/core/llm.py`: provider-aware request building — OpenAI-compatible
  (`/chat/completions`), Anthropic Messages (`/v1/messages` + `anthropic-version`,
  system split out), Ollama (`/api/chat`, `stream:false`). Exposes `chat()`
  (reused by the recommendations engine) and `test_connection()` (one cheap
  round-trip, records ok/message/latency). `masked_settings()` returns a
  client-safe view — the raw key is NEVER serialized.
- `app/api/llm_settings.py` (`/api/v1/llm`): `GET /settings` (masked key +
  `has_key`), `PUT /settings` (key sentinel `__KEEP__` preserves stored key,
  `""` clears, any value replaces), `POST /test`. All gated to super_admin.
- Frontend `AiSettings.tsx` + route `/ai-settings` + Administration nav entry
  "AI Connector" (super-admin only). Provider dropdown, base URL, model,
  write-only API key (masked `••••1234` with Replace key), enable toggle,
  timeout, advanced custom header, and a Test-connection button (disabled while
  there are unsaved changes) with a "Last test" status card.

**Security:** API key entered by the user, stored server-side, masked in all
responses, never reachable by client tenants. **Apply:** migration runs on
`docker compose exec api alembic upgrade head` (or `restart api`).

---

## 27. Phase 42 — Recommendations engine (pre-made library + AI)

Turns maturity gaps into prioritized remediation actions. A control is
"gapped" when its current maturity (the client's self-assessment level, else a
status-derived proxy) sits below its target; each gap yields one or more
recommendations.

- Model `recommendations` (migration `015`): org_id, control_id, source
  (`premade` | `ai` | `manual`), title, text, effort/impact ∈ {low,medium,high},
  current_level/target_level snapshot, status (open/in_progress/done/dismissed).
- `app/recommendation_banks.py`: curated `NIST_171R3_RECS` keyed by control ref
  (effort + impact per item), reused for ITSP (shared refs) and CMMC (mapped via
  `r3_for_cmmc`). Controls with no authored entry fall back to a recommendation
  derived from the maturity ladder's target-level statement, so coverage is
  universal.
- `app/core/recommendations.py`: `gather_gaps()` (perceived from self-assessment
  via `perceived_level`, target from domain override or default 4),
  `premade_for_control()`, `ai_for_control()` (one LLM call → JSON
  {title,text,effort,impact}, uses the Phase 41 connector), plus `is_quick_win`
  (low effort + high impact) and `priority_score` (impact × gap × control risk,
  effort-weighted).
- `app/api/recommendations.py` (`/api/v1/recommendations`): `GET /` rollup
  (all + Top 10 + Quick Wins + counts + has_llm), `POST /generate`
  {source, overwrite} (regenerates that source, keeps manual),
  `GET /control/{id}`, `POST /control/{id}/generate`, `PATCH /{id}`
  (status/effort/impact/title/text), `DELETE /{id}`. Generation/edits restricted
  to reviewer roles; all client-scoped via `resolve_org`.
- Frontend: new **Recommendations** page (Compliance nav) with KPI tiles,
  **Top 10 priorities**, **Quick wins**, a filterable full list, per-item status
  dropdown + remove, and "Generate from library" / "Generate with AI" (AI button
  enabled only when the connector is on). New **Recommendations tab** in the
  control detail view with the same per-control generate + manage actions.
  Control refs deep-link back into `/controls?control=<id>`.

**Apply:** migration runs on `docker compose exec api alembic upgrade head`
(or `restart api`). The AI path requires the Phase 41 connector to be enabled.

---

## 28. Phase 43 — Expert review of self-assessment questions vs r3

Deep accuracy pass over all 97 authored self-assessment questions in
`maturity_banks.py` against the final NIST SP 800-171r3 control catalog. Three
corrected for scope/title fit:

- **03.13.08 (Transmission and Storage Confidentiality)** — r3 folded the
  withdrawn 3.13.16 ("CUI at rest") into this control. The question now covers
  encryption in transit **and at rest**, not transit only. A matching "Encrypt
  CUI at rest" pre-made recommendation was added.
- **03.10.08 (Access Control for Output Devices)** — rewritten to address
  controlling physical access to monitors/printers/scanners/copiers so
  unauthorized people cannot view or collect CUI output (was incorrectly about
  "transmission lines").
- **03.08.09 (Secure Backups)** — tightened to the r3 requirement: protecting
  the **confidentiality** of backup CUI via cryptography (was drifting into
  integrity / restore-testing).

The other 94 verified as correctly mapped. No em-dashes / bracket numbers.

**Apply:** push the corrected questions with
`docker compose exec api python -m app.seed_maturity_questions --yes`
(dry-run without `--yes` first). Idempotent; only updates `maturity_questions`.

### ITSP.10.171 + CMMC L1/L2 validation

- **ITSP.10.171** is r3-aligned and shares the `03.xx.xx` refs, so it inherits
  the same authored bank by ref — including the three corrections above. No
  separate authoring needed; the seed applies questions to every matching
  control across all frameworks.
- **CMMC L1/L2** practices embed the 800-171 **r2** number and are mapped to an
  r3 question via `r3_for_cmmc` (direct-pad + `CMMC_REDIRECT`). Validated by
  statically simulating all 110 L2 practices (and the L1 subset): every redirect
  resolves to a bank question and each mapping was topically checked against the
  r2→r3 change analysis. Two changes:
  - **3.13.16** (Protect CUI at rest) redirect fixed `03.13.11` → **03.13.08**,
    matching r3's consolidation of CUI-at-rest into Transmission and Storage
    Confidentiality.
  - Authored **03.07.01** (general system maintenance) so **MA.L2-3.7.1** — r2's
    "perform maintenance," which r3 dropped as a standalone control — gets a
    control-specific question. That ref is unused by NIST r3 / ITSP, so it only
    affects CMMC. Result: **110/110** CMMC L2 practices now map to a
    control-specific question (0 on the generic ladder).

Bank is now 98 authored questions. Re-run the seed (`--yes`) to push to the DB.

---

## 29. Phase 43 — Real report generation + Top 10 recommendations

Replaced the stubbed Celery report queue with synchronous, downloadable
documents, and added a curated Top 10 to recommendations.

- **Recommendations Top 10** (migration `016`, `recommendations.is_top10`):
  `POST /recommendations/auto-top10` flags the 10 highest-priority active recs
  (impact × gap × control risk); `PATCH /recommendations/{id}` accepts
  `is_top10` for manual pin/unpin. `GET /` returns `top10` = the pinned set if
  any, else the top-10 by priority (`top10_pinned` flag distinguishes).
  Frontend: **★ Auto-pick Top 10** button, per-row ★/☆ pin toggle, "★ Top 10"
  badge, and the Top 10 section reflects curated vs ranked.
- **Reports** (`app/reports_gen.py`, rewritten `app/api/reports.py`): one
  `gather()` builds the org's posture (controls + display status, evidence
  register, recommendations + Top 10 + quick wins, maturity overall). Renderers:
  PDF via **WeasyPrint**, Word via **python-docx** (added to requirements), Excel
  via **openpyxl**. `POST /reports/generate {report_type, format}` streams the
  file as an attachment (no worker needed). Report types: Audit Readiness, Gap
  Analysis, **Recommendations & Top 10**, Executive Summary (PDF/Word) and
  Evidence Register (Excel). Frontend Reports page: per-report PDF/Word/Excel
  download buttons that save the blob directly.

**Apply:** python-docx is a new dependency, so **rebuild the api image** (not
just restart): `docker compose build api && docker compose up -d`, then
`docker compose exec api alembic upgrade head` for migration 016.
