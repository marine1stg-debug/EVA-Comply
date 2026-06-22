# Deploying EVA Comply on a fresh Debian server

End-to-end: from a bare Debian box (nothing installed) to the portal running
behind the password gate. Commands assume you're logged in as **root** (the
default on most fresh VMs). If you're a sudo user instead, prefix each command
with `sudo`.

## Step 0 — On your Mac: push the latest code first

The server pulls from GitHub, so make sure your hardened Dockerfiles and the
deploy override are pushed:

```bash
cd ~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github
git add -A
git commit -m "Add Debian single-host deploy override"
git push
```

## Step 1 — Base tools

```bash
apt-get update
apt-get install -y ca-certificates curl git
```

## Step 2 — Install Docker Engine + Compose

```bash
curl -fsSL https://get.docker.com | sh
docker compose version    # confirm the compose plugin is present
```

## Step 3 — Get the code

```bash
git clone https://github.com/TaoAPPS/EVA-Comply.git
cd EVA-Comply
```

It will ask for your GitHub username and password — the repo is private, so use
a **Personal Access Token** as the password (github.com → Settings → Developer
settings → Personal access tokens → Tokens (classic) → generate with `repo`
scope), not your account password.

## Step 4 — Create the .env with strong, generated secrets

This writes random secrets and a basic-auth password in one shot:

```bash
cat > .env <<EOF
BASIC_AUTH_USER=eva
BASIC_AUTH_PASSWORD=$(openssl rand -hex 12)
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 24)
ENVIRONMENT=development
FRONTEND_URL=http://localhost
EMAIL_BACKEND=console
EOF
```

Now show the login password you'll need (and the whole file):

```bash
cat .env
```

Note the `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` — that's your login to the site.

> Leaving `ENVIRONMENT=development` lets the stack boot without a mail server.
> Real password-reset / invite emails won't send in this mode, but `SECRET_KEY`
> and the DB password are already strong. To enable production mode + real email
> later: set `ENVIRONMENT=production`, `EMAIL_BACKEND=smtp`, and fill the SMTP
> values, then re-run Step 5. (Production refuses to boot on console email.)

## Step 5 — Build and start

```bash
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build
```

First boot takes a few minutes (it builds images, migrates the DB, and seeds the
frameworks/policies/demo data). Watch progress:

```bash
docker compose -f docker-compose.yml -f docker-compose.deploy.yml ps
docker compose -f docker-compose.yml -f docker-compose.deploy.yml logs -f api
```

When the API log ends on "Application startup complete," it's up.

## Step 6 — Firewall (recommended)

The deploy override publishes only nginx:80 — Postgres/Redis/API/frontend are
not reachable from outside. Lock the host down to SSH + HTTP:

```bash
apt-get install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw --force enable
```

## Step 7 — Open it

Browse to `http://YOUR_SERVER_IP`. You'll get a browser password prompt — enter
the basic-auth user/password from your `.env` — then the EVA Comply login.

## Day-2

```bash
# Update to newer code
git pull && docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --build

# Stop (keeps data) / start
docker compose -f docker-compose.yml -f docker-compose.deploy.yml down
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d

# Back up DB + uploaded evidence BEFORE any reset
./scripts/backup.sh
```

Data lives in the `postgres_data` and `uploads_data` Docker volumes. `down`
keeps them; `down -v` deletes them.

## Important: HTTPS

This serves plain **HTTP on port 80**, so the basic-auth password travels
unencrypted. Fine for testing, not for real use over the internet. Before going
live, put HTTPS in front — easiest is Cloudflare (free; see the
`cloudflare-deploy/` files), or add a TLS reverse proxy (Caddy/Let's Encrypt) on
the host. Ask me and I'll set whichever you prefer.
