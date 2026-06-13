# EVA Comply — Live Validation Checklist (Phase 2)

Run this once on your machine after the static pre-flight passed. The goal is to prove
the app actually *runs* end-to-end, not just compiles. Work top to bottom; paste any
failure back and I'll fix it.

## A. Bring the stack up

```bash
cd eva-portal
docker compose up -d --build
docker compose ps            # all services "running"/"healthy"
docker compose logs -f api   # watch: migrations → seeders → "Uvicorn running"
```

What to confirm in the `api` logs, in order:
- [ ] `alembic upgrade head` reaches **034** with no error (esp. no `min(uuid)` error).
- [ ] `seed_catalogs` imports all **7 frameworks** (CMMC L1/L2, 800-171 R3, ITSP.10.171, CyberSecure, CIS v8.1, 800-53 r5).
- [ ] `seed_scripts_all`, `seed`, `seed_maturity_questions` finish without traceback.
- [ ] `Uvicorn running on 0.0.0.0:8000`.

## B. Automated smoke test

```bash
./tools/smoke_test.sh
# or, if API is not on :8000
BASE=http://localhost:8000 ./tools/smoke_test.sh
```
- [ ] Ends with `SMOKE TEST: N passed, 0 failed`.

## C. Manual UI pass (the things a script can't see)

Log in at the frontend as `superadmin@eva.com` / `demo1234`.

**Language switch (the big one):**
- [ ] Toggle EN↔FR in the header — Shell labels, Dashboard, Controls all switch.
- [ ] Open the **domain filter** dropdown in FR — every domain is French (no mixed EN/FR).
- [ ] Open a control in FR — title, requirement/objective, expected evidence all FR; "View in English" still works per-control.

**Controls & evidence:**
- [ ] Controls list loads for each framework; level badges localized.
- [ ] Open a control → Prev/Next navigation works (and warns on unsaved changes).
- [ ] Add a documented evidence (title + note + file) → appears as `eva_pending`.
- [ ] Export (XLSX + ZIP) downloads.

**Billing (test mode):**
- [ ] Billing page shows interval / auto-renew / renews-at.
- [ ] Subscribe via Stripe **test** card `4242 4242 4242 4242` → success.
- [ ] Cancel → shows "cancels at period end"; Resume → clears it.

**Admin:**
- [ ] Tenants page: row action tooltips show on hover; suspend/archive work.
- [ ] Backup & Restore: download frameworks ZIP; take a snapshot (try `fmt=zip`).
- [ ] Aggregate report generates (super_admin = all clients).

**Roles (log in as each):**
- [ ] `msp@acmemsp.com` sees only its own clients in the selector.
- [ ] `admin@novlogix.com` sees only subscribed frameworks.

**Mobile:**
- [ ] Narrow the window → mobile banner appears → `/m` shows cases + "Declare an incident".

## D. What to capture if something fails
- The failing step above.
- `docker compose logs api --tail=80` (backend traceback).
- Browser console error (frontend).

Paste those and I'll patch the code. Most likely failure classes at this stage are
runtime-only issues the static checks can't catch: a Pydantic response-model mismatch,
an async session misuse, a missing env var, or a Stripe key not set.
