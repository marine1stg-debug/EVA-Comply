# EVA Comply — Setup & Update Guide

A plain-language guide to how the app is built, where everything lives, and exactly how to ship a change to the live site. Keep this next to the project.

---

## 1. What the app is, in one paragraph

EVA Comply is a web application made of two halves: a **frontend** (the screens you see, built with React) and a **backend** (the brain that stores data and enforces rules, built with FastAPI/Python). They talk to a **PostgreSQL database** (all the data), a **Redis** cache, and store uploaded files on disk. In front of everything sits **Caddy** (handles HTTPS) and **nginx** (handles the password gate and routing). All of these run as **Docker containers** on a single **Debian server**, started together by **Docker Compose**.

You don't run these pieces by hand — Docker Compose runs them all from one command.

---

## 2. How a request flows (the big picture)

When someone opens the site:

1. Their browser connects over **HTTPS** to **Caddy**, which automatically obtains and renews the TLS certificate and adds security headers.
2. Caddy passes the request to **nginx**, which enforces the **site password gate** (HTTP Basic Auth — the username/password wall that keeps crawlers and strangers out) and decides where the request goes.
3. If it's a normal page, nginx serves the **frontend**. If it's an `/api/...` call, nginx forwards it to the **backend** (which uses its own login with JWT tokens, separate from the password gate).
4. The backend reads/writes the **PostgreSQL database** and the **uploaded files**, and sends the answer back up the chain.

The takeaway: there is **one server**, running **several containers**, and Docker Compose is the conductor.

---

## 3. Where everything lives

There are three locations you care about:

- **GitHub repository** — the source of truth for the code: `https://github.com/marine1stg-debug/EVA-Comply`. The repo is owned by the GitHub account **`marine1stg-debug`**.
- **Your Mac** — your working copy, where you (and I) make changes, in the folder:
  `~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github`
- **The Debian server** — where the live app runs, in the folder:
  `~/EVA-Comply`

The flow of a change is always the same direction: **Mac → GitHub → Server.**

---

## 4. How to update the app (the core workflow)

Updating the live site is always the same three stages. **Run each command on its own line** (press Enter after each — never paste several commands on one line), and always start by going into the right folder.

### Stage A — On your Mac: save and send the changes to GitHub

```
cd ~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github
```

Check you're in the right place (the path should end in `eva-comply-github`):

```
pwd
```

Stage the changes, commit them with a short message (**type the quotes yourself**, keep the message simple — no accents or parentheses), and push:

```
git add -A
```
```
git commit -m "describe what changed"
```
```
git push origin main
```

If `git push` asks for a username and password, enter username **`marine1stg-debug`** and, as the password, a **personal access token** from the `marine1stg-debug` account (see section 5). On success you'll see something like `... main -> main`.

### Stage B — On the Debian server: pull and rebuild

Connect to the server, then:

```
cd ~/EVA-Comply
```
```
git pull
```

`git pull` should show files being updated. If it says **"Already up to date,"** it means Stage A didn't actually send anything — go back and check the push.

```
sudo docker compose up -d --build
```

The `--build` part rebuilds the containers so your new code is included. Database migrations run automatically when the backend starts, so you don't run them by hand.

### Stage C — See the change

Reload the site in your browser with a **hard refresh** (Cmd/Ctrl + Shift + R) to bypass the cache. For favicons specifically, browsers cache them aggressively — you may need to remove and recreate the bookmark to see a new icon.

---

## 5. GitHub authentication (the part that keeps biting)

GitHub no longer accepts your account password for `git push`. It needs a **personal access token (PAT)**, and the token must belong to an account that can write to the repo — here, **`marine1stg-debug`** (the owner).

**The classic error you hit:**
`Permission to marine1stg-debug/EVA-Comply.git denied to TaoAPPS` → this means your Mac is sending the credentials of a **different account (TaoAPPS)** that has no write access. The fix is to make git use the `marine1stg-debug` identity.

### Create a token (once)

