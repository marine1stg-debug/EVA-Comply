import { useI18n } from '../lib/i18n'

/**
 * Configuration & How-it-works guide — Super Admin only (route + nav are gated).
 * Bilingual, self-contained, expandable. For each element: a "how it works"
 * summary and the configuration it needs. Mirrors EVA_Comply_Config_Guide.html.
 */

interface Box { icon: string; title: string; how: string; cfg: string[] }
interface Section { id: string; heading: string; boxes: Box[] }

export default function ConfigGuidePage() {
  const lang = useI18n(s => s.lang)
  const L = (en: string, fr: string) => (lang === 'fr' ? fr : en)

  const sections: Section[] = [
    {
      id: 'deploy', heading: L('1 · Deployment & environment', '1 · Déploiement et environnement'),
      boxes: [
        { icon: '🔐', title: L('App secret & environment mode', 'Secret de l’app et mode d’environnement'),
          how: L('Signs all sessions/tokens and encrypts stored secrets; production mode hardens the app.', 'Signe les sessions/jetons et chiffre les secrets stockés ; le mode production durcit l’app.'),
          cfg: [
            L('SECRET_KEY (env) — required, ≥32 chars in production (openssl rand -hex 32). Changing it logs everyone out and makes stored AI keys / MFA secrets unreadable.', 'SECRET_KEY (env) — requis, ≥32 caractères en production (openssl rand -hex 32). Le changer déconnecte tout le monde et rend illisibles les clés IA / secrets MFA stockés.'),
            L('ENVIRONMENT (env) — development | production (default development). Production hides API docs and enables the startup safety guard.', 'ENVIRONMENT (env) — development | production (défaut development). La production masque la doc API et active la garde de démarrage.'),
            L('FRONTEND_URL (env) — public app URL; used in invite/reset/unlock links and CORS.', 'FRONTEND_URL (env) — URL publique de l’app ; utilisée dans les liens et le CORS.'),
            L('Startup guard: in production the app refuses to start with a default/short SECRET_KEY, the dev DB password, or EMAIL_BACKEND=console.', 'Garde de démarrage : en production, l’app refuse de démarrer avec un SECRET_KEY par défaut/court, le mot de passe BD de dev, ou EMAIL_BACKEND=console.'),
          ] },
        { icon: '🚪', title: L('Site access gate (Basic Auth)', 'Portail d’accès au site (Basic Auth)'),
          how: L('An nginx username/password wall in front of the whole site so crawlers/strangers get 401.', 'Un mur identifiant/mot de passe nginx devant tout le site ; les robots/inconnus reçoivent 401.'),
          cfg: [
            L('BASIC_AUTH_USER + BASIC_AUTH_PASSWORD (env) — required; if missing (and not disabled) the container exits.', 'BASIC_AUTH_USER + BASIC_AUTH_PASSWORD (env) — requis ; si absents (et non désactivés), le conteneur s’arrête.'),
            L('BASIC_AUTH_DISABLED (env) — true/false (default false; true only for local dev).', 'BASIC_AUTH_DISABLED (env) — true/false (défaut false ; true seulement en dev local).'),
            L('The API (/api/) is exempt — it uses its own JWT login.', 'L’API (/api/) est exemptée — elle utilise sa propre connexion JWT.'),
          ] },
        { icon: '🗄️', title: L('Database & cache', 'Base de données et cache'),
          how: L('Postgres holds all data; Redis backs the queue.', 'Postgres contient toutes les données ; Redis sert la file de tâches.'),
          cfg: [
            L('DATABASE_URL (env) — async Postgres URL; must NOT keep the dev default password in production.', 'DATABASE_URL (env) — URL Postgres async ; ne doit pas garder le mot de passe par défaut en production.'),
            L('REDIS_URL (env) — default redis://redis:6379.', 'REDIS_URL (env) — défaut redis://redis:6379.'),
          ] },
      ],
    },
    {
      id: 'auth', heading: L('2 · Authentication & sessions', '2 · Authentification et sessions'),
      boxes: [
        { icon: '⏱️', title: L('Session length & silent refresh', 'Durée de session et rafraîchissement silencieux'),
          how: L('A short access token is refreshed silently from a long-lived refresh token.', 'Un jeton d’accès court est renouvelé en silence depuis un jeton de rafraîchissement de longue durée.'),
          cfg: [
            L('ACCESS_TOKEN_EXPIRE_MINUTES (env) — default 15 (often raised, e.g. 480 = 8 h).', 'ACCESS_TOKEN_EXPIRE_MINUTES (env) — défaut 15 (souvent augmenté, p. ex. 480 = 8 h).'),
            L('REFRESH_TOKEN_EXPIRE_DAYS (env) — default 30.', 'REFRESH_TOKEN_EXPIRE_DAYS (env) — défaut 30.'),
            L('Changing a password revokes all existing sessions (token version bump).', 'Changer un mot de passe révoque toutes les sessions existantes (incrément de version de jeton).'),
          ] },
        { icon: '🔑', title: L('MFA, lockout & password rules', 'MFA, verrouillage et règles de mot de passe'),
          how: L('Two-factor for admin roles, automatic lockout on repeated failures, 12-char minimum.', 'Double authentification pour les rôles admin, verrouillage auto après échecs, minimum 12 caractères.'),
          cfg: [
            L('MFA — required for super_admin, eva_auditor, msp_admin. Opt-in: each user enables it (Settings → enable MFA). Enforced at login only once turned on — no forced enrollment.', 'MFA — requise pour super_admin, eva_auditor, msp_admin. Sur activation : chaque utilisateur l’active (Réglages → activer la MFA). Imposée à la connexion seulement une fois activée — pas d’inscription forcée.'),
            L('Lockout — 3 failed logins → 15-minute lock + emailed unlock link. Admins can also unlock a user.', 'Verrouillage — 3 échecs → verrouillage 15 min + lien de déverrouillage par courriel. Les admins peuvent aussi déverrouiller un utilisateur.'),
            L('Password — minimum 12 characters (no complexity rule).', 'Mot de passe — minimum 12 caractères (pas de règle de complexité).'),
            L('Rate limits (per IP): login 10/5min, MFA 10/5min, refresh 60/5min, register 5/h, verification & unlock 5/15min.', 'Limites (par IP) : connexion 10/5min, MFA 10/5min, refresh 60/5min, inscription 5/h, vérification et déverrouillage 5/15min.'),
            L('These four (MFA roles, lockout, password length, rate limits) are CODE CONSTANTS — changing them needs a code change + redeploy.', 'Ces quatre éléments (rôles MFA, verrouillage, longueur du mot de passe, limites) sont des CONSTANTES DE CODE — les changer demande une modification + redéploiement.'),
          ] },
      ],
    },
    {
      id: 'roles', heading: L('3 · Roles & access control', '3 · Rôles et contrôle d’accès'),
      boxes: [
        { icon: '👥', title: L('The 7 roles & who can invite whom', 'Les 7 rôles & qui peut inviter qui'),
          how: L('Each admin grants only roles within its tier; roles must match the org type.', 'Chaque admin n’attribue que des rôles de son niveau ; les rôles doivent correspondre au type d’org.'),
          cfg: [
            L('Roles: super_admin, eva_auditor, msp_admin, msp_analyst, client_admin, contributor, viewer.', 'Rôles : super_admin, eva_auditor, msp_admin, msp_analyst, client_admin, contributor, viewer.'),
            L('Invite rights: Super Admin → super_admin/eva_auditor; MSP Admin → msp_admin/msp_analyst; Client Admin → client_admin/contributor/viewer.', 'Droits d’invitation : Super Admin → super_admin/eva_auditor ; Admin MSP → msp_admin/msp_analyst ; Admin client → client_admin/contributeur/lecteur.'),
            L('A role must fit the org tier (EVA roles on EVA org, MSP on MSP org, client on client org). Set in Users & Roles.', 'Un rôle doit correspondre au type d’org (EVA sur org EVA, MSP sur org MSP, client sur org client). Réglé dans Utilisateurs et rôles.'),
            L('Viewer is read-only — cannot upload, submit, edit, or manage users. can_coach (per auditor) toggles "under review" power.', 'Lecteur est en lecture seule — ne peut ni téléverser, ni soumettre, ni modifier, ni gérer les utilisateurs. can_coach (par auditeur) active le pouvoir « en revue ».'),
          ] },
      ],
    },
    {
      id: 'tenant', heading: L('4 · Organization & engagement model', '4 · Organisation et modèle d’engagement'),
      boxes: [
        { icon: '🎚️', title: L('Audit level — self / assisted / audited', 'Niveau d’audit — self / assisted / audited'),
          how: L('Decides whether submitted evidence is auto-accepted or sent for review.', 'Décide si une preuve soumise est auto-acceptée ou envoyée en revue.'),
          cfg: [
            L('Values self | assisted | audited; default self. (In-app, per organization.)', 'Valeurs self | assisted | audited ; défaut self. (Dans l’app, par organisation.)'),
            L('self (self-audit): evidence is ACCEPTED IMMEDIATELY on submit — no reviewer.', 'self (auto-audit) : la preuve est ACCEPTÉE IMMÉDIATEMENT à la soumission — aucun réviseur.'),
            L('assisted / audited: routed to a reviewer (MSP if MSP review enabled, else EVA). Both behave the same for routing today.', 'assisted / audited : acheminée vers un réviseur (MSP si revue MSP activée, sinon EVA). Les deux se comportent pareil pour le routage aujourd’hui.'),
            L('Set by Super Admin, EVA Auditor, or MSP Admin (MSP only for its own clients). Every change is audit-logged.', 'Réglé par Super Admin, Auditeur EVA, ou Admin MSP (MSP seulement pour ses clients). Chaque changement est journalisé.'),
          ] },
        { icon: '🏢', title: L('MSP review, activation & lifecycle', 'Revue MSP, activation et cycle de vie'),
          how: L('Optional MSP pre-review step; MSP signups need approval; status gates access.', 'Étape de pré-revue MSP optionnelle ; les inscriptions MSP nécessitent une approbation ; le statut conditionne l’accès.'),
          cfg: [
            L('msp_review_enabled — when on (non-self), submitted evidence goes to the MSP queue first.', 'msp_review_enabled — quand activé (non-self), la preuve soumise passe d’abord par la file MSP.'),
            L('activation_pending — MSP/reseller self-signups can’t log in until a Super Admin authorizes them.', 'activation_pending — les inscriptions MSP/revendeurs ne peuvent se connecter qu’après autorisation d’un Super Admin.'),
            L('subscription_status — active · trialing · past_due · suspended · cancelled (default trialing); suspended → access blocked.', 'subscription_status — active · trialing · past_due · suspended · cancelled (défaut trialing) ; suspended → accès bloqué.'),
            L('plan / monthly_price / billing_mode / parent_msp_id / archived — Super-Admin managed; archived orgs drop off listings.', 'plan / monthly_price / billing_mode / parent_msp_id / archived — gérés par le Super Admin ; les orgs archivées disparaissent des listes.'),
          ] },
      ],
    },
    {
      id: 'evidence', heading: L('5 · Evidence', '5 · Preuves'),
      boxes: [
        { icon: '📄', title: L('Statuses, routing, file rules & renewals', 'Statuts, routage, règles de fichiers et renouvellements'),
          how: L('Upload → submit → (auto-accept or review) → accepted; periodic items renew.', 'Téléverser → soumettre → (auto-accept ou revue) → accepté ; les éléments périodiques se renouvellent.'),
          cfg: [
            L('Statuses: draft → submitted → msp_pending / eva_pending → accepted / needs_more / rejected (or not_applicable).', 'Statuts : brouillon → soumis → msp_pending / eva_pending → accepté / complément / rejeté (ou non applicable).'),
            L('Routing on submit depends on the org’s audit level (see §4).', 'Le routage à la soumission dépend du niveau d’audit de l’org (voir §4).'),
            L('Max size 50 MB. Allowed: documents (pdf, doc/x, xls/x, ppt/x, csv, txt, md, rtf, odt, ods), images (png, jpg, gif, webp, bmp, tiff, heic — NOT SVG), archives (zip, 7z, rar, gz). Executables/HTML/SVG blocked even if renamed.', 'Taille max 50 Mo. Permis : documents (pdf, doc/x, xls/x, ppt/x, csv, txt, md, rtf, odt, ods), images (png, jpg, gif, webp, bmp, tiff, heic — PAS SVG), archives (zip, 7z, rar, gz). Exécutables/HTML/SVG bloqués même renommés.'),
            L('Frequencies once/monthly/quarterly/semi-annual/annual/continuous drive Renewals (expired / due ≤30 days / ok). (Size/type are code constants.)', 'Fréquences once/monthly/quarterly/semi-annual/annual/continuous pilotent les Renouvellements (expiré / dû ≤30 jours / ok). (Taille/type sont des constantes de code.)'),
          ] },
      ],
    },
    {
      id: 'maturity', heading: L('6 · Maturity & recommendations', '6 · Maturité et recommandations'),
      boxes: [
        { icon: '◎', title: L('Maturity scoring', 'Score de maturité'),
          how: L('0–5 ratings per domain; current auto-derives from compliant controls or is overridden.', 'Notes 0–5 par domaine ; le niveau actuel se déduit des contrôles conformes ou est surchargé.'),
          cfg: [
            L('Current (auto or manual override), Target (default 4), frozen Previous via snapshots.', 'Actuel (auto ou surcharge manuelle), Cible (défaut 4), Précédent figé via instantanés.'),
            L('Editable by Super Admin, EVA, MSP. Scale fixed 0–5.', 'Modifiable par Super Admin, EVA, MSP. Échelle fixe 0–5.'),
          ] },
        { icon: '✦', title: L('Recommendations (curated + optional AI)', 'Recommandations (sélectionnées + IA optionnelle)'),
          how: L('Suggested fixes per gap, bilingual; AI generation needs the connector enabled.', 'Correctifs suggérés par écart, bilingues ; la génération IA nécessite le connecteur activé.'),
          cfg: [
            L('Source premade (curated, EN+FR) or ai (one LLM call per control — requires the AI connector; AI output is single-language).', 'Source premade (sélectionnée, EN+FR) ou ai (un appel LLM par contrôle — nécessite le connecteur IA ; sortie IA unilingue).'),
            L('Generated by reviewers (Super / EVA / MSP). Status open → in_progress → done / dismissed.', 'Générées par les réviseurs (Super / EVA / MSP). Statut open → in_progress → done / dismissed.'),
          ] },
      ],
    },
    {
      id: 'policies', heading: L('7 · Policy library', '7 · Bibliothèque de politiques'),
      boxes: [
        { icon: '📘', title: L('Built-in vs uploaded, mapping & availability', 'Intégrées vs téléversées, association et disponibilité'),
          how: L('Bilingual .docx templates; keywords map a policy to a control family; availability controls visibility.', 'Modèles .docx bilingues ; des mots-clés associent une politique à une famille de contrôles ; la disponibilité contrôle la visibilité.'),
          cfg: [
            L('Source builtin (ships with the app) or upload (added by you). FR version via a .fr.docx (has_fr).', 'Source builtin (livrée) ou upload (ajoutée par vous). Version FR via un .fr.docx (has_fr).'),
            L('keywords — comma-separated; a policy shows "available" on a control when all its keywords appear in the control’s domain.', 'keywords — séparés par virgules ; une politique apparaît « disponible » sur un contrôle si tous ses mots-clés figurent dans le domaine du contrôle.'),
            L('is_active off = hidden from non-admins. Upload limit 25 MB, .docx only.', 'is_active désactivé = masquée aux non-admins. Limite 25 Mo, .docx seulement.'),
            L('Everyone can search/preview/download; only Super Admin can add/edit/replace/hide/delete.', 'Tout le monde peut rechercher/prévisualiser/télécharger ; seul le Super Admin peut ajouter/modifier/remplacer/masquer/supprimer.'),
          ] },
      ],
    },
    {
      id: 'llm', heading: L('8 · AI connector (optional)', '8 · Connecteur IA (optionnel)'),
      boxes: [
        { icon: '✦', title: L('Connect an LLM provider', 'Connecter un fournisseur LLM'),
          how: L('Powers AI recommendations & video scripts; off by default; key encrypted; outbound restricted.', 'Alimente les recommandations IA et scripts vidéo ; désactivé par défaut ; clé chiffrée ; sortie restreinte.'),
          cfg: [
            L('In-app (Super Admin · AI Connector): provider (openai/anthropic/ollama), base_url, model, api_key (stored encrypted, never shown back), timeout 5–300 s, enabled (default off).', 'Dans l’app (Super Admin · Connecteur IA) : provider (openai/anthropic/ollama), base_url, model, api_key (chiffrée, jamais réaffichée), timeout 5–300 s, enabled (défaut désactivé).'),
            L('Use Test connection before enabling.', 'Utilisez Tester la connexion avant d’activer.'),
            L('SSRF guard: the connector cannot call private/internal addresses. For an internal LLM (e.g. Ollama on localhost), set env LLM_ALLOW_PRIVATE_NETWORKS=true.', 'Garde SSRF : le connecteur ne peut pas appeler d’adresses privées/internes. Pour un LLM interne (p. ex. Ollama local), définissez l’env LLM_ALLOW_PRIVATE_NETWORKS=true.'),
          ] },
      ],
    },
    {
      id: 'email', heading: L('9 · Email delivery', '9 · Envoi de courriels'),
      boxes: [
        { icon: '✉️', title: L('Email backend & sender addresses', 'Backend courriel et adresses d’expéditeur'),
          how: L('Sends invites, verification, unlock and notifications; production must use a real backend.', 'Envoie invitations, vérifications, déverrouillages et notifications ; la production doit utiliser un vrai backend.'),
          cfg: [
            L('EMAIL_BACKEND (env) — smtp | sendgrid | console (ses is accepted but not implemented → falls back to console).', 'EMAIL_BACKEND (env) — smtp | sendgrid | console (ses accepté mais non implémenté → retombe sur console).'),
            L('smtp needs SMTP_HOST/PORT/USER/PASSWORD/TLS; sendgrid needs SENDGRID_API_KEY.', 'smtp nécessite SMTP_HOST/PORT/USER/PASSWORD/TLS ; sendgrid nécessite SENDGRID_API_KEY.'),
            L('Senders FROM_EMAIL (default) + EMAIL_FROM_INVOICING/CASES/NOREPLY (each falls back to FROM_EMAIL).', 'Expéditeurs FROM_EMAIL (défaut) + EMAIL_FROM_INVOICING/CASES/NOREPLY (chacun retombe sur FROM_EMAIL).'),
            L('Production refuses to start with console. Super Admin can view/test the config in-app.', 'La production refuse de démarrer avec console. Le Super Admin peut voir/tester la config dans l’app.'),
          ] },
      ],
    },
    {
      id: 'storage', heading: L('10 · File storage', '10 · Stockage des fichiers'),
      boxes: [
        { icon: '📦', title: L('Where uploaded files live', 'Où vivent les fichiers téléversés'),
          how: L('Local disk by default; S3/Cloudflare R2 supported for durable storage.', 'Disque local par défaut ; S3/Cloudflare R2 pris en charge pour un stockage durable.'),
          cfg: [
            L('STORAGE_BACKEND (env) — local | s3 | r2 (azure/gcs accepted but not implemented → behave as local).', 'STORAGE_BACKEND (env) — local | s3 | r2 (azure/gcs acceptés mais non implémentés → se comportent comme local).'),
            L('STORAGE_LOCAL_PATH (default /app/uploads); R2/S3 use R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME.', 'STORAGE_LOCAL_PATH (défaut /app/uploads) ; R2/S3 utilisent R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME.'),
            L('Persistent volumes hold uploads (evidence + uploaded policies) and backups.', 'Des volumes persistants contiennent les téléversements (preuves + politiques) et les sauvegardes.'),
          ] },
      ],
    },
    {
      id: 'billing', heading: L('11 · Billing, plans & trials', '11 · Facturation, forfaits et essais'),
      boxes: [
        { icon: '💳', title: L('Plans, entitlements & trial mode', 'Forfaits, droits et mode d’essai'),
          how: L('Plans gate features and seats; a platform billing mode controls trials & locking.', 'Les forfaits conditionnent fonctions et sièges ; un mode de facturation plateforme gère essais et verrouillage.'),
          cfg: [
            L('Billing mode (platform default no_card_trial): no_card_trial (free trial then lock), card_trial (Stripe trial, auto-charge), charge_immediately. Trial days default 14.', 'Mode de facturation (défaut no_card_trial) : no_card_trial (essai puis verrouillage), card_trial (essai Stripe, prélèvement auto), charge_immediately. Jours d’essai défaut 14.'),
            L('Plans — tier (single_client/msp), monthly price, included frameworks, feature flags, seat/client caps. Managed under Plans & Pricing.', 'Forfaits — niveau (single_client/msp), prix mensuel, référentiels inclus, indicateurs de fonctions, plafonds de sièges/clients. Gérés sous Forfaits et tarifs.'),
            L('Enforced feature gates today: reports and import. (Other flags exist but aren’t enforced yet.)', 'Restrictions appliquées aujourd’hui : reports et import. (D’autres indicateurs existent mais ne sont pas encore appliqués.)'),
            L('Stripe — STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET (env). Without a secret key, checkout is SIMULATED (marks active, local invoice).', 'Stripe — STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET (env). Sans clé secrète, le paiement est SIMULÉ (marque actif, facture locale).'),
          ] },
      ],
    },
    {
      id: 'backup', heading: L('12 · Backup & restore', '12 · Sauvegarde et restauration'),
      boxes: [
        { icon: '🗄', title: L('Signed backups & safe restore', 'Sauvegardes signées et restauration sûre'),
          how: L('Export chosen data (and files); restore merges by key and only accepts trusted/signed bundles.', 'Exporte les données choisies (et fichiers) ; la restauration fusionne par clé et n’accepte que des sauvegardes de confiance/signées.'),
          cfg: [
            L('Categories: frameworks, plans, providers, tenants, compliance, support, billing, audit, policies (some scoped to chosen clients).', 'Catégories : référentiels, forfaits, fournisseurs, organisations, conformité, support, facturation, audit, politiques (certaines limitées aux clients choisis).'),
            L('Bundles are HMAC-signed with the app secret. Stored snapshots are trusted; an uploaded file must be signed by this system or it’s rejected.', 'Les sauvegardes sont signées (HMAC) avec le secret de l’app. Les instantanés stockés sont de confiance ; un fichier téléversé doit être signé par ce système, sinon refusé.'),
            L('Restore MERGES (never deletes); passwords/MFA secrets stripped; restored users must reset their password. Every restore is audit-logged.', 'La restauration FUSIONNE (ne supprime jamais) ; mots de passe/secrets MFA retirés ; les utilisateurs restaurés doivent réinitialiser leur mot de passe. Chaque restauration est journalisée.'),
            L('"Full backup" zips all data + every uploaded file with a manifest. Super Admin only.', 'La « sauvegarde complète » archive toutes les données + chaque fichier téléversé avec un manifeste. Super Admin seulement.'),
          ] },
      ],
    },
    {
      id: 'security', heading: L('13 · Security posture', '13 · Posture de sécurité'),
      boxes: [
        { icon: '🛡️', title: L('HTTPS, headers, docs & CORS', 'HTTPS, en-têtes, doc et CORS'),
          how: L('Caddy terminates HTTPS and sets security headers; API docs are off in production.', 'Caddy termine le HTTPS et pose les en-têtes de sécurité ; la doc API est désactivée en production.'),
          cfg: [
            L('Caddy: automatic Let’s Encrypt HTTPS, HSTS, CSP, X-Frame-Options DENY, nosniff, Referrer-Policy, Server header removed (domain + contact email in the Caddyfile).', 'Caddy : HTTPS Let’s Encrypt automatique, HSTS, CSP, X-Frame-Options DENY, nosniff, Referrer-Policy, en-tête Server retiré (domaine + courriel dans le Caddyfile).'),
            L('nginx: computes the real client IP (used by rate limiting), site-wide noindex, robots.txt = Disallow all.', 'nginx : calcule la vraie IP client (utilisée par la limite de débit), noindex sur tout le site, robots.txt = tout interdire.'),
            L('API docs/openapi disabled when ENVIRONMENT=production; CORS limited to known origins, methods and headers.', 'Doc API/openapi désactivées quand ENVIRONMENT=production ; CORS limité aux origines, méthodes et en-têtes connus.'),
          ] },
      ],
    },
    {
      id: 'modules', heading: L('14 · Other modules', '14 · Autres modules'),
      boxes: [
        { icon: '🧩', title: L('Support · Notifications · Training · Marketplace · Partners · Agreement', 'Support · Notifications · Formation · Place de marché · Partenaires · Entente'),
          how: L('Supporting features, each role-gated.', 'Fonctions complémentaires, chacune restreinte par rôle.'),
          cfg: [
            L('Support — users raise cases (≤25 MB); EVA reviews. Module enable + categories set by Super Admin.', 'Support — les utilisateurs ouvrent des cas (≤25 Mo) ; EVA traite. Activation + catégories réglées par le Super Admin.'),
            L('Notifications — role-aware "action required" bell; no config. Training videos — per framework/control (≤200 MB); AI scripts need the connector; Super-Admin managed.', 'Notifications — cloche « action requise » selon le rôle ; aucune config. Vidéos — par référentiel/contrôle (≤200 Mo) ; scripts IA via le connecteur ; gérées par le Super Admin.'),
            L('Marketplace — service-provider directory (providers self-register pending, EVA authorizes). Partners — MSP margin engine (terms set by Super Admin).', 'Place de marché — annuaire de fournisseurs (inscription en attente, EVA autorise). Partenaires — moteur de marge MSP (conditions réglées par le Super Admin).'),
            L('Agreement gate — bilingual subscription agreement accepted at registration; recorded with version + IP.', 'Entente — entente d’abonnement bilingue acceptée à l’inscription ; enregistrée avec version + IP.'),
          ] },
      ],
    },
  ]

  const envRows: [string, string, string][] = [
    ['SECRET_KEY', L('Signs tokens, encrypts secrets', 'Signe les jetons, chiffre les secrets'), L('required, ≥32 chars', 'requis, ≥32 car.')],
    ['ENVIRONMENT', L('Dev vs prod hardening', 'Durcissement dev/prod'), 'production'],
    ['FRONTEND_URL', L('Public URL for links + CORS', 'URL publique liens + CORS'), 'https://…'],
    ['DATABASE_URL', 'Postgres', L('change the password', 'changez le mot de passe')],
    ['BASIC_AUTH_USER / PASSWORD', L('Site access gate', 'Portail d’accès'), L('required', 'requis')],
    ['ACCESS_TOKEN_EXPIRE_MINUTES', L('Access token life', 'Durée jeton d’accès'), '15 (→480 = 8h)'],
    ['REFRESH_TOKEN_EXPIRE_DAYS', L('Refresh token life', 'Durée refresh'), '30'],
    ['EMAIL_BACKEND + SMTP/SendGrid', L('Email delivery', 'Envoi courriel'), L('smtp/sendgrid in prod', 'smtp/sendgrid en prod')],
    ['STORAGE_BACKEND + R2_*', L('File storage', 'Stockage fichiers'), 'local | r2/s3'],
    ['STRIPE_SECRET_KEY / WEBHOOK_SECRET', L('Real payments', 'Paiements réels'), L('blank = simulated', 'vide = simulé')],
    ['LLM_ALLOW_PRIVATE_NETWORKS', L('Allow internal LLM', 'Autoriser LLM interne'), 'false'],
  ]

  const caveats: string[] = [
    L('MFA is opt-in even for admin roles — only enforced once a user enables it. No forced enrollment.', 'La MFA est sur activation même pour les rôles admin — imposée seulement une fois activée. Aucune inscription forcée.'),
    L('Lockout, password length, rate limits and MFA-required roles are code constants, not env/in-app settings.', 'Verrouillage, longueur de mot de passe, limites et rôles MFA requis sont des constantes de code, pas des réglages env/dans l’app.'),
    L('EMAIL_BACKEND=ses and STORAGE_BACKEND=azure/gcs are accepted but not implemented (fall back to console / local).', 'EMAIL_BACKEND=ses et STORAGE_BACKEND=azure/gcs sont acceptés mais non implémentés (retombent sur console / local).'),
    L('Self-audit auto-accept happens on the upload path; submitting an existing draft routes to review even on self-audit orgs.', 'L’auto-acceptation en auto-audit se fait sur le chemin téléversement ; soumettre un brouillon existant part en revue même sur les orgs en auto-audit.'),
    L('Plan flags msp_review/audit_logs/api exist but aren’t enforced yet; only reports and import are gated.', 'Les indicateurs msp_review/audit_logs/api existent mais ne sont pas encore appliqués ; seuls reports et import sont restreints.'),
  ]

  return (
    <div>
      <style>{`
        .cg-box{border:1px solid var(--border, rgba(120,140,170,.25));border-radius:11px;background:var(--card2, rgba(255,255,255,.03));margin:8px 0;overflow:hidden}
        .cg-box>summary{list-style:none;cursor:pointer;display:flex;align-items:flex-start;gap:9px;padding:11px 13px}
        .cg-box>summary::-webkit-details-marker{display:none}
        .cg-ic{font-size:16px;width:22px;text-align:center;flex:0 0 auto;margin-top:1px}
        .cg-sm{flex:1;min-width:0}
        .cg-ttl{font-weight:700;color:var(--text);font-size:13.5px}
        .cg-how{display:block;font-size:12.5px;color:var(--text2);margin-top:2px}
        .cg-chev{margin-left:auto;color:var(--text3,#8a93a3);transition:transform .15s;font-size:12px;flex:0 0 auto;margin-top:2px}
        .cg-box[open] .cg-chev{transform:rotate(90deg)}
        .cg-cfg{padding:0 14px 13px 44px}
        .cg-lbl{font-size:11px;font-weight:700;color:var(--eva-blue,#2E5FA3);text-transform:uppercase;letter-spacing:.04em;margin:2px 0 4px}
        .cg-cfg ul{margin:0;padding-left:16px} .cg-cfg li{font-size:12.5px;color:var(--text2);margin:5px 0;line-height:1.55}
        .cg-sechd{display:flex;align-items:center;gap:8px;margin:22px 0 2px}
        .cg-bar{width:4px;height:18px;border-radius:3px;background:var(--eva-blue,#2E5FA3)}
        .cg-table{width:100%;border-collapse:collapse;margin-top:10px;font-size:12px}
        .cg-table th,.cg-table td{padding:7px 9px;border-bottom:1px solid var(--border,rgba(120,140,170,.2));text-align:left;vertical-align:top}
        .cg-table th{color:var(--text);font-weight:700}
        .cg-warn{border:1px solid #f0d9a8;border-left:4px solid #D97706;border-radius:10px;padding:10px 14px;margin:12px 0;background:rgba(217,151,9,.06)}
        .cg-warn li{font-size:12.5px;color:var(--text2);margin:5px 0}
      `}</style>

      <div className="page-title">{L('Configuration & How it works', 'Configuration et fonctionnement')}</div>
      <div className="page-sub" style={{ marginBottom: 8 }}>
        {L('Super Admin reference. For each element: how it works, and the configuration it needs. Click to expand.',
           'Référence Super Admin. Pour chaque élément : comment ça marche, et la configuration nécessaire. Cliquez pour déplier.')}
      </div>
      <div className="page-sub" style={{ background: 'var(--card2, rgba(46,95,163,.08))', border: '1px solid var(--border, rgba(120,140,170,.2))', borderRadius: 10, padding: '10px 12px', marginBottom: 12 }}>
        ⚙️ {L('Two kinds of settings: environment variables set at deploy (need a redeploy to change) vs in-app settings a role can change live. Each box says which.',
              'Deux types de réglages : variables d’environnement définies au déploiement (redéploiement requis) vs réglages dans l’app modifiables en direct. Chaque boîte le précise.')}
      </div>

      {sections.map(sec => (
        <div key={sec.id}>
          <div className="cg-sechd"><span className="cg-bar" /><span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>{sec.heading}</span></div>
          {sec.boxes.map((b, i) => (
            <details className="cg-box" key={i}>
              <summary>
                <span className="cg-ic">{b.icon}</span>
                <span className="cg-sm"><span className="cg-ttl">{b.title}</span><span className="cg-how">{b.how}</span></span>
                <span className="cg-chev">▸</span>
              </summary>
              <div className="cg-cfg">
                <div className="cg-lbl">{L('Configuration', 'Configuration')}</div>
                <ul>{b.cfg.map((c, j) => <li key={j}>{c}</li>)}</ul>
              </div>
            </details>
          ))}
        </div>
      ))}

      <div className="cg-sechd"><span className="cg-bar" /><span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>{L('15 · Environment variables — cheat sheet', '15 · Variables d’environnement — aide-mémoire')}</span></div>
      <div className="page-sub" style={{ marginTop: 0 }}>{L('Set in the server .env (or container env). Changing any requires a redeploy.', 'À définir dans le .env serveur (ou l’env du conteneur). Tout changement nécessite un redéploiement.')}</div>
      <table className="cg-table">
        <thead><tr><th>{L('Variable', 'Variable')}</th><th>{L('Purpose', 'Rôle')}</th><th>{L('Default / note', 'Défaut / note')}</th></tr></thead>
        <tbody>
          {envRows.map((r, i) => (
            <tr key={i}><td><code>{r[0]}</code></td><td>{r[1]}</td><td>{r[2]}</td></tr>
          ))}
        </tbody>
      </table>

      <div className="cg-sechd"><span className="cg-bar" style={{ background: '#D97706' }} /><span style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>{L('Important caveats', 'Mises en garde importantes')}</span></div>
      <div className="cg-warn"><ul>{caveats.map((c, i) => <li key={i}>{c}</li>)}</ul></div>

      <div className="page-sub" style={{ marginTop: 16, fontStyle: 'italic' }}>
        {L('Grounded in the live code. Defaults and behaviors can change with new releases — re-check after major updates.',
           'Basé sur le code réel. Les défauts et comportements peuvent changer avec les nouvelles versions — revérifiez après une mise à jour majeure.')}
      </div>
    </div>
  )
}
