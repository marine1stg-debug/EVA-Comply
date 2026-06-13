# EVA Cybersecurity Audit Portal

## 🔒 Access gate & search-engine privacy

The whole portal sits behind an **HTTP Basic Auth gate** enforced by nginx:
anyone (including crawlers) who doesn't supply the credentials gets a **401 and
sees nothing**. The app, the API, and `/docs` are all covered by the single gate.

- Credentials come from env vars: `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD`.
- `/robots.txt` is the only open route and returns `Disallow: /`.
- A site-wide `X-Robots-Tag: noindex` header and a `<meta name="robots">` tag
  keep the portal out of every search index.
- For **local development only**, set `BASIC_AUTH_DISABLED=true` to bypass it.

**Deploying to Render?** See [`DEPLOY_RENDER.md`](./DEPLOY_RENDER.md) and
[`render.yaml`](./render.yaml).

## 🚀 Start the entire application

Copy the env template and set at least a basic-auth password first:

```bash
cp .env.example .env   # then edit BASIC_AUTH_PASSWORD (and others)
docker compose up --build
```

Wait ~2 minutes for everything to build and start. You'll get a basic-auth
prompt before the app loads.

## 🌐 Access the app

| Service | URL |
|---|---|
| **Portal (main app)** | http://localhost |
| **API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **API Health** | http://localhost:8000/health |

## 👤 Demo logins (password: demo1234)

| Email | Role |
|---|---|
| superadmin@eva.com | Super Admin |
| auditor@eva.com | EVA Auditor |
| msp@acmemsp.com | MSP Admin |
| analyst@acmemsp.com | MSP Analyst |
| admin@novlogix.com | Client Admin |
| it@novlogix.com | Contributor |
| coo@novlogix.com | Viewer |

## 🛑 Stop

```bash
docker compose down
```

## 🗑 Reset everything (wipe database)

```bash
docker compose down -v
docker compose up --build
```

## 📁 Project structure

```
eva-portal/
├── docker-compose.yml      ← The only file you need to run
├── backend/
│   ├── app/
│   │   ├── main.py         ← FastAPI app
│   │   ├── api/            ← Route handlers
│   │   ├── models/         ← Database models
│   │   ├── core/           ← Config, DB, security
│   │   └── seed.py         ← Demo data loader
│   ├── alembic/            ← Database migrations
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── pages/          ← React pages
│       ├── components/     ← Shared components
│       └── store/          ← Zustand state
└── nginx/
    └── nginx.conf          ← Reverse proxy
```

## ⚙️ Environment variables

Edit `docker-compose.yml` to configure:

- `STORAGE_BACKEND` — `local` (default) | `r2` | `s3`
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, etc. — Cloudflare R2 credentials
- `STRIPE_SECRET_KEY` — Stripe billing
- `EMAIL_BACKEND` — `console` (prints to terminal) | `sendgrid`

## 🔧 Troubleshooting

**Port already in use:**
```bash
docker compose down
# Then try again
docker compose up --build
```

**Database reset:**
```bash
docker compose down -v
docker compose up --build
```

**View logs:**
```bash
docker compose logs api        # Backend logs
docker compose logs frontend   # Frontend logs
docker compose logs db         # Database logs
```