Sign in to GitHub **as `marine1stg-debug`** → Settings → Developer settings → **Personal access tokens (classic)** → Generate new token → tick the **`repo`** scope → copy the token (starts with `ghp_`). **Never paste a token into a chat or share it** — if you do, delete it and make a new one.

### Two ways to use it

**Option 1 — Save it once (recommended).** Clear any old saved login, then push and enter the token when asked. macOS Keychain remembers it afterward:

```
printf "protocol=https\nhost=github.com\n\n" | git credential-osxkeychain erase
```
```
git config --global credential.helper osxkeychain
```
```
git push origin main
```
→ username `marine1stg-debug`, password = your token. (If the old TaoAPPS login keeps coming back, open the **Keychain Access** app, search **github.com**, delete the entry, and try again.)

**Option 2 — Token in the URL (one-off, bypasses the keychain).** One line, straight quotes:

```
git push "https://marine1stg-debug:YOUR_TOKEN@github.com/marine1stg-debug/EVA-Comply.git" main
```

---

## 6. Common problems & quick fixes

- **`fatal: not a git repository`** → You're not inside the project folder. Run the `cd ~/Documents/.../eva-comply-github` command first, then `pwd` to confirm.
- **`403 ... denied to TaoAPPS`** → Wrong GitHub identity. Use a `marine1stg-debug` token (section 5).
- **`too many arguments` on commit/push** → Your quotes turned into "curly" quotes when copy-pasting, or you put several commands on one line. Type the `"` straight quotes yourself and run one command per line.
- **`nothing to commit, working tree clean` but you expected changes** → The changes were already committed. If it also says **"ahead of origin by N commits,"** they just need pushing.
- **Server `git pull` says "Already up to date"** but you expected new code → The push from the Mac didn't go through. Re-check Stage A.
- **`.git/index.lock` error** → A stale lock. Remove it: `rm -f .git/index.lock`, then retry.
- **You pushed and rebuilt but don't see the change** → Hard refresh (Cmd/Ctrl + Shift + R). For the favicon, recreate the bookmark.
- **The version number in the sidebar didn't change** → It's a manual number in `frontend/src/lib/version.ts`. It only changes if that file is edited and deployed.

---

## 7. Operating the server (handy commands)

Run these on the Debian server, in `~/EVA-Comply`:

- See what's running: `sudo docker compose ps` (everything should say "Up").
- Read backend logs (last 50 lines): `sudo docker compose logs --tail=50 api`
- Restart everything without rebuilding: `sudo docker compose restart`
- Apply new code: `git pull && sudo docker compose up -d --build`
- **Avoid** `docker compose down -v` — the `-v` deletes the data volumes (database and files). Don't use it unless you intend to wipe everything.

---

## 8. Configuration & secrets

Settings that change behavior live in two places:

- **Environment variables** in the server's `.env` file (and the container environment): the app secret, database URL, email backend, storage, the site password gate, token lifetimes, Stripe keys, etc. Changing these requires a redeploy. A full reference is in `.env.example` and in the in-app **Configuration Guide** (Super Admin → Administration).
- **In-app settings** a Super Admin changes live: plans & pricing, the AI connector, policy library, per-organization engagement level (self / assisted / audited), etc.

Never commit a real `.env` to GitHub — it's intentionally git-ignored.

---

## 9. Backups (don't skip this)

Data lives in Docker volumes on the server (database + uploaded files). The app also has a built-in **Backup & Restore** page (Super Admin → Administration) that exports signed bundles and a "full backup" (data + files). Take a backup before any risky change. Restores only accept backups produced by this system.

---

## 10. The 30-second cheat sheet

```
# MAC — send changes up
cd ~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github
git add -A
git commit -m "what changed"
git push origin main        # auth as marine1stg-debug + token

# SERVER — go live
cd ~/EVA-Comply
git pull
sudo docker compose up -d --build

# then hard-refresh the browser (Cmd/Ctrl + Shift + R)
```

That's the whole loop: **edit on the Mac → push to GitHub → pull & rebuild on the server.**
