# Deploying EVA Comply to Render

This repo is set up to deploy as a small multi-service stack on Render, with the
whole portal behind an **HTTP Basic Auth gate** (crawlers and anonymous visitors
get a `401` and see nothing) and **`noindex` / `robots.txt`** so nothing is
indexable.

## The access gate, in one place

Everything public goes through one service: **`eva-nginx`**. Its entrypoint
(`nginx/docker-entrypoint-eva.sh`) builds an `htpasswd` from the
`BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` env vars at boot and enforces basic
auth on **every** path — the app, the API, and `/docs`. The only unauthenticated
route is `/robots.txt`, which returns `Disallow: /`. A site-wide
`X-Robots-Tag: noindex` header and a `<meta name="robots" content="noindex">`
tag are added as belt-and-suspenders.

To run locally without the gate (dev only): set `BASIC_AUTH_DISABLED=true`.

## What's in the blueprint (`render.yaml`)

| Service | Type | Public? | Notes |
|---|---|---|---|
| `eva-nginx` | web | **yes** | The basic-auth gate + reverse proxy. The only internet-facing service. |
| `eva-api` | private | no | FastAPI on `:8000`. Runs migrations + seeds on boot. |
| `eva-worker` | worker | no | Celery. |
| `eva-frontend` | private | no | Vite server on `:3000`. |
| `eva-db` | Postgres | no | Managed. |
| `eva-redis` | Key Value | no | Managed (Redis-compatible). |

Private services reach each other by name over Render's private network
(`eva-api:8000`, `eva-frontend:3000`), which is why nginx is the only thing
exposed.

## Step-by-step

1. **Push this folder to GitHub** (see the bottom of `README.md`).
2. In Render: **New → Blueprint**, pick the repo. Render reads `render.yaml`.
3. Render will prompt for every var marked `sync: false`. Set:
   - `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` — your gate credentials.
   - `DATABASE_URL` — **asyncpg form**, built from the `eva-db` internal
     connection info Render shows you:
     `postgresql+asyncpg://eva_user:<password>@<internal-host>:5432/eva_db`
     (set the identical value on `eva-api` and `eva-worker`).
   - `FRONTEND_URL` — your public nginx URL, e.g. `https://eva-nginx.onrender.com`
     (or your custom domain). Used to build invite/reset links.
   - Email: `FROM_EMAIL`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` (or switch
     `EMAIL_BACKEND` to `sendgrid` and set `SENDGRID_API_KEY`).
     **Email is required** — the app refuses to start in production on the
     console backend.
   - Object storage (recommended): `STORAGE_BACKEND=r2` plus the `R2_*` keys, so
     uploaded evidence survives restarts. (Render service disks are per-service
     and not shared; for durable evidence use R2/S3.)
4. **Apply**. First boot of `eva-api` runs `alembic upgrade head` and seeds the
   framework catalogs, policy templates, maturity banks, and demo tenants.
5. Open the `eva-nginx` URL → browser shows a **basic-auth prompt** → enter the
   credentials → EVA Comply login appears.

## Verifying the gate

```bash
# No credentials → 401 (this is what crawlers get):
curl -I https://<your-eva-nginx-url>/

# With credentials → 200:
curl -I -u "$BASIC_AUTH_USER:$BASIC_AUTH_PASSWORD" https://<your-eva-nginx-url>/

# robots.txt is intentionally open and says "go away":
curl https://<your-eva-nginx-url>/robots.txt
```

## Caveats / things to review

- **`DATABASE_URL` is manual** because Render's auto-generated string is in
  `postgresql://` form and this app needs the `postgresql+asyncpg://` driver.
  alembic in this app uses the same URL, so the asyncpg form is correct for both
  migrations and runtime.
- **Redis block keyword**: newer Render accounts use `type: keyvalue`; some older
  ones still use `type: redis`. If the blueprint errors on that block, swap the
  keyword.
- **Frontend is a Vite dev server** (the app ships no production build stage). It
  works behind nginx (we set `allowedHosts: true`), but if you later want a
  hardened static build, add a build stage to `frontend/Dockerfile` and serve the
  output. Not required to go live.
- **Demo accounts are seeded** (e.g. `superadmin@eva.com` / `demo1234`). Remove or
  change them before real use.
- **Plans** in `render.yaml` are conservative defaults — adjust to your needs.

## Alternative: single-host Docker (Cloudflare Tunnel)

If you'd rather run the whole `docker-compose` stack on one VM and expose it via
Cloudflare instead of Render, see the `cloudflare-deploy/` companion files in the
parent project. The same nginx basic-auth gate applies there too.
