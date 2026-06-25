import { useI18n } from '../lib/i18n'

/**
 * Setup & Update Guide - Super Admin only (route + the "What's new" button are gated).
 * Bilingual (follows the app language). Explains how the app is set up and the
 * exact workflow to ship an update. Mirrors SETUP_AND_UPDATE_GUIDE.md.
 */
export default function SetupGuidePage() {
  const lang = useI18n(s => s.lang)
  const L = (en: string, fr: string) => (lang === 'fr' ? fr : en)

  const cmd: React.CSSProperties = {
    background: 'var(--card2, #0d1626)', color: 'var(--text)', border: '1px solid var(--border, rgba(120,140,170,.25))',
    borderRadius: 8, padding: '10px 12px', fontSize: 12.5, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
    whiteSpace: 'pre-wrap', overflowX: 'auto', margin: '6px 0 12px', lineHeight: 1.6,
  }
  const h2: React.CSSProperties = { fontSize: 16, fontWeight: 700, color: 'var(--text)', margin: '22px 0 4px', borderLeft: '4px solid var(--sky, #1A8FD1)', paddingLeft: 10 }
  const p: React.CSSProperties = { fontSize: 13.5, color: 'var(--text2)', lineHeight: 1.6, margin: '6px 0' }
  const li: React.CSSProperties = { fontSize: 13, color: 'var(--text2)', lineHeight: 1.55, margin: '4px 0' }
  const Cmd = ({ children }: { children: string }) => <pre style={cmd}>{children}</pre>

  return (
    <div style={{ maxWidth: 860 }}>
      <div className="page-title">{L('Setup & Update Guide', 'Guide d’installation et de mise à jour')}</div>
      <div className="page-sub" style={{ marginBottom: 8 }}>
        {L('How the app is set up and exactly how to publish a change. For the operator (Super Admin).',
           'Comment l’app est montée et comment publier un changement. Pour l’opérateur (Super Admin).')}
      </div>

      <div style={h2}>{L('1 · What the app is', '1 · Ce qu’est l’app')}</div>
      <p style={p}>{L(
        'EVA Comply has two halves: a frontend (the screens, built with React) and a backend (the brain that stores data and enforces rules, built with FastAPI/Python). They use a PostgreSQL database (all the data), a Redis cache, and store uploaded files on disk. In front sit Caddy (HTTPS) and nginx (the password gate + routing). Everything runs as Docker containers on one Debian server, started together by Docker Compose.',
        'EVA Comply a deux moitiés : un frontend (les écrans, en React) et un backend (le cerveau qui stocke les données et applique les règles, en FastAPI/Python). Ils utilisent une base PostgreSQL (toutes les données), un cache Redis, et stockent les fichiers téléversés sur disque. Devant : Caddy (HTTPS) et nginx (le portail mot de passe + le routage). Tout tourne en conteneurs Docker sur un seul serveur Debian, lancés ensemble par Docker Compose.')}</p>

      <div style={h2}>{L('2 · How a request flows', '2 · Comment circule une requête')}</div>
      <ul>
        <li style={li}>{L('The browser connects over HTTPS to Caddy (TLS certificate + security headers).', 'Le navigateur se connecte en HTTPS à Caddy (certificat TLS + en-têtes de sécurité).')}</li>
        <li style={li}>{L('Caddy passes it to nginx, which enforces the site password gate and routes the request.', 'Caddy passe à nginx, qui applique le portail mot de passe du site et achemine la requête.')}</li>
        <li style={li}>{L('A normal page → the frontend. An /api/… call → the backend (which uses its own JWT login).', 'Une page normale → le frontend. Un appel /api/… → le backend (qui a sa propre connexion JWT).')}</li>
        <li style={li}>{L('The backend reads/writes the database and files, and answers back up the chain.', 'Le backend lit/écrit la base et les fichiers, puis répond en remontant la chaîne.')}</li>
      </ul>

      <div style={h2}>{L('3 · Where everything lives', '3 · Où vit chaque chose')}</div>
      <ul>
        <li style={li}>{L('GitHub (source of truth): ', 'GitHub (source de vérité) : ')}<code>github.com/marine1stg-debug/EVA-Comply</code></li>
        <li style={li}>{L('Your Mac (working copy): ', 'Ton Mac (copie de travail) : ')}<code>~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github</code></li>
        <li style={li}>{L('The Debian server (live app): ', 'Le serveur Debian (app en ligne) : ')}<code>~/EVA-Comply</code></li>
      </ul>
      <p style={p}>{L('The direction is always: Mac → GitHub → Server.', 'Le sens est toujours : Mac → GitHub → Serveur.')}</p>

      <div style={h2}>{L('4 · How to update the app', '4 · Comment mettre à jour l’app')}</div>
      <p style={p}>{L('Run each command on its own line (press Enter after each - never paste several on one line), and start in the right folder.',
        'Lance chaque commande sur sa propre ligne (Entrée après chaque - jamais plusieurs sur une ligne), et commence dans le bon dossier.')}</p>
      <p style={p}><b>{L('A - On your Mac: send changes to GitHub', 'A - Sur ton Mac : envoyer les changements vers GitHub')}</b></p>
      <Cmd>{`cd ~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github
pwd          # ${'should end in eva-comply-github'}
git add -A
git commit -m "describe what changed"
git push origin main`}</Cmd>
      <p style={p}>{L('If asked, username = marine1stg-debug and password = a personal access token from that account (section 5).',
        'Si demandé, identifiant = marine1stg-debug et mot de passe = un token d’accès personnel de ce compte (section 5).')}</p>
      <p style={p}><b>{L('B - On the server: pull and rebuild', 'B - Sur le serveur : récupérer et reconstruire')}</b></p>
      <Cmd>{`cd ~/EVA-Comply
git pull
sudo docker compose up -d --build`}</Cmd>
      <p style={p}>{L('git pull should show files updated. "Already up to date" means the push didn’t go through. Database migrations run automatically on startup.',
        'git pull doit montrer des fichiers mis à jour. « Already up to date » = le push n’est pas passé. Les migrations de base de données s’exécutent automatiquement au démarrage.')}</p>
      <p style={p}><b>{L('C - See it', 'C - Le voir')}</b> - {L('hard refresh the browser (Cmd/Ctrl + Shift + R).', 'recharge en vidant le cache (Cmd/Ctrl + Maj + R).')}</p>

      <div style={h2}>{L('5 · GitHub authentication', '5 · Authentification GitHub')}</div>
      <p style={p}>{L('Pushing needs a personal access token (PAT) from the marine1stg-debug account (the repo owner). The error "denied to TaoAPPS" means your Mac is sending the wrong account’s credentials.',
        'Le push nécessite un token d’accès personnel (PAT) du compte marine1stg-debug (propriétaire du dépôt). L’erreur « denied to TaoAPPS » signifie que ton Mac envoie les identifiants du mauvais compte.')}</p>
      <p style={p}>{L('Create a token: sign in as marine1stg-debug → Settings → Developer settings → Personal access tokens (classic) → tick the “repo” scope. Never share a token; if exposed, delete it and make a new one.',
        'Créer un token : connecte-toi comme marine1stg-debug → Settings → Developer settings → Personal access tokens (classic) → coche la portée « repo ». Ne partage jamais un token ; s’il est exposé, supprime-le et régénère-en un.')}</p>
      <p style={p}><b>{L('Save it once (recommended):', 'L’enregistrer une fois (recommandé) :')}</b></p>
      <Cmd>{`printf "protocol=https\\nhost=github.com\\n\\n" | git credential-osxkeychain erase
git config --global credential.helper osxkeychain
git push origin main      # username: marine1stg-debug, password: token`}</Cmd>
      <p style={p}><b>{L('Or token in the URL (one-off, straight quotes):', 'Ou token dans l’URL (ponctuel, guillemets droits) :')}</b></p>
      <Cmd>{`git push "https://marine1stg-debug:YOUR_TOKEN@github.com/marine1stg-debug/EVA-Comply.git" main`}</Cmd>

      <div style={h2}>{L('6 · Common problems & fixes', '6 · Problèmes fréquents et solutions')}</div>
      <ul>
        <li style={li}><b>not a git repository</b> - {L('you’re not in the project folder. Run the cd command, then pwd.', 'tu n’es pas dans le dossier du projet. Lance la commande cd, puis pwd.')}</li>
        <li style={li}><b>403 denied to TaoAPPS</b> - {L('wrong identity. Use a marine1stg-debug token.', 'mauvaise identité. Utilise un token marine1stg-debug.')}</li>
        <li style={li}><b>too many arguments</b> - {L('curly quotes from copy-paste, or several commands on one line. Type the " yourself, one command per line.', 'guillemets courbés du copier-coller, ou plusieurs commandes sur une ligne. Tape les " toi-même, une commande par ligne.')}</li>
        <li style={li}><b>Already up to date</b> {L('on the server', 'sur le serveur')} - {L('the Mac push didn’t send anything. Re-check stage A.', 'le push du Mac n’a rien envoyé. Revérifie l’étape A.')}</li>
        <li style={li}><b>.git/index.lock</b> - {L('stale lock. Run: ', 'verrou résiduel. Lance : ')}<code>rm -f .git/index.lock</code></li>
        <li style={li}>{L('Pushed & rebuilt but no change → hard refresh. For the favicon, recreate the bookmark.', 'Poussé et reconstruit mais rien ne change → recharge sans cache. Pour le favicon, recrée le favori.')}</li>
        <li style={li}>{L('Version number didn’t change → it’s manual in frontend/src/lib/version.ts.', 'Le numéro de version n’a pas changé → il est manuel dans frontend/src/lib/version.ts.')}</li>
      </ul>

      <div style={h2}>{L('7 · Operating the server', '7 · Exploiter le serveur')}</div>
      <p style={p}>{L('Run these on the server in ~/EVA-Comply:', 'À lancer sur le serveur dans ~/EVA-Comply :')}</p>
      <Cmd>{`sudo docker compose ps                 # ${'status (all should be Up)'}
sudo docker compose logs --tail=50 api # ${'backend logs'}
sudo docker compose restart            # ${'restart without rebuild'}
git pull && sudo docker compose up -d --build   # ${'apply new code'}`}</Cmd>
      <p style={p}>{L('Avoid docker compose down -v - the -v deletes the data volumes (database + files).',
        'Évite docker compose down -v - le -v supprime les volumes de données (base + fichiers).')}</p>

      <div style={h2}>{L('8 · Configuration, secrets & backups', '8 · Configuration, secrets et sauvegardes')}</div>
      <ul>
        <li style={li}>{L('Environment variables (server .env): app secret, database URL, email, storage, the site password gate, token lifetimes, Stripe keys. Changing them needs a redeploy. Full reference in the in-app Configuration Guide.',
          'Variables d’environnement (.env serveur) : secret de l’app, URL de la base, courriel, stockage, portail mot de passe, durées de jeton, clés Stripe. Les changer nécessite un redéploiement. Référence complète dans le Guide de configuration intégré.')}</li>
        <li style={li}>{L('Never commit a real .env (it’s git-ignored).', 'Ne jamais committer un vrai .env (il est ignoré par git).')}</li>
        <li style={li}>{L('Backups: use the in-app Backup & Restore page; take one before any risky change.', 'Sauvegardes : utilise la page Sauvegarde et restauration intégrée ; fais-en une avant tout changement risqué.')}</li>
      </ul>

      <div style={h2}>{L('The 30-second cheat sheet', 'L’aide-mémoire de 30 secondes')}</div>
      <Cmd>{`# MAC
cd ~/Documents/CLAUDE/Projects/EVA_AUDIT_PORTAL_v2/eva-comply-github
git add -A
git commit -m "what changed"
git push origin main        # marine1stg-debug + token

# SERVER
cd ~/EVA-Comply
git pull
sudo docker compose up -d --build
# then hard-refresh (Cmd/Ctrl + Shift + R)`}</Cmd>
      <p style={p} className="page-sub">{L('Edit on the Mac → push to GitHub → pull & rebuild on the server.',
        'Modifie sur le Mac → pousse vers GitHub → récupère et reconstruis sur le serveur.')}</p>
    </div>
  )
}
